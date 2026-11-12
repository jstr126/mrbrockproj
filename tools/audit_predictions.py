"""Explain v3 errors and fixed confidence cutoffs without tuning on tests."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cases', default='results/v3_diagnostics.cases.jsonl')
    ap.add_argument('--out', default='results/v3_failure_audit.md')
    a = ap.parse_args()
    groups = defaultdict(list)
    for line in Path(a.cases).read_text().splitlines():
        case = json.loads(line)
        if case['model'] == 'boltnet_v3':
            groups[Path(case['folder']).name].append(case)
    lines = ['# V3 failure audit', '',
             'These are diagnostic cutoffs fixed before inspecting the case results. They are not a validated routing policy.',
             'Precision counts every automatic size-bin assignment, including non-bolts mistakenly assigned to size bins.',
             'A high confidence is not a calibrated probability of a correct thread/length/head combination.', '',
             '| Set | Minimum confidence on all three heads | Correct / automatic bins | Precision | Correct automatic assignments / all bolts |',
             '|---|---|---|---|---|']
    examples = []
    for folder, rows in groups.items():
        positives = sum(c['truth']['is_bolt'] == '1' for c in rows)
        for cutoff in (0., .7, .8, .9, .95, .99):
            sent = [c for c in rows if not c['prediction']['bin'].startswith(('REVIEW', 'REJECT'))
                    and min(c['prediction'].get(k, 0.) for k in ('bolt_conf', 'system_conf', 'type_conf')) >= cutoff]
            correct = sum(c['prediction']['bin'] == c['truth']['label'] for c in sent)
            precision = f'{correct / len(sent):.1%}' if sent else '—'
            coverage = f'{correct}/{positives} ({correct / positives:.1%})' if positives else '—'
            lines.append(f'| {folder} | {cutoff:.0%} | {correct}/{len(sent)} | {precision} | {coverage} |')
        wrong = [c for c in rows if not c['prediction']['bin'].startswith(('REVIEW', 'REJECT'))
                 and c['prediction']['bin'] != c['truth']['label']]
        counts = Counter()
        for c in rows:
            p, t = c['prediction'], c['truth']
            if t['is_bolt'] == '1':
                counts['bolts sent to REVIEW'] += p['bin'].startswith('REVIEW')
                counts['bolts not recognised'] += not p['is_bolt']
            counts['outline unavailable'] += p.get('outline_missing', False)
            counts['outline/regression disagreement'] += p.get('measurement_disagreement', False)
            if p.get('pitch', {}).get('system') is not None:
                counts['pitch system overrides'] += 1
                counts['incorrect pitch system overrides'] += t['is_bolt'] != '1' or p['pitch']['system'] != int(t['system'])
        examples += ['', f'## {folder}', '', ', '.join(f'{k}: {v}' for k, v in counts.items()), '']
        for c in wrong[:6]:
            p = c['prediction']
            examples.append(f"- `{c['file']}`: {c['truth']['label']} → {p['bin']}; confidence bolt {p.get('bolt_conf', 0):.1%}, system {p.get('system_conf', 0):.1%}, head {p.get('type_conf', 0):.1%}.")
    lines += ['', 'A 100% point result on a handful of retained frames is not evidence of a 99% physical sorting rate. The real-photo composites reuse source photographs and have noisy size labels; actual-camera, independently labeled trials are still required.']
    lines += examples
    Path(a.out).write_text('\n'.join(lines) + '\n')
    print(f'wrote {a.out}')


if __name__ == '__main__':
    main()
