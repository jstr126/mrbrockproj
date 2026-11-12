"""Synthetic data: an object (a bolt, a non-bolt, a photo cutout, or nothing)
lying on a 0.25" checkerboard, seen through a randomly placed, tilted,
cheap camera with lens distortion and sensor noise, then rectified with the
same code path real photos use.

`heavy=True` turns every degradation up for stress-testing: strong blur and
distortion, dim light, glare, cast shadows, coloured light, dust, low JPEG."""
import cv2
import numpy as np

from .board import SQUARE_MM, CANVAS_MM, rectify
from .standards import THREADS, HEAD_TYPES, MAX_LENGTH_MM, lengths_mm, format_label

RES = 8.0            # render resolution, px/mm (well above any camera we simulate)
RENDER_MM = 240.0    # board area rendered around the camera's centre of view

MATERIALS = [        # BGR base colour, diffuse, specular
    ((205, 200, 195), 0.75, 0.50),   # zinc plated
    ((48, 45, 45), 0.60, 0.35),      # black oxide
    ((90, 165, 195), 0.75, 0.45),    # yellow zinc
    ((180, 182, 185), 0.70, 0.60),   # stainless
    ((140, 145, 150), 0.70, 0.30),   # plain steel
]
CAMERA_SIZES = [(640, 480), (960, 720), (1280, 720)]
HEAVY_CAMERA_SIZES = [(640, 480), (800, 600), (1280, 720)]

NOT_BOLT = {"is_bolt": 0, "system": -1, "diameter_mm": 0.0, "length_mm": 0.0, "head_type": -1}


def bolt_labels(thread, head, length_mm):
    return {"label": format_label(thread, length_mm, head), "is_bolt": 1,
            "system": thread.system, "diameter_mm": thread.diameter_mm,
            "length_mm": length_mm, "head_type": HEAD_TYPES.index(head)}


def pick_bolt(rng):
    system = int(rng.integers(2))
    thread = THREADS[system][rng.integers(len(THREADS[system]))]
    head = HEAD_TYPES[rng.integers(len(HEAD_TYPES))]
    d = thread.diameter_mm
    longest = min(MAX_LENGTH_MM, max(25.0, 20 * d))
    choices = [L for L in lengths_mm(system) if 2 * d <= L <= longest + 1e-6]
    return thread, head, choices[rng.integers(len(choices))]


def _head_dims(thread, head):
    """(height along the axis, diameter or width across flats) in mm."""
    d = thread.diameter_mm
    return {"hex": (thread.head_k_mm, thread.head_af_mm),
            "socket_cap": (d, 1.5 * d),
            "carriage": (0.55 * d, 2.2 * d),
            "flat": (0.5 * d, 2.0 * d),
            "button": (0.55 * d, 1.75 * d)}[head]


def _hex_facets(af, roll, ys):
    """Visible (top) facet of a hexagonal prism lying on its side, per y."""
    rc = af / np.sqrt(3)
    ang = roll + np.arange(6) * np.pi / 3
    vy, vz = rc * np.cos(ang), rc * np.sin(ang)
    z_top = np.full(ys.shape, -np.inf)
    ny, nz = np.zeros_like(ys), np.zeros_like(ys)
    for i in range(6):
        y0, z0, y1, z1 = vy[i], vz[i], vy[(i + 1) % 6], vz[(i + 1) % 6]
        if abs(y1 - y0) < 1e-9:
            continue
        t = (ys - y0) / (y1 - y0)
        z = z0 + t * (z1 - z0)
        better = (t >= 0) & (t <= 1) & (z > z_top)
        n = np.array([-(z1 - z0), y1 - y0])
        n /= np.linalg.norm(n)
        if n[1] < 0:
            n = -n
        z_top[better], ny[better], nz[better] = z[better], n[0], n[1]
    return np.isfinite(z_top), ny, nz


def _shade(rng, n, kd):
    """Diffuse shade and specular term for unit normals n (..., 3)."""
    light = np.array([rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6), 1.0])
    light /= np.linalg.norm(light)
    half = light + [0, 0, 1]
    half /= np.linalg.norm(half)
    diff = np.clip(n @ light, 0, None)
    spec = np.clip(n @ half, 0, None) ** rng.uniform(10, 40)
    return 0.3 + kd * diff, spec


def _finish(rng, colour, shade, spec, ks):
    bgr = colour * shade[..., None] + 255 * ks * spec[..., None]
    bgr = bgr * rng.uniform(0.97, 1.03, (1, 1, 3)) + rng.normal(0, 4, bgr.shape)
    return np.clip(bgr, 0, 255).astype(np.float32)


def _revolution_normals(X, Y, r_top, r_bot, drdx):
    """Mask and normals of a surface of revolution with radius profile r(x)."""
    R = np.where(Y < 0, r_top[None, :], r_bot[None, :])
    mask = (np.abs(Y) <= R) & (R > 0)
    ny = np.clip(Y / np.where(R > 0, R, 1), -1, 1)
    nz = np.sqrt(1 - ny ** 2)
    nx = np.broadcast_to(-drdx[None, :], X.shape).copy()
    return mask, nx, ny, nz


def _normalise(nx, ny, nz):
    n = np.stack([nx, ny, nz], -1)
    return n / (np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9)


# --- Bolts ------------------------------------------------------------------

BOLT_MARGIN_MM = 2.0     # empty border render_bolt leaves around the bolt


def render_bolt(rng, thread, head, length_mm, wood_screw=False, fully_threaded=False, return_mask=False):
    """Render a bolt in its own frame: x along the axis (head top at x=0), y across.
    wood_screw=True gives a coarse, deep thread and a pointed tip (a non-bolt).

    Returns (bgr, alpha, centre); return_mask adds head/shank coverage."""
    d = thread.diameter_mm
    p = 0.45 * d if wood_screw else thread.pitch_mm
    kh, hd = _head_dims(thread, head)
    neck = 0.6 * d if head == "carriage" else 0.0
    shank = length_mm - kh if head == "flat" else length_mm
    x_end = kh + shank
    margin = BOLT_MARGIN_MM
    width_mm = max(hd, d) * (1.16 if head == "hex" else 1.0) + 2 * margin

    xs = (np.arange(int((x_end + 2 * margin) * RES)) + 0.5) / RES - margin
    ys = (np.arange(int(width_mm * RES)) + 0.5) / RES - width_mm / 2
    X, Y = np.meshgrid(xs, ys)

    # Radius profile r(x); separate top/bottom edges so threads can be offset
    # by half a pitch (the helix).
    r = np.zeros_like(xs)
    if head in ("carriage", "button"):
        u = np.clip((kh - xs) / kh, 0, 1)
        r = np.where((xs >= 0) & (xs < kh), hd / 2 * np.sqrt(1 - u ** 2), r)
    elif head == "socket_cap":
        r = np.where((xs >= 0) & (xs < kh), hd / 2 - np.clip(0.08 * hd - xs, 0, None), r)
    elif head == "flat":
        r = np.where((xs >= 0) & (xs < kh), hd / 2 - (hd / 2 - d / 2) * xs / kh, r)
    in_shank = (xs >= kh) & (xs <= x_end)
    r = np.where(in_shank, d / 2, r)
    if neck:
        r = np.where((xs >= kh) & (xs < kh + neck), d / 2 * 1.08, r)

    threaded = wood_screw or fully_threaded or rng.uniform() < 0.5 or shank < 2 * d + 6
    b = shank if threaded else min(shank, 2 * d + 6 + rng.uniform(-1, 1))
    in_thread = in_shank & (xs >= x_end - b)
    depth = 0.25 * d if wood_screw else 0.6 * p
    tri = lambda ph: np.abs((ph % 1.0) * 2 - 1)
    phase0 = rng.uniform()
    r_top = np.where(in_thread, r - depth * tri(xs / p + phase0), r)
    r_bot = np.where(in_thread, r - depth * tri(xs / p + phase0 + 0.5), r)
    if wood_screw:
        tip = (x_end - xs) * (d / 2) / (1.5 * d)
    else:
        tip = d / 2 - depth + (x_end - xs)
    r_top = np.where(in_shank, np.minimum(r_top, tip), r_top)
    r_bot = np.where(in_shank, np.minimum(r_bot, tip), r_bot)

    mask, nx, ny, nz = _revolution_normals(X, Y, r_top, r_bot, np.gradient(r, xs))
    if neck:
        sq = (X >= kh) & (X < kh + neck)
        ny[sq], nz[sq], nx[sq] = 0, 1, 0
    if head == "hex":
        hmask, hny, hnz = _hex_facets(hd, rng.uniform(0, np.pi / 3), ys)
        in_head = (X >= 0) & (X < kh)
        mask = np.where(in_head, in_head & hmask[:, None], mask)
        ny = np.where(in_head, hny[:, None], ny)
        nz = np.where(in_head, hnz[:, None], nz)
        nx = np.where(in_head, 0, nx)

    base, kd, ks = MATERIALS[rng.integers(len(MATERIALS))]
    shade, spec = _shade(rng, _normalise(nx, ny, nz), kd)
    crest = 0.72 + 0.28 * np.cos(2 * np.pi * (X / p + phase0 + 0.25 * (Y / (d / 2) + 1)))
    shade = np.where(in_thread[None, :] & mask, shade * crest, shade)
    bgr = _finish(rng, np.array(base, np.float32), shade, spec, ks)
    centre = np.array([(margin + x_end / 2) * RES, width_mm / 2 * RES])
    sprite = bgr, mask.astype(np.float32), centre
    parts = np.stack([mask & (X < kh), mask & (X >= kh)], -1).astype(np.float32)
    return (*sprite, parts) if return_mask else sprite


def synth_bolt(rng):
    thread, head, L = pick_bolt(rng)
    bgr, alpha, centre, parts = render_bolt(
        rng, thread, head, L * (1 + rng.normal(0, 0.005)), return_mask=True)
    return bgr, alpha, centre, bolt_labels(thread, head, L), parts


# --- Non-bolts --------------------------------------------------------------

def _cylinder(rng, length, diameter, colours, ks, chamfer=0.3):
    """Plain cylinder lying on its side; colours(xs) -> (W, 3) BGR per column."""
    margin = 1.5
    xs = (np.arange(int((length + 2 * margin) * RES)) + 0.5) / RES - margin
    ys = (np.arange(int((diameter + 2 * margin) * RES)) + 0.5) / RES - diameter / 2 - margin
    X, Y = np.meshgrid(xs, ys)
    c = min(chamfer, diameter / 3)
    r = np.where((xs >= 0) & (xs <= length), diameter / 2, 0.0)
    r = np.minimum(r, np.clip(diameter / 2 - c + np.minimum(xs, length - xs), 0, None))
    mask, nx, ny, nz = _revolution_normals(X, Y, r, r, np.gradient(r, xs))
    shade, spec = _shade(rng, _normalise(nx, ny, nz), 0.7)
    bgr = _finish(rng, colours(xs)[None, :, :], shade, spec, ks)
    return bgr, mask.astype(np.float32), np.array([X.shape[1] / 2, X.shape[0] / 2])


def _flat_object(rng, mask, colour, ks, bevel_mm=1.0, relief=0.0):
    """Shade a flat object seen from above (nut, washer, coin, blob) with a
    bevelled edge; relief adds embossed texture (coins)."""
    dist = cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2, 5) / RES
    z = np.minimum(dist, bevel_mm)
    if relief:
        noise = cv2.GaussianBlur(rng.normal(0, 1, mask.shape).astype(np.float32), (0, 0), 0.6 * RES)
        z = z + relief * noise * (dist > bevel_mm)
    gy, gx = np.gradient(z * RES)
    shade, spec = _shade(rng, _normalise(-gx, -gy, np.ones_like(z)), 0.7)
    bgr = _finish(rng, np.array(colour, np.float32), shade, spec, ks)
    return bgr, mask.astype(np.float32), np.array([mask.shape[1] / 2, mask.shape[0] / 2])


def _canvas(size_mm):
    n = int(size_mm * RES)
    yy, xx = (np.mgrid[0:n, 0:n] + 0.5) / RES - size_mm / 2
    return n, xx, yy


def synth_not_bolt(rng):
    """A random non-bolt object, or None for an empty board."""
    kind = rng.choice(["empty", "nut", "nut_side", "washer", "coin", "pin", "battery",
                       "wood_screw", "blob"], p=[0.1, 0.12, 0.08, 0.12, 0.12, 0.12, 0.08, 0.16, 0.10])
    labels = dict(NOT_BOLT, label=f"not a bolt ({kind})")
    metal = MATERIALS[rng.integers(len(MATERIALS))]
    if kind == "empty":
        return None
    if kind == "nut":
        af = rng.uniform(5.5, 19)
        n, xx, yy = _canvas(af * 1.3)
        ang = np.arctan2(yy, xx) - rng.uniform(0, np.pi / 3)
        hexr = (af / 2) / np.cos((ang % (np.pi / 3)) - np.pi / 6)
        rad = np.hypot(xx, yy)
        mask = (rad <= hexr) & (rad >= af * 0.32)
        bgr, alpha, c = _flat_object(rng, mask, metal[0], metal[2], bevel_mm=af * 0.08)
        ring = (rad < af * 0.4) & mask
        bgr[ring] *= 0.6
        return bgr, alpha, c, labels
    if kind == "nut_side":
        af = rng.uniform(5.5, 19)
        thick = af * rng.uniform(0.5, 0.9)
        ys = (np.arange(int(af * 1.25 * RES)) + 0.5) / RES - af * 0.625
        hmask, hny, hnz = _hex_facets(af, rng.uniform(0, np.pi / 3), ys)
        w = int((thick + 2) * RES)
        mask = np.repeat(hmask[:, None], w, 1)
        mask[:, :int(RES)] = False
        mask[:, -int(RES):] = False
        nx = np.zeros(mask.shape)
        n_ = _normalise(nx, np.repeat(hny[:, None], w, 1), np.repeat(hnz[:, None], w, 1))
        shade, spec = _shade(rng, n_, metal[1])
        bgr = _finish(rng, np.array(metal[0], np.float32), shade, spec, metal[2])
        return bgr, mask.astype(np.float32), np.array([w / 2, mask.shape[0] / 2]), labels
    if kind == "washer":
        od = rng.uniform(7, 30)
        n, xx, yy = _canvas(od * 1.1)
        rad = np.hypot(xx, yy)
        mask = (rad <= od / 2) & (rad >= od * rng.uniform(0.2, 0.3))
        return (*_flat_object(rng, mask, metal[0], metal[2], bevel_mm=0.4), labels)
    if kind == "coin":
        dia = rng.uniform(15, 31)
        n, xx, yy = _canvas(dia * 1.1)
        mask = np.hypot(xx, yy) <= dia / 2
        colour = [(60, 110, 180), (170, 170, 165), (80, 150, 190)][rng.integers(3)]
        return (*_flat_object(rng, mask, colour, 0.4, bevel_mm=0.8, relief=0.5), labels)
    if kind == "pin":
        d, L = rng.uniform(2, 12), rng.uniform(10, 80)
        wood = rng.uniform() < 0.4
        col = np.array((120, 170, 205) if wood else metal[0], np.float32)
        return (*_cylinder(rng, L, d, lambda xs: np.tile(col, (len(xs), 1)), 0.1 if wood else metal[2]), labels)
    if kind == "battery":
        d, L = [(14.5, 50.5), (10.5, 44.5), (17, 50)][rng.integers(3)]
        wrap = rng.uniform(20, 230, 3).astype(np.float32)
        cap = np.array((180, 180, 180), np.float32)

        def colours(xs):
            out = np.tile(wrap, (len(xs), 1))
            out[(xs < 1.0) | (xs > L - 1.5)] = cap
            out[(xs > rng.uniform(0.3, 0.7) * L) & (xs < 0.75 * L)] *= rng.uniform(0.4, 1.2)
            return out
        return (*_cylinder(rng, L, d, colours, 0.4), labels)
    if kind == "wood_screw":
        thread = THREADS[0][rng.integers(1, 4)]                    # ~4-6 mm
        L = rng.uniform(12, 70)
        head = ["flat", "flat", "button"][rng.integers(3)]
        return (*render_bolt(rng, thread, head, L, wood_screw=True), labels)
    # blob: an irregular flat object (key, eraser, plastic part...)
    size = rng.uniform(8, 60)
    n, xx, yy = _canvas(size * 1.2)
    k = int(rng.integers(5, 12))
    ang = np.sort(rng.uniform(0, 2 * np.pi, k))
    rads = size / 2 * rng.uniform(0.35, 1.0, k)
    stretch = rng.uniform(1, 3)
    pts = np.stack([np.cos(ang) * rads * stretch, np.sin(ang) * rads / stretch], 1)
    pts = ((pts + size * 0.6) * RES).astype(np.int32)
    mask = np.zeros((n, n), np.uint8)
    cv2.fillPoly(mask, [pts], 1)
    mask = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), RES) > 0.5
    colour = rng.uniform(20, 240, 3)
    return (*_flat_object(rng, mask, colour, rng.uniform(0, 0.5), bevel_mm=rng.uniform(0.5, 3)), labels)


def _pad_height(bgr, alpha, h):
    """Pad a sprite top and bottom (keeping the axis centred) to at least h px."""
    extra = max(0, h - alpha.shape[0])
    top, bot = extra // 2, extra - extra // 2
    return (np.pad(bgr, ((top, bot), (0, 0), (0, 0))), np.pad(alpha, ((top, bot), (0, 0))))


def _sprite(bgr, alpha, labels):
    return bgr, alpha, np.array([bgr.shape[1] / 2, bgr.shape[0] / 2]), labels


def synth_junk(rng):
    """Bolt-shaped things that must not land in a size bin: double-headed
    pieces, headless threaded rod, snapped bolts, and bolts with a nut still on."""
    # broken stubs are rarer: only their ragged end separates them from a short bolt
    kind = rng.choice(["double_head", "headless", "broken", "nut_on"], p=[0.3, 0.25, 0.15, 0.3])
    labels = dict(NOT_BOLT, label=f"not a bolt ({kind})")
    thread, head, L = pick_bolt(rng)
    d, m = thread.diameter_mm, int(BOLT_MARGIN_MM * RES)
    kh = _head_dims(thread, head)[0]
    bgr, alpha, _ = render_bolt(rng, thread, head, L, fully_threaded=kind == "headless")
    x_end = alpha.shape[1] - m                       # column of the bolt's tip

    if kind == "double_head":                        # mirror the head end onto the tip end
        half = min(x_end, m + int((kh + rng.uniform(0.25, 0.6) * (x_end / RES - 2 * BOLT_MARGIN_MM - kh)) * RES))
        bgr = np.concatenate([bgr[:, :half], bgr[:, :half][:, ::-1]], 1)
        alpha = np.concatenate([alpha[:, :half], alpha[:, :half][:, ::-1]], 1)
    elif kind == "headless":                         # threaded rod: cut the head off
        cut = m + int(kh * RES)
        bgr, alpha = bgr[:, cut - m:], alpha[:, cut - m:].copy()
        alpha[:, :m] = 0
    elif kind == "broken":                           # snapped shank with a ragged end
        cut = min(x_end, m + int((kh + rng.uniform(0.15, 0.6) * (x_end / RES - BOLT_MARGIN_MM - kh)) * RES))
        bgr, alpha = bgr[:, :cut + m].copy(), alpha[:, :cut + m].copy()
        rag = cv2.GaussianBlur(rng.uniform(0, 0.9 * d * RES, (alpha.shape[0], 1)).astype(np.float32),
                               (0, 0), 2).ravel().astype(int)
        for row, o in enumerate(rag):
            alpha[row, cut - o:] = 0
        face = slice(max(0, cut - int(0.9 * d * RES)), cut)
        bgr[:, face] *= rng.uniform(0.45, 0.75)
    else:                                            # a hex nut threaded onto the shank
        af = thread.head_af_mm * rng.uniform(1.0, 1.1)
        bgr, alpha = _pad_height(bgr, alpha, int(af * 1.2 * RES))
        ys = (np.arange(alpha.shape[0]) + 0.5) / RES - alpha.shape[0] / RES / 2
        hmask, hny, hnz = _hex_facets(af, rng.uniform(0, np.pi / 3), ys)
        start = m + int(kh * RES)
        width = int(0.8 * d * RES)
        x0 = start + int(rng.uniform(0.2, 0.8) * max(1, x_end - start - width))
        cols = slice(x0, x0 + width)
        n = _normalise(np.zeros((len(ys), width)), np.repeat(hny[:, None], width, 1),
                       np.repeat(hnz[:, None], width, 1))
        base, kd, ks = MATERIALS[rng.integers(len(MATERIALS))]
        shade, spec = _shade(rng, n, kd)
        nut = _finish(rng, np.array(base, np.float32), shade, spec, ks)
        inside = hmask[:, None] & np.ones((1, width), bool)
        bgr[:, cols][inside] = nut[inside]
        alpha[:, cols][inside] = 1.0
    return _sprite(bgr.astype(np.float32), alpha.astype(np.float32), labels)


# --- Scene + camera -----------------------------------------------------------

def _rot(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s], [s, c]])


def _soft_blur(mask, sigma):
    """Blur broad shadows at a smaller resolution to bound memory and work."""
    if sigma < 6:
        return cv2.GaussianBlur(mask, (0, 0), sigma)
    h, w = mask.shape[:2]
    small = cv2.resize(mask, (w // 4, h // 4), interpolation=cv2.INTER_AREA)
    return cv2.resize(cv2.GaussianBlur(small, (0, 0), sigma / 4), (w, h))


def render_camera(rng, sprite_fn=synth_bolt, heavy=False, return_mask=False):
    """One simulated camera frame. sprite_fn(rng) -> (bgr, alpha, centre_px,
    labels[, head/shank coverage]) at RES px/mm, or None for an empty board.

    Returns (bgr, H plane-mm -> ideal px, lens, labels); return_mask adds coverage."""
    sizes = HEAVY_CAMERA_SIZES if heavy else CAMERA_SIZES
    W, Hh = sizes[rng.integers(len(sizes))]
    a = rng.uniform(2.2, min(6.0, W / 130)) if heavy else rng.uniform(2.5, min(7.0, W / 140))
    tilt = 0.2 if heavy else 0.12

    S = 100.0
    sq = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]], np.float64) * S / 2
    plane_pts = sq @ _rot(rng.uniform(0, 2 * np.pi)).T + rng.uniform(-50, 50, 2)
    img_pts = (sq * a + [W / 2, Hh / 2] + rng.uniform(-0.05, 0.05, 2) * [W, Hh]
               + np.clip(rng.normal(0, tilt / 2.4 * S * a, (4, 2)), -tilt * S * a, tilt * S * a))
    H = cv2.getPerspectiveTransform(plane_pts.astype(np.float32), img_pts.astype(np.float32))
    centre_mm = cv2.perspectiveTransform(np.array([[[W / 2, Hh / 2]]], np.float64),
                                         np.linalg.inv(H))[0, 0]

    # Board
    n = int(RENDER_MM * RES)
    x0 = centre_mm - RENDER_MM / 2
    coords = (np.arange(n) + 0.5) / RES
    cx = np.floor((x0[0] + coords) / SQUARE_MM).astype(int)
    cy = np.floor((x0[1] + coords) / SQUARE_MM).astype(int)
    checker = ((cy[:, None] + cx[None, :]) % 2).astype(np.float32)
    white = rng.uniform(205, 250) * rng.uniform(0.95, 1.05, 3)
    black = rng.uniform(15, 60) * rng.uniform(0.9, 1.1, 3)
    img = np.empty((n, n, 3), np.float32)
    np.multiply(checker[..., None], (white - black).astype(np.float32), out=img)
    img += black.astype(np.float32)
    if heavy and rng.uniform() < 0.5:                          # dust and crumbs
        for _ in range(int(rng.integers(20, 200))):
            p = tuple(int(v) for v in rng.uniform(0, n, 2))
            cv2.circle(img, p, int(rng.uniform(1, 6)), tuple(float(v) for v in rng.uniform(0, 255, 3)), -1)

    # Object + soft shadow
    parts_w = None
    sprite = sprite_fn(rng)
    if sprite is None:
        labels = dict(NOT_BOLT, label="not a bolt (empty board)")
    else:
        obj, alpha, centre_px, labels = sprite[:4]
        extent = np.hypot(*obj.shape[:2]) / RES
        room = max(0.0, min(20.0, CANVAS_MM / 2 - 6 - extent / 2))
        pos = centre_mm + rng.uniform(-room, room, 2)
        Rm = _rot(rng.uniform(0, 2 * np.pi))
        t = RES * (pos - x0) - Rm @ centre_px
        A = np.hstack([Rm, t[:, None]]).astype(np.float32)
        obj_w = cv2.warpAffine(obj, A, (n, n))
        alpha_w = cv2.warpAffine(alpha, A, (n, n))
        if return_mask and len(sprite) == 5 and labels["is_bolt"]:
            parts_w = cv2.warpAffine(sprite[4], A, (n, n))
        A_sh = A.copy()
        A_sh[:, 2] += rng.uniform(-1, 1, 2) * rng.uniform(1, 4) * RES
        shadow = _soft_blur(cv2.warpAffine(alpha, A_sh, (n, n)), rng.uniform(1, 4) * RES)
        img *= 1 - rng.uniform(0.2, 0.6) * shadow[..., None]
        img *= 1 - alpha_w[..., None]
        obj_w *= alpha_w[..., None]
        img += obj_w

    # Uneven (and in heavy mode, coloured) lighting; heavy mode adds a cast shadow
    g = np.linspace(-1, 1, n, dtype=np.float32)
    amp = 0.35 if heavy else 0.15
    gx, gy = rng.uniform(-amp, amp, 2).astype(np.float32)
    light = (1 + gx * g[None, :] + gy * g[:, None])[..., None]
    if heavy:
        light = light * (1 + rng.uniform(-0.15, 0.15, 3).astype(np.float32) * g[None, :, None])
        if rng.uniform() < 0.5:
            poly = (rng.uniform(0, n, (4, 2))).astype(np.int32)
            sh = np.zeros((n, n), np.float32)
            cv2.fillPoly(sh, [poly], 1.0)
            sh = _soft_blur(sh, rng.uniform(1, 5) * RES)
            light = light * (1 - rng.uniform(0.3, 0.65) * sh[..., None])
    img *= light

    # Project into an ideal pinhole camera, padded so lens distortion has
    # something to pull in from beyond the frame edges.
    img = cv2.GaussianBlur(img, (0, 0), 0.45 * RES / a)
    pad = int(0.25 * max(W, Hh))
    T = np.array([[1 / RES, 0, x0[0] + 0.5 / RES], [0, 1 / RES, x0[1] + 0.5 / RES], [0, 0, 1]])
    shift = np.array([[1, 0, pad], [0, 1, pad], [0, 0, 1]], np.float64)
    table = tuple(float(v) for v in rng.uniform(60, 160, 3))
    ideal = cv2.warpPerspective(img, shift @ H @ T, (W + 2 * pad, Hh + 2 * pad),
                                flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                                borderValue=table)
    if heavy and rng.uniform() < 0.5:                          # specular glare
        gh, gw = ideal.shape[:2]
        blob = np.zeros((gh, gw), np.float32)
        centre = tuple(int(v) for v in rng.uniform([0, 0], [gw, gh]))
        axes = tuple(int(v) for v in rng.uniform(20, 0.25 * W, 2))
        cv2.ellipse(blob, centre, axes, rng.uniform(0, 180), 0, 360, 1.0, -1)
        ideal += rng.uniform(80, 220) * cv2.GaussianBlur(blob, (0, 0), axes[0] / 2 + 1)[..., None]

    lens = random_lens(rng, W, Hh, heavy)
    cam = apply_lens(rng, ideal, lens, W, Hh, pad, heavy)
    cam = camera_noise(rng, cam, heavy)
    if not return_mask:
        return cam, H, lens, labels
    if parts_w is None:
        return cam, H, lens, labels, np.zeros((Hh, W, 2), np.float32)
    ideal_parts = cv2.warpPerspective(parts_w, shift @ H @ T,
                                      (W + 2 * pad, Hh + 2 * pad))
    yd, xd = np.mgrid[0:Hh, 0:W].astype(np.float32)
    xi, yi = lens_to_ideal(lens, xd, yd)
    parts = cv2.remap(ideal_parts, (xi + pad).astype(np.float32),
                      (yi + pad).astype(np.float32), cv2.INTER_LINEAR)
    return cam, H, lens, labels, parts


# --- Lens -----------------------------------------------------------------

def random_lens(rng, W, Hh, heavy=False):
    """Brown-Conrady lens, written as distorted -> ideal pixel coordinates.
    k1 > 0 is barrel distortion (typical of wide Pi camera lenses)."""
    if heavy:
        k, p = (rng.uniform(-0.15, 0.5), rng.uniform(-0.1, 0.2)), tuple(rng.normal(0, 0.004, 2))
    else:
        k_scale = 0.1 if rng.uniform() < 0.3 else 1.0     # 0.1: as if calibrate.py was used
        k = (rng.uniform(-0.08, 0.30) * k_scale, rng.uniform(-0.05, 0.10) * k_scale)
        p = tuple(rng.normal(0, 0.002, 2) * k_scale)
    return {"f": W * rng.uniform(0.7, 1.3), "k": k, "p": p,
            "c": (W / 2 + rng.normal(0, 0.02 * W), Hh / 2 + rng.normal(0, 0.02 * Hh))}


def lens_to_ideal(lens, xd, yd):
    f, (k1, k2), (p1, p2), (cx, cy) = lens["f"], lens["k"], lens["p"], lens["c"]
    x, y = (xd - cx) / f, (yd - cy) / f
    r2 = x * x + y * y
    rad = 1 + k1 * r2 + k2 * r2 * r2
    xi = x * rad + 2 * p1 * x * y + p2 * (r2 + 2 * x * x)
    yi = y * rad + p1 * (r2 + 2 * y * y) + 2 * p2 * x * y
    return xi * f + cx, yi * f + cy


def ideal_to_lens(lens, pts):
    """Inverse of lens_to_ideal by fixed-point iteration (for a few points)."""
    xd = pts.astype(np.float64).copy()
    with np.errstate(all="ignore"):           # far-off-frame points may diverge -> NaN, dropped later
        for _ in range(30):
            xi, yi = lens_to_ideal(lens, xd[:, 0], xd[:, 1])
            xd += np.clip(pts - np.stack([xi, yi], 1), -50, 50)
    return xd


def apply_lens(rng, ideal, lens, W, Hh, pad, heavy=False):
    """Distort, add lateral chromatic aberration and vignetting."""
    yd, xd = np.mgrid[0:Hh, 0:W].astype(np.float32)
    xi, yi = lens_to_ideal(lens, xd, yd)
    cx, cy = lens["c"]
    ca = rng.uniform(0, 0.006 if heavy else 0.003)
    out = np.empty((Hh, W, 3), np.float32)
    for ch, s in zip(range(3), (1 - ca, 1.0, 1 + ca)):        # B, G, R
        mx = (cx + (xi - cx) * s + pad).astype(np.float32)
        my = (cy + (yi - cy) * s + pad).astype(np.float32)
        out[..., ch] = cv2.remap(ideal[..., ch], mx, my, cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_REFLECT)
    r2 = ((xd - cx) ** 2 + (yd - cy) ** 2) / (0.5 * np.hypot(W, Hh)) ** 2
    out *= (1 - rng.uniform(0, 0.6 if heavy else 0.4) * r2)[..., None]
    return out


# --- Sensor / ISP -----------------------------------------------------------

def camera_noise(rng, img, heavy=False):
    """Cheap-camera image pipeline: blur, exposure, white balance, shot/read/
    chroma noise, hot pixels, over-sharpening, gamma, JPEG."""
    h, w = img.shape[:2]
    if heavy or rng.uniform() < 0.8:
        img = cv2.GaussianBlur(img, (0, 0), rng.uniform(0.8, 2.5) if heavy else rng.uniform(0.3, 1.3))
    if rng.uniform() < (0.5 if heavy else 0.25):              # hand shake
        n = int(rng.integers(5, 16) if heavy else rng.integers(3, 8))
        k = np.zeros((n, n), np.float32)
        k[n // 2, :] = 1 / n
        rot = cv2.getRotationMatrix2D(((n - 1) / 2, (n - 1) / 2), rng.uniform(0, 180), 1)
        k = cv2.warpAffine(k, rot, (n, n))
        img = cv2.filter2D(img, -1, k / max(k.sum(), 1e-6))
    if rng.uniform() < (0.5 if heavy else 0.3):               # low-res sensor upscaled
        s = rng.uniform(0.35, 0.8) if heavy else rng.uniform(0.5, 0.9)
        img = cv2.resize(cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA),
                         (w, h), interpolation=cv2.INTER_LINEAR)

    if heavy:
        img = img * rng.uniform(0.35, 1.4) * rng.uniform(0.75, 1.25, 3).astype(np.float32) + rng.uniform(-25, 25)
    else:
        img = img * rng.uniform(0.7, 1.25) * rng.uniform(0.88, 1.12, 3).astype(np.float32) + rng.uniform(-15, 15)
    img = np.clip(img, 0, 255)
    shot = rng.uniform(0.3, 2.0) if heavy else rng.uniform(0.05, 0.8)
    img = img + rng.normal(0, 1, img.shape).astype(np.float32) * np.sqrt(img * shot)
    img = img + rng.normal(0, rng.uniform(4, 15) if heavy else rng.uniform(1, 6), img.shape).astype(np.float32)
    if rng.uniform() < (0.9 if heavy else 0.6):               # chroma blotches
        sd = rng.uniform(4, 14) if heavy else rng.uniform(2, 8)
        small = rng.normal(0, sd, (h // 4, w // 4, 3)).astype(np.float32)
        img = img + cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)
    if rng.uniform() < (0.5 if heavy else 0.3):               # hot pixels
        n = int(h * w * rng.uniform(1e-5, 2e-4))
        img[rng.integers(0, h, n), rng.integers(0, w, n)] = rng.uniform(150, 255, (n, 1))
    img = img.astype(np.float32)
    if rng.uniform() < 0.5:                                    # ISP sharpening halos
        img = img + rng.uniform(0.3, 1.2) * (img - cv2.GaussianBlur(img, (0, 0), 1.0))
    img = 255 * np.clip(img / 255, 0, 1) ** (rng.uniform(0.7, 1.4) if heavy else rng.uniform(0.8, 1.25))

    q = rng.uniform(15, 55) if heavy else rng.uniform(40, 90)
    _, buf = cv2.imencode(".jpg", img.astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, int(q)])
    return cv2.imdecode(buf, cv2.IMREAD_COLOR)


def make_canvas(rng, sprite_fn=synth_bolt, heavy=False, return_mask=False):
    """Synthetic canvas, rectified the way real frames are: a homography fitted
    to a patch of (noisy, lens-distorted) checker corners, so leftover lens
    warp ends up in the training data too. return_mask adds a 256px class mask."""
    result = render_camera(rng, sprite_fn, heavy, return_mask=return_mask)
    cam, H, lens, labels = result[:4]
    h, w = cam.shape[:2]
    ci = lens_to_ideal(lens, np.float64(w / 2), np.float64(h / 2))
    c = cv2.perspectiveTransform(np.array([[ci]], np.float64), np.linalg.inv(H))[0, 0]
    base = np.round(c / SQUARE_MM)
    for _ in range(10):
        nx, ny = rng.integers(5, 16, 2)
        ox, oy = rng.integers(-12, 6, 2)
        jj, ii = np.meshgrid(np.arange(nx) + ox + base[0], np.arange(ny) + oy + base[1])
        plane = np.stack([jj.ravel(), ii.ravel()], 1) * SQUARE_MM
        ideal = cv2.perspectiveTransform(plane[None], H)[0]
        img_pts = ideal_to_lens(lens, ideal) + rng.normal(0, 0.6 if heavy else 0.3, ideal.shape)
        inside = ((img_pts >= 0) & (img_pts < [w, h])).all(1)
        if inside.sum() >= 25:
            break
    Hfit = None
    if inside.sum() >= 4:
        Hfit, _ = cv2.findHomography(plane[inside].astype(np.float32),
                                     img_pts[inside].astype(np.float32))
    canvas, matrix = rectify(cam, H if Hfit is None else Hfit, return_matrix=True)
    if not return_mask:
        return canvas, labels
    parts = cv2.warpPerspective(result[4], matrix, (512, 512),
                                flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)
    parts = cv2.resize(parts, (256, 256), interpolation=cv2.INTER_AREA)
    probs = np.dstack([np.clip(1 - parts.sum(2), 0, 1), parts])
    return canvas, labels, probs.argmax(2).astype(np.uint8)
