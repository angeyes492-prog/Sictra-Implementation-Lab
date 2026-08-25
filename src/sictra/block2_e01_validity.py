from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Iterable


@dataclass(frozen=True)
class ClaimValidityInput:
    claim_id: str
    required_conditions: FrozenSet[str]
    observed_conditions: FrozenSet[str]
    failed_conditions: FrozenSet[str]
    evidence_ids: FrozenSet[str]


@dataclass(frozen=True)
class ResidualEvidence:
    evidence_id: str
    valid_for_claims: FrozenSet[str]
    excluded_claims: FrozenSet[str]
    contaminated_conditions: FrozenSet[str]
    reuse_boundary: FrozenSet[str]


@dataclass(frozen=True)
class ClaimValidityDecision:
    claim_id: str
    status: str
    missing_conditions: tuple[str, ...]
    failed_conditions: tuple[str, ...]
    admissible_evidence_ids: tuple[str, ...]


def evaluate_claim_validity(item: ClaimValidityInput) -> ClaimValidityDecision:
    missing = tuple(sorted(item.required_conditions - item.observed_conditions))
    failed = tuple(sorted(item.required_conditions & item.failed_conditions))
    status = "SUPPORTED" if not missing and not failed else "BLOCKED"
    admissible = tuple(sorted(item.evidence_ids)) if status == "SUPPORTED" else ()
    return ClaimValidityDecision(item.claim_id, status, missing, failed, admissible)


def residual_reusable_for_claim(
    residual: ResidualEvidence,
    target_claim: str,
    target_conditions: Iterable[str],
) -> bool:
    conditions = frozenset(target_conditions)
    if target_claim not in residual.valid_for_claims:
        return False
    if target_claim in residual.excluded_claims:
        return False
    if not conditions.issubset(residual.reuse_boundary):
        return False
    if conditions.intersection(residual.contaminated_conditions):
        return False
    return True
