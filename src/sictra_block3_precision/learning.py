"""M08 Learning Engine: candidate-only learning across a complete outcome chain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .contracts import EngineAssessment, EvidenceRef, PrecisionContractViolation, fingerprint, require_text
from .delivery import DeliveryProposal
from .message import MessageStrategy


ReceiptDisposition = Literal["EXECUTED", "REJECTED"]
OutcomeKind = Literal["RESPONSE", "ESCALATED", "MEETING", "NO_RESPONSE", "UNSUBSCRIBE"]
LearningScope = Literal["PERSON", "ACCOUNT", "SEGMENT", "GLOBAL"]


@dataclass(frozen=True, slots=True)
class DeliveryReceipt:
    receipt_id: str
    proposal_id: str
    disposition: ReceiptDisposition
    occurred_at: int
    executor_authority_reference: str
    evidence: EvidenceRef

    def __post_init__(self) -> None:
        for name in ("receipt_id", "proposal_id", "executor_authority_reference"):
            require_text(name, getattr(self, name))
        if self.disposition not in {"EXECUTED", "REJECTED"}:
            raise PrecisionContractViolation("receipt disposition is not governed")
        if self.occurred_at != self.evidence.observed_at:
            raise PrecisionContractViolation("receipt time must match evidence")


@dataclass(frozen=True, slots=True)
class ObservedOutcome:
    outcome_id: str
    receipt_id: str
    kind: OutcomeKind
    occurred_at: int
    evidence: EvidenceRef

    def __post_init__(self) -> None:
        require_text("outcome_id", self.outcome_id)
        require_text("receipt_id", self.receipt_id)
        if self.kind not in {"RESPONSE", "ESCALATED", "MEETING", "NO_RESPONSE", "UNSUBSCRIBE"}:
            raise PrecisionContractViolation("outcome kind is not governed")
        if self.occurred_at != self.evidence.observed_at:
            raise PrecisionContractViolation("outcome time must match evidence")


@dataclass(frozen=True, slots=True)
class LearningPolicy:
    policy_id: str
    authority_reference: str
    candidate_validity_seconds: int
    default_scope: LearningScope = "ACCOUNT"

    def __post_init__(self) -> None:
        require_text("policy_id", self.policy_id)
        require_text("authority_reference", self.authority_reference)
        if not isinstance(self.candidate_validity_seconds, int) or isinstance(self.candidate_validity_seconds, bool) or self.candidate_validity_seconds < 1:
            raise PrecisionContractViolation("candidate validity must be positive")
        if self.default_scope not in {"PERSON", "ACCOUNT", "SEGMENT", "GLOBAL"}:
            raise PrecisionContractViolation("learning scope is not governed")


@dataclass(frozen=True, slots=True)
class NextBestTest:
    test_id: str
    strategy_id: str
    proposal_id: str
    receipt_id: str
    outcome_id: str
    observed_facts: tuple[str, ...]
    inferences: tuple[str, ...]
    counterhypotheses: tuple[str, ...]
    hypothesis: str
    scope: LearningScope
    baseline_metric: str
    primary_metric: str
    guardrails: tuple[str, ...]
    stopping_rule: str
    expires_at: int
    policy_id: str
    restrictions: tuple[str, ...]

    @property
    def output_fingerprint(self) -> str:
        return fingerprint(self)


@dataclass(frozen=True, slots=True)
class LearningResult:
    assessment: EngineAssessment
    next_best_test: NextBestTest | None


class LearningEngine:
    name = "M08"

    @staticmethod
    def _self_authored(identity: str) -> bool:
        normalized = identity.casefold()
        for separator in (":", "/", "\\", "|", "#"):
            normalized = normalized.replace(separator, " ")
        return "m08" in normalized.split()

    def learn(
        self, *, strategy: MessageStrategy, proposal: DeliveryProposal,
        receipt: DeliveryReceipt | None, outcome: ObservedOutcome | None,
        policy: LearningPolicy, now: int,
    ) -> LearningResult:
        if proposal.strategy_id != strategy.strategy_id:
            raise PrecisionContractViolation("M08 proposal is not bound to strategy")
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise PrecisionContractViolation("now must be a non-negative integer")
        if receipt is None:
            return LearningResult(
                EngineAssessment(self.name, "PARTIAL", ("NO_DELIVERY_RECEIPT_NO_LEARNING",), (), None),
                None,
            )
        if receipt.proposal_id != proposal.proposal_id:
            raise PrecisionContractViolation("M08 receipt is not bound to proposal")
        if not receipt.evidence.current_at(now):
            return LearningResult(
                EngineAssessment(self.name, "RETURN_UPSTREAM", ("RECEIPT_NOT_CURRENT",), (), None),
                None,
            )
        if receipt.disposition == "REJECTED":
            return LearningResult(
                EngineAssessment(
                    self.name, "PARTIAL",
                    ("EXECUTOR_REJECTION_NOT_RECIPIENT_BEHAVIOR",),
                    (receipt.evidence.evidence_id,), None,
                ),
                None,
            )
        if proposal.disposition != "SEND_CANDIDATE":
            raise PrecisionContractViolation(
                "executed receipt requires a SEND_CANDIDATE proposal"
            )
        if outcome is None:
            return LearningResult(
                EngineAssessment(
                    self.name, "PARTIAL", ("NO_ATTRIBUTABLE_OUTCOME_NO_LEARNING",),
                    (receipt.evidence.evidence_id,), None,
                ),
                None,
            )
        if outcome.receipt_id != receipt.receipt_id:
            raise PrecisionContractViolation("M08 outcome is not bound to receipt")
        if outcome.occurred_at < receipt.occurred_at:
            raise PrecisionContractViolation("outcome cannot precede delivery receipt")
        if not outcome.evidence.current_at(now):
            return LearningResult(
                EngineAssessment(self.name, "RETURN_UPSTREAM", ("OUTCOME_NOT_CURRENT",), (), None),
                None,
            )
        if any(
            self._self_authored(value) for value in (
                receipt.evidence.source_identity, receipt.evidence.root_provenance,
                outcome.evidence.source_identity, outcome.evidence.root_provenance,
            )
        ):
            raise PrecisionContractViolation("M08 cannot learn from self-authored evidence")

        positive = outcome.kind in {"RESPONSE", "ESCALATED", "MEETING"}
        if positive:
            hypothesis = "the governed strategy may improve attributable progression in comparable accounts"
            inference = "positive outcome followed execution; causal attribution remains unproven"
            counter = "the outcome may be explained by prior relationship, timing, or external events"
            primary_metric = "ATTRIBUTABLE_PROGRESSION_RATE"
        elif outcome.kind == "NO_RESPONSE":
            hypothesis = "a lower-friction or differently timed strategy may reduce non-response"
            inference = "no response was observed; rejection and irrelevance remain unproven"
            counter = "delivery, attention, timing, workload, or channel conditions may explain non-response"
            primary_metric = "ATTRIBUTABLE_RESPONSE_RATE"
        else:
            hypothesis = "contact pressure policy should be evaluated for stricter suppression"
            inference = "unsubscribe was observed after delivery; causal attribution remains unproven"
            counter = "prior cumulative contact or unrelated preference changes may explain unsubscribe"
            primary_metric = "UNSUBSCRIBE_RATE"
        next_test = NextBestTest(
            test_id=f"{outcome.outcome_id}:next-test:{policy.policy_id}",
            strategy_id=strategy.strategy_id,
            proposal_id=proposal.proposal_id,
            receipt_id=receipt.receipt_id,
            outcome_id=outcome.outcome_id,
            observed_facts=(
                f"DELIVERY_{receipt.disposition}",
                f"OUTCOME_{outcome.kind}",
            ),
            inferences=(inference,),
            counterhypotheses=(counter,),
            hypothesis=hypothesis,
            scope=policy.default_scope,
            baseline_metric=f"BASELINE_{primary_metric}",
            primary_metric=primary_metric,
            guardrails=(
                "NO_AUTHORITY_REGRESSION",
                "NO_PERSONALIZATION_CEILING_INCREASE",
                "NO_FREQUENCY_INCREASE_WITHOUT_REVIEW",
            ),
            stopping_rule="stop on material guardrail regression or insufficient attributable sample",
            expires_at=now + policy.candidate_validity_seconds,
            policy_id=policy.policy_id,
            restrictions=(
                "CANDIDATE_NOT_ACCEPTED_RULE",
                "OBSERVATION_NOT_CAUSALITY",
                "NO_DIRECT_PROFILE_WRITE",
                "FUTURE_VERSION_ONLY",
            ),
        )
        return LearningResult(
            EngineAssessment(
                self.name, "ACCEPTED", ("CANDIDATE_TEST_CREATED",),
                (receipt.evidence.evidence_id, outcome.evidence.evidence_id),
                next_test.output_fingerprint,
            ),
            next_test,
        )

