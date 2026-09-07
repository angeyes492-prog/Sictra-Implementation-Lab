import json
from hashlib import sha256
import hmac
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from sictra_block1 import (
    IntelligenceDossierStore, IntelligenceDossierViolation,
    build_intelligence_dossier,
)


KEY = b"d" * 32
BRIDGE_KEY = b"g" * 32


def resign(value):
    unsigned = {key: item for key, item in value.items() if key != "attestation"}
    value["attestation"] = hmac.new(
        BRIDGE_KEY, json.dumps(unsigned, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(), sha256,
    ).hexdigest()
    return value


def reviewable_delta():
    change = {
        "geo_code": "BE", "geo_label": "Belgium", "time_period": 2021,
        "change_type": "VALUE_CHANGED", "before_value_thousand_tonnes": 13.5,
        "after_value_thousand_tonnes": 15.0, "absolute_delta_thousand_tonnes": 1.5,
        "before_status_flag": None, "after_status_flag": None,
    }
    delta = {
        "scope": "BLOCK1_EUROSTAT_MARITIME_MANUAL_WATCHLIST", "source_id": "eurostat",
        "dataset_code": "tran_r_mago_nm", "selected_geo_level": "COUNTRY",
        "previous": {"content_sha256": "1" * 64, "last_updated": "2026-09-05T06:14", "coverage": {}},
        "current": {"content_sha256": "2" * 64, "last_updated": "2026-09-06T06:14", "coverage": {}},
        "change_count": 1, "changes": [change], "status": "DELTA_DETECTED_NOT_EVIDENCE",
        "evidence_state": "NOT_EVIDENCE", "next_state": "REQUIRES_SOURCE_ATTESTATION_AND_REVIEW",
    }
    digest = sha256(json.dumps(delta, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()).hexdigest()
    result = {
        "scope": "BLOCK1_LOCAL_ATTESTED_WATCHLIST_BRIDGE", "source_id": "eurostat",
        "schema_version": "0.1.0", "attestation_issuer": "watchlist-bridge",
        "observed_at": 10_000, "content_sha256": "2" * 64,
        "source_approval_fingerprint": "3" * 64, "source_binding_fingerprint": "4" * 64,
        "watchlist_receipt": {
            "scope": "BLOCK1_LOCAL_MANUAL_WATCHLIST_CYCLE", "cycle_id": "cycle-001",
            "recorded_at": 10_001, "bundle_sha256": "5" * 64,
            "delta_sha256": digest, "record_hash": "6" * 64,
            "status": "DELTA_DETECTED_NOT_EVIDENCE", "change_count": 1,
            "evidence_state": "NOT_EVIDENCE", "replay": False,
        },
        "delta": delta, "next_state": "REQUIRES_REVIEW",
        "evidence_state": "ATTESTED_INPUT_DELTA_NOT_EVIDENCE",
    }
    return resign(result)


class IntelligenceDossierTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.path = Path(self.temp.name) / "dossiers.json"
        self.now = 10_001
        self.store = IntelligenceDossierStore(
            self.path, integrity_key=KEY, bridge_keys={"watchlist-bridge": BRIDGE_KEY},
            clock=lambda: self.now,
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_builds_literal_facts_and_abstains_from_interpretation(self):
        dossier = build_intelligence_dossier(
            reviewable_delta(), bridge_keys={"watchlist-bridge": BRIDGE_KEY},
        )
        self.assertEqual(len(dossier["facts"]), 1)
        self.assertEqual(dossier["facts"][0]["observed_change"]["absolute_delta_thousand_tonnes"], 1.5)
        self.assertEqual(dossier["interpretations"], [])
        self.assertEqual(dossier["hypotheses"], [])
        self.assertEqual(dossier["review_state"], "REQUIRES_HUMAN_INTERPRETATION")
        self.assertEqual(dossier["publication_state"], "BLOCKED")
        self.assertEqual(dossier["affected_scope"]["geo_codes"], ["BE"])

    def test_persists_replays_reopens_and_returns_defensive_dossiers(self):
        receipt = self.store.persist(reviewable_delta())
        self.assertFalse(receipt["replay"])
        self.assertTrue(self.store.persist(reviewable_delta())["replay"])
        reopened = IntelligenceDossierStore(
            self.path, integrity_key=KEY, bridge_keys={"watchlist-bridge": BRIDGE_KEY},
            clock=lambda: self.now,
        )
        dossiers = reopened.list_dossiers()
        self.assertEqual(len(dossiers), 1)
        dossiers[0]["publication_state"] = "PUBLISHED"
        self.assertEqual(reopened.list_dossiers()[0]["publication_state"], "BLOCKED")

    def test_non_delta_and_broken_lineage_fail_before_persistence(self):
        invalid = reviewable_delta()
        invalid["delta"]["status"] = "NO_DELTA_NOT_EVIDENCE"
        with self.assertRaises(IntelligenceDossierViolation):
            self.store.persist(invalid)
        broken = reviewable_delta()
        broken["watchlist_receipt"]["delta_sha256"] = "0" * 64
        with self.assertRaises(IntelligenceDossierViolation):
            self.store.persist(resign(broken))
        forged = reviewable_delta()
        forged["observed_at"] += 1
        with self.assertRaises(IntelligenceDossierViolation):
            self.store.persist(forged)
        self.assertFalse(self.path.exists())

    def test_tamper_wrong_key_and_atomic_failure_fail_closed(self):
        self.store.persist(reviewable_delta())
        prior = self.path.read_bytes()
        self.store.failure_injector = lambda point: (_ for _ in ()).throw(OSError(point))
        changed = reviewable_delta()
        changed["delta"]["changes"][0]["time_period"] = 2022
        changed["delta"]["current"]["last_updated"] = "2026-09-07T06:14"
        changed["watchlist_receipt"]["delta_sha256"] = sha256(json.dumps(
            changed["delta"], ensure_ascii=False, separators=(",", ":"), sort_keys=True,
        ).encode()).hexdigest()
        with self.assertRaises(IntelligenceDossierViolation):
            self.store.persist(resign(changed))
        self.assertEqual(self.path.read_bytes(), prior)
        with self.assertRaises(IntelligenceDossierViolation):
            IntelligenceDossierStore(
                self.path, integrity_key=b"z" * 32, bridge_keys={"watchlist-bridge": BRIDGE_KEY},
                clock=lambda: self.now,
            ).list_dossiers()
        with self.assertRaises(IntelligenceDossierViolation):
            IntelligenceDossierStore(
                self.path, integrity_key=KEY, bridge_keys={"watchlist-bridge": b"z" * 32},
                clock=lambda: self.now,
            ).list_dossiers()
        malformed = json.loads(self.path.read_text(encoding="utf-8"))
        malformed["config"] = 7
        self.path.write_text(json.dumps(malformed), encoding="utf-8")
        with self.assertRaises(IntelligenceDossierViolation):
            IntelligenceDossierStore(
                self.path, integrity_key=KEY, bridge_keys={"watchlist-bridge": BRIDGE_KEY},
                clock=lambda: self.now,
            ).list_dossiers()
        self.path.write_bytes(prior)
        document = json.loads(self.path.read_text(encoding="utf-8"))
        document["records"][0]["dossier"]["publication_state"] = "PUBLISHED"
        self.path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(IntelligenceDossierViolation):
            IntelligenceDossierStore(
                self.path, integrity_key=KEY, bridge_keys={"watchlist-bridge": BRIDGE_KEY},
                clock=lambda: self.now,
            ).list_dossiers()


if __name__ == "__main__":
    unittest.main()
