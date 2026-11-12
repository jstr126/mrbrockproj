"""Propose measurement metadata from the model's fixed validation partition.

No training weights or v2 files are modified. The internal audit subset is
still development validation, not an independent 99% qualification trial.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import cv2
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bolt_sizer.infer import BoltSizer
from bolt_sizer.measure import calibrated_size, outline_size
from bolt_sizer.standards import HEAD_TYPES, snap, format_label
from tools.calibrate_measurement import fit_linear, fit_fusion, write_metadata


def collect(model, checkpoint, cache):
    import torch
    from train import split, exposure_keys
    ckpt = torch.load(checkpoint, map_location='cpu')
    args = ckpt['args']
    partitions, keys = [], set()
    for folder in args['data']:
        _, val = split(folder, args['val_frac'], 0, folder in args.get('split_by_object', []))
        partitions.append((folder, val))
        keys.update(exposure_keys([val]))
    digest = hashlib.sha256('\n'.join(sorted(keys)).encode()).hexdigest()
    if digest != ckpt.get('validation_keys_sha256') or not ckpt.get('training_keys') or keys & set(ckpt['training_keys']):
        raise ValueError('Unverified or changed validation partition')
    model_sha = hashlib.sha256(Path(model).read_bytes()).hexdigest()
    expected = {(folder, val.dataset.rows[i]['file']) for folder, val in partitions for i in val.indices}
    if cache.exists():
        metadata = json.loads(cache.with_suffix('.meta.json').read_text())
        if metadata['validation_keys_sha256'] != digest or metadata['model_sha256'] != model_sha:
            raise ValueError('Cache model or validation identity mismatch')
        if metadata.get('cache_sha256') and metadata['cache_sha256'] != hashlib.sha256(cache.read_bytes()).hexdigest():
            raise ValueError('Validation cache contents changed')
        rows = [json.loads(line) for line in cache.read_text().splitlines()]
        if {(r['folder'], r['file']) for r in rows} != expected or len(rows) != len(expected):
            raise ValueError('Incomplete, duplicate or foreign validation records')
    else:
        sizer = BoltSizer(str(model), 2)
        rows = []
        for folder, val in partitions:
            for i in val.indices:
                row = val.dataset.rows[i]
                raw = sizer.raw(cv2.imread(str(Path(folder) / row['file'])))
                head = HEAD_TYPES[int(raw[2].argmax())]
                g = outline_size(raw[4], head)
                rows.append(dict(folder=folder, file=row['file'], source=row.get('source', ''), truth=row,
                                 regression=(raw[0] * [10., 50.]).tolist(), system_p=raw[1].tolist(),
                                 type_p=raw[2].tolist(), bolt_p=raw[3].tolist(), head=head,
                                 geometry=None if g is None else [g['diameter_mm'], g['length_mm']],
                                 outline_quality=None if g is None else g['quality']))
            print('validation cached:', folder, len(val), flush=True)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    metadata = dict(validation_keys_sha256=digest, model_sha256=model_sha, records=len(rows),
                    cache_sha256=hashlib.sha256(cache.read_bytes()).hexdigest())
    cache.with_suffix('.meta.json').write_text(json.dumps(metadata, indent=2) + '\n')
    return rows, metadata


def development(row):
    identity = row['source'] or row['folder'] + '/' + row['file']
    return int(hashlib.sha256(identity.encode()).hexdigest()[:8], 16) % 5 != 0


def fit(rows):
    samples = [r for r in rows if r['truth']['is_bolt'] == '1' and r['geometry'] is not None
               and r['outline_quality'] >= .7 and r['folder'] != 'data/train_web']
    if len(samples) < 100:
        raise ValueError('Too few synthetic validation outlines')
    truth = np.array([[float(r['truth']['diameter_mm']), float(r['truth']['length_mm'])] for r in samples])
    reg = np.array([r['regression'] for r in samples])
    geo = np.array([r['geometry'] for r in samples])
    g, r = fit_linear(geo, truth), fit_linear(reg, truth)
    weight = fit_fusion(geo * g['gain'] + g['offset'], reg * r['gain'] + r['offset'], truth)
    return dict(gain=g['gain'], offset=g['offset'], regression_gain=r['gain'],
                regression_offset=r['offset'], fusion_weights=weight, n=len(samples))


def sizes(rows, calibration):
    result = []
    for row in rows:
        reg = np.array(row['regression'])
        if row['geometry'] is None:
            result.append(reg)
        else:
            result.append(calibrated_size(reg, row['geometry'], calibration)[0])
    return np.asarray(result)


def predictions(rows, calibration, evidence=None):
    size = sizes(rows, calibration)
    labels, systems = [], []
    for row, value in zip(rows, size):
        if evidence is None or row['geometry'] is None:
            system = int(np.argmax(row['system_p']))
        else:
            candidates = [snap(s, *value) for s in (0, 1)]
            ds, ls, pw = (evidence[k] for k in ('diameter_sigma', 'length_sigma', 'prior_weight'))
            costs = [((value[0] - t.diameter_mm) / ds) ** 2 + ((value[1] - length) / ls) ** 2
                     - pw * np.log(max(row['system_p'][s], 1e-8)) for s, (t, length) in enumerate(candidates)]
            system = int(np.argmin(costs))
        thread, length = snap(system, *value)
        labels.append(format_label(thread, length, row['head']))
        systems.append(system)
    return labels, systems, size


def evaluate(rows, calibration, evidence=None):
    labels, systems, values = predictions(rows, calibration, evidence)
    stats = {}
    for row, label, system, size in zip(rows, labels, systems, values):
        st = stats.setdefault(row['folder'], dict(n=0, exact=0, bolts=0, bolt_exact=0, diameter_error=0., length_error=0.))
        st['n'] += 1
        truth = row['truth']; is_bolt = truth['is_bolt'] == '1'; pred_bolt = row['bolt_p'][1] >= .5
        if not is_bolt:
            st['exact'] += not pred_bolt
            continue
        correct = pred_bolt and label == truth['label']
        st['bolts'] += 1; st['exact'] += correct; st['bolt_exact'] += correct
        st['diameter_error'] += abs(size[0] - float(truth['diameter_mm']))
        st['length_error'] += abs(size[1] - float(truth['length_mm']))
    for st in stats.values():
        st['exact_acc'] = st['exact'] / st['n']
        st['bolt_exact_acc'] = st['bolt_exact'] / st['bolts'] if st['bolts'] else None
        st['diameter_mae_mm'] = st.pop('diameter_error') / st['bolts'] if st['bolts'] else None
        st['length_mae_mm'] = st.pop('length_error') / st['bolts'] if st['bolts'] else None
    return dict(mean_exact=float(np.mean([st['exact_acc'] for st in stats.values()])), by_folder=stats)


def select_evidence(rows, calibration):
    # Use synthetic validation only: photo size labels do not qualify exact metrology.
    rows = [r for r in rows if r['folder'] != 'data/train_web']
    size = sizes(rows, calibration)
    network_p = np.array([r['system_p'] for r in rows])
    candidates = [[snap(s, *value) for s in (0, 1)] for value in size]
    nominal = np.array([[[t.diameter_mm, length] for t, length in pair] for pair in candidates])
    errors = (size[:, None, :] - nominal) ** 2
    correct = np.array([[format_label(t, length, row['head']) == row['truth']['label']
                         for t, length in pair] for row, pair in zip(rows, candidates)])
    positive = np.array([r['truth']['is_bolt'] == '1' for r in rows])
    pred_bolt = np.array([r['bolt_p'][1] >= .5 for r in rows])
    has_geometry = np.array([r['geometry'] is not None for r in rows])
    folders = sorted({r['folder'] for r in rows})
    masks = [np.array([r['folder'] == folder for r in rows]) for folder in folders]
    best = (-1, None)
    for ds in (.15, .25, .4, .6):
        for ls in (.6, 1.2, 2.5, 5.):
            for pw in (.5, 1., 2., 4., 8.):
                cost = errors[..., 0] / ds ** 2 + errors[..., 1] / ls ** 2 - pw * np.log(np.maximum(network_p, 1e-8))
                systems = np.where(has_geometry, cost.argmin(1), network_p.argmax(1))
                exact = np.where(positive, pred_bolt & correct[np.arange(len(rows)), systems], ~pred_bolt)
                score = float(np.mean([exact[m].mean() for m in masks]))
                if score > best[0]:
                    best = score, dict(diameter_sigma=ds, length_sigma=ls, prior_weight=pw)
    return best


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--model', default='models/boltnet_v3.onnx')
    ap.add_argument('--checkpoint', default='models/boltnet_v3.pt')
    ap.add_argument('--cache', default='work/v3/refinement/validation.jsonl')
    ap.add_argument('--out', default='models/boltnet_v3_refined.onnx')
    ap.add_argument('--report', default='results/v3_refinement_validation.json')
    args = ap.parse_args()
    if Path(args.model).resolve() == Path(args.out).resolve():
        ap.error('Output must preserve the original model')
    cv2.setNumThreads(1)
    rows, provenance = collect(args.model, args.checkpoint, Path(args.cache))
    develop = [r for r in rows if development(r)]
    audit = [r for r in rows if not development(r) and r['folder'] != 'data/train_web']
    proposal = fit(develop)
    score, evidence = select_evidence(develop, proposal)
    proposal['standard_evidence'] = evidence
    proposal.update(provenance=provenance, split='synthetic fixed validation; hash 4/5 fit and parameter selection',
                    qualification='development only; model selection previously saw this validation partition; no 99% or physical qualification')
    original = BoltSizer(args.model, 2).calibration
    report = dict(provenance=provenance, development_score=score, proposal=proposal,
                  baseline_audit=evaluate(audit, original), proposed_audit=evaluate(audit, proposal, evidence),
                  baseline_all_validation=evaluate(rows, original), proposed_all_validation=evaluate(rows, proposal, evidence),
                  audit_note=f'{len(audit)} synthetic validation frames; model selection previously used this partition. These are development diagnostics, not an independent acceptance trial. Photo sources remain grouped; none entered the synthetic audit.')
    if report['proposed_audit']['mean_exact'] <= report['baseline_audit']['mean_exact']:
        raise ValueError('Proposal did not improve internal validation; original model preserved')
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_bytes(Path(args.model).read_bytes())
    write_metadata(args.out, proposal)
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('development_score', 'baseline_audit', 'proposed_audit')}, indent=2))
    print('Candidate written:', args.out, flush=True)


if __name__ == '__main__':
    main()
