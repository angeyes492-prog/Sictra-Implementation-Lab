import unittest

from sictra.block2_e01_validity import (
    ClaimValidityInput,
    ResidualEvidence,
    evaluate_claim_validity,
    residual_reusable_for_claim,
)


class ClaimValidityEnvelopeTests(unittest.TestCase):
    def test_supported_when_all_required_conditions_observed(self):
        item = ClaimValidityInput("narrow", frozenset({"same-task"}), frozenset({"same-task"}), frozenset(), frozenset({"e1"}))
        decision = evaluate_claim_validity(item)
        self.assertEqual(decision.status, "SUPPORTED")
        self.assertEqual(decision.admissible_evidence_ids, ("e1",))

    def test_missing_required_condition_blocks_claim(self):
        item = ClaimValidityInput("broad", frozenset({"same-task", "blinded"}), frozenset({"same-task"}), frozenset(), frozenset({"e1"}))
        decision = evaluate_claim_validity(item)
        self.assertEqual(decision.status, "BLOCKED")
        self.assertEqual(decision.missing_conditions, ("blinded",))

    def test_failed_required_condition_blocks_claim(self):
        item = ClaimValidityInput("broad", frozenset({"same-task", "blinded"}), frozenset({"same-task", "blinded"}), frozenset({"blinded"}), frozenset({"e1"}))
        decision = evaluate_claim_validity(item)
        self.assertEqual(decision.status, "BLOCKED")
        self.assertEqual(decision.failed_conditions, ("blinded",))

    def test_blocked_broad_claim_does_not_destroy_narrow_residual(self):
        narrow = ClaimValidityInput("narrow", frozenset({"same-task"}), frozenset({"same-task"}), frozenset({"blinded"}), frozenset({"e1"}))
        broad = ClaimValidityInput("broad", frozenset({"same-task", "blinded"}), frozenset({"same-task", "blinded"}), frozenset({"blinded"}), frozenset({"e1"}))
        self.assertEqual(evaluate_claim_validity(narrow).status, "SUPPORTED")
        self.assertEqual(evaluate_claim_validity(broad).status, "BLOCKED")

    def test_residual_reuse_requires_explicit_claim_allowance(self):
        r = ResidualEvidence("e1", frozenset({"narrow"}), frozenset({"broad"}), frozenset(), frozenset({"same-task"}))
        self.assertTrue(residual_reusable_for_claim(r, "narrow", {"same-task"}))
        self.assertFalse(residual_reusable_for_claim(r, "broad", {"same-task"}))

    def test_residual_contamination_blocks_reuse(self):
        r = ResidualEvidence("e1", frozenset({"narrow"}), frozenset(), frozenset({"annotation-bias"}), frozenset({"same-task", "annotation-bias"}))
        self.assertFalse(residual_reusable_for_claim(r, "narrow", {"same-task", "annotation-bias"}))

    def test_reuse_outside_boundary_is_blocked(self):
        r = ResidualEvidence("e1", frozenset({"narrow"}), frozenset(), frozenset(), frozenset({"same-task"}))
        self.assertFalse(residual_reusable_for_claim(r, "narrow", {"same-task", "new-population"}))

    def test_excluded_claim_wins_even_if_also_listed_valid(self):
        r = ResidualEvidence("e1", frozenset({"narrow"}), frozenset({"narrow"}), frozenset(), frozenset({"same-task"}))
        self.assertFalse(residual_reusable_for_claim(r, "narrow", {"same-task"}))


if __name__ == "__main__":
    unittest.main()
