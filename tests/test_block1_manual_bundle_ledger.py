import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from sictra_block1 import (
    ManualBundleLedger,
    ManualBundleLedgerViolation,
    build_eurostat_manual_bundle,
)
from test_block1_eurostat_maritime_mapper import workbook


KEY = b"l" * 32
URL = "https://ec.europa.eu/eurostat/databrowser/view/tran_r_mago_nm/default/table?lang=en"


def bundle():
    return build_eurostat_manual_bundle(
        "eurostat.xlsx", workbook(), "COUNTRY", source_url=URL,
        observed_at=10_000, correlation_id="eurostat-ledger-001",
    )


class ManualBundleLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.path = Path(self.temp.name) / "ledger.json"
        self.store = ManualBundleLedger(
            self.path, integrity_key=KEY, clock=lambda: 10_001,
            id_factory=lambda: "bundle-test-0001",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_records_an_unattested_bundle_idempotently_without_minting_evidence(self):
        receipt = self.store.record(bundle())
        self.assertEqual(receipt["status"], "RECORDED_UNATTESTED_NOT_EVIDENCE")
        self.assertEqual(receipt["evidence_state"], "NOT_EVIDENCE")
        self.assertEqual(receipt["previous_hash"], "GENESIS")
        self.assertEqual(self.store.record(bundle()), receipt)
        self.assertEqual(self.store.list_receipts(), [receipt])
        reopened = ManualBundleLedger(self.path, integrity_key=KEY, clock=lambda: 10_002)
        self.assertEqual(reopened.list_receipts(), [receipt])

    def test_tampering_key_mismatch_and_bundle_state_fail_closed(self):
        self.store.record(bundle())
        document = json.loads(self.path.read_text(encoding="utf-8"))
        document["entries"][0]["bundle"]["content"] = "{}"
        self.path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(ManualBundleLedgerViolation):
            self.store.list_receipts()

        clean = ManualBundleLedger(
            Path(self.temp.name) / "other.json", integrity_key=KEY, clock=lambda: 10_001,
        )
        altered = {**bundle(), "attestation": "not allowed"}
        with self.assertRaises(ManualBundleLedgerViolation):
            clean.record(altered)

    def test_capacity_and_entry_identity_collisions_fail_closed(self):
        limited = ManualBundleLedger(
            Path(self.temp.name) / "limited.json", integrity_key=KEY, clock=lambda: 10_001,
            id_factory=lambda: "same-id", max_bundles=1,
        )
        limited.record(bundle())
        second = {**bundle(), "correlation_id": "eurostat-ledger-002"}
        with self.assertRaises(ManualBundleLedgerViolation):
            limited.record(second)

        colliding = ManualBundleLedger(
            Path(self.temp.name) / "colliding.json", integrity_key=KEY, clock=lambda: 10_001,
            id_factory=lambda: "same-id", max_bundles=2,
        )
        colliding.record(bundle())
        with self.assertRaises(ManualBundleLedgerViolation):
            colliding.record(second)

    def test_logical_time_cannot_regress(self):
        times = iter((10_001, 10_000))
        ledger = ManualBundleLedger(
            Path(self.temp.name) / "time.json", integrity_key=KEY,
            clock=lambda: next(times), id_factory=lambda: "time-entry",
            max_bundles=2,
        )
        ledger.record(bundle())
        with self.assertRaises(ManualBundleLedgerViolation):
            ledger.record({**bundle(), "correlation_id": "eurostat-ledger-time-002"})


if __name__ == "__main__":
    unittest.main()
