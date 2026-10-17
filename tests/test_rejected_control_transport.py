import io
from email.message import Message
from http import HTTPStatus
from unittest.mock import Mock, patch
import unittest

from sictra_block4_orchestrator.operations_web import OperationsHandler
from sictra_block4_orchestrator.web import CommandCenterHandler


class RejectedTransportTests(unittest.TestCase):
    def handler(self, body=b'{"action":"pause"}'):
        handler = object.__new__(OperationsHandler)
        handler.command = "POST"
        handler.headers = Message()
        handler.headers["Content-Length"] = str(len(body))
        handler.rfile = io.BufferedReader(io.BytesIO(body))
        handler.wfile = io.BytesIO()
        handler.connection = Mock()
        handler.connection.gettimeout.return_value = None
        return handler

    def test_forbidden_body_is_discarded_not_parsed_before_close(self):
        handler = self.handler()
        with patch.object(CommandCenterHandler, "_json") as response, \
             patch("sictra_block4_orchestrator.operations_web.json.loads", side_effect=AssertionError("must never parse")):
            handler._json(HTTPStatus.FORBIDDEN, {"error": "denied"})
        response.assert_called_once_with(HTTPStatus.FORBIDDEN, {"error": "denied"})
        self.assertEqual(b"", handler.rfile.read())
        self.assertTrue(handler.close_connection)

    def test_unframed_duplicate_oversized_and_transfer_encoded_bodies_are_not_drained(self):
        for mode in ("missing", "duplicate", "oversized", "transfer", "negative"):
            with self.subTest(mode=mode):
                handler = self.handler()
                if mode == "missing":
                    del handler.headers["Content-Length"]
                elif mode == "duplicate":
                    handler.headers["Content-Length"] = "1"
                elif mode == "transfer":
                    handler.headers["Transfer-Encoding"] = "chunked"
                else:
                    handler.headers.replace_header("Content-Length", "16001" if mode == "oversized" else "-1")
                with patch.object(CommandCenterHandler, "_json"):
                    handler._json(HTTPStatus.FORBIDDEN, {})
                self.assertEqual(b'{"action":"pause"}', handler.rfile.read())

    def test_deadline_and_client_cancellation_do_not_parse_or_send_second_response(self):
        handler = self.handler()
        handler.rfile = Mock()
        handler.rfile.read1.side_effect = TimeoutError("injected slow client")
        with patch.object(CommandCenterHandler, "_json") as response:
            handler._json(HTTPStatus.FORBIDDEN, {})
        self.assertEqual(1, response.call_count)
        self.assertEqual(1, handler.rfile.read1.call_count)
        handler = self.handler()
        handler.rfile = Mock()
        with patch.object(CommandCenterHandler, "_json"), \
             patch("sictra_block4_orchestrator.operations_web.time.monotonic", side_effect=[0, 1]):
            handler._json(HTTPStatus.FORBIDDEN, {})
        handler.rfile.read1.assert_not_called()

    def test_non_forbidden_or_non_post_response_preserves_body(self):
        for method, status in (("GET", HTTPStatus.FORBIDDEN), ("POST", HTTPStatus.OK), ("POST", HTTPStatus.BAD_REQUEST)):
            handler = self.handler()
            handler.command = method
            with patch.object(CommandCenterHandler, "_json"):
                handler._json(status, {})
            self.assertEqual(b'{"action":"pause"}', handler.rfile.read())

    def test_socket_closed_during_discard_does_not_escape_or_send_again(self):
        handler = self.handler()
        handler.connection.settimeout.side_effect = OSError("closed peer")
        with patch.object(CommandCenterHandler, "_json") as response:
            handler._json(HTTPStatus.FORBIDDEN, {})
        self.assertEqual(1, response.call_count)
