"""Camera, fp32 inference and a self-hosted Ethernet/LAN inspection page."""
import argparse
from collections import deque
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import signal
import threading
import time
from urllib.parse import urlsplit

import cv2
import numpy as np

from bolt_sizer.board import BoardTracker, Undistorter, frame_to_canvas
from bolt_sizer.infer import BoltSizer

STATIC = Path(__file__).with_name('static')
REVIEW = 'REVIEW: check by hand'
SITE_ORIGIN = 'https://bolt-camera-sorter.design-tech-9382.chatgpt.site'


class Inspection:
    """One replaceable capture slot; never queue camera frames for inference."""
    def __init__(self, model, camera=0, width=1280, height=720, threads=2,
                 calib=None, test_image=None, max_age_ms=500):
        self.sizer = BoltSizer(str(model), threads)
        self.model = Path(model).name
        self.model_sha = hashlib.sha256(Path(model).read_bytes()).hexdigest()
        self.camera, self.width, self.height = camera, width, height
        self.undistort = Undistorter(calib) if calib else None
        self.test_image, self.max_age_ms = test_image, max_age_ms
        self.condition = threading.Condition()
        self.stopped = threading.Event()
        self.frame = None
        self.frame_id = self.preview_id = self.result_id = 0
        self.captured_at = self.result_at = 0.
        self.preview = b''
        self.result = None
        self.state, self.error = 'starting', None
        self.times = deque(maxlen=120)
        self.skipped = 0
        self.started = time.monotonic()
        self.capture = None

    def start(self):
        for target in (self.capture_loop, self.inference_loop):
            threading.Thread(target=target, daemon=True).start()

    def publish(self, frame, captured_at):
        with self.condition:
            self.frame = frame
            self.frame_id += 1
            self.captured_at = captured_at
            self.state, self.error = 'running', None
            self.condition.notify_all()

    def capture_loop(self):
        while not self.stopped.is_set():
            self.capture_session()
            self.stopped.wait(2)

    def capture_session(self):
        last_preview = 0.
        try:
            image = cv2.imread(self.test_image) if self.test_image else None
            if self.test_image and image is None:
                raise RuntimeError('Cannot read test image')
            if image is None:
                self.capture = cv2.VideoCapture(self.camera)
                if not self.capture.isOpened():
                    raise RuntimeError(f'Cannot open camera {self.camera}')
                self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            while not self.stopped.is_set():
                if image is not None:
                    frame = image
                    if self.stopped.wait(.1):
                        break
                else:
                    ok, frame = self.capture.read()
                    if not ok:
                        raise RuntimeError('Camera stopped returning frames')
                now = time.monotonic()
                self.publish(frame, now)
                if now - last_preview >= .1:
                    h, w = frame.shape[:2]
                    small = cv2.resize(frame, (min(w, 640), max(1, round(h * min(w, 640) / w))))
                    ok, encoded = cv2.imencode('.jpg', small, [cv2.IMWRITE_JPEG_QUALITY, 75])
                    if ok:
                        with self.condition:
                            self.preview, self.preview_id = encoded.tobytes(), self.frame_id
                            self.condition.notify_all()
                    last_preview = now
        except Exception as exc:
            with self.condition:
                self.state, self.error = 'camera_offline', str(exc)
                self.condition.notify_all()
        finally:
            if self.capture is not None:
                self.capture.release()

    def inference_loop(self):
        previous = 0
        previous_capture = 0.
        tracker = BoardTracker()
        while not self.stopped.is_set():
            with self.condition:
                self.condition.wait_for(lambda: self.frame_id != previous or self.stopped.is_set(), timeout=1)
                if self.stopped.is_set():
                    return
                if self.frame_id == previous:
                    continue
                frame, frame_id, captured = self.frame, self.frame_id, self.captured_at
                self.skipped += max(0, frame_id - previous - 1)
                previous = frame_id
            start = time.monotonic()
            try:
                if captured - previous_capture > 1 or (tracker.prev is not None and tracker.prev.shape != frame.shape[:2]):
                    tracker = BoardTracker()
                previous_capture = captured
                canvas, native, matrix = frame_to_canvas(frame, self.undistort, tracker, return_matrix=True)
                if canvas is None:
                    result = {'is_bolt': False, 'bin': REVIEW, 'label': 'No checkerboard found'}
                else:
                    result = self.sizer.predict(canvas, frame=native, canvas_to_frame=matrix)
                elapsed = (time.monotonic() - start) * 1000
                result.update(frame_id=frame_id, processing_ms=elapsed)
                with self.condition:
                    self.times.append(elapsed)
                    self.result, self.result_at = result, captured
                    self.result_id += 1
                    self.condition.notify_all()
            except Exception as exc:
                tracker = BoardTracker()
                with self.condition:
                    self.result = {'frame_id': frame_id, 'is_bolt': False, 'bin': REVIEW,
                                   'label': 'Inspection error', 'error': str(exc)}
                    self.result_at = captured
                    self.result_id += 1
                    self.condition.notify_all()

    def snapshot(self):
        with self.condition:
            result = dict(self.result or {'label': 'Waiting for a frame', 'bin': REVIEW})
            age = (time.monotonic() - self.result_at) * 1000 if self.result_at else None
            stale = age is None or age > self.max_age_ms or self.state != 'running'
            candidate = result.pop('bin', REVIEW)
            # The trained model has not met the requested 99% routing target.
            result.update(candidate_bin=candidate, bin=REVIEW, machine_ready=False,
                          routing_locked=True, stale=stale,
                          routing_reason='99% automatic-bin precision has not been validated',
                          frame_age_ms=age, model=self.model, model_sha256=self.model_sha,
                          server_pid=os.getpid(),
                          state=self.state, camera_error=self.error,
                          source='test image' if self.test_image else str(self.camera),
                          skipped_frames=self.skipped, queue_depth=0, result_id=self.result_id)
            if self.times:
                result['timing'] = {'mean_ms': float(np.mean(self.times)),
                                    'p95_ms': float(np.percentile(self.times, 95)),
                                    'p99_ms': float(np.percentile(self.times, 99)),
                                    'over_100ms': sum(t >= 100 for t in self.times), 'n': len(self.times)}
            return result

    def close(self):
        self.stopped.set()
        with self.condition:
            self.condition.notify_all()


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    allowed_origins = frozenset({SITE_ORIGIN})


class Handler(BaseHTTPRequestHandler):
    def end_headers(self):
        origin = self.headers.get('Origin')
        if origin in self.server.allowed_origins:
            self.send_header('Access-Control-Allow-Origin', origin)
        self.send_header('Vary', 'Origin')
        super().end_headers()

    def do_OPTIONS(self):
        if self.headers.get('Origin') not in self.server.allowed_origins:
            self.reply(403, 'text/plain', b'Origin not allowed')
            return
        self.send_response(204)
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_GET(self):
        path = urlsplit(self.path).path
        if path in ('/api/status', '/api/health'):
            body = json.dumps(self.server.inspection.snapshot()).encode()
            self.reply(200, 'application/json', body)
        elif path == '/api/events':
            self.events()
        elif path == '/stream.mjpg':
            self.stream()
        elif path == '/frame.jpg':
            with self.server.inspection.condition:
                image = self.server.inspection.preview
            self.reply(200 if image else 503, 'image/jpeg' if image else 'text/plain',
                       image or b'Waiting for camera')
        else:
            files = {'/': ('index.html', 'text/html; charset=utf-8'),
                     '/index.html': ('index.html', 'text/html; charset=utf-8'),
                     '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                     '/style.css': ('style.css', 'text/css; charset=utf-8'),
                     '/checkerboard.pdf': ('checkerboard.pdf', 'application/pdf')}
            if path not in files:
                self.reply(404, 'text/plain', b'Not found')
                return
            name, mime = files[path]
            self.reply(200, mime, (STATIC / name).read_bytes())

    def reply(self, code, mime, body):
        self.send_response(code)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def events(self):
        inspection = self.server.inspection
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Accel-Buffering', 'no')
        self.end_headers()
        try:
            while not inspection.stopped.is_set():
                snapshot = inspection.snapshot()
                self.wfile.write(b'data: ' + json.dumps(snapshot).encode() + b'\n\n')
                self.wfile.flush()
                with inspection.condition:
                    inspection.condition.wait_for(lambda: inspection.result_id != snapshot['result_id']
                                                  or inspection.state != snapshot['state']
                                                  or inspection.stopped.is_set(), timeout=.5)
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            pass

    def stream(self):
        inspection = self.server.inspection
        self.send_response(200)
        self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        previous = 0
        try:
            while not inspection.stopped.is_set():
                with inspection.condition:
                    inspection.condition.wait_for(lambda: inspection.preview_id != previous or inspection.stopped.is_set(), timeout=1)
                    image, current = inspection.preview, inspection.preview_id
                if not image or current == previous:
                    continue
                previous = current
                self.wfile.write(b'--frame\r\nContent-Type: image/jpeg\r\nContent-Length: ' + str(len(image)).encode() + b'\r\n\r\n' + image + b'\r\n')
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            pass

    def log_message(self, *_):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default='models/boltnet_v3.onnx')
    ap.add_argument('--camera', default='0', help='USB device index or /dev/video path')
    ap.add_argument('--width', type=int, default=1280)
    ap.add_argument('--height', type=int, default=720)
    ap.add_argument('--threads', type=int, default=2)
    ap.add_argument('--calib')
    ap.add_argument('--test-image', help='explicit test source instead of a camera')
    ap.add_argument('--bind', default='0.0.0.0', help='LAN by default; use 127.0.0.1 for SSH-only access')
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--allow-origin', action='append', default=[],
                    help='additional HTTPS website origin allowed to read the Pi feed')
    a = ap.parse_args()
    cv2.setNumThreads(1)
    camera = int(a.camera) if a.camera.isdecimal() else a.camera
    inspection = Inspection(a.model, camera, a.width, a.height, a.threads, a.calib, a.test_image)
    server = Server((a.bind, a.port), Handler)
    server.allowed_origins = frozenset({SITE_ORIGIN, *a.allow_origin})
    server.inspection = inspection
    def stop(*_):
        inspection.close()
        threading.Thread(target=server.shutdown, daemon=True).start()
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    inspection.start()
    print(f'Bolt Camera serving http://{a.bind}:{server.server_port} — automatic routing locked', flush=True)
    try:
        server.serve_forever(poll_interval=.2)
    finally:
        inspection.close()
        server.server_close()


if __name__ == '__main__':
    main()
