"""HTTP integration tests for the local-only Block 1 laboratory UI."""

from __future__ import annotations

from http.client import HTTPConnection
import json
from threading import Thread
import unittest

from sictra_block1.lab_web import UI_SCOPE, create_server


class Block1LabWebTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = create_server(port=0)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, method: str, path: str):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        connection.request(method, path)
        response = connection.getresponse()
        body = response.read()
        connection.close()
        return response.status, response.getheader("Content-Type"), body

    def test_page_and_health_are_local_and_explain_limits(self):
        status, content_type, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn(b"Sin datos reales", body)
        status, _, body = self.request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["scope"], UI_SCOPE)

    def test_valid_scenario_has_controlled_effect_summary(self):
        status, content_type, body = self.request("POST", "/api/scenarios/valid")
        payload = json.loads(body)
        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)
        self.assertEqual(payload["scope"], UI_SCOPE)
        self.assertEqual(payload["summary"]["status"], "COMMITTED")
        self.assertEqual(payload["report"]["memory_record_count"], 1)

    def test_adversarial_scenarios_are_reported_as_correctly_blocked(self):
        for scenario in ("stale-evidence", "missing-authority", "wrong-scope"):
            with self.subTest(scenario=scenario):
                status, _, body = self.request("POST", f"/api/scenarios/{scenario}")
                payload = json.loads(body)
                self.assertEqual(status, 200)
                self.assertEqual(payload["summary"]["status"], "BLOCKED_CORRECTLY")
                self.assertEqual(payload["report"]["memory_record_count"], 0)

    def test_unknown_routes_and_public_bindings_are_rejected(self):
        status, _, body = self.request("POST", "/api/scenarios/arbitrary")
        self.assertEqual(status, 404)
        self.assertIn("Escenario", json.loads(body)["error"])
        status, _, _ = self.request("GET", "/unexpected")
        self.assertEqual(status, 404)
        with self.assertRaises(ValueError):
            create_server(host="0.0.0.0", port=0)


if __name__ == "__main__":
    unittest.main()
