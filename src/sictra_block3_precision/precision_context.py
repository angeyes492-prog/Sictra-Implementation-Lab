"""Shared A∴ context, persona-state and personalization-ceiling projections."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .behavioral import BehavioralEvidenceProfile
from .context import ContextRelevanceMap
from .contracts import PrecisionContractViolation, fingerprint, require_text
from .decision import DecisionHypothesis
from .person import PersonProfile
from .pipeline import PrecisionFoundationResult
from .relationship import RelationshipProfile


PersonaState = Literal[
    "NORMAL", "DISRUPTION", "RISK_AWARE", "SOLUTION_SEEKING",
    "EVALUATION", "DECISION", "STABILIZATION", "UNKNOWN", "CONTRADICTED",
]


@dataclass(frozen=True, slots=True)
class PersonaStatePolicy:
    policy_id: str
    authority_reference: str
    disruption_tags: tuple[str, ...] = ("disruption", "congestion", "strike", "huelga")
    risk_tags: tuple[str, ...] = ("risk", "tariff", "regulation", "compliance")
    stabilization_tags: tuple[str, ...] = ("stabilization", "recovery", "normalized")

    def __post_init__(self) -> None:
        require_text("policy_id", self.policy_id)
        require_text("authority_reference", self.authority_reference)
        for field in ("disruption_tags", "risk_tags", "stabilization_tags"):
            values = tuple(item.casefold().strip() for item in getattr(self, field))
            if not values or any(not item for item in values):
                raise PrecisionContractViolation(f"{field} must contain governed tags")
            object.__setattr__(self, field, values)


@dataclass(frozen=True, slots=True)
class PersonaStateProjection:
    projection_id: str
    person_id: str
    state: PersonaState
    policy_id: str
    evidence_ids: tuple[str, ...]
    input_fingerprints: tuple[str, ...]
    confidence: str
    alternatives: tuple[str, ...]
    restrictions: tuple[str, ...]

    @property
    def output_fingerprint(self) -> str:
        return fingerprint(self)


class PersonaStateProjector:
    """Derives a reversible operational state without psychological labeling."""

    @staticmethod
    def project(
        *, behavioral: BehavioralEvidenceProfile, relationship: RelationshipProfile,
        context: ContextRelevanceMap, policy: PersonaStatePolicy,
    ) -> PersonaStateProjection:
        if behavioral.person_id != relationship.person_id:
            raise PrecisionContractViolation("persona-state inputs do not share one person")
        tags = context.tags
        evidence_ids = tuple(sorted({
            *relationship.state_evidence_ids,
            *(item for signal in behavioral.signals for item in signal.evidence_ids),
            *(item for stage in context.stages for item in stage.evidence_ids),
        }))
        moment_present = any(stage.scope == "MOMENT" for stage in context.stages)
        high_information = sum(
            signal.high_information_event_count for signal in behavioral.signals
        )
        alternatives: tuple[str, ...] = ()
        confidence = "C"
        if context.contradicted_claim_keys:
            state: PersonaState = "CONTRADICTED"
            confidence = "E"
            alternatives = ("UNKNOWN",)
        elif not moment_present:
            state = "UNKNOWN"
            confidence = "E"
        elif relationship.state == "OPPORTUNITY":
            state = "DECISION"
            confidence = "B"
            alternatives = ("EVALUATION",)
        elif tags.intersection(policy.stabilization_tags):
            state = "STABILIZATION"
            confidence = "C"
            alternatives = ("NORMAL",)
        elif relationship.state == "CONVERSATIONAL" and high_information:
            state = "EVALUATION"
            confidence = "C"
            alternatives = ("SOLUTION_SEEKING",)
        elif high_information:
            state = "SOLUTION_SEEKING"
            confidence = "C"
            alternatives = ("RISK_AWARE",)
        elif tags.intersection(policy.risk_tags):
            state = "RISK_AWARE"
            confidence = "C"
            alternatives = ("DISRUPTION", "NORMAL")
        elif tags.intersection(policy.disruption_tags):
            state = "DISRUPTION"
            confidence = "C"
            alternatives = ("NORMAL",)
        else:
            state = "NORMAL"
            confidence = "D"
        projection_id = f"{behavioral.person_id}:persona-state:{policy.policy_id}:v0.1"
        return PersonaStateProjection(
            projection_id=projection_id,
            person_id=behavioral.person_id,
            state=state,
            policy_id=policy.policy_id,
            evidence_ids=evidence_ids,
            input_fingerprints=(
                behavioral.output_fingerprint,
                relationship.output_fingerprint,
                context.output_fingerprint,
            ),
            confidence=confidence,
            alternatives=alternatives,
            restrictions=(
                "TEMPORAL_REVERSIBLE_PROJECTION",
                "NOT_PERSONALITY",
                "NOT_PERMANENT_IDENTITY",
                "NO_DELIVERY_AUTHORITY",
            ),
        )


@dataclass(frozen=True, slots=True)
class CeilingPolicy:
    policy_id: str
    authority_reference: str
    maximum_level: int = 5
    data_sensitivity_cap: int = 5
    channel_cap: int = 5

    def __post_init__(self) -> None:
        require_text("policy_id", self.policy_id)
        require_text("authority_reference", self.authority_reference)
        for name in ("maximum_level", "data_sensitivity_cap", "channel_cap"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 5:
                raise PrecisionContractViolation(f"{name} must be an integer from 0 to 5")


@dataclass(frozen=True, slots=True)
class CeilingLimit:
    source: str
    level: int
    reason: str


@dataclass(frozen=True, slots=True)
class PersonalizationCeiling:
    ceiling_id: str
    person_id: str
    effective_level: int
    limits: tuple[CeilingLimit, ...]
    policy_id: str
    restrictions: tuple[str, ...]

    @property
    def output_fingerprint(self) -> str:
        return fingerprint(self)


class PersonalizationCeilingResolver:
    _RELATIONSHIP_CAP = {
        "NONE": 0,
        "LOW_CONTEXT": 1,
        "OBSERVED_CONTEXT": 2,
        "BILATERAL_CONTEXT": 3,
        "COMMERCIAL_CONTEXT": 3,
    }

    @classmethod
    def resolve(
        cls, *, person: PersonProfile, behavioral: BehavioralEvidenceProfile,
        relationship: RelationshipProfile, context: ContextRelevanceMap,
        policy: CeilingPolicy,
    ) -> PersonalizationCeiling:
        if not (person.person_id == behavioral.person_id == relationship.person_id):
            raise PrecisionContractViolation("ceiling inputs do not share one person")
        scopes = {stage.scope for stage in context.stages}
        evidence_cap = 0
        if "INDUSTRY" in scopes:
            evidence_cap = 1
        if "ACCOUNT" in scopes:
            evidence_cap = 2
        if "ROLE" in scopes and person.attributes:
            evidence_cap = 3
        if behavioral.signals:
            evidence_cap = 4
        if "MOMENT" in scopes and behavioral.signals:
            evidence_cap = 5
        if person.contradictions or context.contradicted_claim_keys:
            evidence_cap = min(evidence_cap, 1)
        limits = (
            CeilingLimit("EVIDENCE", evidence_cap, "highest evidenced context scope"),
            CeilingLimit(
                "RELATIONSHIP",
                cls._RELATIONSHIP_CAP[relationship.communication_permission_level],
                "demonstrated contextual relationship",
            ),
            CeilingLimit("POLICY", policy.maximum_level, "versioned policy maximum"),
            CeilingLimit("DATA_SENSITIVITY", policy.data_sensitivity_cap, "data-use cap"),
            CeilingLimit("CHANNEL", policy.channel_cap, "channel capability cap"),
        )
        effective = min(item.level for item in limits)
        return PersonalizationCeiling(
            ceiling_id=f"{person.person_id}:ceiling:{policy.policy_id}:v0.1",
            person_id=person.person_id,
            effective_level=effective,
            limits=limits,
            policy_id=policy.policy_id,
            restrictions=(
                "MAXIMUM_NOT_TARGET",
                "MESSAGE_APPLIED_LEVEL_MUST_NOT_EXCEED",
                "NOT_CONSENT",
                "NOT_DELIVERY_AUTHORITY",
            ),
        )


@dataclass(frozen=True, slots=True)
class PrecisionContextPack:
    context_snapshot_id: str
    schema_version: str
    policy_version: str
    created_at: int
    valid_until: int
    person_id: str
    insight_id: str
    target_id: str
    foundation_disposition: str
    person: PersonProfile
    behavioral: BehavioralEvidenceProfile
    relationship: RelationshipProfile
    context: ContextRelevanceMap
    decision: DecisionHypothesis
    persona_state: PersonaStateProjection
    ceiling: PersonalizationCeiling
    source_assessments: tuple[str, ...]
    restrictions: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in (
            "context_snapshot_id", "schema_version", "policy_version",
            "person_id", "insight_id", "target_id",
        ):
            require_text(name, getattr(self, name))
        if self.valid_until < self.created_at:
            raise PrecisionContractViolation("context pack validity is invalid")
        if not (
            self.person.person_id == self.behavioral.person_id
            == self.relationship.person_id == self.person_id
        ):
            raise PrecisionContractViolation("context pack person identities do not match")
        if self.context.insight_id != self.insight_id or self.context.target_id != self.target_id:
            raise PrecisionContractViolation("context pack insight or target identity mismatch")
        if self.decision.person_id != self.person_id or self.decision.insight_id != self.insight_id:
            raise PrecisionContractViolation("context pack decision identity mismatch")

    @property
    def output_fingerprint(self) -> str:
        return fingerprint(self)

    def current_at(self, now: int) -> bool:
        return self.created_at <= now <= self.valid_until


class PrecisionContextPackComposer:
    def __init__(self, *, validity_seconds: int = 86_400) -> None:
        if not isinstance(validity_seconds, int) or isinstance(validity_seconds, bool) or validity_seconds < 1:
            raise PrecisionContractViolation("context pack validity must be positive")
        self._validity_seconds = validity_seconds

    def compose(
        self, *, foundation: PrecisionFoundationResult, person_id: str,
        insight_id: str, target_id: str, now: int, policy_version: str,
        persona_policy: PersonaStatePolicy, ceiling_policy: CeilingPolicy,
    ) -> PrecisionContextPack:
        if foundation.disposition in {"RETURN_UPSTREAM", "CONTRADICTED"}:
            raise PrecisionContractViolation("blocked foundation cannot become a context pack")
        if foundation.decision is None or foundation.decision.hypothesis is None:
            raise PrecisionContractViolation("context pack requires a decision hypothesis")
        if foundation.person.profile is None or foundation.context.relevance_map is None:
            raise PrecisionContractViolation("context pack requires foundation profiles")
        require_text("policy_version", policy_version)
        persona = PersonaStateProjector.project(
            behavioral=foundation.behavioral.profile,
            relationship=foundation.relationship.profile,
            context=foundation.context.relevance_map,
            policy=persona_policy,
        )
        ceiling = PersonalizationCeilingResolver.resolve(
            person=foundation.person.profile,
            behavioral=foundation.behavioral.profile,
            relationship=foundation.relationship.profile,
            context=foundation.context.relevance_map,
            policy=ceiling_policy,
        )
        snapshot_seed = (
            person_id, insight_id, target_id, now, policy_version,
            foundation.output_fingerprint, persona.output_fingerprint,
            ceiling.output_fingerprint,
        )
        return PrecisionContextPack(
            context_snapshot_id=f"precision-context:{fingerprint(snapshot_seed)}",
            schema_version="0.1",
            policy_version=policy_version,
            created_at=now,
            valid_until=now + self._validity_seconds,
            person_id=person_id,
            insight_id=insight_id,
            target_id=target_id,
            foundation_disposition=foundation.disposition,
            person=foundation.person.profile,
            behavioral=foundation.behavioral.profile,
            relationship=foundation.relationship.profile,
            context=foundation.context.relevance_map,
            decision=foundation.decision.hypothesis,
            persona_state=persona,
            ceiling=ceiling,
            source_assessments=(
                foundation.person.assessment.output_fingerprint or "NONE",
                foundation.behavioral.assessment.output_fingerprint or "NONE",
                foundation.relationship.assessment.output_fingerprint or "NONE",
                foundation.context.assessment.output_fingerprint or "NONE",
                foundation.decision.assessment.output_fingerprint or "NONE",
            ),
            restrictions=(
                "IMMUTABLE_EXECUTION_SNAPSHOT",
                "MORE_MEMORY_NOT_MORE_AUTHORITY",
                "NO_DELIVERY_AUTHORITY",
            ),
        )
