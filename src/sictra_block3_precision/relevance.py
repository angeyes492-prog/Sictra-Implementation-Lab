"""Explainable Relevance Gate for the bounded A∴ runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .contracts import EngineAssessment, PrecisionContractViolation, fingerprint, require_text
from .precision_context import PrecisionContextPack


DimensionState = Literal["SUPPORTED", "PARTIAL", "ABSENT", "CONTRADICTED", "INAPPLICABLE"]
RelevanceLevel = Literal["HIGH", "MEDIUM", "LOW", "RETURN_UPSTREAM"]


@dataclass(frozen=True, slots=True)
class RelevancePolicy:
    policy_id: str
    authority_reference: str
    minimum_medium_dimensions: int = 2
    medium_ceiling_cap: int = 2

    def __post_init__(self) -> None:
        require_text("policy_id", self.policy_id)
        require_text("authority_reference", self.authority_reference)
        if not isinstance(self.minimum_medium_dimensions, int) or not 1 <= self.minimum_medium_dimensions <= 4:
            raise PrecisionContractViolation("minimum_medium_dimensions must be from 1 to 4")
        if not isinstance(self.medium_ceiling_cap, int) or not 0 <= self.medium_ceiling_cap <= 5:
            raise PrecisionContractViolation("medium ceiling cap must be from 0 to 5")


@dataclass(frozen=True, slots=True)
class RelevanceDimension:
    dimension: str
    state: DimensionState
    evidence_ids: tuple[str, ...]
    root_provenance_ids: tuple[str, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RelevanceDecision:
    decision_id: str
    context_snapshot_id: str
    level: RelevanceLevel
    dimensions: tuple[RelevanceDimension, ...]
    ceiling_cap: int
    policy_id: str
    reasons: tuple[str, ...]
    restrictions: tuple[str, ...]

    @property
    def output_fingerprint(self) -> str:
        return fingerprint(self)


@dataclass(frozen=True, slots=True)
class RelevanceResult:
    assessment: EngineAssessment
    decision: RelevanceDecision


class RelevanceGate:
    name = "RELEVANCE_GATE"
    _CONTEXT_DIMENSIONS = ("GLOBAL", "INDUSTRY", "ACCOUNT", "ROLE", "MOMENT")

    def evaluate(
        self, *, pack: PrecisionContextPack, policy: RelevancePolicy, now: int,
    ) -> RelevanceResult:
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise PrecisionContractViolation("now must be a non-negative integer")
        stage_by_scope = {stage.scope: stage for stage in pack.context.stages}
        dimensions: list[RelevanceDimension] = []
        for name in self._CONTEXT_DIMENSIONS:
            stage = stage_by_scope.get(name)
            if stage is None:
                dimensions.append(RelevanceDimension(
                    name, "ABSENT", (), (), (f"{name}_MISSING",),
                ))
            else:
                state: DimensionState = "SUPPORTED" if stage.fact_statements else "PARTIAL"
                dimensions.append(RelevanceDimension(
                    name, state, stage.evidence_ids, stage.root_provenance_ids,
                    () if state == "SUPPORTED" else (f"{name}_HYPOTHESIS_ONLY",),
                ))
        behavioral_evidence = tuple(sorted({
            evidence_id
            for signal in pack.behavioral.signals
            for evidence_id in signal.evidence_ids
        }))
        high_information = any(
            signal.high_information_event_count > 0 for signal in pack.behavioral.signals
        )
        if high_information:
            interest_state: DimensionState = "SUPPORTED"
            interest_reasons: tuple[str, ...] = ("OBSERVED_INTERACTION_NOT_INTENT",)
        elif pack.behavioral.signals:
            interest_state = "PARTIAL"
            interest_reasons = ("LOW_INFORMATION_INTERACTION_ONLY",)
        else:
            interest_state = "ABSENT"
            interest_reasons = ("NO_OBSERVED_INTEREST_EVIDENCE",)
        dimensions.append(RelevanceDimension(
            "OBSERVED_INTEREST", interest_state, behavioral_evidence, (), interest_reasons,
        ))

        reasons: list[str] = []
        blocker = False
        if not pack.current_at(now):
            blocker = True
            reasons.append("CONTEXT_PACK_NOT_CURRENT")
        if pack.foundation_disposition == "CONTRADICTED":
            blocker = True
            reasons.append("FOUNDATION_CONTRADICTED")
        if pack.person.contradictions or pack.context.contradicted_claim_keys:
            blocker = True
            reasons.append("ESSENTIAL_CONTRADICTION_PRESERVED")
        global_dimension = next(item for item in dimensions if item.dimension == "GLOBAL")
        if global_dimension.state not in {"SUPPORTED", "PARTIAL"}:
            blocker = True
            reasons.append("GLOBAL_RELEVANCE_NOT_ESTABLISHED")

        core = [
            item for item in dimensions
            if item.dimension in {"INDUSTRY", "ACCOUNT", "ROLE", "MOMENT"}
        ]
        supported_count = sum(item.state == "SUPPORTED" for item in core)
        core_roots = [
            root for item in core if item.state == "SUPPORTED"
            for root in item.root_provenance_ids
        ]
        if core_roots and len(set(core_roots)) < len(core_roots):
            reasons.append("CORRELATED_RELEVANCE_ROOTS_PRESERVED")
        if blocker:
            level: RelevanceLevel = "RETURN_UPSTREAM"
            ceiling_cap = 0
            assessment_disposition = "RETURN_UPSTREAM"
        elif supported_count == len(core):
            level = "HIGH"
            ceiling_cap = pack.ceiling.effective_level
            assessment_disposition = "ACCEPTED"
            reasons.append("COMPLETE_RELEVANCE_CHAIN")
        elif supported_count >= policy.minimum_medium_dimensions:
            level = "MEDIUM"
            ceiling_cap = min(pack.ceiling.effective_level, policy.medium_ceiling_cap)
            assessment_disposition = "PARTIAL"
            reasons.append("PARTIAL_RELEVANCE_CHAIN")
        else:
            level = "LOW"
            ceiling_cap = 0
            assessment_disposition = "ACCEPTED"
            reasons.append("INSUFFICIENT_RELEVANCE_CHAIN")
        if interest_state == "ABSENT":
            reasons.append("BEHAVIORAL_PERSONALIZATION_NOT_AVAILABLE")
        decision = RelevanceDecision(
            decision_id=f"{pack.context_snapshot_id}:relevance:{policy.policy_id}",
            context_snapshot_id=pack.context_snapshot_id,
            level=level,
            dimensions=tuple(dimensions),
            ceiling_cap=ceiling_cap,
            policy_id=policy.policy_id,
            reasons=tuple(sorted(set(reasons))),
            restrictions=(
                "EXPLAINABLE_LATTICE_NOT_OPAQUE_SCORE",
                "ABSENT_INTEREST_NOT_DISINTEREST",
                "RELEVANCE_NOT_DELIVERY_PERMISSION",
            ),
        )
        evidence_ids = tuple(sorted({
            evidence_id for dimension in dimensions for evidence_id in dimension.evidence_ids
        }))
        return RelevanceResult(
            EngineAssessment(
                self.name, assessment_disposition, decision.reasons,
                evidence_ids, decision.output_fingerprint,
            ),
            decision,
        )

