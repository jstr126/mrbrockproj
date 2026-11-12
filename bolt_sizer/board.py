"""Find the 0.25" checkerboard in a camera frame and warp the frame into a
top-down "canvas" with a fixed, known scale (PX_PER_MM). The network only ever
sees canvases, so pixel sizes in its input are real millimetres.

No torch here: this module runs on the Raspberry Pi."""
import cv2
import numpy as np

SQUARE_MM = 6.35          # 0.25 inch checker squares
PX_PER_MM = 4.0           # canvas resolution
CANVAS_MM = 128.0         # canvas covers 128 x 128 mm of the board
CANVAS_PX = int(CANVAS_MM * PX_PER_MM)

# Smallest block of inner corners that must be visible. The bolt covers part
# of the board, so we only need one clean patch this big anywhere in view.
MIN_PATTERN = (5, 5)
DETECT_MAX_SIDE = 640     # detect on a downscaled frame (fast on a Pi), refine at full res


def find_corners(gray):
    """Checker corners as (board-plane mm Nx2, image px Nx2) or None."""
    # OpenCV's SB detector and RANSAC consume thread-local random state.
    # A prior frame must not change the rectification of this same image.
    cv2.setRNGSeed(0)
    scale = min(1.0, DETECT_MAX_SIDE / max(gray.shape))
    small = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1 else gray
    flags = cv2.CALIB_CB_LARGER | cv2.CALIB_CB_NORMALIZE_IMAGE | cv2.CALIB_CB_EXHAUSTIVE
    found, corners, meta = cv2.findChessboardCornersSBWithMeta(small, MIN_PATTERN, flags)
    if not found:
        return None
    rows, cols = meta.shape[:2]
    corners = corners.reshape(-1, 1, 2) / scale
    if len(corners) != rows * cols:
        return None
    if scale < 1:
        win = max(2, int(round(1 / scale)))
        h, w = gray.shape
        corners = np.clip(corners, win + 1, [w - win - 2, h - win - 2]).astype(np.float32)
        corners = cv2.cornerSubPix(gray, corners.astype(np.float32), (win, win), (-1, -1),
                                   (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.01))
    corners = corners.reshape(-1, 2).astype(np.float32)
    lattice = _lattice(corners)
    if lattice is None:
        return None
    keep, ij = lattice
    corners = corners[keep]
    plane = _fit_stride(gray, ij, corners)
    return None if plane is None else (plane, corners)


def _lattice(corners):
    """Integer grid coordinates for the corners, worked out from geometry.

    The detector's output order can't be trusted in CALIB_CB_LARGER mode
    (assuming row-major order shears the grid), so walk outwards from the
    corner nearest the middle, one neighbour step at a time, carrying the
    local grid directions along so perspective doesn't throw the walk off."""
    n = len(corners)
    d = np.linalg.norm(corners[:, None] - corners[None], axis=2)
    np.fill_diagonal(d, np.inf)
    nn = np.argsort(d, axis=1)[:, :8]
    seed = int(np.argmin(np.linalg.norm(corners - corners.mean(0), axis=1)))
    u = corners[nn[seed, 0]] - corners[seed]
    v = next((corners[k] - corners[seed] for k in nn[seed, 1:]
              if abs(np.dot(corners[k] - corners[seed], u)) <
              0.5 * np.linalg.norm(u) * np.linalg.norm(corners[k] - corners[seed])), None)
    if v is None:
        return None
    ij = np.full((n, 2), np.iinfo(np.int32).min, np.int64)
    basis = np.zeros((n, 2, 2))
    ij[seed], basis[seed] = (0, 0), (u, v)
    queue = [seed]
    while queue:
        p = queue.pop()
        B = basis[p].T
        for q in nn[p]:
            if ij[q, 0] != np.iinfo(np.int32).min:
                continue
            off = corners[q] - corners[p]
            x, y = np.linalg.solve(B, off)
            step = np.round([x, y])
            if abs(step).sum() != 1 or np.hypot(x - step[0], y - step[1]) > 0.3:
                continue
            ij[q] = ij[p] + step.astype(np.int64)
            basis[q] = basis[p]
            basis[q][0 if step[0] else 1] = off * (step[0] or step[1])
            queue.append(q)
    keep = ij[:, 0] != np.iinfo(np.int32).min
    if keep.sum() < 16:
        return None
    return keep, ij[keep]


def _fit_stride(gray, ij, corners):
    """Board-plane positions (mm) for grid coordinates ij.

    The detector sometimes returns only every other corner along one axis,
    which would make the squares look twice as big. Try a stride of 1 or 2
    squares per axis and keep the one where the square centres alternate
    black/white like a checkerboard; None if none of them do."""
    blur = cv2.GaussianBlur(gray, (0, 0), 1.0)
    h, w = gray.shape
    ij = ij - ij.min(0)
    best, best_score = None, 1.0                     # score ~2 for a clean board
    for sx in (1, 2):
        for sy in (1, 2):
            plane = (ij * [sx, sy]).astype(np.float32) * SQUARE_MM
            H, _ = cv2.findHomography(plane, corners, cv2.RANSAC, 3.0)
            if H is None:
                continue
            x, y = np.meshgrid(np.arange(ij[:, 0].max() * sx), np.arange(ij[:, 1].max() * sy))
            centres = (np.stack([x.ravel(), y.ravel()], 1) + 0.5) * SQUARE_MM
            px = np.round(cv2.perspectiveTransform(centres[None].astype(np.float64), H)[0]).astype(int)
            ok = (px[:, 0] >= 0) & (px[:, 0] < w) & (px[:, 1] >= 0) & (px[:, 1] < h)
            vals = blur[px[ok, 1], px[ok, 0]].astype(np.float32)
            parity = ((x + y) % 2).ravel()[ok]
            if len(vals) < 8 or parity.min() == parity.max():
                continue
            score = abs(vals[parity == 0].mean() - vals[parity == 1].mean()) / (vals.std() + 1e-6)
            if score > best_score:
                best, best_score = plane, score
    return best


def detect_board(frame_bgr):
    """Return H (board-plane mm -> image px) or None if no board found."""
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY) if frame_bgr.ndim == 3 else frame_bgr
    res = find_corners(gray)
    if res is None:
        return None
    plane, corners = res
    H, _ = cv2.findHomography(plane, corners, cv2.RANSAC, 2.0)
    return H


def canvas_to_plane(center_mm):
    """3x3 matrix mapping canvas pixels -> board-plane mm, centred on center_mm."""
    s = 1.0 / PX_PER_MM
    cx, cy = center_mm
    return np.array([[s, 0, cx - CANVAS_PX / 2 * s],
                     [0, s, cy - CANVAS_PX / 2 * s],
                     [0, 0, 1]], dtype=np.float64)


def rectify(frame_bgr, H, center_px=None, return_matrix=False):
    """Warp the board region around center_px (default: image centre) into a
    CANVAS_PX square canvas at PX_PER_MM. Optionally return canvas -> frame."""
    h, w = frame_bgr.shape[:2]
    if center_px is None:
        center_px = (w / 2, h / 2)
    c = cv2.perspectiveTransform(np.array([[center_px]], np.float64), np.linalg.inv(H))[0, 0]
    canvas2img = H @ canvas_to_plane(c)
    canvas = cv2.warpPerspective(frame_bgr, canvas2img, (CANVAS_PX, CANVAS_PX),
                               flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                               borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    return (canvas, canvas2img) if return_matrix else canvas


class Undistorter:
    """Removes lens distortion using a calibration from calibrate.py."""
    def __init__(self, path):
        cal = np.load(path)
        self.K, self.dist = cal["K"], cal["dist"]
        self.calib_size = tuple(int(v) for v in cal["size"])
        self._maps = {}

    def __call__(self, frame):
        h, w = frame.shape[:2]
        if (w, h) not in self._maps:
            sx, sy = w / self.calib_size[0], h / self.calib_size[1]
            K = self.K * np.array([[sx], [sy], [1]])      # same camera, other resolution
            self._maps[(w, h)] = cv2.initUndistortRectifyMap(K, self.dist, None, K, (w, h), cv2.CV_16SC2)
        m1, m2 = self._maps[(w, h)]
        return cv2.remap(frame, m1, m2, cv2.INTER_LINEAR)


class BoardTracker:
    """For live video: run the (slow) checkerboard detector only now and then,
    and follow the corners between detections with optical flow, which takes a
    few ms instead of tens. Corners covered by a moving bolt drop out via a
    forward-backward check."""
    LK = dict(winSize=(21, 21), maxLevel=3,
              criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 20, 0.03))

    def __init__(self, redetect_every=30):
        self.redetect_every = redetect_every
        self.prev, self.pts, self.plane, self.age = None, None, None, 0

    def _track(self, gray):
        nxt, st, _ = cv2.calcOpticalFlowPyrLK(self.prev, gray, self.pts, None, **self.LK)
        back, st2, _ = cv2.calcOpticalFlowPyrLK(gray, self.prev, nxt, None, **self.LK)
        good = (st.ravel() == 1) & (st2.ravel() == 1) & \
               (np.linalg.norm((back - self.pts).reshape(-1, 2), axis=1) < 0.5)
        if good.sum() < 20 or good.mean() < 0.6:
            return None
        H, _ = cv2.findHomography(self.plane[good], nxt[good].reshape(-1, 2), cv2.RANSAC, 2.0)
        if H is not None:
            self.pts, self.plane = nxt[good], self.plane[good]
            self.age += 1
        return H

    def __call__(self, frame_bgr):
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        H = None
        if self.pts is not None and self.age < self.redetect_every:
            H = self._track(gray)
        if H is None:
            self.pts = None
            res = find_corners(gray)
            if res is not None:
                self.plane, corners = res
                self.pts = corners.reshape(-1, 1, 2)
                H, _ = cv2.findHomography(self.plane, corners, cv2.RANSAC, 2.0)
                self.age = 0
        self.prev = gray
        return H


def frame_to_canvas(frame_bgr, undistort=None, tracker=None, return_matrix=False):
    """Full pipeline for one camera frame: undistort -> find board -> rectify.
    Pass a BoardTracker for live video. Returns (canvas or None, frame used);
    return_matrix also returns canvas -> frame at native resolution."""
    if undistort is not None:
        frame_bgr = undistort(frame_bgr)
    H = tracker(frame_bgr) if tracker is not None else detect_board(frame_bgr)
    if return_matrix:
        canvas, matrix = (None, None) if H is None else rectify(frame_bgr, H, return_matrix=True)
        return canvas, frame_bgr, matrix
    return (None if H is None else rectify(frame_bgr, H)), frame_bgr
