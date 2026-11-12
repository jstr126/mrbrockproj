"""Pre-render synthetic training canvases into a folder (same format as capture.py).

    python make_synthetic.py --n 20000 --out data/synth
    python make_synthetic.py --n 12000 --out data/synth_mix --neg-frac 0.5 --heavy-frac 0.5
    python make_synthetic.py --n 10000 --out data/synth_junk --neg-frac 0.5 --junk-frac 0.6 --heavy-frac 0.4
"""
import argparse
import csv
import json
import os
from multiprocessing import Pool
from pathlib import Path

import cv2
import numpy as np

from bolt_sizer.labels import append_label
from bolt_sizer.synth import make_canvas, synth_bolt, synth_junk, synth_not_bolt


def render(args):
    cv2.setNumThreads(1)
    i, seed, out, neg_frac, junk_frac, heavy_frac = args
    rng = np.random.default_rng([seed, i])
    sprite = synth_bolt
    if rng.uniform() < neg_frac:
        sprite = synth_junk if rng.uniform() < junk_frac else synth_not_bolt
    canvas, row, mask = make_canvas(rng, sprite, heavy=rng.uniform() < heavy_frac, return_mask=True)
    name = f"synth_{i:06d}.jpg"
    cv2.imwrite(str(Path(out) / name), canvas, [cv2.IMWRITE_JPEG_QUALITY, 93])
    mask_name = f"masks/synth_{i:06d}.png"
    cv2.imwrite(str(Path(out) / mask_name), mask)
    return {"file": name, "mask": mask_name, **row}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20000)
    ap.add_argument("--out", default="data/synth")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--neg-frac", type=float, default=0.0, help="fraction of non-bolt scenes")
    ap.add_argument("--junk-frac", type=float, default=0.0,
                    help="of the non-bolt scenes, the fraction that are bolt-shaped junk")
    ap.add_argument("--heavy-frac", type=float, default=0.0, help="fraction with heavy degradation")
    ap.add_argument("--resume", action="store_true", help="continue a matching render without repeating saved rows")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args()

    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / "masks").mkdir(exist_ok=True)
    labels_path = Path(a.out) / "labels.csv"
    config = {k: getattr(a, k) for k in ("n", "seed", "neg_frac", "junk_frac", "heavy_frac")}
    config_path = Path(a.out) / "render.json"
    done = set()
    if a.resume and labels_path.exists():
        if config_path.exists() and json.loads(config_path.read_text()) != config:
            raise ValueError('render parameters differ; choose another output folder')
        for row in csv.DictReader(open(labels_path)):
            if not row.get('mask') or not (Path(a.out) / row['mask']).exists():
                raise ValueError('resume requires existing masks for every labeled image')
            done.add(int(Path(row['file']).stem.split('_')[-1]))
    else:
        labels_path.unlink(missing_ok=True)
    config_path.write_text(json.dumps(config, indent=2))
    jobs = [(i, a.seed, a.out, a.neg_frac, a.junk_frac, a.heavy_frac)
            for i in range(a.n) if i not in done]
    with Pool(a.workers) as pool:
        for k, row in enumerate(pool.imap(render, jobs, chunksize=16), len(done) + 1):
            append_label(a.out, row)
            if k % 500 == 0:
                print(f"{k}/{a.n}", flush=True)
    print(f"wrote {a.n} canvases to {a.out}")


if __name__ == "__main__":
    main()
