from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from sictra_block1 import (
    AttestedEvidenceStore, AttestedRuntimeBridge, AttestedRuntimeBridgeViolation,
    AuthorityIssuer, EvidenceIssuer, IntelligenceRuntime, SourceApprovalRecord,
    SourceBindingIssuer, SourceControlStore, SourceRegistration,
    build_eurostat_manual_bundle,
)
from test_block1_eurostat_maritime_mapper import workbook


NOW = 20_000
BINDING_KEY = b"b" * 32
EVIDENCE_KEY = b"e" * 32
CONTROL_KEY = b"c" * 32
STORE_KEY = b"s" * 32
AUTHORITY_KEY = b"a" * 32
EXECUTION_KEY = b"x" * 32
DECISION_KEY = b"d" * 32
RUNTIME_KEY = b"r" * 32
SCOPE = "BLOCK1_EUROPE_MARITIME_INTELLIGENCE"
CLAIM = "maritime_freight_weight_thousand_tonnes"
URL = "https://ec.europa.eu/eurostat/databrowser/view/tran_r_mago_nm/default/table"


class AttestedRuntimeBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.now = NOW
        registration = SourceRegistration(
            "eurostat", "Eurostat / European Commission", SCOPE, ("ec.europa.eu",),
            frozenset((CLAIM,)), "MANUAL_SOURCE_BUNDLE", 131_072, "BOUND",
        )
        approval = SourceApprovalRecord(
            "eurostat", "PROJECT_OWNER", NOW - 1,
            "evidence/block1_eurostat_maritime_registration_draft_v0.1.md",
            registration.allowed_hosts, registration.claim_keys,
            registration.access_method, registration.max_content_bytes, "APPROVED",
        )
        binding = SourceBindingIssuer("review-control", BINDING_KEY).issue(
            registration, approval, now=NOW, ttl=100,
        )
        controls = SourceControlStore(
            Path(self.temp.name) / "control.json", binding_keys={"review-control": BINDING_KEY},
            integrity_key=CONTROL_KEY, clock=lambda: self.now,
        )
        controls.persist(registration, approval, binding)
        gateway = controls.build_gateway(
            "eurostat", evidence_issuer=EvidenceIssuer("gateway", EVIDENCE_KEY), now=NOW,
        )
        bundle = build_eurostat_manual_bundle(
            "eurostat.xlsx", workbook(), "COUNTRY", source_url=URL,
            observed_at=NOW, correlation_id="attested-runtime-001",
        )
        evidence = gateway.attest_manual_bundle(bundle, now=NOW)
        self.store = AttestedEvidenceStore(
            Path(self.temp.name) / "evidence.json", evidence_keys={"gateway": EVIDENCE_KEY},
            evidence_scope=SCOPE, evidence_max_age=10, evidence_claims=frozenset((CLAIM,)),
            integrity_key=STORE_KEY, clock=lambda: self.now,
        )
        self.store.persist(evidence)
        self.runtime = IntelligenceRuntime.operational(
            store_path=Path(self.temp.name) / "runtime.sqlite3",
            authority_keys={"governance": AUTHORITY_KEY}, authority_audience="block1-runtime",
            authority_epoch=1, evidence_keys={"gateway": EVIDENCE_KEY}, evidence_scope=SCOPE,
            evidence_max_age=10, evidence_claims=frozenset((CLAIM,)),
            execution_key=EXECUTION_KEY, decision_key=DECISION_KEY,
            storage_integrity_key=RUNTIME_KEY, clock=lambda: self.now,
        )
        self.bridge = AttestedRuntimeBridge(self.store, self.runtime)
        self.authority = AuthorityIssuer("governance", AUTHORITY_KEY, "block1-runtime", 1).issue(
            task_id="attested-task", run_id="attested-run", actions=("store_candidate",),
            now=NOW, ttl=20, nonce="attested-bridge",
        )

    def tearDown(self):
        self.runtime.close()
        self.temp.cleanup()

    def test_current_durable_evidence_reaches_e01_to_e08_without_caller_sources(self):
        result = self.bridge.run(
            task_id="attested-task", run_id="attested-run", objective="analyse maritime change",
            authority=self.authority, now=NOW,
        )
        self.assertEqual(result.envelope.payload["enforcement"]["status"], "COMMITTED")
        self.assertEqual(len(result.envelope.payload["evidence"]), 1)
        self.assertEqual(result.envelope.payload["evidence"][0]["source_id"], "eurostat")
        self.assertEqual(result.envelope.payload["outcome"]["evidence_count"], 1)
        self.assertEqual([item["status"] for item in result.evidence_receipts], ["CURRENT"])
        result.evidence_receipts[0]["status"] = "mutated"
        self.assertEqual(self.store.list_receipts(now=NOW)[0]["status"], "CURRENT")

    def test_empty_or_stale_store_fails_before_runtime_effect(self):
        self.now = NOW + 11
        with self.assertRaises(AttestedRuntimeBridgeViolation):
            self.bridge.run(
                task_id="stale-task", run_id="stale-run", objective="x",
                authority=self.authority, now=self.now,
            )
        self.assertEqual(self.runtime.memory.history("stale-task"), ())

    def test_clock_disagreement_fails_before_e01(self):
        with self.assertRaises(AttestedRuntimeBridgeViolation):
            self.bridge.run(
                task_id="clock-task", run_id="clock-run", objective="x",
                authority=self.authority, now=NOW + 1,
            )
        self.assertEqual(self.runtime.memory.history("clock-task"), ())


if __name__ == "__main__":
    unittest.main()
