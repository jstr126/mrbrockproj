"""Accuracy + speed of the full pipeline (board detection -> rectification ->
network -> measurement) on a folder of raw camera frames with labels.csv.

    python benchmark.py --model models/boltnet.onnx models/boltnet_v3.onnx \
                        --data data/test_webhold_heavy data/test_webhold_normal

Writes results/benchmark.md. Torch-free, so it also runs on the Pi.
"""
import argparse
import csv
import json
import platform
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np

from bolt_sizer.board import detect_board, rectify
from bolt_sizer.infer import BoltSizer
from bolt_sizer.standards import HEAD_TYPE_NAMES, HEAD_TYPES, snap

BUDGET_MS = 100


def evaluate(sizer, folder, tta):
    rows = list(csv.DictReader(open(Path(folder) / "labels.csv")))
    t_det, t_rect, t_net, t_measure, t_total = [], [], [], [], []
    res = {k: [] for k in ["found", "bolt_ok", "neg_ok", "diam_ok", "thread_ok", "len_ok",
                           "type_ok", "system_ok", "exact", "exact_all", "size_right", "correct", "d_err", "l_err"]}
    confusions, per_bolt = [], []
    for row in rows:
        frame = cv2.imread(str(Path(folder) / row["file"]))
        is_bolt = int(row["is_bolt"]) == 1
        sized = is_bolt and row["length_mm"] != ""      # angled photos: recognition only
        t0 = time.perf_counter()
        H = detect_board(frame)
        t1 = time.perf_counter()
        if H is None:
            t_det.append(t1 - t0)
            t_total.append(t1 - t0)
            res["found"].append(False)
            if is_bolt and not sized:
                res["bolt_ok"].append(False)
                continue
            res["correct"].append(False)
            if is_bolt:
                res["bolt_ok"].append(False)
                res["exact_all"].append(False)
                res["size_right"].append(False)
                sys_t = int(row["system"])
                thread, _ = snap(sys_t, float(row["diameter_mm"]), float(row["length_mm"]))
                head = HEAD_TYPE_NAMES[HEAD_TYPES[int(row["head_type"])]]
                per_bolt.append((head, thread.name, False, False, False))
            else:
                res["neg_ok"].append(False)
            continue
        canvas, matrix = rectify(frame, H, return_matrix=True)
        t2 = time.perf_counter()
        raw = sizer.raw(canvas, tta)
        t3 = time.perf_counter()
        r = sizer.decode_raw(raw, frame=frame, canvas_to_frame=matrix)
        t4 = time.perf_counter()
        t_det.append(t1 - t0)
        t_rect.append(t2 - t1)
        t_net.append(t3 - t2)
        t_measure.append(t4 - t3)
        t_total.append(t4 - t0)
        res["found"].append(True)

        if not is_bolt:
            res["neg_ok"].append(not r["is_bolt"])
            res["correct"].append(not r["is_bolt"])
            continue
        res["bolt_ok"].append(r["is_bolt"])
        if not sized:
            continue
        res["exact_all"].append(r["is_bolt"] and r["label"] == row["label"])
        res["size_right"].append(r["bin"] == row["label"])
        sys_t = int(row["system"])
        true_thread, true_len = snap(sys_t, float(row["diameter_mm"]), float(row["length_mm"]))
        head_t = HEAD_TYPE_NAMES[HEAD_TYPES[int(row["head_type"])]]
        if not r["is_bolt"]:
            res["correct"].append(False)
            per_bolt.append((head_t, true_thread.name, False, False, False))
            continue
        thread_ok = r["thread"] == true_thread.name
        len_ok = abs(r["length_mm"] - true_len) < 0.01
        type_ok = r["head_type"] == head_t
        res["thread_ok"].append(thread_ok)
        res["len_ok"].append(len_ok)
        res["type_ok"].append(type_ok)
        res["system_ok"].append(r["system"] == ["metric", "imperial"][sys_t])
        # diameter right regardless of metric/imperial (M8 vs 5/16" counts as right)
        res["diam_ok"].append(abs(r["diameter_mm"] - true_thread.diameter_mm) < 0.5)
        res["d_err"].append(abs(r["measured_diameter_mm"] - float(row["diameter_mm"])))
        res["l_err"].append(abs(r["measured_length_mm"] - float(row["length_mm"])))
        exact = thread_ok and len_ok and type_ok
        per_bolt.append((head_t, true_thread.name, abs(r["diameter_mm"] - true_thread.diameter_mm) < 0.5,
                         type_ok, exact))
        res["exact"].append(exact)
        res["correct"].append(exact)
        if not exact and len(confusions) < 12:
            confusions.append(f"{row['label']}  ->  {r['label']}")
    ms = lambda v: np.array(v) * 1000
    return {"n": len(rows), "n_bolt": sum(int(r["is_bolt"]) for r in rows),
            "n_angled": sum(r["is_bolt"] == "1" and r["length_mm"] == "" for r in rows), "res": res,
            "times": {"detect": ms(t_det), "rectify": ms(t_rect), "network": ms(t_net), "measurement": ms(t_measure), "total": ms(t_total)},
            "confusions": confusions, "per_bolt": per_bolt}


def _breakdown(per_bolt, key):
    groups = {}
    for rec in per_bolt:
        groups.setdefault(rec[key], []).append(rec)
    return [f"| {k} | {len(v)} | {pct([x[2] for x in v])} | {pct([x[3] for x in v])} | {pct([x[4] for x in v])} |"
            for k, v in groups.items()]


def pct(v):
    return f"{np.mean(v):.1%}" if len(v) else "n/a"


def report(name, folder, e):
    r, t = e["res"], e["times"]
    lines = [f"### {name} on `{folder}` ({e['n']} frames: {e['n_bolt']} bolts, {e['n'] - e['n_bolt']} not bolts)"
             + (f"; {e['n_angled']} bolts are angled photos, scored for recognition only" if e["n_angled"] else ""), "",
             "| Metric | Result |", "|---|---|",
             f"| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **{pct(r['correct'])}** |",
             f"| Checkerboard found | {pct(r['found'])} |",
             f"| Bolts recognised as bolts (all bolts) | {pct(r['bolt_ok'])} |",
             f"| Fully right (all sized bolts) | {pct(r['exact_all'])} |",
             f"| Right size bin (all sized bolts) | {pct(r['size_right'])} |",
             f"| Non-bolts rejected as 'not a bolt' | {pct(r['neg_ok'])} |",
             f"| Diameter right (ignoring metric/imperial) | {pct(r['diam_ok'])} |",
             f"| Thread exactly right (incl. metric/imperial) | {pct(r['thread_ok'])} |",
             f"| Length exactly right | {pct(r['len_ok'])} |",
             f"| Head type right | {pct(r['type_ok'])} |",
             f"| Metric/imperial right | {pct(r['system_ok'])} |",
             f"| Exact size + type (of bolts recognised) | {pct(r['exact'])} |",
             f"| Mean diameter error | {np.mean(r['d_err']):.2f} mm |" if r["d_err"] else "| Mean diameter error | n/a |",
             f"| Mean length error | {np.mean(r['l_err']):.1f} mm |" if r["l_err"] else "| Mean length error | n/a |",
             "", "| Time per frame (ms) | mean | median | p95 | p99 | max |", "|---|---|---|---|---|---|"]
    for k in ["detect", "rectify", "network", "measurement", "total"]:
        v = t[k]
        if len(v):
            lines.append(f"| {k} | {v.mean():.1f} | {np.median(v):.1f} | {np.percentile(v, 95):.1f} | {np.percentile(v, 99):.1f} | {v.max():.1f} |")
    lines.append(f"\nFrames under {BUDGET_MS} ms: **{np.mean(t['total'] < BUDGET_MS):.1%}**")
    lines.append(f"Frames at or above {BUDGET_MS} ms: **{int((t['total'] >= BUDGET_MS).sum())}/{len(t['total'])}**")
    if e["per_bolt"]:
        lines += ["", "| By head type | n | diameter right | head type right | fully right |", "|---|---|---|---|---|"]
        lines += _breakdown(e["per_bolt"], 0)
        lines += ["", "| By size | n | diameter right | head type right | fully right |", "|---|---|---|---|---|"]
        lines += _breakdown(e["per_bolt"], 1)
    if e["confusions"]:
        lines += ["", "Sample mistakes (truth -> predicted):", ""] + [f"- {c}" for c in e["confusions"]]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", nargs="+", default=["models/boltnet.onnx"])
    ap.add_argument("--data", nargs="+", default=["data/test_web_heavy"])
    ap.add_argument("--tta", type=int, default=1)
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--out", default="results/benchmark.md")
    a = ap.parse_args()

    cv2.setNumThreads(max(1, a.threads) if a.threads else cv2.getNumThreads())
    uptime = subprocess.run(["uptime"], capture_output=True, text=True).stdout.strip()
    out = ["# Bolt sizer benchmark", "", f"Host: {platform.platform()}; CPU threads: {a.threads or 'auto'}", uptime, ""]
    summaries = {}
    for m in a.model:
        sizer = BoltSizer(m, a.threads)
        sizer.raw(np.zeros((512, 512, 3), np.uint8))           # warm-up
        for folder in a.data:
            evaluation = evaluate(sizer, folder, a.tta)
            text = report(Path(m).name, folder, evaluation)
            summaries.setdefault(Path(m).stem, {})[folder] = {
                "n": evaluation['n'], "n_bolt": evaluation['n_bolt'],
                "metrics": {k: float(np.mean(v)) if v else None for k, v in evaluation['res'].items()},
                "times_ms": {k: {'mean': float(v.mean()), 'median': float(np.median(v)),
                                  'p95': float(np.percentile(v, 95)), 'p99': float(np.percentile(v, 99)),
                                  'max': float(v.max())} for k, v in evaluation['times'].items() if len(v)},
                "frames_at_or_above_100ms": int((evaluation['times']['total'] >= BUDGET_MS).sum()),
                "under_100ms": float(np.mean(evaluation['times']['total'] < BUDGET_MS))}
            print(text)
            out.append(text)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(out))
    Path(a.out).with_suffix(".json").write_text(json.dumps({"uptime": uptime, "platform": platform.platform(), "threads": a.threads, "models": summaries}, indent=2))
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
