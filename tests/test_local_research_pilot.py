from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sictra_block4_orchestrator.operations_store import OperationsError
from sictra_block4_orchestrator.pilot import run_pilot


class LocalResearchPilotTests(unittest.TestCase):
    def test_multicycle_pilot_proves_restart_pause_and_operations_restore(self):
        with tempfile.TemporaryDirectory() as parent:
            report = run_pilot(Path(parent) / "pilot")
            self.assertEqual("SYNTHETIC_LOCAL_PILOT", report["scope"])
            self.assertEqual(3, len(report["cycles"]))
            self.assertEqual(2, len(report["outputs"]))
            self.assertEqual({"evaluations": 3, "state": "TASK_SPECIFIC_WAITS_ENFORCED",
                              "restart_replay": "VERIFIED", "pause": "VERIFIED",
                              "resolution": "NOT_RESOLVED"}, report["research"])
            self.assertEqual("VERIFIED", report["restore"])
            self.assertEqual("BLOCKED", report["publication"])
            self.assertEqual("NONE", report["delivery"])

    def test_existing_directory_is_never_reinitialized(self):
        with tempfile.TemporaryDirectory() as parent:
            root = Path(parent) / "retained"
            root.mkdir()
            marker = root / "retained.txt"
            marker.write_text("keep", encoding="utf-8")
            with patch("sictra_block4_orchestrator.pilot.initialize") as initialize:
                with self.assertRaisesRegex(OperationsError, "PILOT_REQUIRES_FRESH_PATH"):
                    run_pilot(root)
                initialize.assert_not_called()
            self.assertEqual("keep", marker.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
