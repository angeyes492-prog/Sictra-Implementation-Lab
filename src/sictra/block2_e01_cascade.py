from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Iterable


@dataclass(frozen=True)
class Failure:
    failure_id: str
    layer: str
    observed_order: int
    invalidates_claims: FrozenSet[str]
    required_predecessors: FrozenSet[str]
    causally_sufficient: bool


@dataclass(frozen=True)
class CascadeDecision:
    claim_id: str
    earliest_sufficient_failure_id: str | None
    contained_failure_ids: tuple[str, ...]
    residual_failure_ids: tuple[str, ...]
    status: str


def earliest_sufficient_failure(claim_id: str, failures: Iterable[Failure]) -> CascadeDecision:
    """Select claim-relative causal failure, not merely chronological first failure.

    A candidate must invalidate the target claim, be marked causally sufficient,
    and have every required predecessor present as a failure that also applies to
    the same claim. Among eligible candidates, causal depth is primary and
    observed order is only a deterministic tie-breaker.
    """
    items = tuple(failures)
    by_id = {f.failure_id: f for f in items}

    def applicable(fid: str) -> bool:
        p = by_id.get(fid)
        return p is not None and claim_id in p.invalidates_claims

    eligible = []
    for f in items:
        if claim_id not in f.invalidates_claims or not f.causally_sufficient:
            continue
        if not all(applicable(pid) for pid in f.required_predecessors):
            continue
        eligible.append(f)

    if not eligible:
        return CascadeDecision(claim_id, None, (), tuple(sorted(f.failure_id for f in items)), "NO_SUFFICIENT_FAILURE")

    def causal_depth(f: Failure, seen: frozenset[str] = frozenset()) -> int:
        if f.failure_id in seen:
            return 10**6
        preds = [by_id[p] for p in f.required_predecessors if p in by_id and applicable(p)]
        if not preds:
            return 0
        return 1 + max(causal_depth(p, seen | {f.failure_id}) for p in preds)

    chosen = min(eligible, key=lambda f: (causal_depth(f), f.observed_order, f.failure_id))

    contained = {chosen.failure_id}
    stack = list(chosen.required_predecessors)
    while stack:
        fid = stack.pop()
        if fid in contained or not applicable(fid):
            continue
        contained.add(fid)
        stack.extend(by_id[fid].required_predecessors)

    residual = tuple(sorted(f.failure_id for f in items if f.failure_id not in contained))
    return CascadeDecision(claim_id, chosen.failure_id, tuple(sorted(contained)), residual, "CLAIM_BLOCKED")
