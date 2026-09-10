from __future__ import annotations

from typing import Iterable

from sictra.block2_e01_claims import ClaimEvidence, ClaimRelationship


def expected_composition_status(
    claim_a: str,
    claim_b: str,
    evidence: Iterable[ClaimEvidence],
    relationship: ClaimRelationship | None,
) -> tuple[str, str, tuple[str, ...]]:
    """Independent declarative oracle for E01 claim composition.

    This intentionally does not call evaluate_claim_composition or reuse its
    helper functions. It expresses acceptance as a set predicate.
    """
    items = tuple(evidence)
    has_a = any(x.claim_id == claim_a and x.admissible for x in items)
    has_b = any(x.claim_id == claim_b and x.admissible for x in items)
    if not (has_a and has_b):
        return "BLOCKED", "CLAIM_SUPPORT_INCOMPLETE", ()

    if relationship is None:
        return "BLOCKED", "RELATIONSHIP_UNSUPPORTED", ()

    if frozenset((relationship.claim_a, relationship.claim_b)) != frozenset((claim_a, claim_b)):
        return "BLOCKED", "RELATIONSHIP_IDENTITY_MISMATCH", ()

    referenced = tuple(
        x for x in items
        if x.evidence_id in relationship.support_evidence_ids and x.admissible
    )
    if not referenced:
        return "BLOCKED", "RELATIONSHIP_EVIDENCE_MISSING", ()

    good = tuple(sorted(
        x.evidence_id for x in referenced
        if relationship.shared_conditions <= x.valid_scope
        and relationship.shared_conditions <= x.observed_conditions
        and relationship.shared_conditions.isdisjoint(x.failed_conditions)
    ))
    if not good:
        return "BLOCKED", "SHARED_CONDITIONS_UNSUPPORTED", ()

    return "SUPPORTED", "RELATIONSHIP_EVIDENCE_ADMISSIBLE", good
