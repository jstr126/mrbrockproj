"""Fit outline-to-mm calibration on the checkpoint's validation canvases only."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bolt_sizer.infer import BoltSizer
from bolt_sizer.measure import outline_size
from bolt_sizer.standards import HEAD_TYPES


def fit_linear(measured, truth):
    gains, offsets, errors = [], [], []
    for i in range(2):
        x, y = measured[:, i], truth[:, i]
        keep = np.isfinite(x) & np.isfinite(y)
        for _ in range(4):
            design = np.stack([x[keep], np.ones(keep.sum())], 1)
            gain, offset = np.linalg.lstsq(design, y[keep], rcond=None)[0]
            residual = y - (gain * x + offset)
            mad = np.median(np.abs(residual[keep] - np.median(residual[keep])))
            keep = np.abs(residual) < max(3 * 1.4826 * mad, .3 if i == 0 else 1.)
        gains.append(float(gain))
        offsets.append(float(offset))
        errors.append(float(np.mean(np.abs(y - (gain * x + offset)))))
    return {'gain': gains, 'offset': offsets, 'validation_mae_mm': errors}


def fit_fusion(geometry, regression, truth):
    """Choose one blend per dimension from validation errors, with outlier caps."""
    weights = []
    for i in range(2):
        candidates = np.linspace(.05, .95, 19)
        scores = []
        for weight in candidates:
            err = np.abs(weight * geometry[:, i] + (1 - weight) * regression[:, i] - truth[:, i])
            scores.append(np.minimum(err, np.percentile(err, 95)).mean())
        weights.append(float(candidates[int(np.argmin(scores))]))
    return weights


def calibrate(model_path, ckpt_path, limit=0):
    # Import training dependencies here, never from the Pi runtime.
    import torch
    from train import split, exposure_keys, initializer_sources
    ckpt = torch.load(ckpt_path, map_location='cpu')
    args = ckpt.get('args', {})
    folders = args.get('data', ckpt.get('data', []))
    if not folders:
        raise ValueError('Checkpoint has no validation provenance')
    expected_digest = ckpt.get('validation_keys_sha256')
    if not expected_digest or not ckpt.get('training_keys'):
        raise ValueError('Checkpoint lacks verified train/validation exposure history')
    sizer = BoltSizer(str(model_path), threads=2)
    measured, truth, regression, provenance = [], [], [], []
    validation_keys = set()
    seen = initializer_sources(args.get('init'))
    for folder in folders:
        grouped = folder.rstrip('/') in [p.rstrip('/') for p in args.get('split_by_object', ['data/real'])]
        _, val = split(folder, args.get('val_frac', .1), seed=0, by_object=grouped, seen=seen)
        validation_keys.update(exposure_keys([val]))
        indices = val.indices[:limit] if limit else val.indices
        for i in indices:
            row = val.dataset.rows[i]
            if int(row['is_bolt']) != 1:
                continue
            canvas = cv2.imread(str(Path(folder) / row['file']))
            raw = sizer.raw(canvas)
            g = outline_size(raw[4], HEAD_TYPES[int(raw[2].argmax())])
            if g is None or g['quality'] < .7:
                continue
            measured.append([g['diameter_mm'], g['length_mm']])
            regression.append(np.asarray(raw[0]) * [10., 50.])
            truth.append([float(row['diameter_mm']), float(row['length_mm'])])
            provenance.append(f'{folder}/{row["file"]}')
        print(f'calibration [{folder}]: {len(measured)} cumulative outlines', flush=True)
    digest = hashlib.sha256('\n'.join(sorted(validation_keys)).encode()).hexdigest()
    if digest != expected_digest or validation_keys & set(ckpt['training_keys']):
        raise ValueError('Validation partition changed or overlaps checkpoint training history')
    if len(measured) < 20:
        raise ValueError(f'Only {len(measured)} usable validation outlines; train the decoder longer')
    measured, regression, truth = map(np.array, (measured, regression, truth))
    result = fit_linear(measured, truth)
    corrected = measured * result['gain'] + result['offset']
    weights = fit_fusion(corrected, regression, truth)
    fused = corrected * weights + regression * (1 - np.asarray(weights))
    result.update(fusion_weights=weights, regression_validation_mae_mm=np.abs(regression - truth).mean(0).tolist(),
                  fusion_validation_mae_mm=np.abs(fused - truth).mean(0).tolist())
    result.update(n=len(measured), folders=folders, split='validation only; seed 0',
                  validation_keys_sha256=digest,
                  sample_sha256=hashlib.sha256('\n'.join(provenance).encode()).hexdigest())
    return result


def write_metadata(path, calibration):
    import onnx
    graph = onnx.load(str(path))
    props = {p.key: p.value for p in graph.metadata_props}
    props['measurement_calibration'] = json.dumps(calibration)
    props['outline_classes'] = json.dumps(['background', 'head', 'shank'])
    props['head_types'] = json.dumps(HEAD_TYPES)
    props['canvas_px_per_mm'] = '4.0'
    onnx.helper.set_model_props(graph, props)
    onnx.checker.check_model(graph)
    onnx.save(graph, str(path))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True)
    ap.add_argument('--ckpt', required=True)
    ap.add_argument('--limit-per-folder', type=int, default=0)
    a = ap.parse_args()
    result = calibrate(a.model, a.ckpt, a.limit_per_folder)
    write_metadata(a.model, result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
