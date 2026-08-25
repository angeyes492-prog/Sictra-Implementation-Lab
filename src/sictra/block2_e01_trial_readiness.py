"""Block 2 E01 clean external-trial readiness boundary.

A trial may only become admissible perception evidence when observer independence,
task non-leakage and fixture equivalence survive explicit checks. This module does
not claim that a human trial occurred; it prevents contaminated fixtures from
being promoted as empirical evidence.
"""
from dataclasses import dataclass
from typing import FrozenSet, Mapping

FIXTURE_DIMENSIONS = frozenset({
    "content", "task", "labels", "scale", "uncertainty", "annotation",
    "context", "order", "attention", "implementation_burden",
})


@dataclass(frozen=True)
class ObserverIndependenceProfile:
    observer_id: str
    observer_role: str
    prior_exposure: bool = False
    thesis_exposure: bool = False
    examples_seen: bool = False
    evaluation_context_disclosed: bool = False


@dataclass(frozen=True)
class TaskLeakageRecord:
    wording: str
    required_context: FrozenSet[str]
    potential_cues: FrozenSet[str] = frozenset()
    version: str = "v1"


@dataclass(frozen=True)
class TrialFixture:
    fixture_id: str
    parity: Mapping[str, bool]
    hidden_semantic_changes: FrozenSet[str] = frozenset()
    randomized_order: bool = False
    familiarity_balanced: bool = False


@dataclass(frozen=True)
class TrialReadinessAssessment:
    ready: bool
    reasons: tuple[str, ...]


def assess_trial_readiness(
    observer: ObserverIndependenceProfile,
    task: TaskLeakageRecord,
    fixture: TrialFixture,
) -> TrialReadinessAssessment:
    reasons: list[str] = []
    if not observer.observer_id or not observer.observer_role:
        reasons.append("OBSERVER_IDENTITY_INCOMPLETE")
    if observer.prior_exposure or observer.thesis_exposure or observer.examples_seen:
        reasons.append("OBSERVER_EXPOSURE_CONTAMINATION")
    if observer.evaluation_context_disclosed:
        reasons.append("EVALUATION_CONTEXT_LEAKAGE")
    if not task.wording or not task.version:
        reasons.append("TASK_IDENTITY_INCOMPLETE")
    if task.potential_cues:
        reasons.append("TASK_WORDING_LEAKAGE")
    missing_dimensions = FIXTURE_DIMENSIONS - frozenset(fixture.parity)
    if missing_dimensions:
        reasons.append("FIXTURE_DIMENSIONS_MISSING")
    elif not all(fixture.parity[d] for d in FIXTURE_DIMENSIONS):
        reasons.append("FIXTURE_ASYMMETRY")
    if fixture.hidden_semantic_changes:
        reasons.append("HIDDEN_SEMANTIC_CHANGE")
    if not fixture.randomized_order:
        reasons.append("ORDER_EFFECT_UNCONTROLLED")
    if not fixture.familiarity_balanced:
        reasons.append("FAMILIARITY_UNCONTROLLED")
    return TrialReadinessAssessment(not reasons, tuple(reasons))
