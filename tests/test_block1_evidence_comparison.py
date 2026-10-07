"""Reference cases use declared measurements, not the evaluator as oracle."""

from copy import deepcopy
import unittest

from sictra_block1.evidence_comparison import (
    EvidenceComparisonViolation, compare_dossier_measurements,
)


def maritime(root, value=14.0, period=2025, geography="BE"):
    return {"dossier_id": f"maritime:{root}", "source": {
        "source_id": "eurostat", "root_source_identity": root,
        "content_sha256": "a" * 64},
        "facts": [{"fact_id": "FACT-001", "observed_change": {
            "geo_code": geography, "time_period": period,
            "after_value_thousand_tonnes": value}}],
        "interpretations": [], "hypotheses": [], "publication_state": "BLOCKED"}


def customs():
    return {"dossier_id": "hn-customs:one", "source": {
        "source_id": "HN_ADUANAS_BULLETINS", "root_source_identity": "HN_SARAH",
        "content_sha256": "b" * 64},
        "facts": [{"fact_id": "FACT-001", "observed_change": {
            "customs_point": "Puerto Cortes", "after_period": "2025Q1",
            "after_value_usd_million": 14.0}}],
        "interpretations": [], "hypotheses": [], "publication_state": "BLOCKED"}


class EvidenceComparisonTests(unittest.TestCase):
    def test_exact_matching_measurement_is_only_a_review_candidate(self):
        result = compare_dossier_measurements(maritime("publisher-a"), maritime("publisher-b"))
        self.assertEqual("EXACT_VALUE_AGREEMENT_REVIEW_REQUIRED", result["status"])
        self.assertEqual(["publisher-a", "publisher-b"], result["source_roots"])
        self.assertEqual(["FACT-001", "FACT-001"], [result["matched"][0]["primary_fact_id"],
                                                      result["matched"][0]["candidate_fact_id"]])
        self.assertEqual("NOT_RESOLVED", result["resolution"])
        self.assertEqual("NOT_ACCEPTED", result["acceptance"])
        self.assertEqual("BLOCKED", result["publication"])

    def test_different_values_and_partial_coverage_preserve_ambiguity(self):
        result = compare_dossier_measurements(maritime("publisher-a"), maritime("publisher-b", 15.0))
        self.assertEqual("VALUE_DIFFERENCE_REVIEW_REQUIRED", result["status"])
        self.assertEqual("DIFFERENT_AFTER_VALUE", result["matched"][0]["comparison"])
        primary = maritime("publisher-a")
        primary["facts"].append({"fact_id": "FACT-002", "observed_change": {
            "geo_code": "DE", "time_period": 2025, "after_value_thousand_tonnes": 6.0}})
        result = compare_dossier_measurements(primary, maritime("publisher-b"))
        self.assertEqual("PARTIAL_COVERAGE_REVIEW_REQUIRED", result["status"])
        self.assertEqual(["FACT-002"], result["unmatched_primary_fact_ids"])
        self.assertEqual([], result["unmatched_candidate_fact_ids"])
        candidate = maritime("publisher-b")
        candidate["facts"].append({"fact_id": "FACT-002", "observed_change": {
            "geo_code": "FR", "time_period": 2025, "after_value_thousand_tonnes": 6.0}})
        result = compare_dossier_measurements(maritime("publisher-a"), candidate)
        self.assertEqual("PARTIAL_COVERAGE_REVIEW_REQUIRED", result["status"])
        self.assertEqual(["FACT-002"], result["unmatched_candidate_fact_ids"])
        result = compare_dossier_measurements(maritime("publisher-a", 12.0), candidate)
        self.assertEqual("VALUE_DIFFERENCE_REVIEW_REQUIRED", result["status"])
        self.assertEqual(["FACT-002"], result["unmatched_candidate_fact_ids"])

    def test_metric_geography_and_period_mismatch_cannot_corroborate(self):
        primary = maritime("publisher-a")
        for candidate in (customs(), maritime("publisher-b", geography="DE"),
                          maritime("publisher-b", period=2024)):
            result = compare_dossier_measurements(primary, candidate)
            self.assertEqual("NO_SHARED_MEASUREMENT", result["status"])
            self.assertEqual([], result["matched"])
            self.assertEqual("NOT_RESOLVED", result["resolution"])

    def test_same_root_forged_or_duplicate_measurements_reject(self):
        with self.assertRaisesRegex(EvidenceComparisonViolation, "INDEPENDENT_ROOT_REQUIRED"):
            compare_dossier_measurements(maritime("publisher-a"), maritime("publisher-a"))
        bad = maritime("publisher-b")
        bad["facts"].append(deepcopy(bad["facts"][0]))
        with self.assertRaisesRegex(EvidenceComparisonViolation, "MEASUREMENT_INVALID_OR_DUPLICATED"):
            compare_dossier_measurements(maritime("publisher-a"), bad)
        bad = maritime("publisher-b", float("nan"))
        with self.assertRaisesRegex(EvidenceComparisonViolation, "MEASUREMENT_INVALID_OR_DUPLICATED"):
            compare_dossier_measurements(maritime("publisher-a"), bad)
        bad = maritime("publisher-b")
        bad["interpretations"] = ["invented"]
        with self.assertRaisesRegex(EvidenceComparisonViolation, "DOSSIER_BOUNDARY_INVALID"):
            compare_dossier_measurements(maritime("publisher-a"), bad)

    def test_missing_dossier_identity_rejects_before_comparison(self):
        for missing_id in ("", "   "):
            with self.subTest(dossier_id=missing_id):
                bad = maritime("publisher-b")
                bad["dossier_id"] = missing_id
                with self.assertRaisesRegex(EvidenceComparisonViolation, "DOSSIER_BOUNDARY_INVALID"):
                    compare_dossier_measurements(maritime("publisher-a"), bad)
        bad = maritime("publisher-b")
        bad["facts"][0]["fact_id"] = "  "
        with self.assertRaisesRegex(EvidenceComparisonViolation, "MEASUREMENT_INVALID_OR_DUPLICATED"):
            compare_dossier_measurements(maritime("publisher-a"), bad)
        bad = maritime("publisher-b")
        bad["source"]["root_source_identity"] = "  "
        with self.assertRaisesRegex(EvidenceComparisonViolation, "INDEPENDENT_ROOT_REQUIRED"):
            compare_dossier_measurements(maritime("publisher-a"), bad)

    def test_whitespace_only_measurement_scope_rejects(self):
        blank_customs_point = customs()
        blank_customs_point["facts"][0]["observed_change"]["customs_point"] = "  "
        blank_customs_period = customs()
        blank_customs_period["facts"][0]["observed_change"]["after_period"] = "  "
        for candidate in (maritime("publisher-b", geography="   "),
                          blank_customs_point, blank_customs_period):
            with self.subTest(change=candidate["facts"][0]["observed_change"]):
                with self.assertRaisesRegex(EvidenceComparisonViolation, "MEASUREMENT_SCOPE_INVALID"):
                    compare_dossier_measurements(maritime("publisher-a"), candidate)

    def test_padded_root_cannot_appear_independent_from_same_root(self):
        for root in (" publisher-a", "publisher-a ", " publisher-b "):
            with self.subTest(root=root):
                with self.assertRaisesRegex(EvidenceComparisonViolation, "INDEPENDENT_ROOT_REQUIRED"):
                    compare_dossier_measurements(maritime("publisher-a"), maritime(root))


if __name__ == "__main__":
    unittest.main()
