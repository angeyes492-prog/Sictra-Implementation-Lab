"""Bounded continuous execution from durable Block 1 dossiers to human review.

This worker never acquires a source, invents a target profile, publishes, or
delivers.  Once a caller supplies an explicit precision-plan resolver, it can
pick up eligible durable dossiers from the configured Block 1 pipeline and
advance each independently through the signed Block 2 and Block 3 runtimes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import time
from typing import Callable

from sictra_block1.operator_pipeline import OperatorPipelineViolation, load_operator_pipeline
from sictra_block3_precision.pipeline import PrecisionInput

from .producer_adapters import (
    AdaptivePlanningPolicyBundle,
    Block1DossierPackageAdapter,
    SupervisedFederatedRunner,
)
from .runtime import FederatedContractError


class AutonomyViolation(ValueError):
    """The bounded autonomous cycle cannot safely progress."""


@dataclass(frozen=True, slots=True)
class AutonomousCasePlan:
    """A configured target mapping, not an inferred person or permission."""

    precision_request: PrecisionInput
    adaptive_planning: AdaptivePlanningPolicyBundle | Callable[[str], AdaptivePlanningPolicyBundle]


@dataclass(frozen=True, slots=True)
class AutonomyOutcome:
    dossier_id: str
    case_id: str | None
    state: str
    reason: str | None = None


PlanResolver = Callable[[dict, int], AutonomousCasePlan | None]


class SupervisedAutonomyWorker:
    """Poll durable dossiers and stop every admissible case at human review.

    The resolver is deliberately injected.  Mapping a dossier to an account or
    person is business semantics owned outside this worker; an absent or broken
    mapping records ``WAITING_FOR_PLAN`` and never invokes Block 2 or Block 3.
    """

    def __init__(self, *, pipeline, dossier_adapter: Block1DossierPackageAdapter,
                 runner: SupervisedFederatedRunner, resolve_plan: PlanResolver,
                 clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)):
        if not callable(resolve_plan) or not callable(clock):
            raise AutonomyViolation("AUTONOMY_CONFIGURATION_INVALID")
        self.pipeline = pipeline
        self.dossier_adapter = dossier_adapter
        self.runner = runner
        self.resolve_plan = resolve_plan
        self.clock = clock
        self._cursor = 0

    def _now(self) -> datetime:
        value = self.clock()
        if not isinstance(value, datetime) or value.tzinfo is None:
            raise AutonomyViolation("AUTONOMY_CLOCK_INVALID")
        return value.astimezone(timezone.utc)

    def _eligible_dossiers(self) -> tuple[str, ...]:
        now = int(self._now().timestamp())
        try:
            pipeline = load_operator_pipeline(self.pipeline, clock=lambda: now)
        except OperatorPipelineViolation as error:
            raise AutonomyViolation("BLOCK1_PIPELINE_INTEGRITY_ERROR") from error
        return tuple(sorted(
            dossier["dossier_id"] for dossier in pipeline.dossiers.list_dossiers()
            if dossier.get("review_state") == "REQUIRES_HUMAN_INTERPRETATION"
            and dossier.get("publication_state") == "BLOCKED"
        ))

    def run_once(self, *, max_cases: int = 16) -> tuple[AutonomyOutcome, ...]:
        """Advance each eligible dossier once; exact replay remains idempotent."""
        if type(max_cases) is not int or not 1 <= max_cases <= 32:
            raise AutonomyViolation("AUTONOMY_CASE_BUDGET_INVALID")
        outcomes: list[AutonomyOutcome] = []
        eligible = self._eligible_dossiers()
        if not eligible:
            return ()
        start = self._cursor % len(eligible)
        batch = (eligible[start:] + eligible[:start])[:max_cases]
        self._cursor = (start + len(batch)) % len(eligible)
        for dossier_id in batch:
            current = self._now()
            try:
                package = self.dossier_adapter.export(dossier_id, now=current)
            except FederatedContractError as error:
                outcomes.append(AutonomyOutcome(dossier_id, None, "ABSTAINED", str(error)))
                continue
            snapshot = self.runner.store.ingest(package, now=current)
            if snapshot.state in {"HUMAN_REVIEW_REQUIRED", "RETURN_UPSTREAM", "REJECTED", "ABSTAINED"}:
                outcomes.append(AutonomyOutcome(dossier_id, snapshot.case_id, snapshot.state))
                continue
            try:
                plan = self.resolve_plan(package, int(current.timestamp()))
            except Exception:
                plan = None
            if not isinstance(plan, AutonomousCasePlan):
                outcomes.append(AutonomyOutcome(dossier_id, snapshot.case_id, "WAITING_FOR_PLAN",
                                                "PRECISION_PLAN_NOT_CONFIGURED"))
                continue
            try:
                snapshot = self.runner.execute(
                    package, precision_request=plan.precision_request,
                    adaptive_planning=plan.adaptive_planning, now=current,
                )
            except (FederatedContractError, ValueError) as error:
                snapshot = self.runner.store.invalidate(snapshot.case_id, "AUTONOMY_EXECUTION_FAILED", now=current)
                outcomes.append(AutonomyOutcome(dossier_id, snapshot.case_id, snapshot.state, type(error).__name__))
                continue
            outcomes.append(AutonomyOutcome(dossier_id, snapshot.case_id, snapshot.state))
        return tuple(outcomes)

    def watch(self, *, cycles: int = 1, interval_seconds: int = 5,
              max_cases: int = 16, sleep: Callable[[float], None] = time.sleep) -> tuple[AutonomyOutcome, ...]:
        """Bounded polling only; a service wrapper may schedule later invocations."""
        if type(cycles) is not int or not 1 <= cycles <= 120:
            raise AutonomyViolation("AUTONOMY_CYCLE_BUDGET_INVALID")
        if type(interval_seconds) is not int or not 1 <= interval_seconds <= 60:
            raise AutonomyViolation("AUTONOMY_INTERVAL_INVALID")
        results: list[AutonomyOutcome] = []
        for cycle in range(cycles):
            results.extend(self.run_once(max_cases=max_cases))
            if cycle + 1 < cycles:
                sleep(interval_seconds)
        return tuple(results)
