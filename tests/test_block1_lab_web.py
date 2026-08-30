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

    def request(self, method: str, path: str, body=None, headers=None):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        body = response.read()
        connection.close()
        return response.status, response.getheader("Content-Type"), body

    def test_page_and_health_are_local_and_explain_limits(self):
        status, content_type, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn(b"Intelligence Workspace", body)
        self.assertIn(b"No consulta internet", body)
        self.assertIn(b"Readiness de fuentes", body)
        status, content_type, body = self.request("GET", "/app.css")
        self.assertEqual(status, 200)
        self.assertIn("text/css", content_type)
        self.assertIn(b"scope-lens", body)
        status, content_type, body = self.request("GET", "/app.js")
        self.assertEqual(status, 200)
        self.assertIn("text/javascript", content_type)
        self.assertIn(b"compareStrategies", body)
        self.assertIn(b"renderSourceReadiness", body)
        status, _, body = self.request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["scope"], UI_SCOPE)

    def test_workspace_exposes_traceable_synthetic_investigations(self):
        status, content_type, body = self.request("GET", "/api/workspace")
        payload = json.loads(body)
        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)
        self.assertEqual(payload["fixture_class"], "SYNTHETIC_FIELD_TEST")
        self.assertEqual(len(payload["investigations"]), 3)
        self.assertEqual(
            {item["scope"]["level"] for item in payload["investigations"]},
            {"GLOBAL", "REGIONAL", "LOCAL"},
        )

    def test_source_readiness_is_read_only_and_never_claims_admissible_data(self):
        status, _, body = self.request("GET", "/api/source-readiness?region=AMERICAS&domain=TRADE")
        payload = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(payload["admissible_source_count"], 0)
        self.assertEqual(payload["status"], "RESEARCH_BLOCKED_PENDING_SOURCE_BINDING")
        self.assertIn("cepal", {item["source_id"] for item in payload["candidates"]})
        status, _, _ = self.request("GET", "/api/source-readiness?region=AMERICAS")
        self.assertEqual(status, 400)

    def test_investigation_and_strategy_comparison_endpoints(self):
        status, _, body = self.request("GET", "/api/investigations/global-components-001")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["question_id"], "Q-GLOBAL-001")
        status, _, body = self.request(
            "GET", "/api/comparisons/global-components-001?left=STR-G-A&right=STR-G-B"
        )
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["comparison"]["verdict"], "PREFER_LEFT")

    def test_comparison_rejects_missing_or_arbitrary_strategy(self):
        status, _, _ = self.request("GET", "/api/comparisons/global-components-001")
        self.assertEqual(status, 400)
        status, _, body = self.request(
            "GET", "/api/comparisons/global-components-001?left=STR-G-A&right=ARBITRARY"
        )
        self.assertEqual(status, 400)
        self.assertIn("unknown strategy", json.loads(body)["error"])
        status, _, _ = self.request(
            "GET", "/api/comparisons/global-components-001?left=STR-G-A&right=STR-G-B&extra=1"
        )
        self.assertEqual(status, 400)
        status, _, _ = self.request(
            "GET", "/api/comparisons/missing?left=STR-G-A&right=STR-G-B"
        )
        self.assertEqual(status, 404)

    def test_untrusted_host_origin_and_cross_site_requests_are_rejected(self):
        status, _, body = self.request("GET", "/api/workspace", headers={"Host": "attacker.example"})
        self.assertEqual(status, 403)
        self.assertIn("Host", json.loads(body)["error"])
        local_host = f"127.0.0.1:{self.server.server_port}"
        status, _, body = self.request(
            "POST", "/api/scenarios/valid",
            headers={"Host": local_host, "Origin": "https://attacker.example"},
        )
        self.assertEqual(status, 403)
        self.assertIn("Origen", json.loads(body)["error"])
        status, _, _ = self.request(
            "GET", "/api/workspace",
            headers={"Host": local_host, "Sec-Fetch-Site": "cross-site"},
        )
        self.assertEqual(status, 403)

    def test_unsupported_methods_return_bounded_json_error(self):
        for method in ("DELETE", "OPTIONS", "PATCH", "PUT"):
            with self.subTest(method=method):
                status, content_type, body = self.request(method, "/api/workspace")
                self.assertEqual(status, 405)
                self.assertIn("application/json", content_type)
                self.assertIn("Método", json.loads(body)["error"])

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
        status, _, _ = self.request("GET", "/../../AGENTS.md")
        self.assertEqual(status, 404)
        status, _, body = self.request("POST", "/api/scenarios/valid", body=b"{}")
        self.assertEqual(status, 400)
        self.assertIn("payload", json.loads(body)["error"])
        with self.assertRaises(ValueError):
            create_server(host="0.0.0.0", port=0)


if __name__ == "__main__":
    unittest.main()
