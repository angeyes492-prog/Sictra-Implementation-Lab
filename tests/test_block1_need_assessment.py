import unittest

from sictra_block1.need_assessment import (
    NeedAssessmentViolation, assess_linked_data_need,
)


EURO_NEED = "Independent corroborating source for the same geography and period."
METHODOLOGY_NEED = "Source metadata explaining revisions and coverage changes."


def comparison(status, matched, *, unmatched_primary=(), unmatched_candidate=()):
    return {"primary_dossier_id": "dossier-a", "candidate_dossier_id": "dossier-b",
            "status": status, "matched": matched, "resolution": "NOT_RESOLVED",
            "unmatched_primary_fact_ids": list(unmatched_primary),
            "unmatched_candidate_fact_ids": list(unmatched_candidate),
            "acceptance": "NOT_ACCEPTED", "publication": "BLOCKED"}


class NeedAssessmentTests(unittest.TestCase):
    def test_unrelated_candidate_cannot_resolve_known_corroboration_need(self):
        result = assess_linked_data_need("eurostat", EURO_NEED,
            comparison("NO_SHARED_MEASUREMENT", []))
        self.assertEqual("INDEPENDENT_CORROBORATION", result["need_kind"])
        self.assertEqual("INSUFFICIENT", result["verdict"])
        self.assertEqual("NO_SHARED_MEASUREMENT", result["reason_code"])
        self.assertEqual("REQUEST_COMPARABLE_APPROVED_SOURCE", result["next_action"])
        self.assertEqual("NOT_RESOLVED", result["resolution"])

    def test_agreement_still_needs_review_and_disagreement_is_not_causality(self):
        matched = [{"primary_value": 14, "candidate_value": 14,
                    "comparison": "EXACT_AFTER_VALUE"}]
        agreed = assess_linked_data_need("eurostat", EURO_NEED,
            comparison("EXACT_VALUE_AGREEMENT_REVIEW_REQUIRED", matched))
        self.assertEqual("REVIEW_REQUIRED", agreed["verdict"])
        self.assertEqual("EXACT_AFTER_VALUES_NOT_CORROBORATION", agreed["reason_code"])
        disputed = assess_linked_data_need("eurostat", EURO_NEED,
            comparison("VALUE_DIFFERENCE_REVIEW_REQUIRED", [{"primary_value": 14,
                "candidate_value": 15, "comparison": "DIFFERENT_AFTER_VALUE"}]))
        self.assertEqual("MEASUREMENT_DISAGREEMENT", disputed["verdict"])
        self.assertEqual("REVIEW_REVISIONS_AND_COVERAGE", disputed["next_action"])
        self.assertEqual("NOT_ACCEPTED", disputed["acceptance"])
        self.assertEqual("BLOCKED", disputed["publication"])

    def test_partial_other_need_and_unknown_wording_remain_insufficient(self):
        partial = comparison("PARTIAL_COVERAGE_REVIEW_REQUIRED", [
            {"primary_value": 14, "candidate_value": 14,
             "comparison": "EXACT_AFTER_VALUE"}], unmatched_primary=("unmatched-1",))
        self.assertEqual("INSUFFICIENT", assess_linked_data_need(
            "eurostat", EURO_NEED, partial)["verdict"])
        self.assertEqual("DIFFERENT_EVIDENCE_TYPE_REQUIRED", assess_linked_data_need(
            "eurostat", METHODOLOGY_NEED, partial)["reason_code"])
        self.assertEqual("NEED_UNCLASSIFIED", assess_linked_data_need(
            "eurostat", "Corroborate by guessing.", partial)["reason_code"])

    def test_forged_resolution_and_impossible_status_reject(self):
        forged = comparison("NO_SHARED_MEASUREMENT", [])
        forged["resolution"] = "RESOLVED"
        with self.assertRaisesRegex(NeedAssessmentViolation, "COMPARISON_BOUNDARY_INVALID"):
            assess_linked_data_need("eurostat", EURO_NEED, forged)
        with self.assertRaisesRegex(NeedAssessmentViolation, "COMPARISON_MATCH_STATUS_INVALID"):
            assess_linked_data_need("eurostat", EURO_NEED,
                comparison("EXACT_VALUE_AGREEMENT_REVIEW_REQUIRED", []))

    def test_internal_comparison_contradictions_reject_before_verdict(self):
        equal = {"primary_value": 14, "candidate_value": 14,
                 "comparison": "EXACT_AFTER_VALUE"}
        different = {"primary_value": 14, "candidate_value": 15,
                     "comparison": "DIFFERENT_AFTER_VALUE"}
        contradictions = (
            comparison("VALUE_DIFFERENCE_REVIEW_REQUIRED", [equal]),
            comparison("EXACT_VALUE_AGREEMENT_REVIEW_REQUIRED", [different]),
            comparison("PARTIAL_COVERAGE_REVIEW_REQUIRED", [equal]),
            comparison("PARTIAL_COVERAGE_REVIEW_REQUIRED", [different],
                       unmatched_primary=("unmatched-1",)),
            comparison("EXACT_VALUE_AGREEMENT_REVIEW_REQUIRED", [
                {**equal, "comparison": "DIFFERENT_AFTER_VALUE"}]),
        )
        for forged in contradictions:
            with self.subTest(status=forged["status"], matched=forged["matched"]):
                with self.assertRaisesRegex(NeedAssessmentViolation,
                                            "COMPARISON_MATCH_STATUS_INVALID"):
                    assess_linked_data_need("eurostat", EURO_NEED, forged)


if __name__ == "__main__":
    unittest.main()
