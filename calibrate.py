"""One-time lens calibration with the same 0.25" checkerboard (optional, but
recommended for wide-angle lenses such as most Raspberry Pi cameras).

Live:   python calibrate.py --camera 0        (SPACE = grab view, C = compute, Q = quit)
        python calibrate.py --picamera
Files:  python calibrate.py --images "calib/*.jpg"

Show the board WITHOUT a bolt, filling most of the frame, from ~15 different
tilts and positions (include the corners of the frame). Writes camera_calib.npz.
"""
import argparse
import glob

import cv2
import numpy as np

from bolt_sizer.board import find_corners
from bolt_sizer.camera import open_camera, draw_lines


def calibrate(frames, out):
    obj, img = [], []
    for f in frames:
        res = find_corners(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))
        if res is None:
            continue
        p, corners = res
        obj.append(np.hstack([p, np.zeros((len(p), 1), np.float32)]))
        img.append(corners)
    if len(obj) < 5:
        raise SystemExit(f"only {len(obj)} usable views; need at least 5 (15+ is better)")
    h, w = frames[0].shape[:2]
    rms, K, dist, _, _ = cv2.calibrateCamera(obj, img, (w, h), None, None)
    np.savez(out, K=K, dist=dist, size=np.array([w, h]))
    print(f"calibrated from {len(obj)} views, reprojection error {rms:.3f}px -> {out}")
    if rms > 1.0:
        print("  error is high; try more views, sharper focus, or a flatter board")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--picamera", action="store_true", help="use the Raspberry Pi camera via picamera2")
    ap.add_argument("--images", help="glob of saved board photos instead of a live camera")
    ap.add_argument("--out", default="camera_calib.npz")
    a = ap.parse_args()

    if a.images:
        calibrate([cv2.imread(p) for p in sorted(glob.glob(a.images))], a.out)
        return

    cam = open_camera(a.camera, picamera=a.picamera)
    views = []
    while True:
        frame = cam.read()
        show = frame.copy()
        draw_lines(show, [f"views: {len(views)}  SPACE grab  C compute  Q quit"])
        cv2.imshow("calibrate", show)
        k = cv2.waitKey(1) & 0xFF
        if k == ord(" "):
            if find_corners(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)) is None:
                print("no board found in that frame")
            else:
                views.append(frame)
        elif k == ord("c"):
            calibrate(views, a.out)
            break
        elif k == ord("q"):
            break
    cam.release()


if __name__ == "__main__":
    main()
