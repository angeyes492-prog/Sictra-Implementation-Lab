import http.client
from html.parser import HTMLParser
import json
from pathlib import Path
import tempfile
import threading
import unittest

from sictra_block2_design.design_console_web import bootstrap_demo, create_server
from sictra_block2_design.project_graph import ProjectGraphStore


class _StructureParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.attributes = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attributes.append((tag, dict(attrs)))


class DesignConsoleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "design-console.sqlite3"
        bootstrap_demo(self.database)
        self.server = create_server(self.database, "PROJECT-DEMO", port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def request(self, method, path, *, headers=None, body=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=2)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        body = response.read()
        result = response.status, dict(response.getheaders()), body
        connection.close()
        return result

    @staticmethod
    def create_payload(**changes):
        payload = {
            "create_id": "CREATE-HTTP-001", "object_id": "INTEL-HTTP-001",
            "source_identity": "INTELLIGENCE:HTTP:001", "fact_ids": ["FACT-001"],
            "evidence_refs": ["EVIDENCE-001"], "certainty": "VERIFIED",
            "contradictions": [], "authority_reference": "AUTHORITY-001",
            "temporal_state": "CURRENT", "provenance_refs": ["PROVENANCE-001"],
            "audience": "operations leaders", "decision": "understand the claim",
            "task": "create an accessible brief", "channel": "EMAIL",
            "success_criterion": "claim and limitation are locatable",
            "accessibility_requirements": ["WCAG-AA"], "legal_constraints": [],
            "channel_constraints": ["EMAIL-600PX"], "references_declared": False,
            "brand_manifest_ref": "BRAND-001", "reference_rights_manifest_ref": None,
            "uncertainty": [], "non_claims": ["NO-CAUSAL-CLAIM"],
            "created_at": "2026-08-31T22:00:00+00:00",
        }
        payload.update(changes)
        return json.dumps(payload).encode("utf-8")

    def test_snapshot_is_a_read_model_with_lineage_and_no_authority(self):
        with ProjectGraphStore(self.database) as graph:
            snapshot = graph.snapshot("PROJECT-DEMO")
        self.assertEqual("NOT_ACCEPTED", snapshot["authority"]["acceptance"])
        self.assertEqual(8, len([node for node in snapshot["nodes"] if node["node_type"] == "ENGINE_STAGE"]))
        self.assertEqual("CANDIDATE_NOT_ACCEPTED", snapshot["documents"][-1]["document"]["state"])

    def test_local_api_and_static_security_headers(self):
        status, headers, body = self.request("GET", "/api/project")
        self.assertEqual(200, status)
        self.assertEqual("no-store", headers["Cache-Control"])
        self.assertEqual("NOT_ACCEPTED", json.loads(body)["authority"]["acceptance"])
        status, headers, _ = self.request("GET", "/")
        self.assertEqual(200, status)
        self.assertIn("default-src 'self'", headers["Content-Security-Policy"])
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])

    def test_host_origin_and_mutation_methods_fail_closed(self):
        status, _, _ = self.request("GET", "/health", headers={"Host": "attacker.invalid"})
        self.assertEqual(403, status)
        status, _, _ = self.request("GET", "/health", headers={"Origin": "https://attacker.invalid"})
        self.assertEqual(403, status)
        status, _, _ = self.request("POST", "/api/edits", headers={"Content-Type": "application/json"}, body=b"{}")
        self.assertEqual(403, status)
        status, _, body = self.request("PUT", "/api/project")
        self.assertEqual(405, status)
        self.assertIn("sólo lectura", json.loads(body)["error"])

    def test_controlled_edit_creates_diff_invalidation_and_idempotent_replay(self):
        _, _, session_body = self.request("GET", "/api/session")
        token = json.loads(session_body)["edit_token"]
        _, _, project_body = self.request("GET", "/api/project")
        project = json.loads(project_body)
        base = project["documents"][-1]
        element = base["document"]["elements"][0]
        payload = json.dumps({
            "edit_id": "EDIT-HTTP-001",
            "base_version_id": base["version_id"],
            "base_content_hash": base["content_hash"],
            "element_id": element["element_id"],
            "field": "content",
            "value": "Edited through the controlled Design Studio boundary",
            "actor_id": "TEST-EDITOR",
            "created_at": "2026-08-31T12:00:00+00:00",
        }).encode("utf-8")
        headers = {"Content-Type": "application/json", "X-SICTrA-Edit-Token": token}
        status, _, body = self.request("POST", "/api/edits", headers=headers, body=payload)
        result = json.loads(body)
        self.assertEqual(201, status)
        self.assertEqual("EDITED_CANDIDATE_NOT_VALIDATED", result["document"]["state"])
        self.assertEqual(["CONTENT"], result["diff"]["domains"])
        self.assertEqual(["E04", "E05", "E06", "E07", "E08"], result["invalidation"]["reexecute"])
        self.assertEqual("NOT_ACCEPTED", result["authority"]["acceptance"])

        replay_status, _, replay_body = self.request("POST", "/api/edits", headers=headers, body=payload)
        self.assertEqual(200, replay_status)
        self.assertEqual("IDEMPOTENT", json.loads(replay_body)["store_action"])
        _, _, updated_body = self.request("GET", "/api/project")
        updated = json.loads(updated_body)
        self.assertEqual(2, len(updated["documents"]))
        self.assertEqual("Edited through the controlled Design Studio boundary", updated["documents"][-1]["document"]["elements"][0]["content"])

    def test_create_compiles_and_persists_a_candidate_envelope(self):
        _, _, session_body = self.request("GET", "/api/session")
        token = json.loads(session_body)["edit_token"]
        headers = {"Content-Type": "application/json", "X-SICTrA-Edit-Token": token}
        status, _, body = self.request("POST", "/api/create", headers=headers, body=self.create_payload())
        result = json.loads(body)
        self.assertEqual(201, status)
        self.assertEqual("CONTINUE", result["disposition"])
        self.assertEqual(64, len(result["envelope"]["fingerprint"]))
        self.assertEqual("NOT_ACCEPTED", result["authority"]["acceptance"])
        with ProjectGraphStore(self.database) as graph:
            types = {node["node_type"] for node in graph.snapshot("PROJECT-DEMO")["nodes"]}
        self.assertIn("DESIGN_CONTEXT_ENVELOPE", types)

    def test_create_returns_all_missing_fields_without_envelope(self):
        _, _, session_body = self.request("GET", "/api/session")
        token = json.loads(session_body)["edit_token"]
        headers = {"Content-Type": "application/json", "X-SICTrA-Edit-Token": token}
        body = self.create_payload(object_id="", fact_ids=[], evidence_refs=[], audience="")
        status, _, response = self.request("POST", "/api/create", headers=headers, body=body)
        result = json.loads(response)
        self.assertEqual(201, status)
        self.assertEqual("RETURN_UPSTREAM", result["disposition"])
        self.assertIsNone(result["envelope"])
        self.assertTrue({"OBJECT_ID_MISSING", "FACTS_MISSING", "EVIDENCE_MISSING", "AUDIENCE_MISSING"}.issubset(result["reasons"]))

    def test_create_rejects_missing_token_and_non_allowlisted_schema(self):
        status, _, _ = self.request(
            "POST", "/api/create", headers={"Content-Type": "application/json"},
            body=self.create_payload(),
        )
        self.assertEqual(403, status)
        _, _, session_body = self.request("GET", "/api/session")
        token = json.loads(session_body)["edit_token"]
        payload = json.loads(self.create_payload())
        payload["unexpected"] = "field"
        status, _, body = self.request(
            "POST", "/api/create",
            headers={"Content-Type": "application/json", "X-SICTrA-Edit-Token": token},
            body=json.dumps(payload).encode("utf-8"),
        )
        self.assertEqual(409, status)
        self.assertIn("ALLOWLISTED", json.loads(body)["error"])

    def test_missing_project_is_explicit_not_an_empty_pass(self):
        other = create_server(self.database, "PROJECT-MISSING", port=0)
        thread = threading.Thread(target=other.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection("127.0.0.1", other.server_port, timeout=2)
            connection.request("GET", "/api/project")
            response = connection.getresponse()
            self.assertEqual(404, response.status)
            self.assertIn("no disponible", json.loads(response.read())["error"])
            connection.close()
        finally:
            other.shutdown()
            other.server_close()
            thread.join(timeout=2)

    def test_markup_has_landmarks_labels_live_regions_and_no_inline_code(self):
        html = (Path(__file__).parents[1] / "src" / "sictra_block2_design" / "design_console" / "index.html").read_text(encoding="utf-8")
        parser = _StructureParser()
        parser.feed(html)
        self.assertIn("main", parser.tags)
        self.assertIn("nav", parser.tags)
        self.assertTrue(any(attrs.get("href") == "#studio" for tag, attrs in parser.attributes if tag == "a"))
        self.assertTrue(any(attrs.get("role") == "alert" for _, attrs in parser.attributes))
        self.assertTrue(any(attrs.get("aria-live") == "polite" for _, attrs in parser.attributes))
        self.assertFalse(any(tag == "style" for tag in parser.tags))
        scripts = [attrs for tag, attrs in parser.attributes if tag == "script"]
        self.assertTrue(scripts and all(attrs.get("src") for attrs in scripts))
        buttons = [attrs for tag, attrs in parser.attributes if tag == "button"]
        self.assertTrue(buttons and all(attrs.get("type") in {"button", "submit"} for attrs in buttons))
        self.assertEqual(1, len([attrs for attrs in buttons if attrs.get("type") == "submit"]))

    def test_css_preserves_focus_reduced_motion_and_touch_targets(self):
        css = (Path(__file__).parents[1] / "src" / "sictra_block2_design" / "design_console" / "app.css").read_text(encoding="utf-8")
        self.assertIn(":focus-visible", css)
        self.assertIn("prefers-reduced-motion:reduce", css)
        self.assertIn("min-height:44px", css)
        self.assertIn("min-width:48px", css)
        self.assertIn("[hidden]{display:none!important}", css)

    def test_ops_view_is_enabled_and_uses_a_separate_stylesheet(self):
        root = Path(__file__).parents[1] / "src" / "sictra_block2_design" / "design_console"
        html = (root / "index.html").read_text(encoding="utf-8")
        ops_css = (root / "ops.css").read_text(encoding="utf-8")
        self.assertIn('data-view="ops"', html)
        self.assertIn('id="execution-tape"', html)
        self.assertIn('href="/ops.css"', html)
        self.assertIn(".execution-tape li.reused", ops_css)

    def test_create_view_has_three_contract_sections_and_handoff_seal(self):
        root = Path(__file__).parents[1] / "src" / "sictra_block2_design" / "design_console"
        html = (root / "index.html").read_text(encoding="utf-8")
        create_css = (root / "create.css").read_text(encoding="utf-8")
        self.assertIn('data-view="create"', html)
        self.assertEqual(3, html.count("<fieldset>"))
        self.assertIn('id="handoff-seal"', html)
        self.assertIn('aria-live="polite"', html)
        self.assertIn(".handoff-seal.return", create_css)
        self.assertNotIn('name="object_id" required', html)

    def test_studio_exposes_immutable_history_and_visual_diff_regions(self):
        root = Path(__file__).parents[1] / "src" / "sictra_block2_design" / "design_console"
        html = (root / "index.html").read_text(encoding="utf-8")
        history_css = (root / "history.css").read_text(encoding="utf-8")
        self.assertIn('id="history-section"', html)
        self.assertIn('id="version-list"', html)
        self.assertIn('id="visual-diff"', html)
        self.assertIn('aria-live="polite"', html)
        self.assertIn(".diff-entry", history_css)


if __name__ == "__main__":
    unittest.main()
