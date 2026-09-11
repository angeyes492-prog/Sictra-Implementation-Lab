from __future__ import annotations

from typing import Iterable

from sictra.block2_e01_validity import ClaimValidityInput, ResidualEvidence


def expected_claim_validity(item: ClaimValidityInput) -> tuple[str, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    missing = tuple(sorted(c for c in item.required_conditions if c not in item.observed_conditions))
    failed = tuple(sorted(c for c in item.required_conditions if c in item.failed_conditions))
    status = "SUPPORTED" if not missing and not failed else "BLOCKED"
    admissible = tuple(sorted(item.evidence_ids)) if status == "SUPPORTED" else ()
    return status, missing, failed, admissible


def expected_residual_reuse(
    residual: ResidualEvidence,
    target_claim: str,
    target_conditions: Iterable[str],
) -> bool:
    requested = frozenset(target_conditions)
    return (
        target_claim in residual.valid_for_claims
        and target_claim not in residual.excluded_claims
        and all(c in residual.reuse_boundary for c in requested)
        and all(c not in residual.contaminated_conditions for c in requested)
    )
