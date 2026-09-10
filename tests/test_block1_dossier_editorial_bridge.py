import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from sictra_block1 import (
    DossierEditorialBridge, DossierEditorialBridgeViolation,
    IntelligenceDossierStore, IntelligenceDossierViolation,
)
from test_block1_intelligence_dossier import BRIDGE_KEY, KEY, reviewable_delta


class DossierEditorialBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.path = Path(self.temp.name) / "dossiers.json"
        self.store = IntelligenceDossierStore(
            self.path, integrity_key=KEY, bridge_keys={"watchlist-bridge": BRIDGE_KEY},
            clock=lambda: 10_001,
        )
        self.receipt = self.store.persist(reviewable_delta())
        self.bridge = DossierEditorialBridge(self.store)

    def tearDown(self):
        self.temp.cleanup()

    def test_unreviewed_dossier_is_traceable_and_editorially_blocked(self):
        result = self.bridge.candidate(self.receipt["dossier_id"])
        candidate, assessment = result["candidate"], result["assessment"]
        self.assertEqual(assessment["disposition"], "RESEARCH_NEEDED")
        self.assertEqual(assessment["editorial_readiness"], "BLOCKED")
        self.assertIn("INSUFFICIENT_INDEPENDENT_ROOTS", assessment["reasons"])
        self.assertIn("MATERIAL_UNCERTAINTY", assessment["reasons"])
        self.assertEqual(candidate["event_id"], self.receipt["dossier_id"])
        self.assertEqual(candidate["evidence"]["source_ids"], ["eurostat"])
        self.assertEqual(result["publication_state"], "BLOCKED")
        self.assertIsNone(result["handoff"])

    def test_unknown_identity_and_tampered_store_fail_closed(self):
        with self.assertRaises(DossierEditorialBridgeViolation):
            self.bridge.candidate("unknown")
        document = json.loads(self.path.read_text(encoding="utf-8"))
        document["records"][0]["dossier"]["interpretations"] = ["forged"]
        self.path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(IntelligenceDossierViolation):
            self.bridge.candidate(self.receipt["dossier_id"])


if __name__ == "__main__":
    unittest.main()
