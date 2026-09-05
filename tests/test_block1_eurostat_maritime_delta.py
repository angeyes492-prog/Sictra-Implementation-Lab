import unittest

from sictra_block1 import (
    EurostatMaritimeDeltaViolation,
    build_eurostat_manual_bundle,
    compare_eurostat_manual_bundles,
    compare_eurostat_maritime_workbooks,
)
from test_block1_eurostat_maritime_mapper import workbook


class EurostatMaritimeDeltaTests(unittest.TestCase):
    def test_identical_file_is_an_explicit_non_evidentiary_no_change(self):
        payload = workbook()
        result = compare_eurostat_maritime_workbooks(
            "previous.xlsx", payload, "current.xlsx", payload, "COUNTRY"
        )
        self.assertEqual(result["status"], "IDENTICAL_FILE_NOT_EVIDENCE")
        self.assertEqual(result["change_count"], 0)
        self.assertEqual(result["evidence_state"], "NOT_EVIDENCE")
        self.assertEqual(result["next_state"], "NO_REVIEWABLE_DELTA")

    def test_newer_release_reports_value_addition_and_removal_without_inference(self):
        previous = workbook(
            last_updated="01/09/2026 00:00",
            rows=(("BE", "Belgium", "12.5", None, "13.5"),),
        )
        current = workbook(
            last_updated="05/09/2026 06:14",
            rows=(("BE", "Belgium", "14.0", None, ":"), ("NL", "Netherlands", "8", None, ":")),
        )
        result = compare_eurostat_maritime_workbooks(
            "previous.xlsx", previous, "current.xlsx", current, "COUNTRY"
        )
        self.assertEqual(result["status"], "DELTA_DETECTED_NOT_EVIDENCE")
        self.assertEqual(
            [item["change_type"] for item in result["changes"]],
            ["VALUE_CHANGED", "REMOVED_OBSERVATION", "ADDED_OBSERVATION"],
        )
        self.assertEqual(result["changes"][0]["absolute_delta_thousand_tonnes"], 1.5)
        self.assertIsNone(result["changes"][1]["absolute_delta_thousand_tonnes"])
        self.assertEqual(result["next_state"], "REQUIRES_SOURCE_ATTESTATION_AND_REVIEW")

    def test_same_release_content_drift_time_regression_and_bad_level_fail_closed(self):
        base = workbook(last_updated="05/09/2026 06:14")
        changed_same_time = workbook(
            last_updated="05/09/2026 06:14",
            rows=(("BE", "Belgium", "99", None, "13.5"),),
        )
        older = workbook(last_updated="04/09/2026 06:14")
        for previous, current, level in (
            (base, changed_same_time, "COUNTRY"),
            (base, older, "COUNTRY"),
            (base, base, "ALL"),
        ):
            with self.subTest(level=level), self.assertRaises(EurostatMaritimeDeltaViolation):
                compare_eurostat_maritime_workbooks(
                    "previous.xlsx", previous, "current.xlsx", current, level
                )

    def test_ledger_compatible_bundles_form_a_durable_delta_boundary(self):
        source_url = "https://ec.europa.eu/eurostat/databrowser/view/tran_r_mago_nm/default/table"
        previous = build_eurostat_manual_bundle(
            "previous.xlsx", workbook(last_updated="01/09/2026 00:00"),
            "COUNTRY", source_url=source_url, observed_at=10_000,
            correlation_id="watchlist-previous",
        )
        current = build_eurostat_manual_bundle(
            "current.xlsx",
            workbook(
                last_updated="05/09/2026 06:14",
                rows=(("BE", "Belgium", "14", None, "13.5"),),
            ),
            "COUNTRY", source_url=source_url, observed_at=10_001,
            correlation_id="watchlist-current",
        )
        result = compare_eurostat_manual_bundles(previous, current)
        self.assertEqual(result["status"], "DELTA_DETECTED_NOT_EVIDENCE")
        self.assertEqual(result["change_count"], 1)
        self.assertEqual(result["changes"][0]["absolute_delta_thousand_tonnes"], 1.5)

        with self.assertRaises(EurostatMaritimeDeltaViolation):
            compare_eurostat_manual_bundles(
                previous, {**current, "observed_at": 9_999}
            )


if __name__ == "__main__":
    unittest.main()
