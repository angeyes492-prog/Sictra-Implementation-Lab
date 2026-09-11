"""M03 Behavioral Intelligence: observed patterns without intent attribution."""

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


BehaviorEventType = Literal[
    "DELIVERED", "OPEN", "CLICK", "CONTENT_INTERACTION", "REPLY", "QUESTION",
    "SHARE", "MEETING", "CALL_INTERACTION", "SILENCE", "UNSUBSCRIBE",
]
_EVENT_TYPES = frozenset(BehaviorEventType.__args__)
_ENGAGEMENT_TYPES = frozenset({
    "CLICK", "CONTENT_INTERACTION", "REPLY", "QUESTION", "SHARE", "MEETING",
    "CALL_INTERACTION",
})
_HIGH_INFORMATION_TYPES = frozenset({"REPLY", "QUESTION", "SHARE", "MEETING", "CALL_INTERACTION"})


@dataclass(frozen=True, slots=True)
class BehaviorEvent:
    event_id: str
    person_id: str
    event_type: BehaviorEventType
    occurred_at: int
    evidence: EvidenceRef
    topic: str = ""
    format: str = ""
    channel: str = ""
    cta: str = ""

    def __post_init__(self) -> None:
        for name in ("event_id", "person_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise PrecisionContractViolation(f"{name} must be non-empty")
        if self.event_type not in _EVENT_TYPES:
            raise PrecisionContractViolation("behavior event type is not governed")
        if not isinstance(self.occurred_at, int) or isinstance(self.occurred_at, bool):
            raise PrecisionContractViolation("occurred_at must be an integer")
        if self.occurred_at < 0 or self.occurred_at != self.evidence.observed_at:
            raise PrecisionContractViolation("event time must match its evidence observation time")
        if any(not isinstance(value, str) for value in (self.topic, self.format, self.channel, self.cta)):
            raise PrecisionContractViolation("behavior dimensions must be strings")


@dataclass(frozen=True, slots=True)
class BehavioralSignal:
    dimension: str
    value: str
    observed_event_count: int
    independent_root_count: int
    high_information_event_count: int
    evidence_ids: tuple[str, ...]
    latest_observed_at: int
    interpretation: str


@dataclass(frozen=True, slots=True)
class BehavioralEvidenceProfile:
    profile_id: str
    person_id: str
    signals: tuple[BehavioralSignal, ...]
    neutral_event_ids: tuple[str, ...]
    silence_event_ids: tuple[str, ...]
    unsubscribe_event_ids: tuple[str, ...]
    omitted_evidence_ids: tuple[str, ...]
    restrictions: tuple[str, ...]

    @property
    def output_fingerprint(self) -> str:
        return fingerprint(self)


@dataclass(frozen=True, slots=True)
class BehavioralResult:
    assessment: EngineAssessment
    profile: BehavioralEvidenceProfile | None


class BehavioralIntelligenceEngine:
    name = "M03"

    def __init__(self, *, max_events: int = 2_000) -> None:
        if max_events < 1:
            raise PrecisionContractViolation("max_events must be positive")
        self._max_events = max_events

    def interpret(
        self, *, person_id: str, events: tuple[BehaviorEvent, ...], now: int,
    ) -> BehavioralResult:
        if not isinstance(person_id, str) or not person_id.strip():
            raise PrecisionContractViolation("person_id must be non-empty")
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise PrecisionContractViolation("now must be a non-negative integer")
        events = tuple(events)
        validate_identity_set(events, id_attribute="event_id", limit=self._max_events)
        if any(item.person_id != person_id for item in events):
            raise PrecisionContractViolation("M03 cannot combine different person identities")
        unique = {item.event_id: item for item in events}
        current = [item for item in unique.values() if item.evidence.current_at(now)]
        omitted = tuple(sorted(
            item.evidence.evidence_id for item in unique.values() if not item.evidence.current_at(now)
        ))

        grouped: dict[tuple[str, str], list[BehaviorEvent]] = {}
        for event in current:
            if event.event_type not in _ENGAGEMENT_TYPES:
                continue
            for dimension, value in (
                ("topic", event.topic), ("format", event.format),
                ("channel", event.channel), ("cta", event.cta),
            ):
                if value.strip():
                    grouped.setdefault((dimension, value.strip()), []).append(event)

        signals: list[BehavioralSignal] = []
        for (dimension, value), supporting in sorted(grouped.items()):
            high_information = sum(
                1 for event in supporting if event.event_type in _HIGH_INFORMATION_TYPES
            )
            signals.append(BehavioralSignal(
                dimension=dimension,
                value=value,
                observed_event_count=len(supporting),
                independent_root_count=len({event.evidence.root_provenance for event in supporting}),
                high_information_event_count=high_information,
                evidence_ids=tuple(sorted({event.evidence.evidence_id for event in supporting})),
                latest_observed_at=max(event.occurred_at for event in supporting),
                interpretation=(
                    "observed stronger interaction evidence; preference and purchase intent remain unproven"
                    if high_information else
                    "observed interaction only; interest and intent remain unproven"
                ),
            ))

        neutral = tuple(sorted(
            event.event_id for event in current if event.event_type in {"DELIVERED", "OPEN"}
        ))
        silence = tuple(sorted(event.event_id for event in current if event.event_type == "SILENCE"))
        unsubscribes = tuple(sorted(
            event.event_id for event in current if event.event_type == "UNSUBSCRIBE"
        ))
        restrictions = (
            "OBSERVATION_NOT_INTENT",
            "OPEN_NOT_INTEREST",
            "CLICK_NOT_PURCHASE_INTENT",
            "SILENCE_NOT_REJECTION",
        )
        if unsubscribes:
            restrictions += ("UNSUBSCRIBE_OBSERVED_REQUIRES_DELIVERY_ENFORCEMENT",)
        profile = BehavioralEvidenceProfile(
            profile_id=f"{person_id}:behavior-profile:v0.1",
            person_id=person_id,
            signals=tuple(signals),
            neutral_event_ids=neutral,
            silence_event_ids=silence,
            unsubscribe_event_ids=unsubscribes,
            omitted_evidence_ids=omitted,
            restrictions=restrictions,
        )
        reasons: tuple[str, ...] = ()
        if not current:
            reasons += ("NO_CURRENT_BEHAVIORAL_EVIDENCE",)
        elif not signals:
            reasons += ("NO_INTERACTION_PATTERN_SUPPORTED",)
        if silence:
            reasons += ("SILENCE_RETAINED_WITHOUT_REJECTION_INFERENCE",)
        if unsubscribes:
            reasons += ("UNSUBSCRIBE_OBSERVED",)
        if omitted:
            reasons += ("NON_CURRENT_EVIDENCE_OMITTED",)
        disposition = "PARTIAL" if reasons else "ACCEPTED"
        evidence_ids = tuple(sorted({event.evidence.evidence_id for event in current}))
        return BehavioralResult(
            EngineAssessment(self.name, disposition, reasons, evidence_ids, profile.output_fingerprint),
            profile,
        )
