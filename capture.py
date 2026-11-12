"""Photograph and label your own bolts (and non-bolts) for training. Works on the Pi too.

    python capture.py --label "M6x30" --type hex --finish zinc
    python capture.py --picamera --calib camera_calib.npz --label "1/4-20x1-1/2" --type carriage
    python capture.py --label none                      # a nut, washer, wood screw... (not a bolt)

Keys: SPACE save a shot, N next object (type its label in the terminal), Q quit.
Take ~20 shots per object: move/rotate it and the camera between shots, change
the lighting. Every object gets its own id, so training can hold out whole
objects for an honest score. Saves rectified canvases + labels.csv to data/real
(and the raw frames to data/real/raw, in case you want to re-process them).
Labels, head types and finishes come from bolt_sizer/catalog.py.
"""
import argparse
import time
from pathlib import Path

import cv2

from bolt_sizer.board import Undistorter, frame_to_canvas
from bolt_sizer.camera import open_camera, draw_lines
from bolt_sizer.catalog import CATALOG
from bolt_sizer.labels import append_label
from bolt_sizer.standards import HEAD_TYPES, format_label, parse_head_type, parse_label

NOT_BOLT_LABELS = ("none", "not", "not_bolt", "not-a-bolt", "reject")
FINISHES = list(CATALOG["finishes"])


def make_row(label, head=None, finish=None):
    """One labels.csv row for an object; source is a fresh id per object."""
    obj = {"source": f"obj{time.time_ns() // 1_000_000}", "finish": finish or ""}
    if finish and finish not in FINISHES:
        raise ValueError(f"unknown finish {finish!r}; use one of {FINISHES}")
    if label.strip().lower() in NOT_BOLT_LABELS:
        return {**obj, "label": "not a bolt", "is_bolt": 0, "system": -1,
                "diameter_mm": 0, "length_mm": 0, "head_type": -1}
    if not head:
        raise ValueError(f"a bolt needs a head type: {', '.join(HEAD_TYPES)}")
    thread, length = parse_label(label)
    head = parse_head_type(head)
    return {**obj, "label": format_label(thread, length, head), "is_bolt": 1,
            "system": thread.system, "diameter_mm": thread.diameter_mm,
            "length_mm": length, "head_type": HEAD_TYPES.index(head)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True,
                    help="e.g. M6x30, 1/4-20x1-1/2, #10-24x3/4, or 'none' for a non-bolt")
    ap.add_argument("--type", help=f"head type (bolts only): {', '.join(HEAD_TYPES)}")
    ap.add_argument("--finish", help=f"optional: {', '.join(FINISHES)}")
    ap.add_argument("--out", default="data/real")
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--picamera", action="store_true")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--calib", help="camera_calib.npz from calibrate.py")
    a = ap.parse_args()

    out = Path(a.out)
    (out / "raw").mkdir(parents=True, exist_ok=True)
    row = make_row(a.label, a.type, a.finish)
    undistort = Undistorter(a.calib) if a.calib else None
    cam = open_camera(a.camera, a.width, a.height, a.picamera)
    n = len(list(out.glob("*.png")))
    shots = 0

    while True:
        raw = cam.read()
        canvas, frame = frame_to_canvas(raw, undistort)
        show = frame.copy()
        status = "board OK" if canvas is not None else "NO BOARD - can't save"
        draw_lines(show, [row["label"], f"{status}   shots of this object: {shots}",
                          "SPACE save  N next object  Q quit"],
                   color=(0, 255, 0) if canvas is not None else (0, 0, 255))
        cv2.imshow("capture", show)
        if canvas is not None:
            cv2.imshow("rectified", canvas)
        k = cv2.waitKey(1) & 0xFF
        if k == ord(" ") and canvas is not None:
            name = f"real_{n:05d}.png"
            cv2.imwrite(str(out / name), canvas)
            cv2.imwrite(str(out / "raw" / f"real_{n:05d}.jpg"), raw)
            append_label(out, {"file": name, **row})
            n, shots = n + 1, shots + 1
        elif k == ord("n"):
            while True:
                try:
                    label = input("label (e.g. M8x40, or none): ")
                    head = None if label.strip().lower() in NOT_BOLT_LABELS else \
                        input(f"head type ({', '.join(HEAD_TYPES)}): ")
                    row = make_row(label, head, input(f"finish (optional: {', '.join(FINISHES)}): ") or None)
                    shots = 0
                    break
                except ValueError as e:
                    print(e)
        elif k == ord("q"):
            break
    cam.release()
    print(f"{n} images in {out}")


if __name__ == "__main__":
    main()
