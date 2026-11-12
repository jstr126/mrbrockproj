"""Read bolt diameter, length and head type from one camera. Runs on a
Raspberry Pi: needs only numpy, OpenCV and onnxruntime.

    python predict.py --camera 0                       # live USB webcam
    python predict.py --picamera --calib camera_calib.npz
    python predict.py --picamera --headless            # no screen: print to terminal
    python predict.py --image photo1.jpg photo2.jpg    # still photos

Put the bolt flat on the checkerboard, in the middle of the view, with some
clean checkerboard visible around it.
"""
import argparse
import time

import cv2

from bolt_sizer.board import BoardTracker, Undistorter, frame_to_canvas
from bolt_sizer.camera import open_camera, draw_lines
from bolt_sizer.infer import BoltSizer, Smoother


def describe(r):
    if not r["is_bolt"]:
        return [f"not a bolt ({r['bolt_conf']:.0%})", f"bin: {r['bin']}"]
    lines = [r["label"],
             f"d {r['measured_diameter_mm']:.2f}mm  L {r['measured_length_mm']:.1f}mm  "
             f"{r['system']} {r['system_conf']:.0%}  type {r['type_conf']:.0%}"]
    if r["system_conf"] < 0.8:
        lines.append(f"(could also be {r['alternative']} - check thread pitch)")
    lines.append(f"bin: {r['bin']}")
    return lines


def run_images(sizer, paths, undistort, tta, show):
    for path in paths:
        frame = cv2.imread(path)
        if frame is None:
            print(f"{path}: can't read image")
            continue
        canvas, used, matrix = frame_to_canvas(frame, undistort, return_matrix=True)
        if canvas is None:
            print(f"{path}: no checkerboard found")
            continue
        lines = describe(sizer.predict(canvas, tta, frame=used, canvas_to_frame=matrix))
        print(f"{path}: " + " | ".join(lines))
        if show:
            draw_lines(canvas, lines, scale=0.55)
            cv2.imshow("bolt", canvas)
            cv2.waitKey(0)


def run_camera(sizer, cam, undistort, tta, headless, smooth_frames=1):
    smooth = Smoother(smooth_frames) if smooth_frames > 1 else None
    tracker = BoardTracker()
    last_print, t_prev = 0.0, time.time()
    while True:
        frame = cam.read()
        canvas, frame, matrix = frame_to_canvas(frame, undistort, tracker, return_matrix=True)
        now = time.time()
        fps, t_prev = 1 / max(now - t_prev, 1e-6), now
        if canvas is None:
            if smooth is not None:
                smooth.reset()
            lines = ["no checkerboard in view"]
        else:
            lines = describe(sizer.predict(canvas, tta, frame=frame, canvas_to_frame=matrix, smoother=smooth))
        lines.append(f"{fps:.1f} fps")

        if headless:
            if now - last_print > 1.0:
                print(" | ".join(lines), flush=True)
                last_print = now
            continue
        draw_lines(frame, lines, color=(0, 255, 0) if canvas is not None else (0, 0, 255))
        cv2.imshow("bolt", frame)
        if canvas is not None:
            cv2.imshow("rectified (what the network sees)", canvas)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cam.release()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="models/boltnet.onnx")
    ap.add_argument("--image", nargs="+", help="photos to measure instead of a live camera")
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--picamera", action="store_true", help="use the Raspberry Pi camera via picamera2")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--calib", help="camera_calib.npz from calibrate.py")
    ap.add_argument("--tta", type=int, choices=range(1, 9), default=1,
                    help="views averaged per prediction; default 1 for speed and to match v3 calibration")
    ap.add_argument("--threads", type=int, default=0, help="CPU threads for onnxruntime (0 = auto)")
    ap.add_argument("--smooth", type=int, default=1,
                    help="live frames to average; default 1 avoids mixing successive bolts. Use >1 only for a stationary bolt")
    ap.add_argument("--headless", action="store_true", help="print results instead of opening windows")
    a = ap.parse_args()
    if a.smooth < 1:
        ap.error('--smooth must be at least 1')

    sizer = BoltSizer(a.model, a.threads)
    undistort = Undistorter(a.calib) if a.calib else None
    if a.image:
        run_images(sizer, a.image, undistort, a.tta, not a.headless)
    else:
        cam = open_camera(a.camera, a.width, a.height, a.picamera)
        run_camera(sizer, cam, undistort, a.tta, a.headless, a.smooth)


if __name__ == "__main__":
    main()
