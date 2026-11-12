"""Cut real bolts (and non-bolt objects) out of downloaded Wikimedia Commons
photos, for compositing into the test set.

    python tools/make_cutouts.py   -> data/web/cutouts/*.png + data/web/cutouts.json
    python tools/make_cutouts.py --remeasure   # refresh size fields only

Each selected photo is segmented with GrabCut; photos with several objects
are split into one cutout per object. For bolts we measure the shank width
and the length under the head (in photo pixels) along the bolt's axis, so a
cutout can later be scaled to an exact standard size.
"""
import argparse
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

WEB = Path("data/web")

# candidates.json index -> (class, system the photo's thread can be scaled to)
# class is a head type for bolts, or "not_bolt". "metric" = DIN / known metric photo.
SELECT = {
    0: ("hex", "any"), 1: ("hex", "any"),
    165: ("hex", "metric"), 166: ("hex", "metric"), 167: ("hex", "metric"),
    168: ("hex", "metric"), 169: ("hex", "metric"),
    35: ("socket_cap", "any"), 37: ("socket_cap", "any"),
    181: ("socket_cap", "metric"), 182: ("socket_cap", "metric"),
    40: ("button", "any"), 41: ("button", "any"), 45: ("button", "any"), 46: ("button", "any"),
    60: ("carriage", "any"),
    91: ("flat", "metric"),
    # not bolts: wood/drywall screws, nuts, washers, coins, pins, batteries
    77: ("not_bolt", None), 78: ("not_bolt", None), 80: ("not_bolt", None), 81: ("not_bolt", None),
    84: ("not_bolt", None), 85: ("not_bolt", None), 86: ("not_bolt", None), 87: ("not_bolt", None),
    107: ("not_bolt", None), 116: ("not_bolt", None),
    259: ("not_bolt", None), 270: ("not_bolt", None),
    303: ("not_bolt", None), 304: ("not_bolt", None), 322: ("not_bolt", None),
    353: ("not_bolt", None), 356: ("not_bolt", None), 363: ("not_bolt", None),
    375: ("not_bolt", None), 376: ("not_bolt", None), 379: ("not_bolt", None), 380: ("not_bolt", None),
    385: ("not_bolt", None), 388: ("not_bolt", None), 390: ("not_bolt", None),
    391: ("not_bolt", None), 395: ("not_bolt", None), 398: ("not_bolt", None),
}
# Cutouts that segment badly or are seen head-on (can't be measured).
DROP = {"091_0"}
# Bolts photographed at a three-quarter angle: the shank is foreshortened, so
# their length is unknown. They only test bolt / not-a-bolt, never size.
ANGLED = {"000_0", "001_0", "035_0", "040_0", "041_0", "045_0", "046_0", "091_1"}


def load(path):
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    if img.shape[2] == 4:
        a = img[..., 3:] / 255.0
        img = (img[..., :3] * a + 255 * (1 - a)).astype(np.uint8)
    return img


def segment(img):
    """GrabCut seeded by colour: the frame border is background, and bright
    near-white or saturated orange (studio vignette) pixels start as probable
    background; everything else starts as probable foreground."""
    h, w = img.shape[:2]
    m = max(2, int(0.02 * min(h, w)))
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    sat, val = hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    border = np.median(np.concatenate([img[:m].reshape(-1, 3), img[-m:].reshape(-1, 3),
                                       img[:, :m].reshape(-1, 3), img[:, -m:].reshape(-1, 3)]), 0)
    like_border = np.abs(img.astype(int) - border).sum(2) < 45
    bg_like = like_border | ((val > 225) & (sat < 35)) | ((sat > 90) & (val > 150))
    mask = np.where(bg_like, cv2.GC_PR_BGD, cv2.GC_PR_FGD).astype(np.uint8)
    mask[:m], mask[-m:], mask[:, :m], mask[:, -m:] = cv2.GC_BGD, cv2.GC_BGD, cv2.GC_BGD, cv2.GC_BGD
    bgd, fgd = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(img, mask, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
    fg = np.isin(mask, (cv2.GC_FGD, cv2.GC_PR_FGD)).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    return fg


def components(fg, min_frac=0.15):
    n, lab, stats, _ = cv2.connectedComponentsWithStats(fg)
    areas = stats[1:, cv2.CC_STAT_AREA]
    if len(areas) == 0:
        return []
    big = areas.max()
    out = []
    for k in np.argsort(-areas):
        if areas[k] < min_frac * big:
            break
        comp = (lab == k + 1).astype(np.uint8)
        out.append(cv2.morphologyEx(comp, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)))
    return out


def measure_bolt(comp, return_mask=False):
    """Shank width and length under the head, in px, along the principal axis.
    Returns (shank_px, length_px, flat_total_px, axis_angle_deg) or None."""
    ys, xs = np.nonzero(comp)
    if len(xs) < 20:
        return None
    pts = np.stack([xs, ys], 1).astype(np.float64)
    mean = pts.mean(0)
    _, _, vt = np.linalg.svd(pts - mean, full_matrices=False)
    ax, perp = vt[0], vt[1]
    t = (pts - mean) @ ax
    s = (pts - mean) @ perp
    t0, t1 = t.min(), t.max()
    bins = np.arange(np.floor(t0), np.ceil(t1) + 1)
    idx = np.digitize(t, bins) - 1
    width = np.zeros(len(bins))
    for i in range(len(bins)):
        sel = idx == i
        if sel.any():
            width[i] = s[sel].max() - s[sel].min()
    n = len(width)
    if n < 20:
        return None
    width = np.convolve(width, np.ones(3) / 3, mode="same")
    # head is the end whose first 15% is widest
    k = max(3, n // 7)
    head_first = width[:k].mean() > width[-k:].mean()
    if not head_first:
        width = width[::-1]
    shank = float(np.percentile(width[int(0.45 * n):int(0.9 * n)], 40))
    # Ignore narrow tip pixels before the wide part of the head.
    wide = np.flatnonzero(width[:max(k, int(0.45 * n))] > 1.18 * shank)
    if shank <= 0 or not len(wide):
        return None
    head_len = int(wide[-1] + 1)
    result = shank, float(n - head_len), float(n), float(np.degrees(np.arctan2(ax[1], ax[0]))), head_first
    if not return_mask:
        return result
    along = t - t0 if head_first else t1 - t
    parts = np.zeros((*comp.shape, 2), np.float32)
    parts[ys, xs, 0] = along < head_len
    parts[ys, xs, 1] = along >= head_len
    return result, parts



def cut(job):
    idx, cls, system, c = job
    img = load(WEB / "raw" / c["file"])
    fg = segment(img)
    meta = []
    for j, comp in enumerate(components(fg)):
        x, y, w, h = cv2.boundingRect(comp)
        pad = 4
        x0, y0 = max(0, x - pad), max(0, y - pad)
        x1, y1 = min(img.shape[1], x + w + pad), min(img.shape[0], y + h + pad)
        alpha = cv2.GaussianBlur(comp.astype(np.float32), (0, 0), 0.8)[y0:y1, x0:x1]
        rgba = np.dstack([img[y0:y1, x0:x1], (alpha * 255).astype(np.uint8)])
        name = f"{idx:03d}_{j}.png"
        if name[:-4] in DROP:
            continue
        entry = {"file": name, "class": cls, "system": system, "source": c["title"],
                 "page": c["page"], "license": c["license"]}
        if cls != "not_bolt":
            size = bolt_size(name, cls, comp[y0:y1, x0:x1])
            if size is None:
                continue
            entry.update(size)
        cv2.imwrite(str(WEB / "cutouts" / name), rgba)
        meta.append(entry)
    return meta


def bolt_size(name, cls, comp):
    """cutouts.json size fields: length is under the head (overall for flat heads)."""
    m = measure_bolt(comp)
    if m is None:
        return None
    shank, length, total, _, _ = m
    length = total if cls == "flat" else length
    return {"shank_px": shank, "length_px": length, "ratio": length / shank,
            "view": "angled" if name[:-4] in ANGLED else "side"}


def remeasure():
    """Re-measure the existing cutouts in place, without re-running GrabCut."""
    meta = json.load(open(WEB / "cutouts.json"))
    for e in meta:
        if e["class"] == "not_bolt":
            continue
        alpha = cv2.imread(str(WEB / "cutouts" / e["file"]), cv2.IMREAD_UNCHANGED)[..., 3]
        e.update(bolt_size(e["file"], e["class"], (alpha >= 128).astype(np.uint8)))
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--remeasure", action="store_true",
                    help="update the size fields of the existing cutouts only")
    a = ap.parse_args()
    if a.remeasure:
        meta = remeasure()
    else:
        cands = json.load(open(WEB / "candidates.json"))
        out_dir = WEB / "cutouts"
        out_dir.mkdir(parents=True, exist_ok=True)
        for p in out_dir.glob("*.png"):
            p.unlink()
        jobs = [(idx, cls, system, cands[idx]) for idx, (cls, system) in SELECT.items()]
        with Pool(4) as pool:
            meta = [e for part in pool.map(cut, jobs) for e in part]
    json.dump(meta, open(WEB / "cutouts.json", "w"), indent=1)
    bolts = [m for m in meta if m["class"] != "not_bolt"]
    print(f"{len(meta)} cutouts ({len(bolts)} bolts, {len(meta) - len(bolts)} not-bolts)")
    for m in bolts:
        print(f"  {m['file']} {m['class']:<10} {m['view']:<6} shank {m['shank_px']:.0f}px  "
              f"L/d {m['ratio']:.2f}  {m['source'][5:45]}")


if __name__ == "__main__":
    main()
