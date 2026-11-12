"""Build a test set of raw camera frames: real bolt photos (cut out of
Wikimedia Commons images by make_cutouts.py) and real non-bolt objects,
composited onto the checkerboard and put through the camera simulator,
heavy degradation by default.

    python tools/make_testset.py --out data/test_web_heavy
    python tools/make_testset.py --out data/test_web_normal --normal
    python tools/make_testset.py --source synth --out data/test_synth_heavy
    python tools/make_testset.py --source catalog --out data/test_catalog_normal --normal
    python tools/make_testset.py --cutouts data/ai --out data/test_ai_heavy   # other cutout sets

--source catalog renders every active catalog thread x head type at its
shortest, middle and longest length (plus non-bolts), so every bin is tested.

Each bolt cutout is scaled to an exact standard size: its measured length-to-
diameter ratio picks the standard (thread, length) pairs it can represent,
and one is chosen per scene. Frames are saved unrectified, so the benchmark
times the whole pipeline (board detection included).
"""
import argparse
import json
import os
import re
import sys
from multiprocessing import Pool
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bolt_sizer.labels import append_label
from bolt_sizer.standards import HEAD_TYPE_NAMES, HEAD_TYPES, THREADS, METRIC, IMPERIAL, MAX_LENGTH_MM, lengths_mm
from bolt_sizer.synth import (RES, NOT_BOLT, bolt_labels, render_bolt, render_camera, synth_bolt,
                              synth_junk, synth_not_bolt)

WEB = Path("data/web")
# Plausible real sizes (longest side, mm) for the non-bolt photos.
NOT_BOLT_SIZES = [(r"coin|penny|cent|quarter", (17, 31)), (r"batter|energizer|remington|varta|aa", (44, 51)),
                  (r"nut|arfisa|mutter|tuerca", (8, 25)), (r"washer|scheibe", (8, 30)),
                  (r"dowel|kołki|pin|peg", (15, 60)), (r".", (12, 70))]


def _systems(entry):
    return [METRIC] if entry["system"] == "metric" else [METRIC, IMPERIAL]


def size_options(entry):
    """Standard (thread, length) pairs this bolt photo can be scaled to."""
    opts = []
    for sys_ in _systems(entry):
        for t in THREADS[sys_]:
            L = entry["ratio"] * t.diameter_mm
            if L > MAX_LENGTH_MM:
                continue
            for nominal in lengths_mm(sys_):
                if abs(L - nominal) / nominal < 0.05:
                    opts.append((t, nominal, L))
    return opts


def web_sprite(rng, entry, rgba, parts=None):
    """A photo cutout as a sprite at a real-world size (see module docstring)."""
    if entry.get("view") == "angled":
        # Any thread width that keeps it on the board; its length is unknown.
        threads = [t for s in _systems(entry) for t in THREADS[s]
                   if entry["ratio"] * t.diameter_mm <= MAX_LENGTH_MM]
        thread = threads[rng.integers(len(threads))]
        scale = thread.diameter_mm * RES / entry["shank_px"]
        labels = {"label": f"{HEAD_TYPE_NAMES[entry['class']]} (angled photo, size not scored)",
                  "is_bolt": 1, "system": "", "diameter_mm": "", "length_mm": "",
                  "head_type": HEAD_TYPES.index(entry["class"])}
    elif entry["class"] != "not_bolt":
        opts = size_options(entry)
        thread, nominal, _ = opts[rng.integers(len(opts))]
        scale = thread.diameter_mm * RES / entry["shank_px"]
        labels = bolt_labels(thread, entry["class"], nominal)
    else:
        lo, hi = next(r for pat, r in NOT_BOLT_SIZES if re.search(pat, entry["source"], re.I))
        scale = rng.uniform(lo, hi) * RES / max(rgba.shape[:2])
        labels = dict(NOT_BOLT, label="not a bolt")
    img = cv2.resize(rgba, None, fx=scale, fy=scale,
                     interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
    bgr = img[..., :3].astype(np.float32)
    alpha = img[..., 3].astype(np.float32) / 255
    centre = np.array([img.shape[1] / 2, img.shape[0] / 2])
    result = bgr, alpha, centre, {**labels, "source": entry["source"]}
    if parts is not None:
        return (*result, cv2.resize(parts, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR))
    return result


def catalog_jobs():
    """(system, thread name, head, length) for every active catalog combination."""
    jobs = []
    for system, threads in THREADS.items():
        for t in threads:
            d = t.diameter_mm
            longest = min(MAX_LENGTH_MM, max(25.0, 20 * d))
            ok = [L for L in lengths_mm(system) if 2 * d <= L <= longest + 1e-6]
            for L in sorted({ok[0], ok[len(ok) // 2], ok[-1]}):
                for head in HEAD_TYPES:
                    jobs.append((system, t.name, head, L))
    return jobs


def catalog_sprite(rng, entry):
    system, name, head, L = entry
    thread = next(t for t in THREADS[system] if t.name == name)
    bgr, alpha, centre = render_bolt(rng, thread, head, L)
    return bgr, alpha, centre, {**bolt_labels(thread, head, L), "source": "catalog"}


def render(job):
    cv2.setNumThreads(1)
    i, seed, out, kind, entry, heavy, cutouts = job
    rng = np.random.default_rng([seed, i])
    if kind == "web":
        rgba = cv2.imread(str(Path(cutouts) / "cutouts" / entry["file"]), cv2.IMREAD_UNCHANGED)
        sprite_fn = lambda r: web_sprite(r, entry, rgba)
    elif kind == "catalog":
        sprite_fn = lambda r: catalog_sprite(r, entry)
    elif kind == "empty":
        sprite_fn = lambda r: None
    elif kind == "synth_junk":
        sprite_fn = synth_junk
    elif kind == "synth_bolt":
        sprite_fn = synth_bolt
    else:
        sprite_fn = synth_not_bolt
    frame, _, _, labels = render_camera(rng, sprite_fn, heavy=heavy)
    name = f"test_{i:05d}.jpg"
    cv2.imwrite(str(Path(out) / name), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return {"file": name, "source": labels.get("source", kind), **labels}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/test_web_heavy")
    ap.add_argument("--source", choices=["web", "synth", "catalog", "junk"], default="web")
    ap.add_argument("--cutouts", default=str(WEB), help="folder with cutouts.json + cutouts/ (web source)")
    ap.add_argument("--split", choices=["all", "train", "heldout"], default="all")
    ap.add_argument("--normal", action="store_true", help="normal instead of heavy degradation")
    ap.add_argument("--per-bolt", type=int, default=12, help="scenes per bolt photo")
    ap.add_argument("--per-not-bolt", type=int, default=5, help="scenes per non-bolt photo")
    ap.add_argument("--empty", type=int, default=30, help="empty-board scenes")
    ap.add_argument("--n", type=int, default=600, help="scenes for --source synth")
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args()
    heavy = not a.normal

    jobs = []
    if a.source == "web":
        if a.split == "all":
            cutouts = json.load(open(Path(a.cutouts) / "cutouts.json"))
        else:
            manifest = json.load(open(Path(a.cutouts) / "split.json"))
            cutouts = [e for e in manifest["entries"] if e["split"] == a.split]
        for e in cutouts:
            if e["class"] != "not_bolt" and e.get("view") != "angled" and not size_options(e):
                print(f"skipping {e['file']}: no standard size fits L/d {e['ratio']:.2f}")
                continue
            k = a.per_bolt if e["class"] != "not_bolt" else a.per_not_bolt
            jobs += [("web", e)] * k
        jobs += [("empty", None)] * (a.empty if a.cutouts == str(WEB) else 0)
    elif a.source == "junk":
        jobs = [("synth_junk", None)] * a.n
    elif a.source == "catalog":
        jobs = [("catalog", e) for e in catalog_jobs()]
        jobs += [("synth_not_bolt", None)] * (len(jobs) // 4)
    else:
        jobs = [("synth_bolt" if i % 4 else "synth_not_bolt", None) for i in range(a.n)]

    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / "labels.csv").unlink(missing_ok=True)
    args = [(i, a.seed, a.out, k, e, heavy, a.cutouts) for i, (k, e) in enumerate(jobs)]
    with Pool(a.workers) as pool:
        for row in pool.imap(render, args, chunksize=4):
            append_label(a.out, row)
    print(f"wrote {len(jobs)} frames to {a.out}")


if __name__ == "__main__":
    main()
