"""Split cutouts by source photo, build training masks and render web canvases."""
import argparse
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bolt_sizer.labels import append_label
from bolt_sizer.synth import make_canvas
from tools.make_cutouts import measure_bolt
from tools.make_testset import size_options, web_sprite


def prepare(root, seed=2026):
    entries = json.loads((root / 'cutouts.json').read_text())
    rng = np.random.default_rng(seed)
    groups = {}
    for e in entries:
        groups.setdefault(e['class'], set()).add(e['source'])
    train = set()
    for cls in sorted(groups):
        photos = rng.permutation(sorted(groups[cls]))
        train.update(photos[:len(photos) // 2])
    (root / 'masks').mkdir(exist_ok=True)
    for e in entries:
        e['split'] = 'train' if e['source'] in train else 'heldout'
        rgba = cv2.imread(str(root / 'cutouts' / e['file']), cv2.IMREAD_UNCHANGED)
        parts = np.zeros((*rgba.shape[:2], 2), np.float32)
        if e['class'] != 'not_bolt':
            result = measure_bolt((rgba[..., 3] >= 128).astype(np.uint8), return_mask=True)
            if result is None:
                raise ValueError(f"Cannot measure {e['file']}; inspect cutout")
            _, parts = result
        mask = (parts[..., 0] + 2 * parts[..., 1]).astype(np.uint8)
        e['mask'] = f"masks/{e['file']}"
        cv2.imwrite(str(root / e['mask']), mask)
    manifest = {'seed': seed, 'group_key': 'source', 'entries': entries}
    (root / 'split.json').write_text(json.dumps(manifest, indent=2))
    assert not {e['source'] for e in entries if e['split'] == 'train'} & {e['source'] for e in entries if e['split'] == 'heldout'}
    for part in ('train', 'heldout'):
        es = [e for e in entries if e['split'] == part]
        print(part, len({e['source'] for e in es}), 'photos,', sum(e['class'] != 'not_bolt' for e in es), 'bolt cutouts')
    return entries


def render(job):
    i, seed, out, root, entries = job
    cv2.setNumThreads(1)
    rng = np.random.default_rng([seed, i])
    # Balanced objects, independently of how many cutouts came from each photo.
    positive = i % 3 != 0
    options = [e for e in entries if (e['class'] != 'not_bolt') == positive]
    entry = options[int(rng.integers(len(options)))]
    root = Path(root)
    rgba = cv2.imread(str(root / 'cutouts' / entry['file']), cv2.IMREAD_UNCHANGED)
    mask = cv2.imread(str(root / entry['mask']), cv2.IMREAD_GRAYSCALE)
    parts = np.stack([mask == 1, mask == 2], -1).astype(np.float32)
    sprite = lambda r: web_sprite(r, entry, rgba, parts)
    canvas, row, mask = make_canvas(rng, sprite, heavy=rng.random() < .35, return_mask=True)
    file, mfile = f'web2_{i:06d}.jpg', f'masks/web2_{i:06d}.png'  # web_ = stale-length build
    cv2.imwrite(str(Path(out) / file), canvas, [cv2.IMWRITE_JPEG_QUALITY, 93])
    cv2.imwrite(str(Path(out) / mfile), mask)
    return dict(row, file=file, mask=mfile, source=entry['source'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, default=Path('data/web'))
    ap.add_argument('--out', type=Path, default=Path('data/train_web'))
    ap.add_argument('--n', type=int, default=4000)
    ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()
    entries = prepare(a.root)
    # Angled photos have no usable size label, and the camera never sees that view.
    entries = [e for e in entries if e['split'] == 'train' and
               (e['class'] == 'not_bolt' or (e['view'] == 'side' and size_options(e)))]
    (a.out / 'masks').mkdir(parents=True, exist_ok=True)
    (a.out / 'labels.csv').unlink(missing_ok=True)
    jobs = [(i, 31415, str(a.out), str(a.root), entries) for i in range(a.n)]
    with Pool(a.workers) as pool:
        for i, row in enumerate(pool.imap(render, jobs, chunksize=8), 1):
            append_label(a.out, row)
            if i % 500 == 0:
                print(i, '/', a.n, flush=True)


if __name__ == '__main__':
    main()
