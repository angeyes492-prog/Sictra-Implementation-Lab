import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from sictra_block1 import (
    ManualWatchlistCycle,
    ManualWatchlistCycleViolation,
    build_eurostat_manual_bundle,
)
from test_block1_eurostat_maritime_mapper import workbook


KEY = b"w" * 32
URL = "https://ec.europa.eu/eurostat/databrowser/view/tran_r_mago_nm/default/table"


def source_bundle(*, updated, observed, value="12.5", correlation="watchlist"):
    return build_eurostat_manual_bundle(
        "eurostat.xlsx",
        workbook(last_updated=updated, rows=(("BE", "Belgium", value, None, "13.5"),)),
        "COUNTRY", source_url=URL, observed_at=observed,
        correlation_id=correlation,
    )


class ManualWatchlistCycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.path = Path(self.temp.name) / "watchlist.json"
        identities = iter(("cycle-001", "cycle-002", "cycle-003"))
        times = iter((10_001, 10_002, 10_003))
        self.cycle = ManualWatchlistCycle(
            self.path, integrity_key=KEY,
            clock=lambda: next(times), id_factory=lambda: next(identities),
        )
        self.first = source_bundle(
            updated="01/09/2026 00:00", observed=10_000,
            correlation="watchlist-first",
        )
        self.second = source_bundle(
            updated="05/09/2026 06:14", observed=10_001, value="14",
            correlation="watchlist-second",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_baseline_replay_and_new_delta_are_durable_and_recomputable(self):
        baseline = self.cycle.ingest(self.first)
        self.assertEqual(baseline["status"], "BASELINE_ESTABLISHED_NOT_EVIDENCE")
        replay = self.cycle.ingest({**self.first, "observed_at": 10_001})
        self.assertTrue(replay["replay"])
        self.assertEqual(len(self.cycle.list_cycles()), 1)

        current = self.cycle.ingest(self.second)
        self.assertEqual(current["status"], "DELTA_DETECTED_NOT_EVIDENCE")
        self.assertEqual(current["change_count"], 1)
        self.assertEqual(len(self.cycle.list_cycles()), 2)
        delta = self.cycle.latest_delta()
        self.assertEqual(delta["changes"][0]["absolute_delta_thousand_tonnes"], 1.5)
        delta["changes"][0]["absolute_delta_thousand_tonnes"] = 999
        self.assertEqual(
            self.cycle.latest_delta()["changes"][0]["absolute_delta_thousand_tonnes"], 1.5
        )

        reopened = ManualWatchlistCycle(
            self.path, integrity_key=KEY, clock=lambda: 10_004,
        )
        self.assertEqual(len(reopened.list_cycles()), 2)
        self.assertEqual(reopened.latest_delta()["status"], "DELTA_DETECTED_NOT_EVIDENCE")

    def test_tampered_delta_wrong_key_and_capacity_configuration_fail_closed(self):
        self.cycle.ingest(self.first)
        document = json.loads(self.path.read_text(encoding="utf-8"))
        document["entries"][0]["delta"]["status"] = "VERIFIED"
        self.path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(ManualWatchlistCycleViolation):
            self.cycle.list_cycles()
        with self.assertRaises(ManualWatchlistCycleViolation):
            ManualWatchlistCycle(
                self.path, integrity_key=b"z" * 32, clock=lambda: 10_004,
            ).list_cycles()

    def test_failed_atomic_replace_preserves_prior_checkpoint(self):
        self.cycle.ingest(self.first)
        prior = self.path.read_bytes()
        self.cycle.failure_injector = lambda point: (_ for _ in ()).throw(
            OSError(point)
        )
        with self.assertRaises(ManualWatchlistCycleViolation):
            self.cycle.ingest(self.second)
        self.assertEqual(self.path.read_bytes(), prior)
        reopened = ManualWatchlistCycle(
            self.path, integrity_key=KEY, clock=lambda: 10_004,
        )
        self.assertEqual(len(reopened.list_cycles()), 1)

    def test_same_release_drift_regression_and_capacity_fail_without_advancing(self):
        limited = ManualWatchlistCycle(
            Path(self.temp.name) / "limited.json", integrity_key=KEY,
            clock=lambda: 10_001, id_factory=lambda: "limited-cycle", max_cycles=1,
        )
        limited.ingest(self.first)
        with self.assertRaises(ManualWatchlistCycleViolation):
            limited.ingest(self.second)

        same_release_drift = source_bundle(
            updated="01/09/2026 00:00", observed=10_001, value="99",
            correlation="watchlist-drift",
        )
        with self.assertRaises(ManualWatchlistCycleViolation):
            self.cycle.ingest(self.first)
            self.cycle.ingest(same_release_drift)

        regressed = source_bundle(
            updated="31/08/2026 00:00", observed=10_002,
            correlation="watchlist-regressed",
        )
        with self.assertRaises(ManualWatchlistCycleViolation):
            self.cycle.ingest(regressed)

    def test_empty_cycle_has_no_delta(self):
        self.assertIsNone(self.cycle.latest_delta())
        self.assertEqual(self.cycle.list_cycles(), [])


if __name__ == "__main__":
    unittest.main()
