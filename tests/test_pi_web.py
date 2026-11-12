"""Check API routing, expiry and serving without camera hardware."""
import io
import json
from pathlib import Path
import shlex
from types import SimpleNamespace
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

import numpy as np

from pi_web.server import Handler, Inspection, REVIEW, Server, SITE_ORIGIN
from tools.deploy_pi import bundle, main as deploy


class ServerTests(unittest.TestCase):
    def inspection(self):
        with patch('pi_web.server.BoltSizer'):
            obj = Inspection('models/boltnet_v3.onnx')
        obj.state = 'running'
        obj.result = {'frame_id': 12, 'bin': 'M6 x 30 hex bolt', 'is_bolt': True, 'label': 'M6 x 30 hex bolt'}
        obj.result_at = time.monotonic()
        return obj

    def test_candidate_cannot_become_an_actuator_command(self):
        result = self.inspection().snapshot()
        self.assertEqual(result['candidate_bin'], 'M6 x 30 hex bolt')
        self.assertEqual(result['bin'], REVIEW)
        self.assertFalse(result['machine_ready'])
        self.assertFalse(result['stale'])

    def test_stale_and_disconnected_frames_remain_review(self):
        obj = self.inspection()
        obj.result_at -= 2
        self.assertTrue(obj.snapshot()['stale'])
        obj.result_at = time.monotonic()
        obj.state = 'camera_offline'
        self.assertTrue(obj.snapshot()['stale'])
        self.assertEqual(obj.snapshot()['bin'], REVIEW)

    def test_capture_replaces_the_previous_frame(self):
        obj = self.inspection()
        first, second = np.zeros((2, 2, 3), np.uint8), np.ones((2, 2, 3), np.uint8)
        obj.publish(first, time.monotonic())
        obj.publish(second, time.monotonic())
        self.assertIs(obj.frame, second)
        self.assertEqual(obj.frame_id, 2)
        self.assertEqual(obj.snapshot()['queue_depth'], 0)

    def test_http_health_static_and_path_allowlist(self):
        obj = self.inspection()
        server = Server(('127.0.0.1', 0), Handler)
        server.inspection = obj
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = 'http://127.0.0.1:' + str(server.server_port)
        try:
            with urlopen(base + '/api/health') as response:
                self.assertEqual(json.load(response)['bin'], REVIEW)
            with urlopen(base + '/') as response:
                self.assertIn(b'Raspberry Pi', response.read())
            with self.assertRaises(HTTPError) as exc:
                urlopen(base + '/../../models/boltnet_v3.pt')
            self.assertEqual(exc.exception.code, 404)
        finally:
            obj.close()
            server.shutdown()
            server.server_close()
            thread.join(2)

    def test_bundle_contains_runtime_model_and_no_training_data(self):
        import tarfile
        root = Path(__file__).resolve().parents[1]
        archive = bundle(root, root / 'models/boltnet_v3.onnx')
        with tarfile.open(fileobj=io.BytesIO(archive)) as packed:
            names = packed.getnames()
        self.assertIn('pi_web/server.py', names)
        self.assertIn('models/boltnet_v3.onnx', names)
        self.assertFalse(any(n.startswith(('data/', 'work/')) for n in names))
        self.assertNotIn('bolt_sizer/model.py', names)

    def test_hosted_site_can_read_status_and_jpeg_but_other_origins_cannot(self):
        obj = self.inspection()
        obj.preview = b'\xff\xd8jpeg-test\xff\xd9'
        server = Server(('127.0.0.1', 0), Handler)
        server.inspection = obj
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = 'http://127.0.0.1:' + str(server.server_port)
        try:
            for path in ('/api/status', '/frame.jpg'):
                with urlopen(Request(base + path, headers={'Origin': SITE_ORIGIN})) as response:
                    self.assertEqual(response.headers['Access-Control-Allow-Origin'], SITE_ORIGIN)
                    if path.endswith('.jpg'):
                        self.assertEqual(response.headers['Content-Type'], 'image/jpeg')
                        self.assertEqual(response.read(), obj.preview)
                with urlopen(Request(base + path, headers={'Origin': 'https://unrelated.invalid'})) as response:
                    self.assertIsNone(response.headers.get('Access-Control-Allow-Origin'))
            with urlopen(Request(base + '/api/status', method='OPTIONS', headers={'Origin': SITE_ORIGIN})) as response:
                self.assertEqual(response.status, 204)
                self.assertEqual(response.headers['Access-Control-Allow-Methods'], 'GET, OPTIONS')
            with self.assertRaises(HTTPError) as exc:
                urlopen(Request(base + '/api/status', method='OPTIONS', headers={'Origin': 'https://unrelated.invalid'}))
            self.assertEqual(exc.exception.code, 403)
        finally:
            obj.close()
            server.shutdown()
            server.server_close()
            thread.join(2)

    def test_deployment_programs_compile_and_default_to_lan(self):
        calls = []

        def fake_ssh(command, **kwargs):
            self.assertEqual(command[0], 'ssh')
            code = shlex.split(command[-1])
            self.assertEqual(code[:2], ['python3', '-c'])
            compile(code[2], '<remote-deployment>', 'exec')
            calls.append((code[2], kwargs))
            return SimpleNamespace(stdout=json.dumps({
                'home': '/home/pi', 'arch': 'aarch64',
                'system': 'Linux', 'python': [3, 11, 9],
            }).encode())

        root = Path(__file__).resolve().parents[1]
        with patch('sys.argv', ['deploy_pi.py', 'pi@example.invalid', '--model',
                                str(root / 'models/boltnet_v3.onnx')]), \
                patch('tools.deploy_pi.subprocess.run', side_effect=fake_ssh), \
                patch('builtins.print'):
            deploy()
        self.assertEqual(len(calls), 3)
        self.assertIsInstance(calls[1][1]['input'], bytes)
        setup = calls[2][0]
        self.assertIn("'--bind','0.0.0.0'", setup)
        self.assertIn('http://127.0.0.1:8080/api/health', setup)
        self.assertIn("['ip','-j','-4','addr','show']", setup)


if __name__ == '__main__':
    unittest.main()
