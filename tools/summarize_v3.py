"""Summarize v3 acceptance with explicit numerators and benchmark evidence."""
import argparse
import json
from pathlib import Path


def checks(comparison, benchmark):
    results = []
    for folder, data in comparison.items():
        old, new = (data['models'][m] for m in ('boltnet', 'boltnet_v3'))
        name = Path(folder).name
        if 'catalog' in name:
            for field, label in [('exact', 'fully right'), ('bolt_size_right', 'correct-bin coverage')]:
                results.append((name + ': ' + label, new[field] / new['bolt_n'] > old[field] / old['bolt_n']))
            results.append((name + ': bin precision', new['size_right'] / max(new['size'], 1) > old['size_right'] / max(old['size'], 1)))
        if 'junk' in name or '_ai_' in name:
            results.append((name + ': rejection', new['neg_rejected'] >= old['neg_rejected']))
            results.append((name + ': no extra size-bin errors', new['neg_in_size'] <= old['neg_in_size']))
        if 'webhold' in name:
            results.append((name + ': recognition improves by at least 5 points',
                            new['bolt_kept'] / new['bolt_n'] - old['bolt_kept'] / old['bolt_n'] >= .05))
        if 'catalog' in name or 'webhold' in name:
            results.append((name + ': at least 99% of automatic size-bin assignments correct',
                            new['size'] > 0 and new['size_right'] / new['size'] >= .99))
    for folder, data in benchmark['models']['boltnet_v3'].items():
        times = data['times_ms']['total']
        results.append((Path(folder).name + ': mean and p95 below 100 ms', times['mean'] < 100 and times['p95'] < 100))
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--comparison', default='results/v2_vs_v3.json')
    ap.add_argument('--benchmark', default='results/benchmark_v3.json')
    ap.add_argument('--out', default='results/v3_acceptance.md')
    a = ap.parse_args()
    comparison = json.loads(Path(a.comparison).read_text())
    benchmark = json.loads(Path(a.benchmark).read_text())
    gates = checks(comparison, benchmark)
    passed = all(ok for _, ok in gates)
    lines = ['# V3 acceptance', '', 'Status: ' + ('all measured checks pass' if passed else 'requirements remain unmet'), '',
             'Precision is correct size-bin assignments / all size-bin assignments; coverage is correct assignments / all bolts.',
             'Board failures count as REVIEW. Timing is from this Mac; Raspberry Pi timing remains unmeasured.', '',
             'Target: at least 99% correct automatic bin assignments, with bypass/REVIEW coverage reported separately. A 99% model confidence is not measured 99% accuracy.',
             'Rendered and Wikimedia composites do not qualify the physical machine. No labeled capture from the actual camera/feed has been evaluated; vision accuracy cannot prove a jam-free mechanism.', '',
             '| Test set | Model | Fully right / bolts | Right size bin / bolts | Right bin / sent | Bolts recognised / bolts | Non-bolts REJECT / negatives | Negatives in size bins | Mean / p95 ms |',
             '|---|---|---|---|---|---|---|---|---|']
    for folder, data in comparison.items():
        for model in ('boltnet', 'boltnet_v3'):
            s = data['models'][model]
            t = benchmark['models'][model][folder]['times_ms']['total']
            fmt = lambda num, den: f'{num}/{den} ({num/den:.1%})' if den else '—'
            lines.append(f"| {Path(folder).name} | {model} | {fmt(s['exact'],s.get('sized_n',s['bolt_n']))} | {fmt(s['bolt_size_right'],s.get('sized_n',s['bolt_n']))} | {fmt(s['size_right'],s['size'])} | {fmt(s['bolt_kept'],s['bolt_n'])} | {fmt(s['neg_rejected'],s['neg_n'])} | {s['neg_in_size']} | {t['mean']:.1f} / {t['p95']:.1f} |")
    lines += ['', '| Check | Outcome |', '|---|---|']
    lines += [f"| {label} | {'PASS' if ok else 'FAIL'} |" for label, ok in gates]
    Path(a.out).write_text('\n'.join(lines) + '\n')
    Path(a.out).with_suffix('.json').write_text(json.dumps({'passed': passed, 'checks': dict(gates)}, indent=2))
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
