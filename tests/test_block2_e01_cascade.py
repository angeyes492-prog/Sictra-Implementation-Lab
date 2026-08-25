import unittest

from sictra.block2_e01_cascade import Failure, earliest_sufficient_failure


def f(fid, layer, order, claims=("C",), preds=(), sufficient=True):
    return Failure(fid, layer, order, frozenset(claims), frozenset(preds), sufficient)


class CascadeContainmentTests(unittest.TestCase):
    def test_chronological_first_is_not_automatically_causal_first(self):
        failures = [
            f("symptom", "visual", 1, sufficient=False),
            f("semantic", "semantic", 2, sufficient=True),
        ]
        d = earliest_sufficient_failure("C", failures)
        self.assertEqual(d.earliest_sufficient_failure_id, "semantic")
        self.assertEqual(d.residual_failure_ids, ("symptom",))

    def test_failure_for_other_claim_cannot_block_target_claim(self):
        failures = [f("other", "task", 1, claims=("OTHER",)), f("target", "semantic", 2)]
        self.assertEqual(earliest_sufficient_failure("C", failures).earliest_sufficient_failure_id, "target")

    def test_missing_required_predecessor_blocks_candidate(self):
        failures = [f("downstream", "encoding", 1, preds=("task",))]
        self.assertEqual(earliest_sufficient_failure("C", failures).status, "NO_SUFFICIENT_FAILURE")

    def test_predecessor_must_apply_to_same_claim(self):
        failures = [f("task", "task", 2, claims=("OTHER",)), f("encoding", "encoding", 1, preds=("task",))]
        self.assertEqual(earliest_sufficient_failure("C", failures).status, "NO_SUFFICIENT_FAILURE")

    def test_shallower_causal_failure_wins_over_earlier_downstream_observation(self):
        failures = [
            f("task", "task", 5),
            f("semantic", "semantic", 2, preds=("task",)),
            f("visual", "visual", 1, preds=("semantic",)),
        ]
        d = earliest_sufficient_failure("C", failures)
        self.assertEqual(d.earliest_sufficient_failure_id, "task")

    def test_reverse_order_cascade_contains_required_chain_only(self):
        failures = [
            f("visual", "visual", 1, preds=("semantic",)),
            f("semantic", "semantic", 2, preds=("task",)),
            f("task", "task", 3, sufficient=False),
            f("unrelated", "annotation", 0, claims=("OTHER",)),
        ]
        d = earliest_sufficient_failure("C", failures)
        self.assertEqual(d.earliest_sufficient_failure_id, "semantic")
        self.assertEqual(set(d.contained_failure_ids), {"semantic", "task"})
        self.assertIn("visual", d.residual_failure_ids)
        self.assertIn("unrelated", d.residual_failure_ids)

    def test_no_sufficient_failure_preserves_all_as_residual(self):
        failures = [f("a", "task", 1, sufficient=False), f("b", "semantic", 2, sufficient=False)]
        d = earliest_sufficient_failure("C", failures)
        self.assertEqual(d.residual_failure_ids, ("a", "b"))

    def test_tie_breaker_is_deterministic_without_changing_claim_scope(self):
        failures = [f("b", "task", 2), f("a", "semantic", 2)]
        d = earliest_sufficient_failure("C", failures)
        self.assertEqual(d.earliest_sufficient_failure_id, "a")


if __name__ == "__main__":
    unittest.main()
