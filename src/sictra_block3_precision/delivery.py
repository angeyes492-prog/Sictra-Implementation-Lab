"""M07 Timing & Channel Intelligence: proposals without external effects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .adaptive import AdaptiveLevelDecision
from .contracts import (
    EngineAssessment, EvidenceRef, PrecisionContractViolation, fingerprint, require_text,
)
from .message import MessageStrategy
from .precision_context import PrecisionContextPack
from .relevance import RelevanceDecision


DeliveryDisposition = Literal["SEND_CANDIDATE", "WAIT", "DO_NOT_SEND", "RETURN_UPSTREAM"]


@dataclass(frozen=True, slots=True)
class ChannelPolicy:
    policy_id: str
    authority_reference: str
    allowed_channels: tuple[str, ...]
    minimum_interval_seconds: int
    proposal_validity_seconds: int
    maximum_contacts_in_window: int
    maximum_pressure: int

    def __post_init__(self) -> None:
        require_text("policy_id", self.policy_id)
        require_text("authority_reference", self.authority_reference)
        channels = tuple(item.strip().upper() for item in self.allowed_channels)
        if not channels or any(not item for item in channels):
            raise PrecisionContractViolation("allowed channels are required")
        object.__setattr__(self, "allowed_channels", channels)
        for name in (
            "minimum_interval_seconds", "proposal_validity_seconds",
            "maximum_contacts_in_window", "maximum_pressure",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise PrecisionContractViolation(f"{name} must be a non-negative integer")
        if self.proposal_validity_seconds < 1:
            raise PrecisionContractViolation("proposal validity must be positive")
        if not 0 <= self.maximum_pressure <= 3:
            raise PrecisionContractViolation("maximum pressure must be from 0 to 3")


@dataclass(frozen=True, slots=True)
class ChannelHistory:
    history_id: str
    person_id: str
    channel: str
    last_contact_at: int | None
    contacts_in_window: int
    window_started_at: int
    evidence: EvidenceRef

    def __post_init__(self) -> None:
        require_text("history_id", self.history_id)
        require_text("person_id", self.person_id)
        require_text("channel", self.channel)
        object.__setattr__(self, "channel", self.channel.upper())
        for name in ("contacts_in_window", "window_started_at"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise PrecisionContractViolation(f"{name} must be non-negative")
        if self.last_contact_at is not None and (
            not isinstance(self.last_contact_at, int)
            or isinstance(self.last_contact_at, bool)
            or self.last_contact_at < 0
        ):
            raise PrecisionContractViolation("last contact must be a non-negative timestamp")


@dataclass(frozen=True, slots=True)
class DeliveryProposal:
    proposal_id: str
    strategy_id: str
    context_snapshot_id: str
    disposition: DeliveryDisposition
    channel: str | None
    not_before: int | None
    expires_at: int | None
    contact_pressure: int
    follow_up_after_seconds: int | None
    policy_id: str
    reasons: tuple[str, ...]
    required_executor_checks: tuple[str, ...]
    restrictions: tuple[str, ...]

    @property
    def output_fingerprint(self) -> str:
        return fingerprint(self)


@dataclass(frozen=True, slots=True)
class DeliveryResult:
    assessment: EngineAssessment
    proposal: DeliveryProposal


class TimingChannelIntelligenceEngine:
    name = "M07"
    _STATE_PRESSURE = {
        "COLD": 1, "AWARE": 1, "ENGAGED": 1,
        "CONVERSATIONAL": 2, "OPPORTUNITY": 2, "DORMANT": 1,
    }

    def propose(
        self, *, strategy: MessageStrategy, pack: PrecisionContextPack,
        relevance: RelevanceDecision, adaptive: AdaptiveLevelDecision,
        history: ChannelHistory, requested_channel: str,
        policy: ChannelPolicy, now: int,
    ) -> DeliveryResult:
        if strategy.context_snapshot_id != pack.context_snapshot_id:
            raise PrecisionContractViolation("M07 strategy is not bound to context pack")
        if strategy.relevance_decision_id != relevance.decision_id:
            raise PrecisionContractViolation("M07 strategy is not bound to relevance")
        if strategy.adaptive_decision_id != adaptive.decision_id:
            raise PrecisionContractViolation("M07 strategy is not bound to adaptive decision")
        if history.person_id != pack.person_id:
            raise PrecisionContractViolation("M07 history person identity mismatch")
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise PrecisionContractViolation("now must be a non-negative integer")
        channel = requested_channel.strip().upper()
        reasons: list[str] = []
        disposition: DeliveryDisposition
        not_before: int | None = None
        expires_at: int | None = None
        pressure = 0
        follow_up: int | None = None
        selected_channel: str | None = None
        if not history.evidence.current_at(now):
            disposition = "RETURN_UPSTREAM"
            reasons.append("CHANNEL_HISTORY_NOT_CURRENT")
        elif not pack.current_at(now):
            disposition = "RETURN_UPSTREAM"
            reasons.append("CONTEXT_PACK_EXPIRED")
        elif relevance.level == "RETURN_UPSTREAM":
            disposition = "RETURN_UPSTREAM"
            reasons.append("RELEVANCE_RETURN_UPSTREAM")
        elif relevance.level == "LOW":
            disposition = "DO_NOT_SEND"
            reasons.append("LOW_RELEVANCE")
        elif pack.relationship.unsubscribe_observed:
            disposition = "DO_NOT_SEND"
            reasons.append("UNSUBSCRIBE_OBSERVED")
        elif channel not in policy.allowed_channels:
            disposition = "RETURN_UPSTREAM"
            reasons.append("CHANNEL_NOT_AUTHORIZED_BY_POLICY")
        elif history.channel != channel:
            disposition = "RETURN_UPSTREAM"
            reasons.append("CHANNEL_HISTORY_IDENTITY_MISMATCH")
        elif history.contacts_in_window >= policy.maximum_contacts_in_window:
            disposition = "WAIT"
            selected_channel = channel
            reasons.append("FREQUENCY_POLICY_WINDOW_FULL")
            not_before = max(now, history.window_started_at + policy.minimum_interval_seconds)
            expires_at = now + policy.proposal_validity_seconds
        else:
            selected_channel = channel
            earliest = now
            if history.last_contact_at is not None:
                earliest = max(earliest, history.last_contact_at + policy.minimum_interval_seconds)
            not_before = earliest
            expires_at = now + policy.proposal_validity_seconds
            if earliest > now:
                disposition = "WAIT"
                reasons.append("MINIMUM_INTERVAL_NOT_REACHED")
            else:
                disposition = "SEND_CANDIDATE"
                reasons.append("AUTHORIZED_EXECUTOR_RECHECK_REQUIRED")
            pressure = min(
                self._STATE_PRESSURE[pack.relationship.state],
                policy.maximum_pressure,
                1 if relevance.level == "MEDIUM" else 3,
            )
            follow_up = policy.minimum_interval_seconds if pressure > 0 else None
        proposal = DeliveryProposal(
            proposal_id=f"{strategy.strategy_id}:proposal:{policy.policy_id}:{now}",
            strategy_id=strategy.strategy_id,
            context_snapshot_id=pack.context_snapshot_id,
            disposition=disposition,
            channel=selected_channel,
            not_before=not_before,
            expires_at=expires_at,
            contact_pressure=pressure,
            follow_up_after_seconds=follow_up,
            policy_id=policy.policy_id,
            reasons=tuple(reasons),
            required_executor_checks=(
                "CONSENT_CURRENT",
                "OPT_OUT_NOT_ACTIVE",
                "FREQUENCY_POLICY_CURRENT",
                "CHANNEL_CREDENTIAL_AUTHORIZED",
                "PROPOSAL_NOT_EXPIRED",
            ),
            restrictions=(
                "PROPOSAL_NOT_EXECUTION",
                "NO_CREDENTIALS",
                "NO_CONSENT_AUTHORITY",
                "EXECUTOR_MUST_REVALIDATE",
            ),
        )
        assessment_disposition = (
            "RETURN_UPSTREAM" if disposition == "RETURN_UPSTREAM"
            else "PARTIAL" if disposition == "WAIT"
            else "ACCEPTED"
        )
        return DeliveryResult(
            EngineAssessment(
                self.name, assessment_disposition, proposal.reasons,
                tuple(sorted({
                    *pack.relationship.state_evidence_ids,
                    history.evidence.evidence_id,
                })), proposal.output_fingerprint,
            ),
            proposal,
        )
