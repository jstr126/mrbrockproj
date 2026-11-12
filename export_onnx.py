"""Export fp32 ONNX, check torch agreement, and fit v3 validation calibration."""
import argparse
from pathlib import Path

import numpy as np
import torch

from bolt_sizer.board import CANVAS_PX
from bolt_sizer.model import load


def export(ckpt, out):
    model, _ = load(ckpt, 'cpu')
    dummy = torch.rand(1, 3, CANVAS_PX, CANVAS_PX)
    names = ['size', 'system', 'type', 'bolt'] + (['mask'] if model.segmentation else [])
    torch.onnx.export(model, (dummy,), out, input_names=['canvas'],
                      output_names=names, opset_version=17,
                      dynamic_axes={k: {0: 'batch'} for k in ['canvas', *names]},
                      dynamo=False)
    return model


def verify(model, out):
    import onnx
    import onnxruntime as ort
    onnx.checker.check_model(onnx.load(out))
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 2
    sess = ort.InferenceSession(out, opts, providers=['CPUExecutionProvider'])
    largest = 0.
    for batch in (1, 2):
        x = torch.rand(batch, 3, CANVAS_PX, CANVAS_PX)
        with torch.no_grad():
            ref = [t.numpy() for t in model(x)]
        got = sess.run(None, {'canvas': x.numpy()})
        if len(ref) != len(got):
            raise AssertionError('ONNX output count differs from torch')
        for name, r, g in zip([o.name for o in sess.get_outputs()], ref, got):
            np.testing.assert_allclose(r, g, rtol=1e-3, atol=2e-4, err_msg=name)
            largest = max(largest, float(np.abs(r - g).max()))
    return largest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ckpt', default='models/boltnet.pt')
    ap.add_argument('--out', help='default: <ckpt>.onnx')
    ap.add_argument('--skip-measurement-calibration', action='store_true', help='development only; v3 size bins disabled')
    a = ap.parse_args()
    out = a.out or str(Path(a.ckpt).with_suffix('.onnx'))
    model = export(a.ckpt, out)
    error = verify(model, out)
    print(f'wrote {out} ({Path(out).stat().st_size / 1e6:.1f} MB), max torch diff {error:.2e}', flush=True)
    if model.segmentation and not a.skip_measurement_calibration:
        from tools.calibrate_measurement import calibrate, write_metadata
        calibration = calibrate(out, a.ckpt)
        write_metadata(out, calibration)
        print(f'validation measurement calibration: {calibration}', flush=True)


if __name__ == '__main__':
    main()
