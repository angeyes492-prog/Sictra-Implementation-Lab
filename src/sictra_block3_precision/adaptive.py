"""Adaptive Frontier Controller with hard constraints before marginal benefit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .contracts import EngineAssessment, PrecisionContractViolation, fingerprint, require_text
from .relevance import RelevanceDecision


AdaptiveLevel = Literal[0, 1, 2, 3]


@dataclass(frozen=True, slots=True)
class AdaptivePolicy:
    policy_id: str
    authority_reference: str
    maximum_level: int = 3
    upgrade_margin: int = 1

    def __post_init__(self) -> None:
        require_text("policy_id", self.policy_id)
        require_text("authority_reference", self.authority_reference)
        if not isinstance(self.maximum_level, int) or isinstance(self.maximum_level, bool) or not 0 <= self.maximum_level <= 3:
            raise PrecisionContractViolation("adaptive maximum level must be from 0 to 3")
        if not isinstance(self.upgrade_margin, int) or isinstance(self.upgrade_margin, bool) or self.upgrade_margin < 0:
            raise PrecisionContractViolation("adaptive upgrade margin cannot be negative")


@dataclass(frozen=True, slots=True)
class HardConstraints:
    authority_ok: bool
    privacy_ok: bool
    provenance_ok: bool
    auditability_ok: bool
    rollback_ok: bool
    slo_ok: bool

    @property
    def failed(self) -> tuple[str, ...]:
        return tuple(
            name.upper().removesuffix("_OK")
            for name, value in (
                ("authority_ok", self.authority_ok),
                ("privacy_ok", self.privacy_ok),
                ("provenance_ok", self.provenance_ok),
                ("auditability_ok", self.auditability_ok),
                ("rollback_ok", self.rollback_ok),
                ("slo_ok", self.slo_ok),
            )
            if not value
        )


@dataclass(frozen=True, slots=True)
class AdaptiveEvidence:
    evidence_id: str
    requested_level: int
    benefit_units: int
    sacrifice_units: int
    evidence_sufficient: bool
    baseline_preserved: bool

    def __post_init__(self) -> None:
        require_text("evidence_id", self.evidence_id)
        if not isinstance(self.requested_level, int) or isinstance(self.requested_level, bool) or not 0 <= self.requested_level <= 3:
            raise PrecisionContractViolation("requested adaptive level must be from 0 to 3")
        for name in ("benefit_units", "sacrifice_units"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise PrecisionContractViolation(f"{name} must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class AdaptiveLevelDecision:
    decision_id: str
    relevance_decision_id: str
    level: AdaptiveLevel
    policy_id: str
    benefit_units: int
    sacrifice_units: int
    failed_constraints: tuple[str, ...]
    reasons: tuple[str, ...]
    restrictions: tuple[str, ...]

    @property
    def output_fingerprint(self) -> str:
        return fingerprint(self)


@dataclass(frozen=True, slots=True)
class AdaptiveResult:
    assessment: EngineAssessment
    decision: AdaptiveLevelDecision


class AdaptiveFrontierController:
    name = "ADAPTIVE_FRONTIER"
    _GATE_CAP = {"RETURN_UPSTREAM": 0, "LOW": 0, "MEDIUM": 1, "HIGH": 3}

    def decide(
        self, *, relevance: RelevanceDecision, constraints: HardConstraints,
        evidence: AdaptiveEvidence, policy: AdaptivePolicy,
    ) -> AdaptiveResult:
        reasons: list[str] = []
        failed = constraints.failed
        if failed:
            level = 0
            reasons.extend(f"HARD_CONSTRAINT_FAILED:{item}" for item in failed)
        elif relevance.level in {"RETURN_UPSTREAM", "LOW"}:
            level = 0
            reasons.append("RELEVANCE_DOES_NOT_ALLOW_ADAPTATION")
        elif not evidence.evidence_sufficient:
            level = 0
            reasons.append("ADAPTIVE_EVIDENCE_INSUFFICIENT")
        elif not evidence.baseline_preserved:
            level = 0
            reasons.append("BASELINE_REGRESSION_CIRCUIT_BREAK")
        elif evidence.benefit_units - evidence.sacrifice_units < policy.upgrade_margin:
            level = 0
            reasons.append("MARGINAL_BENEFIT_DOES_NOT_EXCEED_SACRIFICE")
        else:
            level = min(
                evidence.requested_level,
                policy.maximum_level,
                self._GATE_CAP[relevance.level],
            )
            reasons.append(f"ADAPTIVE_LEVEL_{level}_EARNED")
        decision = AdaptiveLevelDecision(
            decision_id=f"{relevance.decision_id}:adaptive:{policy.policy_id}:{evidence.evidence_id}",
            relevance_decision_id=relevance.decision_id,
            level=level,  # type: ignore[arg-type]
            policy_id=policy.policy_id,
            benefit_units=evidence.benefit_units,
            sacrifice_units=evidence.sacrifice_units,
            failed_constraints=failed,
            reasons=tuple(reasons),
            restrictions=(
                "HARD_CONSTRAINTS_CANNOT_BE_TRADED",
                "LOWER_LEVEL_WINS_ON_UNCERTAINTY",
                "NO_SELF_MODIFYING_LEVEL",
                "NO_DELIVERY_AUTHORITY",
            ),
        )
        disposition = "ACCEPTED" if level > 0 or not failed else "PARTIAL"
        return AdaptiveResult(
            EngineAssessment(
                self.name, disposition, decision.reasons,
                (evidence.evidence_id,), decision.output_fingerprint,
            ),
            decision,
        )

