"""Immutable review records for source candidates; never gateway activation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .common import ContractViolation
from .source_portfolio import SourceCandidate
from .source_primitives import normalized_dns_host as _host, required_text as _required_text


APPROVAL_VERSION = "0.1.0"
MANUAL_SOURCE_BUNDLE = "MANUAL_SOURCE_BUNDLE"
DECISIONS = frozenset(("APPROVED", "REJECTED"))


def _claims(values: Iterable[str]) -> frozenset[str]:
    try:
        normalized = frozenset(_required_text("approved_claim_key", value) for value in values)
    except TypeError as error:
        raise ContractViolation("approved_claim_keys must be iterable") from error
    if not normalized:
        raise ContractViolation("at least one approved claim is required")
    return normalized


@dataclass(frozen=True, slots=True)
class SourceApprovalRecord:
    source_id: str
    reviewer_id: str
    reviewed_at: int
    terms_evidence_ref: str
    approved_hosts: tuple[str, ...]
    approved_claim_keys: frozenset[str]
    max_content_bytes: int
    access_method: str
    decision: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _required_text("source_id", self.source_id))
        object.__setattr__(self, "reviewer_id", _required_text("reviewer_id", self.reviewer_id))
        object.__setattr__(self, "terms_evidence_ref", _required_text("terms_evidence_ref", self.terms_evidence_ref))
        if not isinstance(self.reviewed_at, int) or isinstance(self.reviewed_at, bool) or self.reviewed_at < 0:
            raise ContractViolation("reviewed_at must be a non-negative integer")
        hosts = tuple(sorted({_host(host) for host in self.approved_hosts}))
        if not hosts:
            raise ContractViolation("at least one approved host is required")
        object.__setattr__(self, "approved_hosts", hosts)
        object.__setattr__(self, "approved_claim_keys", _claims(self.approved_claim_keys))
        if not isinstance(self.max_content_bytes, int) or isinstance(self.max_content_bytes, bool) or self.max_content_bytes < 1:
            raise ContractViolation("max_content_bytes must be a positive integer")
        if self.access_method != MANUAL_SOURCE_BUNDLE:
            raise ContractViolation("source approval access method is unsupported")
        if self.decision not in DECISIONS:
            raise ContractViolation("source approval decision is unsupported")

    def readiness_for(self, candidate: SourceCandidate, *, now: int) -> dict[str, object]:
        if not isinstance(candidate, SourceCandidate):
            raise ContractViolation("source approval requires a SourceCandidate")
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise ContractViolation("approval now must be a non-negative integer")
        if self.reviewed_at > now:
            raise ContractViolation("source approval reviewed_at must not be future")
        if candidate.source_id != self.source_id:
            raise ContractViolation("source approval does not match candidate")
        if candidate.status != "PROPOSED":
            raise ContractViolation("source candidate must remain PROPOSED")
        if not set(self.approved_hosts) <= set(candidate.candidate_hosts):
            raise ContractViolation("source approval expands candidate host allowlist")
        status = "READY_FOR_GATEWAY_CONFIGURATION_REVIEW" if self.decision == "APPROVED" else "NOT_APPROVED"
        return {
            "approval_version": APPROVAL_VERSION,
            "source_id": self.source_id,
            "reviewer_id": self.reviewer_id,
            "reviewed_at": self.reviewed_at,
            "terms_evidence_ref": self.terms_evidence_ref,
            "approved_hosts": list(self.approved_hosts),
            "approved_claim_keys": sorted(self.approved_claim_keys),
            "max_content_bytes": self.max_content_bytes,
            "access_method": self.access_method,
            "decision": self.decision,
            "status": status,
            "candidate_status": candidate.status,
        }
