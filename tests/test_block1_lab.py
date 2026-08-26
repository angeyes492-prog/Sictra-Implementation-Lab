"""Regression coverage for the interactive Block 1 laboratory boundary."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from sictra_block1.lab import LAB_SCOPE, execute_scenario


class Block1LabTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = Path(self.temp.name) / "lab.sqlite3"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_valid_scenario_exposes_full_trace_and_one_effect(self):
        report = execute_scenario("valid", store_path=self.store)
        self.assertEqual(report["scope"], LAB_SCOPE)
        self.assertEqual(report["memory_record_count"], 1)
        self.assertEqual(report["result"]["enforcement"]["status"], "COMMITTED")
        self.assertEqual(
            report["result"]["trace"],
            ["E01->E02", "E02->E03", "E03->E05", "E05->E06",
             "E06->E07", "E07->E08", "E08->RUNTIME", "RUNTIME->CALLER"],
        )
        self.assertIn("global gate acceptance", report["non_claims"])

    def test_adversarial_scenarios_fail_closed_without_memory_effect(self):
        for scenario in ("missing-authority", "stale-evidence", "wrong-scope"):
            with self.subTest(scenario=scenario):
                report = execute_scenario(scenario, store_path=self.store)
                self.assertEqual(report["memory_record_count"], 0)
                self.assertEqual(report["result"]["enforcement"]["status"], "NOT_EXECUTED")
                self.assertEqual(report["journal"][-1]["state"], "TERMINAL_NO_EFFECT")

    def test_unknown_scenario_is_rejected_before_runtime(self):
        with self.assertRaises(ValueError):
            execute_scenario("unknown", store_path=self.store)


if __name__ == "__main__":
    unittest.main()
