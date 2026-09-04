"""Bounded A∴ planning pipeline over the unchanged M01-M05 foundation."""

from __future__ import annotations

from dataclasses import dataclass

from .adaptive import (
    AdaptiveEvidence, AdaptiveFrontierController, AdaptivePolicy, AdaptiveResult,
    HardConstraints,
)
from .contracts import PrecisionContractViolation, fingerprint
from .delivery import (
    ChannelHistory, ChannelPolicy, DeliveryResult, TimingChannelIntelligenceEngine,
)
from .message import AuthorizedAsset, MessageIntelligenceEngine, MessagePolicy, MessageResult
from .pipeline import PrecisionFoundationResult
from .precision_context import (
    CeilingPolicy, PersonaStatePolicy, PrecisionContextPack,
    PrecisionContextPackComposer,
)
from .relevance import RelevanceGate, RelevancePolicy, RelevanceResult


@dataclass(frozen=True, slots=True)
class AdaptivePlanningInput:
    foundation: PrecisionFoundationResult
    person_id: str
    insight_id: str
    target_id: str
    policy_version: str
    persona_policy: PersonaStatePolicy
    ceiling_policy: CeilingPolicy
    relevance_policy: RelevancePolicy
    adaptive_policy: AdaptivePolicy
    adaptive_evidence: AdaptiveEvidence
    hard_constraints: HardConstraints
    message_policy: MessagePolicy
    assets: tuple[AuthorizedAsset, ...]
    channel_policy: ChannelPolicy
    channel_history: ChannelHistory
    requested_channel: str


@dataclass(frozen=True, slots=True)
class AdaptivePlanningResult:
    context_pack: PrecisionContextPack | None
    relevance: RelevanceResult | None
    adaptive: AdaptiveResult | None
    message: MessageResult | None
    delivery: DeliveryResult | None
    disposition: str
    reasons: tuple[str, ...]

    @property
    def output_fingerprint(self) -> str:
        return fingerprint(self)


class PrecisionAdaptivePipeline:
    """Plans strategy and delivery proposal; performs no external effect."""

    def __init__(self) -> None:
        self.composer = PrecisionContextPackComposer()
        self.relevance = RelevanceGate()
        self.adaptive = AdaptiveFrontierController()
        self.message = MessageIntelligenceEngine()
        self.delivery = TimingChannelIntelligenceEngine()

    def plan(self, request: AdaptivePlanningInput, *, now: int) -> AdaptivePlanningResult:
        if request.foundation.disposition in {"RETURN_UPSTREAM", "CONTRADICTED"}:
            return AdaptivePlanningResult(
                None, None, None, None, None,
                request.foundation.disposition,
                ("FOUNDATION_BLOCKED",),
            )
        pack = self.composer.compose(
            foundation=request.foundation,
            person_id=request.person_id,
            insight_id=request.insight_id,
            target_id=request.target_id,
            now=now,
            policy_version=request.policy_version,
            persona_policy=request.persona_policy,
            ceiling_policy=request.ceiling_policy,
        )
        relevance = self.relevance.evaluate(
            pack=pack, policy=request.relevance_policy, now=now,
        )
        adaptive = self.adaptive.decide(
            relevance=relevance.decision,
            constraints=request.hard_constraints,
            evidence=request.adaptive_evidence,
            policy=request.adaptive_policy,
        )
        if relevance.decision.level == "RETURN_UPSTREAM":
            return AdaptivePlanningResult(
                pack, relevance, adaptive, None, None,
                "RETURN_UPSTREAM", relevance.decision.reasons,
            )
        if relevance.decision.level == "LOW":
            return AdaptivePlanningResult(
                pack, relevance, adaptive, None, None,
                "DO_NOT_SEND", relevance.decision.reasons,
            )
        message = self.message.formulate(
            pack=pack,
            relevance=relevance.decision,
            adaptive=adaptive.decision,
            assets=request.assets,
            policy=request.message_policy,
        )
        if message.strategy is None:
            return AdaptivePlanningResult(
                pack, relevance, adaptive, message, None,
                "RETURN_UPSTREAM", message.assessment.reasons,
            )
        delivery = self.delivery.propose(
            strategy=message.strategy,
            pack=pack,
            relevance=relevance.decision,
            adaptive=adaptive.decision,
            history=request.channel_history,
            requested_channel=request.requested_channel,
            policy=request.channel_policy,
            now=now,
        )
        if delivery.proposal.disposition == "RETURN_UPSTREAM":
            disposition = "RETURN_UPSTREAM"
        elif delivery.proposal.disposition == "DO_NOT_SEND":
            disposition = "DO_NOT_SEND"
        elif delivery.proposal.disposition == "WAIT":
            disposition = "WAIT"
        else:
            disposition = "SEND_CANDIDATE"
        if disposition == "SEND_CANDIDATE" and delivery.proposal.contact_pressure < 0:
            raise PrecisionContractViolation("delivery pressure cannot be negative")
        reasons = tuple(sorted({
            *relevance.assessment.reasons,
            *adaptive.assessment.reasons,
            *message.assessment.reasons,
            *delivery.assessment.reasons,
        }))
        return AdaptivePlanningResult(
            pack, relevance, adaptive, message, delivery, disposition, reasons,
        )

