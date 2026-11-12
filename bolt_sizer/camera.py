"""Camera access for a USB webcam (OpenCV) or the Raspberry Pi camera (picamera2)."""
import cv2


class _OpenCVCamera:
    def __init__(self, index, width, height):
        self.cap = cv2.VideoCapture(index)
        if not self.cap.isOpened():
            raise SystemExit(f"could not open camera {index}")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def read(self):
        ok, frame = self.cap.read()
        if not ok:
            raise SystemExit("camera stopped returning frames")
        return frame

    def release(self):
        self.cap.release()


class _PiCamera:
    def __init__(self, width, height):
        from picamera2 import Picamera2     # apt install python3-picamera2
        self.cam = Picamera2()
        self.cam.configure(self.cam.create_video_configuration(
            main={"size": (width, height), "format": "RGB888"}))
        self.cam.start()

    def read(self):
        return self.cam.capture_array()     # "RGB888" is BGR byte order, as OpenCV wants

    def release(self):
        self.cam.stop()


def open_camera(index=0, width=1280, height=720, picamera=False):
    return _PiCamera(width, height) if picamera else _OpenCVCamera(index, width, height)


def draw_lines(img, lines, color=(0, 255, 0), scale=0.7):
    y = 30
    for line in lines:
        cv2.putText(img, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(img, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, 2, cv2.LINE_AA)
        y += int(32 * scale / 0.7)
