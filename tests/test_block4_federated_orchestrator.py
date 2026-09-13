from datetime import datetime, timedelta, timezone
import copy
import hmac
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
import http.client

from sictra_block4_orchestrator.runtime import (
    FederatedContractError, FederatedOrchestratorStore, build_controlled_block1_package,
)
from sictra_block4_orchestrator.web import create_server


NOW = datetime(2026, 9, 12, 18, 0, tzinfo=timezone.utc)
KEY = b"federated-orchestrator-test-key-0001"


class FederatedOrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "journal.sqlite"
        self.store = FederatedOrchestratorStore(self.path, integrity_key=KEY)

    def tearDown(self): self.temp.cleanup()

    def package(self, **kwargs): return build_controlled_block1_package(integrity_key=KEY, now=NOW, **kwargs)

    def test_controlled_package_progresses_only_to_human_gate(self):
        accepted = self.store.ingest(self.package())
        self.assertEqual("BLOCK1_ATTESTED", accepted.state)
        final = self.store.process_to_human_gate(accepted.case_id, now=NOW)
        self.assertEqual("HUMAN_REVIEW_REQUIRED", final.state)
        self.assertEqual(("BLOCK1", "BLOCK2", "BLOCK3"), final.lineage)
        self.assertEqual(("NO_NETWORK", "NO_PUBLICATION"), final.restrictions)
        self.assertEqual(
            ("INGESTED", "BLOCK2_COORDINATION_RECEIPT", "BLOCK3_COORDINATION_RECEIPT", "HUMAN_GATE_REACHED"),
            tuple(event["event_type"] for event in self.store.audit_events(final.case_id)),
        )

    def test_exact_replay_is_idempotent_and_identity_mutation_collides(self):
        package = self.package()
        first = self.store.ingest(package)
        self.assertEqual(first, self.store.ingest(copy.deepcopy(package)))
        changed = self.package(source_hash="a" * 64)
        with self.assertRaisesRegex(FederatedContractError, "CASE_IDENTITY_COLLISION"):
            self.store.ingest(changed)

    def test_tampered_signature_and_lineage_are_rejected_before_write(self):
        package = self.package(); package["payload"]["summary"] = "tampered"
        with self.assertRaisesRegex(FederatedContractError, "PACKAGE_SIGNATURE_INVALID"):
            self.store.ingest(package)
        forged = self.package(); forged["lineage"] = ["BLOCK2"]
        forged["signature"] = hmac.new(KEY, json.dumps({k:v for k,v in forged.items() if k != "signature"}, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(), "sha256").hexdigest()
        with self.assertRaisesRegex(FederatedContractError, "INITIAL_PRODUCER_OR_LINEAGE_INVALID"):
            self.store.ingest(forged)
        self.assertEqual((), self.store.list_cases())

    def test_expired_and_contradicted_package_returns_upstream_without_downstream_progression(self):
        expired = self.package(case_id="CASE-EXPIRED", expires_at=NOW + timedelta(seconds=1))
        result = self.store.ingest(expired, now=NOW + timedelta(seconds=2))
        self.assertEqual("RETURN_UPSTREAM", result.state)
        contradictory = self.package(case_id="CASE-CONTRADICTED", certainty="CONTRADICTED")
        result = self.store.ingest(contradictory)
        self.assertEqual("RETURN_UPSTREAM", result.state)
        self.assertEqual(("INGESTED",), tuple(event["event_type"] for event in self.store.audit_events("CASE-CONTRADICTED")))

    def test_restart_recovers_checkpoint_but_tampered_journal_fails_closed(self):
        item = self.store.ingest(self.package()); self.store.process_to_human_gate(item.case_id, now=NOW)
        reopened = FederatedOrchestratorStore(self.path, integrity_key=KEY)
        self.assertEqual("HUMAN_REVIEW_REQUIRED", reopened.get_case(item.case_id).state)
        db = sqlite3.connect(self.path)
        try:
            db.execute("UPDATE events SET payload_json='{}' WHERE sequence=1"); db.commit()
        finally:
            db.close()
        with self.assertRaisesRegex(FederatedContractError, "JOURNAL_INTEGRITY_ERROR"):
            FederatedOrchestratorStore(self.path, integrity_key=KEY)

    def test_retries_are_bounded_and_never_skip_expiry(self):
        package = self.package(case_id="CASE-RETRY", expires_at=NOW + timedelta(seconds=1))
        self.store.ingest(package, now=NOW + timedelta(seconds=2))
        for attempt in range(1, 4):
            item = self.store.retry("CASE-RETRY", now=NOW + timedelta(seconds=2))
            self.assertEqual(attempt, item.retry_count); self.assertEqual("RETURN_UPSTREAM", item.state)
        with self.assertRaisesRegex(FederatedContractError, "RETRY_LIMIT_EXHAUSTED"):
            self.store.retry("CASE-RETRY", now=NOW + timedelta(seconds=2))


class FederatedCommandCenterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); path = Path(self.temp.name) / "journal.sqlite"
        self.store = FederatedOrchestratorStore(path, integrity_key=KEY)
        item = self.store.ingest(build_controlled_block1_package(integrity_key=KEY, now=NOW)); self.store.process_to_human_gate(item.case_id, now=NOW)
        self.server = create_server(self.store, port=0); self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2); self.temp.cleanup()

    def request(self, method, path, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=2)
        connection.request(method, path, headers=headers or {}); response = connection.getresponse(); result = response.status, dict(response.getheaders()), response.read(); connection.close(); return result

    def test_console_exposes_cases_but_not_acceptance_or_mutation(self):
        status, headers, body = self.request("GET", "/api/cases"); payload = json.loads(body)
        self.assertEqual(200, status); self.assertEqual("no-store", headers["Cache-Control"])
        self.assertEqual("CONTROLLED_LOCAL_PACKAGES_ONLY", payload["fixture"])
        self.assertEqual("HUMAN_REVIEW_REQUIRED", payload["cases"][0]["state"])
        self.assertEqual("NOT_ACCEPTED", payload["authority"]["acceptance"])
        status, _, body = self.request("POST", "/api/cases")
        self.assertEqual(405, status); self.assertIn("sólo lectura", json.loads(body)["error"])

    def test_loopback_security_and_markup_boundaries(self):
        self.assertEqual(403, self.request("GET", "/health", {"Host": "attacker.invalid"})[0])
        self.assertEqual(403, self.request("GET", "/health", {"Origin": "https://attacker.invalid"})[0])
        self.assertEqual(403, self.request("GET", "/health", {"Sec-Fetch-Site": "cross-site"})[0])
        root = Path(__file__).parents[1] / "src" / "sictra_block4_orchestrator" / "command_center"
        html = (root / "index.html").read_text(encoding="utf-8"); css = (root / "app.css").read_text(encoding="utf-8")
        self.assertIn("http://127.0.0.1:8765/", html); self.assertIn("http://127.0.0.1:8766/", html); self.assertIn("http://127.0.0.1:8767/", html)
        self.assertIn("frame-ancestors 'none'", self.request("GET", "/")[1]["Content-Security-Policy"])
        for marker in (":focus-visible", "prefers-reduced-motion:reduce", "forced-colors:active"):
            self.assertIn(marker, css)


if __name__ == "__main__": unittest.main()
