"""Bounded orchestration for M01-M05; this is not the Relevance Gate."""

from __future__ import annotations

from dataclasses import dataclass

from .behavioral import BehaviorEvent, BehavioralIntelligenceEngine, BehavioralResult
from .context import ContextIntelligenceEngine, ContextResult, ContextSignal
from .decision import DecisionIntelligenceEngine, DecisionResult, DecisionSignal
from .person import PersonIntelligenceEngine, PersonResult, ProfessionalFact
from .relationship import (
    RelationshipEvent,
    RelationshipIntelligenceEngine,
    RelationshipPolicy,
    RelationshipResult,
)
from .contracts import PrecisionContractViolation, fingerprint


@dataclass(frozen=True, slots=True)
class PrecisionInput:
    person_id: str
    insight_id: str
    target_id: str
    professional_facts: tuple[ProfessionalFact, ...]
    behavior_events: tuple[BehaviorEvent, ...]
    relationship_events: tuple[RelationshipEvent, ...]
    context_signals: tuple[ContextSignal, ...]
    decision_signals: tuple[DecisionSignal, ...]
    relationship_policy: RelationshipPolicy


@dataclass(frozen=True, slots=True)
class PrecisionFoundationResult:
    person: PersonResult
    behavioral: BehavioralResult
    relationship: RelationshipResult
    context: ContextResult
    decision: DecisionResult | None
    disposition: str
    reasons: tuple[str, ...]

    @property
    def output_fingerprint(self) -> str:
        return fingerprint(self)


class PrecisionFoundationPipeline:
    """Executes independent evidence engines before M02 synthesis.

    The order is M01/M03/M04/M05 -> M02.  It deliberately does not decide
    relevance, construct a message, choose a channel, or authorize delivery.
    """

    def __init__(self) -> None:
        self.person = PersonIntelligenceEngine()
        self.behavioral = BehavioralIntelligenceEngine()
        self.relationship = RelationshipIntelligenceEngine()
        self.context = ContextIntelligenceEngine()
        self.decision = DecisionIntelligenceEngine()

    def execute(self, request: PrecisionInput, *, now: int) -> PrecisionFoundationResult:
        person = self.person.build(
            person_id=request.person_id, facts=request.professional_facts, now=now,
        )
        behavioral = self.behavioral.interpret(
            person_id=request.person_id, events=request.behavior_events, now=now,
        )
        relationship = self.relationship.determine(
            person_id=request.person_id,
            events=request.relationship_events,
            policy=request.relationship_policy,
            now=now,
        )
        context = self.context.map_relevance(
            insight_id=request.insight_id,
            target_id=request.target_id,
            signals=request.context_signals,
            now=now,
        )
        blocking = tuple(
            result.assessment.engine
            for result in (person, context)
            if result.assessment.disposition == "RETURN_UPSTREAM"
        )
        if blocking:
            return PrecisionFoundationResult(
                person, behavioral, relationship, context, None,
                "RETURN_UPSTREAM",
                tuple(f"{engine}_BLOCKED" for engine in blocking),
            )
        if person.profile is None or context.relevance_map is None:
            raise PrecisionContractViolation("non-blocked foundation result lacks required output")
        decision = self.decision.formulate(
            person=person.profile,
            context=context.relevance_map,
            behavioral=behavioral.profile,
            relationship=relationship.profile,
            signals=request.decision_signals,
            now=now,
        )
        dispositions = {
            person.assessment.disposition,
            behavioral.assessment.disposition,
            relationship.assessment.disposition,
            context.assessment.disposition,
            decision.assessment.disposition,
        }
        if "RETURN_UPSTREAM" in dispositions:
            disposition = "RETURN_UPSTREAM"
        elif "CONTRADICTED" in dispositions:
            disposition = "CONTRADICTED"
        elif "PARTIAL" in dispositions:
            disposition = "PARTIAL"
        else:
            disposition = "ACCEPTED"
        reasons = tuple(sorted({
            reason
            for result in (person, behavioral, relationship, context, decision)
            for reason in result.assessment.reasons
        }))
        return PrecisionFoundationResult(
            person, behavioral, relationship, context, decision, disposition, reasons,
        )
