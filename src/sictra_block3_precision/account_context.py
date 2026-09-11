"""Account-research admission boundary for the M05 context engine.

This module turns a previously approved and durably recorded official-site
dossier into ACCOUNT-scoped M05 hypotheses. It does not create facts, person
attributes, relevance decisions, delivery permission, or network activity.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import hmac

from .account_knowledge import AccountKnowledgeDossier
from .account_memory import AccountKnowledgeStore
from .account_research import AccountResearchReceipt, ResearchReceiptLedger
from .context import ContextSignal
from .contracts import EngineAssessment, PrecisionContractViolation, fingerprint, require_text


@dataclass(frozen=True, slots=True)
class AccountContextAdmissionPolicy:
    policy_id: str
    authority_reference: str
    max_context_signals: int = 1_000
    issuer_id: str = "LOCAL_ACCOUNT_CONTEXT_INGRESS"

    def __post_init__(self) -> None:
        require_text("policy_id", self.policy_id)
        require_text("authority_reference", self.authority_reference)
        require_text("issuer_id", self.issuer_id)
        if not isinstance(self.max_context_signals, int) or isinstance(self.max_context_signals, bool) or self.max_context_signals < 1:
            raise PrecisionContractViolation("max_context_signals must be a positive integer")


@dataclass(frozen=True, slots=True)
class AccountContextAdmission:
    admission_id: str
    policy_id: str
    issuer_id: str
    tenant_id: str
    account_id: str
    insight_id: str
    receipt_id: str
    dossier_id: str
    dossier_fingerprint: str
    admitted_at: int
    expires_at: int
    context_signals: tuple[ContextSignal, ...]
    restrictions: tuple[str, ...]
    attestation: str

    def __post_init__(self) -> None:
        for name in ("admission_id", "policy_id", "issuer_id", "tenant_id", "account_id", "insight_id", "receipt_id", "dossier_id", "dossier_fingerprint"):
            require_text(name, getattr(self, name))
        if not all(isinstance(item, int) and not isinstance(item, bool) and item >= 0 for item in (self.admitted_at, self.expires_at)):
            raise PrecisionContractViolation("account context admission times are invalid")
        if self.expires_at < self.admitted_at:
            raise PrecisionContractViolation("account context admission expires before admission")
        if any(signal.insight_id != self.insight_id or signal.target_id != self.account_id or signal.scope != "ACCOUNT" or signal.kind != "HYPOTHESIS" for signal in self.context_signals):
            raise PrecisionContractViolation("account context admission contains an out-of-bound signal")
        object.__setattr__(self, "context_signals", tuple(self.context_signals))
        object.__setattr__(self, "restrictions", tuple(self.restrictions))
        if not isinstance(self.attestation, str) or len(self.attestation) != 64 or any(
            character not in "0123456789abcdef" for character in self.attestation
        ):
            raise PrecisionContractViolation("account context admission attestation is invalid")

    @property
    def attestation_material(self) -> tuple[object, ...]:
        """Stable content bound by the local ingress attestation."""
        return (
            self.admission_id, self.policy_id, self.issuer_id, self.tenant_id,
            self.account_id, self.insight_id, self.receipt_id, self.dossier_id,
            self.dossier_fingerprint, self.admitted_at, self.expires_at,
            self.context_signals, self.restrictions,
        )

    @property
    def output_fingerprint(self) -> str:
        return fingerprint(self.attestation_material)


def admission_attestation(*, admission: AccountContextAdmission, key: bytes) -> str:
    """Return a local HMAC for one exact admission, without exposing key material."""
    if not isinstance(key, bytes) or len(key) < 16:
        raise PrecisionContractViolation("account context attestation key is invalid")
    return hmac.new(key, admission.output_fingerprint.encode("utf-8"), sha256).hexdigest()


@dataclass(frozen=True, slots=True)
class AccountContextAdmissionResult:
    assessment: EngineAssessment
    admission: AccountContextAdmission | None


class AccountContextIngress:
    """Verifies durable research lineage before admitting M05 account context."""

    name = "M05_ACCOUNT_INGRESS"

    def __init__(self, *, policy: AccountContextAdmissionPolicy, knowledge_store: AccountKnowledgeStore,
                 receipt_ledger: ResearchReceiptLedger, attestation_key: bytes) -> None:
        self._policy = policy
        self._knowledge_store = knowledge_store
        self._receipt_ledger = receipt_ledger
        if not isinstance(attestation_key, bytes) or len(attestation_key) < 16:
            raise PrecisionContractViolation("account context attestation key is invalid")
        self._attestation_key = attestation_key

    def admit(self, *, receipt: AccountResearchReceipt, dossier: AccountKnowledgeDossier, insight_id: str, now: int) -> AccountContextAdmissionResult:
        require_text("insight_id", insight_id)
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise PrecisionContractViolation("account context admission requires non-negative logical time")
        if not isinstance(receipt, AccountResearchReceipt) or not isinstance(dossier, AccountKnowledgeDossier):
            raise PrecisionContractViolation("account context admission requires typed receipt and dossier")
        if (
            receipt.tenant_id != dossier.tenant_id or receipt.account_id != dossier.account_id
            or receipt.dossier_id != dossier.dossier_id or receipt.dossier_fingerprint != dossier.output_fingerprint
            or receipt.captured_at != dossier.captured_at or receipt.persisted_at > now or dossier.captured_at > now
            or receipt.expires_at < now or dossier.expires_at < now
        ):
            raise PrecisionContractViolation("receipt and dossier do not form one current account research lineage")
        self._receipt_ledger.assert_current(receipt, now=now)
        durable_snapshot = self._knowledge_store.snapshot(tenant_id=dossier.tenant_id, account_id=dossier.account_id, dossier_id=dossier.dossier_id, now=now)
        if durable_snapshot is None or fingerprint(durable_snapshot) != dossier.output_fingerprint:
            raise PrecisionContractViolation("dossier is absent or differs from durable account memory")
        signals = dossier.to_context_hypotheses(insight_id=insight_id)
        if len(signals) > self._policy.max_context_signals:
            raise PrecisionContractViolation("account context signal count exceeds policy")
        if not signals:
            return AccountContextAdmissionResult(EngineAssessment(self.name, "RETURN_UPSTREAM", ("NO_ADMISSIBLE_OFFICIAL_SITE_OBSERVATIONS",), (), None), None)
        expires_at = min(receipt.expires_at, dossier.expires_at, *(signal.valid_until for signal in signals))
        admission = AccountContextAdmission(
            admission_id="account-context-admission:" + fingerprint((self._policy.policy_id, receipt.receipt_id, dossier.output_fingerprint, insight_id)),
            policy_id=self._policy.policy_id, issuer_id=self._policy.issuer_id,
            tenant_id=dossier.tenant_id, account_id=dossier.account_id,
            insight_id=insight_id, receipt_id=receipt.receipt_id, dossier_id=dossier.dossier_id,
            dossier_fingerprint=dossier.output_fingerprint, admitted_at=now, expires_at=expires_at,
            context_signals=signals,
            restrictions=(
                "ACCOUNT_CONTEXT_ONLY", "OFFICIAL_SITE_DECLARATION_REMAINS_HYPOTHESIS", "NO_FACT_PROMOTION",
                "NO_PERSON_ATTRIBUTE_INFERENCE", "NO_RELEVANCE_OR_DELIVERY_AUTHORITY",
                "REQUIRES_GLOBAL_INDUSTRY_ROLE_AND_MOMENT_CONTEXT_FOR_M05_COMPLETENESS",
            ),
            attestation="0" * 64,
        )
        admission = replace(admission, attestation=admission_attestation(admission=admission, key=self._attestation_key))
        return AccountContextAdmissionResult(
            EngineAssessment(self.name, "PARTIAL", ("ACCOUNT_CONTEXT_ADMITTED_REMAINS_HYPOTHESIS",), tuple(signal.evidence.evidence_id for signal in signals), admission.output_fingerprint),
            admission,
        )
