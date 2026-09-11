from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Iterable


@dataclass(frozen=True)
class ClaimEvidence:
    evidence_id: str
    claim_id: str
    valid_scope: FrozenSet[str]
    observed_conditions: FrozenSet[str]
    failed_conditions: FrozenSet[str]
    provenance_root: str
    admissible: bool = True


@dataclass(frozen=True)
class ClaimRelationship:
    claim_a: str
    claim_b: str
    shared_conditions: FrozenSet[str]
    support_evidence_ids: FrozenSet[str]


@dataclass(frozen=True)
class CompositionDecision:
    status: str
    reason: str
    admissible_evidence_ids: tuple[str, ...]
    residual_evidence_ids: tuple[str, ...]


def _claim_evidence(evidence: Iterable[ClaimEvidence], claim_id: str) -> tuple[ClaimEvidence, ...]:
    return tuple(e for e in evidence if e.claim_id == claim_id and e.admissible)


def evaluate_claim_composition(
    claim_a: str,
    claim_b: str,
    evidence: Iterable[ClaimEvidence],
    relationship: ClaimRelationship | None,
) -> CompositionDecision:
    """Prevent valid claim-scoped evidence from being silently recombined.

    Evidence that independently supports A and B is not sufficient to support A+B.
    Composition is allowed only when an explicit relationship record exists and
    its evidence is admissible for the shared conditions claimed by the relation.
    """
    items = tuple(evidence)
    a_items = _claim_evidence(items, claim_a)
    b_items = _claim_evidence(items, claim_b)
    independent = tuple(sorted({e.evidence_id for e in (*a_items, *b_items)}))

    if not a_items or not b_items:
        return CompositionDecision("BLOCKED", "CLAIM_SUPPORT_INCOMPLETE", (), independent)

    if relationship is None:
        return CompositionDecision("BLOCKED", "RELATIONSHIP_UNSUPPORTED", (), independent)

    if {relationship.claim_a, relationship.claim_b} != {claim_a, claim_b}:
        return CompositionDecision("BLOCKED", "RELATIONSHIP_IDENTITY_MISMATCH", (), independent)

    support = tuple(e for e in items if e.evidence_id in relationship.support_evidence_ids and e.admissible)
    if not support:
        return CompositionDecision("BLOCKED", "RELATIONSHIP_EVIDENCE_MISSING", (), independent)

    valid_ids: list[str] = []
    for e in support:
        if not relationship.shared_conditions.issubset(e.valid_scope):
            continue
        if not relationship.shared_conditions.issubset(e.observed_conditions):
            continue
        if relationship.shared_conditions.intersection(e.failed_conditions):
            continue
        valid_ids.append(e.evidence_id)

    if not valid_ids:
        return CompositionDecision("BLOCKED", "SHARED_CONDITIONS_UNSUPPORTED", (), independent)

    admitted = tuple(sorted(set(valid_ids)))
    residual = tuple(sorted(set(independent) - set(admitted)))
    return CompositionDecision("SUPPORTED", "RELATIONSHIP_EVIDENCE_ADMISSIBLE", admitted, residual)
