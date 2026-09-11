import unittest
from dataclasses import replace
from datetime import datetime, timezone

from sictra_block2_design.assistive_review import (
    AssistiveReviewReceipt, AssistiveReviewTarget, AssistiveReviewViolation,
    assess_assistive_review,
)


BUILT = datetime(2026, 9, 3, 12, tzinfo=timezone.utc)
REVIEWED = datetime(2026, 9, 3, 13, tzinfo=timezone.utc)


def target(**changes):
    value = AssistiveReviewTarget(
        "a" * 40, "PROJECT-DEMO", "http://127.0.0.1:8766/", "b" * 64, BUILT,
    )
    return replace(value, **changes)


def receipt(value=None, **changes):
    value = value or target()
    base = AssistiveReviewReceipt(
        "A11Y-RECEIPT-001", "0.1.0", value.git_sha, value.fixture_id, value.console_url,
        value.probe_sha256, "REVIEWER-001", "ACCESSIBILITY-REVIEWER", True,
        "NVDA", "2025.1", "Windows 11", "Edge", "136", 200, "DEFAULT",
        "SKIP_LINK", "skip link announced", "skip link announced", "PASS_LOCAL", "NONE",
        ("LOCAL-NOTE-001",), ("synthetic fixture",), REVIEWED,
    )
    return replace(base, **changes)


class AssistiveReviewTests(unittest.TestCase):
    def test_complete_human_receipt_is_recorded_without_promotion(self):
        result = assess_assistive_review(target(), receipt())
        self.assertTrue(result.recorded)
        self.assertEqual("NOT_PROMOTED", result.promotion_state)
        self.assertEqual("NOT_ACCEPTED", result.acceptance_state)

    def test_target_substitution_and_pre_target_review_return_upstream(self):
        value = target()
        result = assess_assistive_review(value, receipt(
            value, git_sha="c" * 40, probe_sha256="d" * 64,
            reviewed_at=datetime(2026, 9, 3, 11, tzinfo=timezone.utc),
        ))
        self.assertEqual("RETURN_UPSTREAM", result.disposition)
        self.assertEqual(
            ("TARGET_GIT_SHA_MISMATCH", "TARGET_PROBE_MISMATCH", "REVIEW_BEFORE_TARGET"),
            result.reasons,
        )

    def test_review_authority_and_outcome_severity_mismatches_are_invalid(self):
        result = assess_assistive_review(target(), receipt(
            reviewer_authorized=False, severity="MAJOR",
        ))
        self.assertEqual("INVALID_REVIEW", result.disposition)
        self.assertEqual(
            ("REVIEWER_AUTHORITY_UNVERIFIED", "PASS_WITH_NONZERO_SEVERITY"), result.reasons,
        )

    def test_reviewer_can_return_missing_or_unreproducible_evidence_upstream(self):
        result = assess_assistive_review(target(), receipt(outcome="RETURN_UPSTREAM"))
        self.assertEqual("RETURN_UPSTREAM", result.disposition)
        self.assertEqual(("REVIEWER_RETURNED_UPSTREAM",), result.reasons)

    def test_malformed_contract_version_technology_hash_and_evidence_are_rejected(self):
        for changes in (
            {"contract_version": "1.0.0"},
            {"technology": "EDGE_READER"},
            {"probe_sha256": "NOT-A-HASH"},
            {"evidence_refs": ()},
        ):
            with self.subTest(changes=changes):
                with self.assertRaises(AssistiveReviewViolation):
                    receipt(**changes)


if __name__ == "__main__":
    unittest.main()
