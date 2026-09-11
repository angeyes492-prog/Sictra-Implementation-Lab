import unittest

from sictra.block2_e01_cascade import Failure, earliest_sufficient_failure
from sictra.block2_e01_cascade_oracle import expected_earliest_failure


def f(fid, layer, order, claims=("C",), preds=(), sufficient=True):
    return Failure(fid, layer, order, frozenset(claims), frozenset(preds), sufficient)


def impl_signature(claim, failures):
    d = earliest_sufficient_failure(claim, failures)
    return d.earliest_sufficient_failure_id, d.contained_failure_ids, d.residual_failure_ids, d.status


class CascadeOracleDifferentialTests(unittest.TestCase):
    def assert_matches(self, failures, claim="C"):
        self.assertEqual(impl_signature(claim, failures), expected_earliest_failure(claim, failures))

    def test_reverse_order_cascade(self):
        self.assert_matches([
            f("visual", "visual", 1, preds=("semantic",)),
            f("semantic", "semantic", 2, preds=("task",)),
            f("task", "task", 3, sufficient=False),
        ])

    def test_multi_confounder_claim_scope(self):
        self.assert_matches([
            f("task-c", "task", 4),
            f("semantic-c", "semantic", 2, preds=("task-c",)),
            f("other-first", "task", 1, claims=("OTHER",)),
            f("annotation", "annotation", 3, sufficient=False),
        ])

    def test_missing_predecessor_mutation(self):
        self.assert_matches([f("encoding", "encoding", 1, preds=("missing",))])

    def test_non_sufficient_symptom_before_cause(self):
        self.assert_matches([f("symptom", "visual", 1, sufficient=False), f("cause", "semantic", 5)])

    def test_multiple_roots_deterministic_tie(self):
        self.assert_matches([f("b", "task", 2), f("a", "semantic", 2), f("c", "annotation", 3)])

    def test_other_claim_predecessor_does_not_satisfy_target(self):
        self.assert_matches([f("p", "task", 1, claims=("OTHER",)), f("x", "encoding", 2, preds=("p",))])

    def test_no_sufficient_failures(self):
        self.assert_matches([f("a", "task", 1, sufficient=False), f("b", "semantic", 2, sufficient=False)])

    def test_containment_excludes_unrelated_residuals(self):
        failures = [f("root", "task", 3, sufficient=False), f("child", "semantic", 2, preds=("root",)), f("residual", "visual", 1, sufficient=False)]
        self.assert_matches(failures)
        self.assertIn("residual", impl_signature("C", failures)[2])


if __name__ == "__main__":
    unittest.main()
