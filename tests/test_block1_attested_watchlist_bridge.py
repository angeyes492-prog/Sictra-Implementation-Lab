from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from sictra_block1 import (
    AttestedEvidenceStore, AttestedWatchlistBridge,
    AttestedWatchlistBridgeViolation, EvidenceIssuer, ManualWatchlistCycle,
    SourceApprovalRecord, SourceBindingIssuer, SourceGateway, SourceRegistration,
    build_eurostat_manual_bundle, build_intelligence_dossier,
)
from test_block1_attested_evidence_store import (
    BINDING_KEY, CLAIM, EVIDENCE_KEY, INTEGRITY_KEY, NOW, SCOPE, URL,
    observed_source,
)
from test_block1_eurostat_maritime_mapper import workbook

BRIDGE_KEY = b"g" * 32


class AttestedWatchlistBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.now = NOW
        self.store = AttestedEvidenceStore(
            Path(self.temp.name) / "evidence.json", evidence_keys={"gateway": EVIDENCE_KEY},
            evidence_scope=SCOPE, evidence_max_age=10, evidence_claims=frozenset((CLAIM,)),
            integrity_key=INTEGRITY_KEY, clock=lambda: self.now,
        )
        cycle_ids = iter(("attested-cycle-001", "attested-cycle-002"))
        self.cycle = ManualWatchlistCycle(
            Path(self.temp.name) / "watchlist.json", integrity_key=b"w" * 32,
            clock=lambda: self.now, id_factory=lambda: next(cycle_ids),
        )
        self.bridge = AttestedWatchlistBridge(
            self.store, self.cycle, receipt_issuer="watchlist-bridge", receipt_key=BRIDGE_KEY,
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_current_attested_record_creates_only_a_non_evidentiary_baseline(self):
        source = observed_source()
        self.store.persist(source)
        receipt = self.bridge.ingest("eurostat", now=NOW)
        self.assertEqual(receipt["watchlist_receipt"]["status"], "BASELINE_ESTABLISHED_NOT_EVIDENCE")
        self.assertEqual(receipt["evidence_state"], "ATTESTED_INPUT_DELTA_NOT_EVIDENCE")
        self.assertEqual(receipt["next_state"], "AWAIT_NEWER_SOURCE")
        self.assertEqual(receipt["source_approval_fingerprint"], source["source_approval_fingerprint"])

    def test_stale_source_fails_and_duplicate_same_release_does_not_advance(self):
        self.store.persist(observed_source())
        self.now = NOW + 11
        with self.assertRaises(AttestedWatchlistBridgeViolation):
            self.bridge.ingest("eurostat", now=self.now)
        self.assertEqual(self.cycle.list_cycles(), [])

        self.now = NOW
        self.store.persist(observed_source(correlation="watchlist-second"))
        receipt = self.bridge.ingest("eurostat", now=self.now)
        self.assertEqual(receipt["watchlist_receipt"]["status"], "BASELINE_ESTABLISHED_NOT_EVIDENCE")
        self.assertEqual(len(self.cycle.list_cycles()), 1)

    def test_new_attested_version_after_baseline_expiry_generates_reviewable_delta(self):
        baseline = observed_source(observed=NOW)
        self.store.persist(baseline)
        self.assertEqual(
            self.bridge.ingest("eurostat", now=NOW)["watchlist_receipt"]["status"],
            "BASELINE_ESTABLISHED_NOT_EVIDENCE",
        )

        self.now = NOW + 11
        registration = SourceRegistration(
            "eurostat", "Eurostat / European Commission", SCOPE, ("ec.europa.eu",),
            frozenset((CLAIM,)), "MANUAL_SOURCE_BUNDLE", 131_072, "BOUND",
        )
        approval = SourceApprovalRecord(
            "eurostat", "PROJECT_OWNER", NOW, "evidence/block1_eurostat_maritime_registration_draft_v0.1.md",
            registration.allowed_hosts, registration.claim_keys,
            registration.access_method, registration.max_content_bytes, "APPROVED",
        )
        binding = SourceBindingIssuer("review-control", BINDING_KEY).issue(
            registration, approval, now=NOW, ttl=100,
        )
        gateway = SourceGateway(
            registrations=(registration,), issuer=EvidenceIssuer("gateway", EVIDENCE_KEY),
            binding_keys={"review-control": BINDING_KEY}, bindings={"eurostat": binding},
            now=self.now,
        )
        newer = build_eurostat_manual_bundle(
            "eurostat-newer.xlsx", workbook(
                last_updated="06/09/2026 06:14", rows=(("BE", "Belgium", "14", None, "15"),),
            ), "COUNTRY", source_url=URL, observed_at=self.now,
            correlation_id="watchlist-newer-version",
        )
        self.store.persist(gateway.attest_manual_bundle(newer, now=self.now))
        receipt = self.bridge.ingest("eurostat", now=self.now)
        self.assertEqual(receipt["watchlist_receipt"]["status"], "DELTA_DETECTED_NOT_EVIDENCE")
        self.assertEqual(receipt["watchlist_receipt"]["change_count"], 2)
        self.assertEqual(receipt["next_state"], "REQUIRES_REVIEW")
        dossier = build_intelligence_dossier(receipt, bridge_keys={"watchlist-bridge": BRIDGE_KEY})
        self.assertEqual(len(dossier["facts"]), 2)
        self.assertEqual(dossier["interpretations"], [])
        self.assertEqual(dossier["publication_state"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
