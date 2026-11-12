"""Compare two (or more) ONNX models on the same test frames, from the
sorter's point of view: where does each object end up?

    python tools/compare_models.py --model models/boltnet_v1.onnx models/boltnet.onnx \
        --data data/test_catalog_normal data/test_junk_normal ... --out results/v1_vs_v2.md

The board is detected once per frame and every model sees the same canvas and
native frame, so the comparison covers network and measurement differences.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bolt_sizer.board import detect_board, rectify
from bolt_sizer.infer import BoltSizer


def route(bin_name):
    if bin_name.startswith("REJECT"):
        return "reject"
    if bin_name.startswith("REVIEW"):
        return "review"
    return "size"


def run(models, folder, details=None):
    rows = list(csv.DictReader(open(Path(folder) / "labels.csv")))
    stats = {m: {"bolt_n": 0, "sized_n": 0, "neg_n": 0, "bolt_kept": 0, "neg_rejected": 0, "neg_in_size": 0,
                 "size": 0, "size_right": 0, "bolt_size_right": 0, "review": 0, "exact": 0, "board_found": 0, "neg_not_bolt": 0, "outline_missing": 0, "disagreement": 0, "pitch_used": 0, "pitch_correct": 0} for m in models}
    for row in rows:
        frame = cv2.imread(str(Path(folder) / row["file"]))
        H = detect_board(frame)
        canvas, matrix = rectify(frame, H, return_matrix=True) if H is not None else (None, None)
        is_bolt = row["is_bolt"] == "1"
        sized = is_bolt and row["length_mm"] != ""      # angled photos: recognition only
        for name, sizer in models.items():
            st = stats[name]
            r = sizer.predict(canvas, frame=frame, canvas_to_frame=matrix) if canvas is not None else {"is_bolt": False, "label": "", "bin": "REVIEW"}
            if details is not None:
                details.append({'folder': folder, 'file': row['file'], 'model': name,
                                'truth': row, 'prediction': r})
            where = route(r["bin"])
            st["outline_missing"] += r.get('outline_missing', False)
            st["disagreement"] += r.get('measurement_disagreement', False)
            pitch_system = r.get('pitch', {}).get('system')
            if pitch_system is not None:
                st['pitch_used'] += 1
                st['pitch_correct'] += sized and pitch_system == int(row['system'])
            st["review"] += where == "review"
            st["board_found"] += canvas is not None
            if where == "size" and (sized or not is_bolt):
                st["size"] += 1
                st["size_right"] += r["bin"] == row["label"]
            if is_bolt:
                st["bolt_n"] += 1
                st["bolt_kept"] += r["is_bolt"]
            if sized:
                st["sized_n"] += 1
                st["exact"] += r["is_bolt"] and r["label"] == row["label"]
                st["bolt_size_right"] += where == "size" and r["bin"] == row["label"]
            else:
                st["neg_n"] += 1
                st["neg_rejected"] += where == "reject"
                st["neg_not_bolt"] += canvas is not None and not r["is_bolt"]
                st["neg_in_size"] += where == "size"
    return len(rows), stats


def pct(a, b):
    return f"{a / b:.0%}" if b else "-"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", nargs="+", required=True)
    ap.add_argument("--data", nargs="+", required=True)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--out", default="results/compare.md")
    a = ap.parse_args()

    cv2.setNumThreads(a.threads)
    models = {Path(m).stem: BoltSizer(m, a.threads) for m in a.model}
    for sizer in models.values():
        sizer.raw(np.zeros((512, 512, 3), np.uint8))
    raw_stats, details = {}, []
    lines = ["# Model comparison", "",
             "Bolts: share still recognised as bolts, and share fully right (size + head type).",
             "Non-bolts: share rejected, and share wrongly put in a size bin.",
             "Right-bin precision: fraction of size-bin assignments correct. Coverage: correct size-bin assignments / all bolts.",
             "Rejection counts actual REJECT routing; a missing board is REVIEW. All bolts, including board failures, remain in denominators.",
             "Bolts photographed at an angle (no known length) count toward recognition only.", "",
             "| Test set | Model | Bolts recognised | Bolts fully right | Non-bolts rejected "
             "| Non-bolts in a size bin | Right-bin precision | Right-bin coverage | Sent to REVIEW |",
             "|---|---|---|---|---|---|---|---|---|"]
    for folder in a.data:
        n, stats = run(models, folder, details)
        raw_stats[folder] = {"n": n, "models": stats}
        for name, st in stats.items():
            line = (f"| {Path(folder).name} | {name} | {pct(st['bolt_kept'], st['bolt_n'])} | "
                    f"{pct(st['exact'], st['sized_n'])} | {pct(st['neg_rejected'], st['neg_n'])} | "
                    f"{pct(st['neg_in_size'], st['neg_n'])} | {pct(st['size_right'], st['size'])} | "
                    f"{pct(st['bolt_size_right'], st['sized_n'])} | {pct(st['review'], n)} |")
            lines.append(line)
            print(line, flush=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(lines) + "\n")
    Path(a.out).with_suffix(".json").write_text(json.dumps(raw_stats, indent=2))
    Path(a.out).with_suffix('.cases.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in details))
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
