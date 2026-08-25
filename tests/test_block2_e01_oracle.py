import unittest

from sictra.block2_e01_claims import (
    ClaimEvidence,
    ClaimRelationship,
    evaluate_claim_composition,
)
from sictra.block2_e01_oracle import expected_composition_status


def ev(eid, claim, scope=("same-task",), observed=("same-task",), failed=(), admissible=True):
    return ClaimEvidence(
        evidence_id=eid,
        claim_id=claim,
        valid_scope=frozenset(scope),
        observed_conditions=frozenset(observed),
        failed_conditions=frozenset(failed),
        provenance_root=f"root:{eid}",
        admissible=admissible,
    )


def impl_signature(a, b, evidence, relationship):
    r = evaluate_claim_composition(a, b, evidence, relationship)
    return r.status, r.reason, r.admissible_evidence_ids


class ClaimCompositionOracleTests(unittest.TestCase):
    def assert_matches(self, a, b, evidence, relationship):
        self.assertEqual(
            impl_signature(a, b, evidence, relationship),
            expected_composition_status(a, b, evidence, relationship),
        )

    def test_oracle_matches_unsupported_relationship(self):
        self.assert_matches("A", "B", [ev("a1", "A"), ev("b1", "B")], None)

    def test_oracle_matches_supported_relationship(self):
        xs = [ev("a1", "A"), ev("b1", "B"), ev("r1", "REL", ("same-task", "blind"), ("same-task", "blind"))]
        rel = ClaimRelationship("A", "B", frozenset({"same-task", "blind"}), frozenset({"r1"}))
        self.assert_matches("A", "B", xs, rel)

    def test_oracle_matches_failed_condition_mutation(self):
        xs = [ev("a1", "A"), ev("b1", "B"), ev("r1", "REL", ("same-task", "blind"), ("same-task", "blind"), ("blind",))]
        rel = ClaimRelationship("A", "B", frozenset({"same-task", "blind"}), frozenset({"r1"}))
        self.assert_matches("A", "B", xs, rel)

    def test_oracle_matches_scope_mutation(self):
        xs = [ev("a1", "A"), ev("b1", "B"), ev("r1", "REL", ("same-task",), ("same-task", "blind"))]
        rel = ClaimRelationship("A", "B", frozenset({"same-task", "blind"}), frozenset({"r1"}))
        self.assert_matches("A", "B", xs, rel)

    def test_oracle_matches_observation_mutation(self):
        xs = [ev("a1", "A"), ev("b1", "B"), ev("r1", "REL", ("same-task", "blind"), ("same-task",))]
        rel = ClaimRelationship("A", "B", frozenset({"same-task", "blind"}), frozenset({"r1"}))
        self.assert_matches("A", "B", xs, rel)

    def test_oracle_matches_admissibility_mutation(self):
        xs = [ev("a1", "A"), ev("b1", "B"), ev("r1", "REL", admissible=False)]
        rel = ClaimRelationship("A", "B", frozenset({"same-task"}), frozenset({"r1"}))
        self.assert_matches("A", "B", xs, rel)

    def test_oracle_matches_identity_mutation(self):
        xs = [ev("a1", "A"), ev("b1", "B"), ev("r1", "REL")]
        rel = ClaimRelationship("A", "C", frozenset({"same-task"}), frozenset({"r1"}))
        self.assert_matches("A", "B", xs, rel)

    def test_oracle_matches_multi_evidence_partial_survival(self):
        xs = [
            ev("a1", "A"), ev("b1", "B"),
            ev("r-good", "REL", ("same-task", "blind"), ("same-task", "blind")),
            ev("r-bad", "REL", ("same-task", "blind"), ("same-task", "blind"), ("blind",)),
        ]
        rel = ClaimRelationship("A", "B", frozenset({"same-task", "blind"}), frozenset({"r-good", "r-bad"}))
        self.assert_matches("A", "B", xs, rel)
        self.assertEqual(impl_signature("A", "B", xs, rel)[2], ("r-good",))


if __name__ == "__main__":
    unittest.main()
