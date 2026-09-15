from contextlib import closing
from http.client import HTTPConnection
from pathlib import Path
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from sictra_block4_orchestrator.operations import initialize
from sictra_block4_orchestrator.operations_web import create_operations_server
from sictra_block4_orchestrator.operations_web import OperationsHandler


class CommandSurfaceTests(unittest.TestCase):
    def test_cancelled_browser_read_does_not_attempt_second_response(self):
        handler = object.__new__(OperationsHandler)
        handler.path = '/api/operations'
        handler._allowed = lambda: True
        handler.server = SimpleNamespace(operations=SimpleNamespace(snapshot=lambda:{}),control_token='test')
        handler._json = Mock(side_effect=BrokenPipeError)
        handler.do_GET()
        self.assertEqual(1,handler._json.call_count)

    def test_delivers_self_contained_scene_and_rejects_unlisted_assets(self):
        with tempfile.TemporaryDirectory() as temp:
            service = initialize(Path(temp) / 'state')
            server = create_operations_server(service, port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            def get(path, headers=None):
                with closing(HTTPConnection('127.0.0.1', server.server_port)) as connection:
                    connection.request('GET', path, headers=headers or {})
                    response = connection.getresponse()
                    return response.status, dict(response.getheaders()), response.read()
            try:
                for path, mime in [('/command.css','text/css'),('/command.js','text/javascript'),('/command-scene.png','image/png')]:
                    status, headers, body = get(path)
                    self.assertEqual(200, status)
                    self.assertTrue(headers['Content-Type'].startswith(mime))
                    self.assertIn("connect-src 'self'", headers['Content-Security-Policy'])
                    self.assertGreater(len(body), 100)
                self.assertTrue(get('/command-scene.png')[2].startswith(b'\x89PNG\r\n\x1a\n'))
                self.assertEqual(404, get('/../operations.py')[0])
                self.assertEqual(403, get('/command-scene.png', {'Origin':'https://untrusted.example'})[0])
                html=get('/')[2].decode()
                self.assertIn('id="scene-output-count">—', html)
                self.assertNotIn('72%', html)
                self.assertIn('sandbox=""', html)
            finally:
                server.shutdown();server.server_close();thread.join(timeout=2);service.stop()
