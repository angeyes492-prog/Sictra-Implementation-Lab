import unittest

from sictra.block2_e01_claims import (
    ClaimEvidence,
    ClaimRelationship,
    evaluate_claim_composition,
)


def ev(eid, claim, scope=("same-task",), observed=("same-task",), failed=(), root="r1", admissible=True):
    return ClaimEvidence(
        evidence_id=eid,
        claim_id=claim,
        valid_scope=frozenset(scope),
        observed_conditions=frozenset(observed),
        failed_conditions=frozenset(failed),
        provenance_root=root,
        admissible=admissible,
    )


class ClaimCompositionBoundaryTests(unittest.TestCase):
    def test_independently_supported_claims_do_not_imply_relationship(self):
        result = evaluate_claim_composition("A", "B", [ev("a1", "A"), ev("b1", "B")], None)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.reason, "RELATIONSHIP_UNSUPPORTED")
        self.assertEqual(result.residual_evidence_ids, ("a1", "b1"))

    def test_explicit_relationship_with_shared_condition_support_can_pass(self):
        evidence = [
            ev("a1", "A"),
            ev("b1", "B"),
            ev("rel1", "REL", scope=("same-task", "blinded"), observed=("same-task", "blinded")),
        ]
        relation = ClaimRelationship("A", "B", frozenset({"same-task", "blinded"}), frozenset({"rel1"}))
        result = evaluate_claim_composition("A", "B", evidence, relation)
        self.assertEqual(result.status, "SUPPORTED")
        self.assertEqual(result.admissible_evidence_ids, ("rel1",))
        self.assertEqual(result.residual_evidence_ids, ("a1", "b1"))

    def test_failed_shared_condition_blocks_composition(self):
        evidence = [ev("a1", "A"), ev("b1", "B"), ev("rel1", "REL", failed=("blinded",), scope=("same-task", "blinded"), observed=("same-task", "blinded"))]
        relation = ClaimRelationship("A", "B", frozenset({"same-task", "blinded"}), frozenset({"rel1"}))
        result = evaluate_claim_composition("A", "B", evidence, relation)
        self.assertEqual(result.reason, "SHARED_CONDITIONS_UNSUPPORTED")

    def test_scope_leakage_blocks_composition(self):
        evidence = [ev("a1", "A"), ev("b1", "B"), ev("rel1", "REL", scope=("same-task",), observed=("same-task", "blinded"))]
        relation = ClaimRelationship("A", "B", frozenset({"same-task", "blinded"}), frozenset({"rel1"}))
        self.assertEqual(evaluate_claim_composition("A", "B", evidence, relation).status, "BLOCKED")

    def test_unobserved_condition_blocks_composition(self):
        evidence = [ev("a1", "A"), ev("b1", "B"), ev("rel1", "REL", scope=("same-task", "blinded"), observed=("same-task",))]
        relation = ClaimRelationship("A", "B", frozenset({"same-task", "blinded"}), frozenset({"rel1"}))
        self.assertEqual(evaluate_claim_composition("A", "B", evidence, relation).status, "BLOCKED")

    def test_nonadmissible_relationship_evidence_blocks(self):
        evidence = [ev("a1", "A"), ev("b1", "B"), ev("rel1", "REL", admissible=False)]
        relation = ClaimRelationship("A", "B", frozenset({"same-task"}), frozenset({"rel1"}))
        self.assertEqual(evaluate_claim_composition("A", "B", evidence, relation).reason, "RELATIONSHIP_EVIDENCE_MISSING")

    def test_relationship_identity_mismatch_blocks(self):
        evidence = [ev("a1", "A"), ev("b1", "B"), ev("rel1", "REL")]
        relation = ClaimRelationship("A", "C", frozenset({"same-task"}), frozenset({"rel1"}))
        self.assertEqual(evaluate_claim_composition("A", "B", evidence, relation).reason, "RELATIONSHIP_IDENTITY_MISMATCH")

    def test_missing_claim_support_blocks_even_with_relationship_record(self):
        evidence = [ev("a1", "A"), ev("rel1", "REL")]
        relation = ClaimRelationship("A", "B", frozenset({"same-task"}), frozenset({"rel1"}))
        self.assertEqual(evaluate_claim_composition("A", "B", evidence, relation).reason, "CLAIM_SUPPORT_INCOMPLETE")


if __name__ == "__main__":
    unittest.main()
