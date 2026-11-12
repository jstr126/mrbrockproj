"""Sub-pixel outline measurements and native-frame pitch. No torch."""
import cv2
import numpy as np

from .board import PX_PER_MM
from .standards import THREADS, lengths_mm, snap


def calibrated_size(regression, geometry, calibration):
    """Apply validation-fitted size correction; retain legacy metadata behavior."""
    reg, geo = np.asarray(regression), np.asarray(geometry)
    reg = reg * np.asarray(calibration.get('regression_gain', [1., 1.]))
    reg = reg + np.asarray(calibration.get('regression_offset', [0., 0.]))
    geo = geo * np.asarray(calibration['gain']) + np.asarray(calibration['offset'])
    weights = np.asarray(calibration.get('fusion_weights', [.8, .8]))
    return weights * geo + (1 - weights) * reg, reg, geo


def standard_evidence(size, system_p, parameters):
    """Combine network evidence with distance to each system's standard sizes.

    This score is not a calibrated probability. A conflict with the network
    must still bypass, rather than become a confident automatic assignment.
    """
    scales = np.array([parameters['diameter_sigma'], parameters['length_sigma']])
    prior_weight = float(parameters['prior_weight'])
    if not np.isfinite(scales).all() or (scales <= 0).any() or not np.isfinite(prior_weight) or prior_weight <= 0:
        raise ValueError('Invalid standard-evidence calibration')
    costs = []
    for system in (0, 1):
        thread, length = snap(system, *size)
        residual = (np.asarray(size) - [thread.diameter_mm, length]) / scales
        costs.append(float(residual @ residual - prior_weight * np.log(max(float(system_p[system]), 1e-8))))
    logits = -np.asarray(costs)
    probabilities = np.exp(logits - logits.max())
    probabilities /= probabilities.sum()
    return probabilities, {'network_system': int(np.argmax(system_p)),
                           'selected_system': int(np.argmax(probabilities)),
                           'costs': costs}


def _crossings(values, threshold=0.5):
    inside = np.flatnonzero(values >= threshold)
    if not len(inside):
        return None
    lo, hi = int(inside[0]), int(inside[-1])
    left, right = float(lo) - .5, float(hi) + .5
    if lo > 0:
        left = lo - 1 + (threshold - values[lo - 1]) / max(values[lo] - values[lo - 1], 1e-8)
    if hi + 1 < len(values):
        right = hi + (values[hi] - threshold) / max(values[hi] - values[hi + 1], 1e-8)
    return left, right


def outline_size(prob, head='hex'):
    """Measure a (background, head, shank) probability map; canvas coordinates."""
    prob = np.asarray(prob, np.float32)
    if prob.shape != (3, 256, 256) or not np.isfinite(prob).all():
        return None
    fg = prob[1:].sum(0)
    n, labels, stats, _ = cv2.connectedComponentsWithStats((fg >= .5).astype(np.uint8))
    if n < 2:
        return None
    k = 1 + int(stats[1:, cv2.CC_STAT_AREA].argmax())
    component = labels == k
    if component.sum() < 20 or component.sum() < .6 * (fg >= .5).sum():
        return None
    ys, xs = np.nonzero(component)
    if min(xs.min(), ys.min()) < 2 or max(xs.max(), ys.max()) > 253:
        return None
    support = cv2.dilate(component.astype(np.uint8), np.ones((5, 5), np.uint8))
    weights = fg * support
    yy, xx = np.mgrid[:256, :256]
    pts = np.stack([xx.ravel(), yy.ravel()], 1)
    w = weights.ravel()
    centre = np.average(pts, axis=0, weights=w)
    cov = ((pts - centre) * w[:, None]).T @ (pts - centre) / w.sum()
    eig, basis = np.linalg.eigh(cov)
    axis = basis[:, -1]
    head_w, shank_w = ((prob[i] * support).ravel() for i in (1, 2))
    if head_w.sum() < 2 or shank_w.sum() < 8 or eig[-1] < 1.2 * eig[0]:
        return None
    hc, sc = (np.average(pts, axis=0, weights=v) for v in (head_w, shank_w))
    if np.dot(sc - hc, axis) < 0:
        axis = -axis
    perp = np.array([-axis[1], axis[0]])
    occupied = np.stack([xs, ys], 1) - centre
    ta, sa = occupied @ axis, occupied @ perp
    dt = .5
    ts = np.arange(np.floor(ta.min()) - 3, np.ceil(ta.max()) + 3, dt)
    ss = np.arange(np.floor(sa.min()) - 3, np.ceil(sa.max()) + 3, dt)
    xy = centre + ts[:, None, None] * axis + ss[None, :, None] * perp
    maps = [cv2.remap(prob[i] * support, xy[..., 0].astype(np.float32),
                      xy[..., 1].astype(np.float32), cv2.INTER_LINEAR) for i in (1, 2)]
    shank_bounds = _crossings(maps[1].max(1))
    total_bounds = _crossings((maps[0] + maps[1]).max(1))
    if shank_bounds is None or total_bounds is None:
        return None
    start, tip = (ts[0] + dt * x for x in shank_bounds)
    overall = ts[0] + dt * total_bounds[0]
    length = tip - (overall if head == 'flat' else start)
    rows = (ts > start + .25 * (tip - start)) & (ts < tip - .10 * (tip - start))
    widths = []
    for values in maps[1][rows]:
        bounds = _crossings(values)
        if bounds is not None:
            widths.append((bounds[1] - bounds[0]) * dt)
    if len(widths) < 5 or length < 4:
        return None
    diameter = float(np.percentile(widths, 90))
    # Mask pixels have centres at 2*x + 0.5 in the 512 canvas.
    scale = 2 / PX_PER_MM
    return {'diameter_mm': diameter * scale, 'length_mm': length * scale,
            'centre': centre * 2 + .5, 'axis': axis, 'shank_start_px': start * 2,
            'tip_px': tip * 2, 'quality': float(np.mean(fg[component]))}


def half_step(system, diameter, length):
    """Half the nearest local standard step, separately within one system."""
    out = []
    for values, x in (([t.diameter_mm for t in THREADS[system]], diameter),
                      (lengths_mm(system), length)):
        values = np.sort(values)
        i = int(np.abs(values - x).argmin())
        gaps = [abs(values[j] - values[i]) for j in (i - 1, i + 1) if 0 <= j < len(values)]
        out.append(min(gaps) / 2)
    return np.array(out)


def thread_pitch(frame, matrix, geometry, shank_prob=None):
    """FFT on native-frame lines. Return evidence only when both pitches resolve."""
    if frame is None or matrix is None or geometry is None:
        return None
    d = geometry['diameter_mm']
    choices = [min(THREADS[s], key=lambda t: abs(t.diameter_mm - d)) for s in (0, 1)]
    pitches = np.array([t.pitch_mm for t in choices])
    if any(abs(t.diameter_mm - d) > max(.7, .12 * d) for t in choices):
        return None
    centre, axis = geometry['centre'], geometry['axis']
    start, end = geometry['shank_start_px'], geometry['tip_px']
    # The distal half is threaded even on a partly threaded bolt.
    start = start + .45 * (end - start)
    end -= min(d * PX_PER_MM * .35, (end - start) * .1)
    span_mm = (end - start) / PX_PER_MM
    if span_mm < 6 * pitches.max():
        return None
    endpoints = centre + np.array([start, (start + end) / 2, end])[:, None] * axis
    native = cv2.perspectiveTransform(endpoints[None].astype(np.float64), matrix)[0]
    density = np.linalg.norm(np.diff(native, axis=0), axis=1) / (span_mm / 2)
    if density.min() * pitches.min() < 3.5:
        return None
    count = int(np.ceil(span_mm * density.max())) + 1
    if count < 32 or count > 4096:
        return None
    ts = np.linspace(start, end, count)
    perp = np.array([-axis[1], axis[0]])
    offsets = np.array([-.30, -.15, 0, .15, .30]) * d * PX_PER_MM
    points = centre + ts[None, :, None] * axis + offsets[:, None, None] * perp
    if shank_prob is not None:
        confidence = cv2.remap(shank_prob.astype(np.float32),
                               ((points[..., 0] - .5) / 2).astype(np.float32),
                               ((points[..., 1] - .5) / 2).astype(np.float32), cv2.INTER_LINEAR)
        good = (confidence >= .7).mean(1) >= .85
        points = points[good]
        if len(points) < 3:
            return None
    native = cv2.perspectiveTransform(points.reshape(1, -1, 2).astype(np.float64), matrix)[0].reshape(-1, count, 2)
    h, w = frame.shape[:2]
    if ((native < 1).any() or (native[..., 0] >= w - 2).any() or (native[..., 1] >= h - 2).any()):
        return None
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
    signals = cv2.remap(gray.astype(np.float32), native[..., 0].astype(np.float32),
                         native[..., 1].astype(np.float32), cv2.INTER_LINEAR)
    x = np.linspace(-1, 1, count)
    trends = np.stack([np.ones(count), x], 1)
    signals -= (trends @ np.linalg.lstsq(trends, signals.T, rcond=None)[0]).T
    if np.median(signals.std(1)) < 2:
        return None
    fft_n = 1 << int(np.ceil(np.log2(count * 4)))
    powers = np.abs(np.fft.rfft(signals * np.hanning(count), n=fft_n, axis=1)) ** 2
    spacing = span_mm / (count - 1)
    freq = np.fft.rfftfreq(fft_n, spacing)
    band_energy = powers[:, (freq > .3) & (freq < 2.8)].sum(1, keepdims=True)
    # Require agreement across lines; a stray board edge must not dominate.
    power = np.median(powers / np.maximum(band_energy, 1e-12), axis=0)
    allowed = (freq >= .75 / pitches.max()) & (freq <= 1.25 / pitches.min())
    ids = np.flatnonzero(allowed)
    if len(ids) < 3:
        return None
    peak = int(ids[np.argmax(power[ids])])
    if peak == ids[0] or peak == ids[-1]:
        return None
    logp = np.log(power[peak - 1:peak + 2] + 1e-12)
    off = .5 * (logp[0] - logp[2]) / (logp[0] - 2 * logp[1] + logp[2] + 1e-12)
    period = 1 / ((peak + float(np.clip(off, -.5, .5))) / (fft_n * spacing))
    errors = np.abs(pitches - period) / pitches
    winner = int(errors.argmin())
    # FFT main-lobe power and a clear margin over the other thread system.
    band = np.abs(freq - freq[peak]) < 1.25 / span_mm
    strength = float(power[band].sum() / max(power[(freq > .3) & (freq < 2.8)].sum(), 1e-12))
    separation = abs(1 / pitches[0] - 1 / pitches[1]) * span_mm
    strong = strength >= .35 and errors[winner] < .07 and errors[1 - winner] - errors[winner] > .05 and separation > 1.5
    return {'pitch_mm': float(period), 'strength': strength, 'system': winner if strong else None,
            'native_px_per_mm': float(density.min())}
