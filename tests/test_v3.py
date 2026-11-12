"""Checks for physical dimensions, transform alignment and safe routing."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np

from bolt_sizer.board import rectify, detect_board
from bolt_sizer.infer import BoltSizer, Smoother, decode
from bolt_sizer.measure import outline_size, thread_pitch, calibrated_size, standard_evidence
from bolt_sizer.standards import HEAD_TYPES, THREADS
from bolt_sizer.synth import render_bolt
from tools.calibrate_measurement import fit_linear, fit_fusion


def rectangle():
    prob = np.zeros((3, 256, 256), np.float32)
    prob[1, 110:146, 40:50] = 1
    prob[2, 120:136, 50:130] = 1
    prob[0] = 1 - prob[1:].sum(0)
    return prob


class GeometryTests(unittest.TestCase):
    def test_rectangles_and_flat_convention(self):
        p = rectangle()
        a, b = outline_size(p), outline_size(p, 'flat')
        self.assertAlmostEqual(a['diameter_mm'], 8., delta=.02)
        self.assertAlmostEqual(a['length_mm'], 40., delta=.02)
        self.assertAlmostEqual(b['length_mm'], 45., delta=.02)

    def test_rotation_and_soft_edges(self):
        p = rectangle()
        for angle in (0, 27, 90, 143, 270):
            A = cv2.getRotationMatrix2D((128, 128), angle, 1)
            q = np.stack([cv2.warpAffine(v, A, (256, 256), borderValue=int(i == 0)) for i, v in enumerate(p)])
            q = np.stack([cv2.GaussianBlur(v, (0, 0), .5) for v in q])
            g = outline_size(q)
            self.assertIsNotNone(g)
            self.assertAlmostEqual(g['diameter_mm'], 8., delta=.25)
            self.assertAlmostEqual(g['length_mm'], 40., delta=.4)

    def test_empty_missing_shank_and_clipped(self):
        p = rectangle()
        for q in (np.zeros_like(p), np.roll(p, -40, axis=2)):
            self.assertIsNone(outline_size(q))
        p[2] = 0
        self.assertIsNone(outline_size(p))

    def test_carriage_neck_is_shank(self):
        thread = THREADS[0][3]
        _, alpha, _, parts = render_bolt(np.random.default_rng(0), thread, 'carriage', 30, return_mask=True)
        np.testing.assert_array_equal(parts.sum(2), alpha)
        # Head is 0.55d long; square neck begins immediately after it.
        neck_x = int((2 + .55 * thread.diameter_mm + .15 * thread.diameter_mm) * 8)
        self.assertGreater(parts[:, neck_x, 1].sum(), 0)
        self.assertEqual(parts[:, neck_x, 0].sum(), 0)

    def test_rectification_matrix_roundtrip(self):
        frame = np.zeros((720, 960, 3), np.uint8)
        H = np.array([[5., .3, 400], [.1, 4.5, 300], [.0002, -.0001, 1]])
        _, matrix = rectify(frame, H, return_matrix=True)
        centre = cv2.perspectiveTransform(np.array([[[256., 256.]]]), matrix)[0, 0]
        np.testing.assert_allclose(centre, [480, 360], atol=1e-7)
        points = np.array([[[20., 40.], [260., 200.]]])
        native = cv2.perspectiveTransform(points, matrix)
        np.testing.assert_allclose(cv2.perspectiveTransform(native, np.linalg.inv(matrix)), points, atol=1e-7)

    def test_board_rectification_does_not_depend_on_previous_frames_rng(self):
        path = Path(__file__).with_name('fixtures') / 'checkerboard_camera.jpg'
        frame = cv2.imread(str(path))
        self.assertIsNotNone(frame)
        canvases = []
        for seed in (1, 42, 123):
            cv2.setRNGSeed(seed)
            matrix = detect_board(frame)
            self.assertIsNotNone(matrix)
            canvases.append(rectify(frame, matrix))
        for canvas in canvases[1:]:
            np.testing.assert_array_equal(canvas, canvases[0])

    def test_native_pitch_and_unresolved_inputs(self):
        g = outline_size(rectangle())
        _, xs = np.mgrid[:1024, :1024]
        for pitch, system in ((1.25, 0), (25.4 / 18, 1)):
            frame = (120 + 70 * np.cos(2 * np.pi * (xs / 8) / pitch)).astype(np.uint8)
            r = thread_pitch(frame, np.diag([2., 2., 1.]), g)
            self.assertIsNotNone(r)
            self.assertEqual(r['system'], system)
            self.assertIsNone(thread_pitch(frame, np.diag([2., 2., 1.]), g, np.zeros((256, 256), np.float32)))
            self.assertAlmostEqual(r['pitch_mm'], pitch, delta=.02)
            self.assertIsNone(thread_pitch(frame, np.diag([.4, .4, 1.]), g))
        self.assertIsNone(thread_pitch(np.full((1024, 1024), 120, np.uint8), np.diag([2., 2., 1.]), g))
        self.assertIsNone(thread_pitch(None, None, g))

    def test_robust_calibration(self):
        rng = np.random.default_rng(5)
        x = rng.uniform([2, 8], [12, 100], (200, 2))
        y = x * [1.06, .97] + [.3, .4]
        y[:5] += 30
        fit = fit_linear(x, y)
        np.testing.assert_allclose(fit['gain'], [1.06, .97], atol=1e-6)
        np.testing.assert_allclose(fit['offset'], [.3, .4], atol=1e-6)

    def test_validation_fusion_uses_better_measurement(self):
        rng = np.random.default_rng(8)
        truth = rng.uniform([3, 8], [12, 100], (1000, 2))
        geo = truth + rng.normal(size=(1000, 2)) * [.5, .2]
        reg = truth + rng.normal(size=(1000, 2)) * [.1, 2.]
        weights = fit_fusion(geo, reg, truth)
        self.assertLess(weights[0], .2)
        self.assertGreater(weights[1], .8)

    def test_regression_and_outline_calibration_have_legacy_defaults(self):
        c = {'gain': [1, 1], 'offset': [0, 0], 'fusion_weights': [.25, .5]}
        fused, reg, geo = calibrated_size([7, 38], [8, 40], c)
        np.testing.assert_allclose(fused, [7.25, 39])
        c.update(regression_gain=[1, 1], regression_offset=[1, 2])
        fused, reg, geo = calibrated_size([7, 38], [8, 40], c)
        np.testing.assert_allclose(fused, [8, 40])
        np.testing.assert_allclose(reg, geo)

    def test_invalid_standard_scales_are_rejected(self):
        for scales in ((0, 1), (-1, 1), (1, float('nan'))):
            with self.assertRaises(ValueError):
                standard_evidence([8, 40], [.9, .1], dict(diameter_sigma=scales[0], length_sigma=scales[1], prior_weight=1))


class RuntimeTests(unittest.TestCase):
    def make_sizer(self):
        s = BoltSizer.__new__(BoltSizer)
        s.calibration = {'gain': [1, 1], 'offset': [0, 0]}
        return s

    def test_disagreement_review_and_v2_decode(self):
        s = self.make_sizer()
        raw = (np.array([.8, .8]), np.array([.95, .05]), np.array([1, 0, 0, 0, 0]), np.array([.01, .99]))
        legacy = s.decode_raw(raw)
        self.assertEqual(legacy, decode(*raw))
        r = s.decode_raw((*raw, rectangle()))
        self.assertFalse(r['measurement_disagreement'])
        self.assertFalse(r['bin'].startswith('REVIEW'))
        bad = (np.array([.8, 1.]), *raw[1:], rectangle())
        r = s.decode_raw(bad)
        self.assertTrue(r['measurement_disagreement'])
        self.assertTrue(r['bin'].startswith('REVIEW'))

    def test_pitch_candidates_use_calibrated_diameter(self):
        s = self.make_sizer()
        s.calibration['gain'] = [1.2, 1.0]
        raw = (np.array([.96, .8]), np.array([.95, .05]), np.array([1, 0, 0, 0, 0]),
               np.array([.01, .99]), rectangle())
        with patch('bolt_sizer.infer.thread_pitch', return_value=None) as pitch:
            s.decode_raw(raw)
            self.assertAlmostEqual(pitch.call_args.args[2]['diameter_mm'], 9.6, delta=.01)

    def test_standard_conflict_is_a_candidate_only_and_always_review(self):
        s = self.make_sizer()
        s.calibration['standard_evidence'] = dict(diameter_sigma=.2, length_sigma=.2, prior_weight=.2)
        raw = (np.array([.8, .8]), np.array([.01, .99]), np.array([1, 0, 0, 0, 0]),
               np.array([.01, .99]), rectangle())
        r = s.decode_raw(raw)
        self.assertEqual(r['system'], 'metric')
        self.assertTrue(r['system_evidence_disagreement'])
        self.assertTrue(r['bin'].startswith('REVIEW'))
        self.assertLessEqual(r['system_conf'], .01)
        with patch('bolt_sizer.infer.thread_pitch', return_value={'system': 1}):
            pitched = s.decode_raw(raw)
        self.assertEqual(pitched['system'], 'imperial')
        self.assertNotIn('system_evidence', pitched)

    def test_uncalibrated_missing_masks_and_negatives(self):
        s = self.make_sizer()
        raw = (np.array([.8, .8]), np.array([.95, .05]), np.array([1, 0, 0, 0, 0]), np.array([.01, .99]))
        for p in (np.zeros((3, 256, 256)), rectangle()):
            s.calibration = None
            self.assertTrue(s.decode_raw((*raw, p))['bin'].startswith('REVIEW'))
        negative = (*raw[:3], np.array([.99, .01]), rectangle())
        self.assertTrue(s.decode_raw(negative)['bin'].startswith('REJECT'))

    def test_smoother_keeps_current_mask(self):
        sm = Smoother(2)
        raw = (np.zeros(2), np.zeros(2), np.zeros(5), np.zeros(2), rectangle())
        sm.average(raw)
        current = (*raw[:4], np.rot90(rectangle(), axes=(1, 2)))
        self.assertIs(sm.average(current)[4], current[4])

    def test_tta_inverts_spatial_transforms(self):
        class Session:
            def run(self, _, feed):
                x = feed['canvas']; n = len(x)
                m = x[:, :, ::2, ::2]
                return np.zeros((n, 2)), np.zeros((n, 2)), np.zeros((n, 5)), np.zeros((n, 2)), m
        s = self.make_sizer();s.sess = Session();s.input = 'canvas'
        canvas = np.zeros((512, 512, 3), np.uint8)
        canvas[128:200, 320:400, 2] = 255
        # Odd/even pixel sampling shifts rotated boundaries by one source pixel;
        # aligned uniform blocks still agree in their interiors for all 8 views.
        one, eight = s.raw(canvas, 1)[4], s.raw(canvas, 8)[4]
        np.testing.assert_allclose(one[:, 66:98, 162:198], eight[:, 66:98, 162:198], atol=1e-6)
        self.assertEqual(np.unravel_index(eight[0].argmax(), (256, 256)), (64, 160))

    def test_onnx_head_order_must_match_catalog(self):
        from types import SimpleNamespace
        class Session:
            def get_inputs(self):
                return [SimpleNamespace(name='canvas')]
            def get_modelmeta(self):
                return SimpleNamespace(custom_metadata_map={'head_types': json.dumps(HEAD_TYPES[::-1])})
        with patch('onnxruntime.InferenceSession', return_value=Session()):
            with self.assertRaisesRegex(ValueError, 'head order'):
                BoltSizer('unused.onnx')

    def test_web_split_is_by_photo(self):
        manifest = Path('data/web/split.json')
        if not manifest.exists():
            self.skipTest('web data unavailable')
        es = json.loads(manifest.read_text())['entries']
        train = {e['source'] for e in es if e['split'] == 'train'}
        heldout = {e['source'] for e in es if e['split'] == 'heldout'}
        self.assertTrue(train and heldout)
        self.assertFalse(train & heldout)


class PartitionTests(unittest.TestCase):
    def subset(self, folder, filename, source=''):
        from types import SimpleNamespace
        dataset = SimpleNamespace(folder=Path(folder), rows=[{'file': filename, 'source': source}])
        return SimpleNamespace(dataset=dataset, indices=[0])

    def test_photo_sources_cannot_cross_partition(self):
        from train import verify_partition
        train = self.subset('data/train_web', 'a.jpg', 'same photo')
        val = self.subset('data/train_web', 'b.jpg', 'same photo')
        with self.assertRaisesRegex(ValueError, 'photo sources'):
            verify_partition([train], [val])

    def test_snapshot_exposure_cannot_enter_later_validation(self):
        from train import verify_partition, exposure_keys
        old = self.subset('work/snapshot/synth', '/data/synth/synth_000001.jpg')
        checkpoint = {'segmentation': True, 'training_keys': list(exposure_keys([old]))}
        train = self.subset('data/synth', 'synth_000002.jpg')
        val = self.subset('data/synth', 'synth_000001.jpg')
        with self.assertRaisesRegex(ValueError, 'Initializer trained on'):
            verify_partition([train], [val], checkpoint)

    def test_unverified_v3_initializer_is_rejected(self):
        from train import verify_partition
        train, val = (self.subset('data/synth', p) for p in ('a.jpg', 'b.jpg'))
        with self.assertRaisesRegex(ValueError, 'no training provenance'):
            verify_partition([train], [val], {'segmentation': True})

    def test_clean_stages_keep_the_same_validation_digest(self):
        from train import verify_partition
        train, val = (self.subset('data/synth', p) for p in ('a.jpg', 'b.jpg'))
        keys, digest = verify_partition([train], [val], {'segmentation': False})
        again, second = verify_partition([train], [val], {'segmentation': True, 'training_keys': keys})
        self.assertEqual(keys, again)
        self.assertEqual(digest, second)


if __name__ == '__main__':
    unittest.main()
