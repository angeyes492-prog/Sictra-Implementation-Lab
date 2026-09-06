from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from sictra_block1 import (
    AttestedEvidenceStore, AttestedWatchlistBridge,
    AttestedWatchlistBridgeViolation, ManualWatchlistCycle,
)
from test_block1_attested_evidence_store import (
    CLAIM, EVIDENCE_KEY, INTEGRITY_KEY, NOW, SCOPE, observed_source,
)


class AttestedWatchlistBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.now = NOW
        self.store = AttestedEvidenceStore(
            Path(self.temp.name) / "evidence.json", evidence_keys={"gateway": EVIDENCE_KEY},
            evidence_scope=SCOPE, evidence_max_age=10, evidence_claims=frozenset((CLAIM,)),
            integrity_key=INTEGRITY_KEY, clock=lambda: self.now,
        )
        self.cycle = ManualWatchlistCycle(
            Path(self.temp.name) / "watchlist.json", integrity_key=b"w" * 32,
            clock=lambda: self.now, id_factory=lambda: "attested-cycle-001",
        )
        self.bridge = AttestedWatchlistBridge(self.store, self.cycle)

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

    def test_stale_or_ambiguous_current_source_fails_before_watchlist_advance(self):
        self.store.persist(observed_source())
        self.now = NOW + 11
        with self.assertRaises(AttestedWatchlistBridgeViolation):
            self.bridge.ingest("eurostat", now=self.now)
        self.assertEqual(self.cycle.list_cycles(), [])

        self.now = NOW
        self.store.persist(observed_source(correlation="watchlist-second"))
        with self.assertRaises(AttestedWatchlistBridgeViolation):
            self.bridge.ingest("eurostat", now=self.now)
        self.assertEqual(self.cycle.list_cycles(), [])


if __name__ == "__main__":
    unittest.main()
