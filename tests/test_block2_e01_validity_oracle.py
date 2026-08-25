import unittest

from sictra.block2_e01_validity import (
    ClaimValidityInput,
    ResidualEvidence,
    evaluate_claim_validity,
    residual_reusable_for_claim,
)
from sictra.block2_e01_validity_oracle import expected_claim_validity, expected_residual_reuse


def signature(item):
    d = evaluate_claim_validity(item)
    return d.status, d.missing_conditions, d.failed_conditions, d.admissible_evidence_ids


class ClaimValidityOracleTests(unittest.TestCase):
    def test_oracle_matches_supported_claim(self):
        item = ClaimValidityInput("narrow", frozenset({"same-task"}), frozenset({"same-task"}), frozenset(), frozenset({"e1"}))
        self.assertEqual(signature(item), expected_claim_validity(item))

    def test_oracle_matches_missing_condition(self):
        item = ClaimValidityInput("broad", frozenset({"same-task", "blind"}), frozenset({"same-task"}), frozenset(), frozenset({"e1"}))
        self.assertEqual(signature(item), expected_claim_validity(item))

    def test_oracle_matches_failed_condition(self):
        item = ClaimValidityInput("broad", frozenset({"same-task", "blind"}), frozenset({"same-task", "blind"}), frozenset({"blind"}), frozenset({"e1"}))
        self.assertEqual(signature(item), expected_claim_validity(item))

    def test_oracle_matches_multiple_missing_and_failed(self):
        item = ClaimValidityInput("broad", frozenset({"a", "b", "c"}), frozenset({"a", "c"}), frozenset({"c"}), frozenset({"e2", "e1"}))
        self.assertEqual(signature(item), expected_claim_validity(item))

    def assert_reuse_matches(self, residual, claim, conditions):
        self.assertEqual(
            residual_reusable_for_claim(residual, claim, conditions),
            expected_residual_reuse(residual, claim, conditions),
        )

    def test_reuse_oracle_matches_allowed_residual(self):
        r = ResidualEvidence("e1", frozenset({"narrow"}), frozenset({"broad"}), frozenset(), frozenset({"same-task"}))
        self.assert_reuse_matches(r, "narrow", {"same-task"})

    def test_reuse_oracle_matches_excluded_claim(self):
        r = ResidualEvidence("e1", frozenset({"narrow"}), frozenset({"narrow"}), frozenset(), frozenset({"same-task"}))
        self.assert_reuse_matches(r, "narrow", {"same-task"})

    def test_reuse_oracle_matches_boundary_mutation(self):
        r = ResidualEvidence("e1", frozenset({"narrow"}), frozenset(), frozenset(), frozenset({"same-task"}))
        self.assert_reuse_matches(r, "narrow", {"same-task", "new-population"})

    def test_reuse_oracle_matches_contamination_mutation(self):
        r = ResidualEvidence("e1", frozenset({"narrow"}), frozenset(), frozenset({"annotation-bias"}), frozenset({"same-task", "annotation-bias"}))
        self.assert_reuse_matches(r, "narrow", {"same-task", "annotation-bias"})


if __name__ == "__main__":
    unittest.main()
