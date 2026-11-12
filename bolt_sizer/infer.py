"""Runtime for the exported ONNX model. Needs only numpy, OpenCV and
onnxruntime, so it runs on a Raspberry Pi without PyTorch."""
from collections import deque
import json

import numpy as np

from .catalog import CATALOG
from .measure import outline_size, half_step, thread_pitch, calibrated_size, standard_evidence
from .standards import (HEAD_TYPES, HEAD_TYPE_NAMES, SYSTEM_NAMES, snap, format_label)

DIAM_SCALE, LEN_SCALE = 10.0, 50.0       # must match bolt_sizer/model.py


def _softmax(z):
    e = np.exp(z - z.max(-1, keepdims=True))
    return e / e.sum(-1, keepdims=True)


def preprocess(canvas_bgr):
    rgb = canvas_bgr[:, :, ::-1].astype(np.float32) / 255.0
    return np.ascontiguousarray(rgb.transpose(2, 0, 1))[None]


def sort_bin(r):
    """Which bin a decoded result goes to, using the catalog's sorting rules."""
    rules = CATALOG["sorting_rules"]
    if not r["is_bolt"]:
        return rules["reject_bin"] if r["bolt_conf"] >= rules["min_bolt_conf"] else rules["review_bin"]
    if r.get("measurement_disagreement") or r.get("outline_missing") or r.get('system_evidence_disagreement'):
        return rules["review_bin"]
    if (r["bolt_conf"] < rules["min_bolt_conf"] or r["system_conf"] < rules["min_system_conf"]
            or r["type_conf"] < rules["min_type_conf"]):
        return rules["review_bin"]
    return r["label"]


def decode(size, system_p, type_p, bolt_p):
    """size: (2,) scaled diameter/length; the rest are class probabilities."""
    if bolt_p[1] < 0.5:
        r = {"is_bolt": False, "label": "not a bolt", "bolt_conf": float(bolt_p[0])}
        return {**r, "bin": sort_bin(r)}
    diameter, length = float(size[0]) * DIAM_SCALE, float(size[1]) * LEN_SCALE
    system = int(np.argmax(system_p))
    head = HEAD_TYPES[int(np.argmax(type_p))]
    thread, nominal_len = snap(system, diameter, length)
    alt_thread, alt_len = snap(1 - system, diameter, length)
    r = {
        "is_bolt": True,
        "bolt_conf": float(bolt_p[1]),
        "label": format_label(thread, nominal_len, head),
        "thread": thread.name,
        "diameter_mm": thread.diameter_mm,
        "length_mm": nominal_len,
        "head_type": HEAD_TYPE_NAMES[head],
        "system": SYSTEM_NAMES[system],
        "system_conf": float(system_p[system]),
        "type_conf": float(np.max(type_p)),
        "measured_diameter_mm": diameter,
        "measured_length_mm": length,
        "alternative": format_label(alt_thread, alt_len),
    }
    return {**r, "bin": sort_bin(r)}


class BoltSizer:
    def __init__(self, onnx_path, threads=0):
        import onnxruntime as ort
        opts = ort.SessionOptions()
        if threads:
            opts.intra_op_num_threads = threads
        self.sess = ort.InferenceSession(onnx_path, opts, providers=["CPUExecutionProvider"])
        self.input = self.sess.get_inputs()[0].name
        metadata = self.sess.get_modelmeta().custom_metadata_map
        if "head_types" in metadata and json.loads(metadata["head_types"]) != HEAD_TYPES:
            raise ValueError("ONNX head order differs from the active catalog")
        self.calibration = json.loads(metadata.get("measurement_calibration", "null"))

    def raw(self, canvas_bgr, tta=1):
        """Network outputs; tta>1 also averages over rotated/flipped copies
        (better accuracy, tta x slower)."""
        if not 1 <= tta <= 8:
            raise ValueError("tta must be between 1 and 8")
        x = preprocess(canvas_bgr)
        views = [x]
        for k in range(1, tta):
            v = np.rot90(x, k % 4, axes=(2, 3))
            views.append(np.ascontiguousarray(v[..., ::-1] if k >= 4 else v))
        outputs = self.sess.run(None, {self.input: np.concatenate(views)})
        size, sys_l, type_l, bolt_l = outputs[:4]
        result = (size.mean(0), _softmax(sys_l).mean(0), _softmax(type_l).mean(0),
                  _softmax(bolt_l).mean(0))
        if len(outputs) == 5:
            z = outputs[4]
            exp = np.exp(z - z.max(1, keepdims=True))
            probs = exp / exp.sum(1, keepdims=True)
            aligned = []
            for k, prob in enumerate(probs):
                if k >= 4:
                    prob = prob[..., ::-1]
                aligned.append(np.rot90(prob, -(k % 4), axes=(1, 2)))
            return (*result, np.mean(aligned, axis=0))
        return result

    def decode_raw(self, raw, frame=None, canvas_to_frame=None):
        size, system_p, type_p, bolt_p = raw[:4]
        if len(raw) == 4 or bolt_p[1] < .5:
            return decode(size, system_p, type_p, bolt_p)
        head = HEAD_TYPES[int(np.argmax(type_p))]
        geometry = outline_size(raw[4], head)
        if geometry is None:
            r = decode(size, system_p, type_p, bolt_p)
            r['outline_missing'] = True
            r['bin'] = sort_bin(r)
            return r
        reg = np.asarray(size, np.float64) * [DIAM_SCALE, LEN_SCALE]
        geo = np.array([geometry['diameter_mm'], geometry['length_mm']])
        fused = reg
        if self.calibration is not None:
            fused, reg, geo = calibrated_size(reg, geo, self.calibration)
        pitch_geometry = {**geometry, 'diameter_mm': float(fused[0])}
        pitch = thread_pitch(frame, canvas_to_frame, pitch_geometry, raw[4][2])
        evidence = None
        if pitch is not None and pitch['system'] is not None:
            system_p = np.full(2, .05, np.float32)
            system_p[pitch['system']] = .95
        elif self.calibration is not None and 'standard_evidence' in self.calibration:
            network_p = system_p
            system_p, evidence = standard_evidence(fused, system_p, self.calibration['standard_evidence'])
        r = decode(fused / [DIAM_SCALE, LEN_SCALE], system_p, type_p, bolt_p)
        if evidence is not None:
            r['system_evidence'] = evidence
            r['system_evidence_disagreement'] = evidence['network_system'] != evidence['selected_system']
            r['network_system_conf'] = float(network_p[evidence['selected_system']])
            # The combined score cannot inflate confidence beyond network evidence.
            r['system_conf'] = min(r['system_conf'], r['network_system_conf'])
        if self.calibration is None:
            # An uncalibrated decoder may be inspected but cannot route to size bins.
            r['outline_missing'] = True
        else:
            steps = half_step(int(np.argmax(system_p)), *fused)
            disagreement = np.abs(geo - reg) / steps
            r['measurement_disagreement'] = bool(np.any(disagreement > 1))
            r['measurement_disagreement_steps'] = disagreement.tolist()
            r['bin_offset_steps'] = (np.abs(fused - [r['diameter_mm'], r['length_mm']]) / steps).tolist()
        r['outline_quality'] = geometry['quality']
        r['outline_diameter_mm'], r['outline_length_mm'] = map(float, geo)
        r['regression_diameter_mm'], r['regression_length_mm'] = map(float, reg)
        if pitch is not None:
            r['pitch'] = pitch
        r['bin'] = sort_bin(r)
        return r

    def predict(self, canvas_bgr, tta=1, frame=None, canvas_to_frame=None, smoother=None):
        raw = self.raw(canvas_bgr, tta)
        if smoother is not None:
            raw = smoother.average(raw)
        return self.decode_raw(raw, frame, canvas_to_frame)


class Smoother:
    """Averages the last few frames' outputs so a live readout doesn't flicker."""
    def __init__(self, n=8):
        self.buf = deque(maxlen=n)

    def reset(self):
        self.buf.clear()

    def average(self, raw):
        self.buf.append(raw[:4])
        means = tuple(np.mean([r[i] for r in self.buf], 0) for i in range(4))
        # The outline stays in the current frame's coordinates.
        return (*means, raw[4]) if len(raw) == 5 else means

    def __call__(self, raw):
        return decode(*self.average(raw)[:4])
