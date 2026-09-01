"""M04 Relationship Intelligence: demonstrable relationship and contextual permission."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .contracts import (
    EngineAssessment,
    EvidenceRef,
    PrecisionContractViolation,
    fingerprint,
    validate_identity_set,
)


RelationshipState = Literal[
    "COLD", "AWARE", "ENGAGED", "CONVERSATIONAL", "OPPORTUNITY", "DORMANT",
]
InteractionKind = Literal[
    "DELIVERED", "EXPOSURE_CONFIRMED", "CONTENT_INTERACTION", "REPLY", "QUESTION",
    "SHARE", "BILATERAL_EXCHANGE", "MEETING", "OPPORTUNITY_ACTIVE",
    "OPPORTUNITY_CLOSED", "UNSUBSCRIBE",
]
ContextPermission = Literal[
    "NONE", "LOW_CONTEXT", "OBSERVED_CONTEXT", "BILATERAL_CONTEXT", "COMMERCIAL_CONTEXT",
]
_KINDS = frozenset(InteractionKind.__args__)
_MEANINGFUL = frozenset(_KINDS - {"DELIVERED", "UNSUBSCRIBE"})


@dataclass(frozen=True, slots=True)
class RelationshipPolicy:
    policy_id: str
    authority_reference: str
    dormancy_after_seconds: int

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or not self.authority_reference.strip():
            raise PrecisionContractViolation("relationship policy identity and authority are required")
        if (
            not isinstance(self.dormancy_after_seconds, int)
            or isinstance(self.dormancy_after_seconds, bool)
            or self.dormancy_after_seconds < 1
        ):
            raise PrecisionContractViolation("dormancy threshold must be a positive integer")


@dataclass(frozen=True, slots=True)
class RelationshipEvent:
    event_id: str
    person_id: str
    kind: InteractionKind
    occurred_at: int
    evidence: EvidenceRef

    def __post_init__(self) -> None:
        if not self.event_id.strip() or not self.person_id.strip():
            raise PrecisionContractViolation("relationship event and person identities are required")
        if self.kind not in _KINDS:
            raise PrecisionContractViolation("relationship event kind is not governed")
        if not isinstance(self.occurred_at, int) or isinstance(self.occurred_at, bool):
            raise PrecisionContractViolation("relationship occurred_at must be an integer")
        if self.occurred_at < 0 or self.occurred_at != self.evidence.observed_at:
            raise PrecisionContractViolation("relationship event time must match evidence")


@dataclass(frozen=True, slots=True)
class RelationshipProfile:
    profile_id: str
    person_id: str
    state: RelationshipState
    communication_permission_level: ContextPermission
    state_evidence_ids: tuple[str, ...]
    last_meaningful_interaction_at: int | None
    policy_id: str
    policy_authority_reference: str
    unsubscribe_observed: bool
    omitted_evidence_ids: tuple[str, ...]
    restrictions: tuple[str, ...]

    @property
    def output_fingerprint(self) -> str:
        return fingerprint(self)


@dataclass(frozen=True, slots=True)
class RelationshipResult:
    assessment: EngineAssessment
    profile: RelationshipProfile


class RelationshipIntelligenceEngine:
    name = "M04"

    def __init__(self, *, max_events: int = 2_000) -> None:
        if max_events < 1:
            raise PrecisionContractViolation("max_events must be positive")
        self._max_events = max_events

    def determine(
        self, *, person_id: str, events: tuple[RelationshipEvent, ...],
        policy: RelationshipPolicy, now: int,
    ) -> RelationshipResult:
        if not isinstance(person_id, str) or not person_id.strip():
            raise PrecisionContractViolation("person_id must be non-empty")
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise PrecisionContractViolation("now must be a non-negative integer")
        events = tuple(events)
        validate_identity_set(events, id_attribute="event_id", limit=self._max_events)
        if any(item.person_id != person_id for item in events):
            raise PrecisionContractViolation("M04 cannot combine different person identities")
        unique = {item.event_id: item for item in events}
        usable = [event for event in unique.values() if event.evidence.current_at(now)]
        omitted = tuple(sorted(
            event.evidence.evidence_id for event in unique.values()
            if not event.evidence.current_at(now)
        ))
        kinds = {event.kind for event in usable}
        opportunity_events = [
            event for event in usable
            if event.kind in {"OPPORTUNITY_ACTIVE", "OPPORTUNITY_CLOSED"}
        ]
        latest_opportunity_kinds: set[str] = set()
        if opportunity_events:
            latest_opportunity_at = max(event.occurred_at for event in opportunity_events)
            latest_opportunity_kinds = {
                event.kind for event in opportunity_events
                if event.occurred_at == latest_opportunity_at
            }
        opportunity_contradicted = latest_opportunity_kinds == {
            "OPPORTUNITY_ACTIVE", "OPPORTUNITY_CLOSED"
        }
        state: RelationshipState
        if latest_opportunity_kinds == {"OPPORTUNITY_ACTIVE"}:
            state = "OPPORTUNITY"
        elif kinds & {"BILATERAL_EXCHANGE", "MEETING"}:
            state = "CONVERSATIONAL"
        elif kinds & {"CONTENT_INTERACTION", "REPLY", "QUESTION", "SHARE"}:
            state = "ENGAGED"
        elif "EXPOSURE_CONFIRMED" in kinds:
            state = "AWARE"
        else:
            state = "COLD"

        meaningful = [event for event in usable if event.kind in _MEANINGFUL]
        last_meaningful = max((event.occurred_at for event in meaningful), default=None)
        if (
            state not in {"COLD", "OPPORTUNITY"}
            and last_meaningful is not None
            and now - last_meaningful > policy.dormancy_after_seconds
        ):
            state = "DORMANT"

        permission_by_state: dict[str, ContextPermission] = {
            "COLD": "LOW_CONTEXT",
            "AWARE": "OBSERVED_CONTEXT",
            "ENGAGED": "OBSERVED_CONTEXT",
            "CONVERSATIONAL": "BILATERAL_CONTEXT",
            "OPPORTUNITY": "COMMERCIAL_CONTEXT",
            "DORMANT": "LOW_CONTEXT",
        }
        unsubscribe = "UNSUBSCRIBE" in kinds
        permission = "NONE" if unsubscribe else permission_by_state[state]
        restrictions = (
            "CONTEXTUAL_PERMISSION_NOT_LEGAL_CONSENT",
            "RELATIONSHIP_STATE_NOT_DELIVERY_AUTHORITY",
        )
        if unsubscribe:
            restrictions += ("UNSUBSCRIBE_OBSERVED_REQUIRES_DELIVERY_ENFORCEMENT",)
        profile = RelationshipProfile(
            profile_id=f"{person_id}:relationship-profile:v0.1",
            person_id=person_id,
            state=state,
            communication_permission_level=permission,
            state_evidence_ids=tuple(sorted({event.evidence.evidence_id for event in usable})),
            last_meaningful_interaction_at=last_meaningful,
            policy_id=policy.policy_id,
            policy_authority_reference=policy.authority_reference,
            unsubscribe_observed=unsubscribe,
            omitted_evidence_ids=omitted,
            restrictions=restrictions,
        )
        reasons: tuple[str, ...] = ()
        if state == "COLD":
            reasons += ("NO_SIGNIFICANT_RELATIONSHIP_DEMONSTRATED",)
        if state == "DORMANT":
            reasons += ("POLICY_DEFINED_DORMANCY_REACHED",)
        if unsubscribe:
            reasons += ("UNSUBSCRIBE_OBSERVED",)
        if opportunity_contradicted:
            reasons += ("CONTRADICTORY_OPPORTUNITY_STATE_AT_SAME_TIME",)
        if omitted:
            reasons += ("NON_CURRENT_EVIDENCE_OMITTED",)
        disposition = "CONTRADICTED" if opportunity_contradicted else (
            "PARTIAL" if reasons else "ACCEPTED"
        )
        return RelationshipResult(
            EngineAssessment(
                self.name, disposition, reasons,
                tuple(sorted({event.evidence.evidence_id for event in usable})),
                profile.output_fingerprint,
            ),
            profile,
        )
