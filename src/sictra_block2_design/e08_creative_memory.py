"""Bounded E08 append-only creative-memory candidate store."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Literal

from .e07_visual_red_team import VisualAssessment


E08Disposition = Literal[
    "MEMORY_CANDIDATE_READY",
    "RETURN_TO_EVALUATION",
    "RETURN_UPSTREAM",
    "QUARANTINE_MEMORY",
    "IDENTITY_COLLISION",
    "UNSUPPORTED_VERSION",
]
_VERSION_PREFIX = "0.1."


class E08ContractViolation(ValueError):
    """Malformed memory proposals cannot enter the store."""


def _text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise E08ContractViolation(f"{name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class ExternalValidationRecord:
    validation_id: str
    reviewer_id: str
    authority_reference: str
    current: bool
    accepted_for_memory: bool
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for name, value in (
            ("validation_id", self.validation_id), ("reviewer_id", self.reviewer_id),
            ("authority_reference", self.authority_reference),
        ):
            _text(value, name)
        if not isinstance(self.current, bool) or not isinstance(self.accepted_for_memory, bool):
            raise E08ContractViolation("validation flags must be boolean")


@dataclass(frozen=True, slots=True)
class MemoryProposal:
    memory_id: str
    contract_version: str
    source_review_id: str
    source_candidate_id: str
    source_generation: int
    eligible_generation: int
    observation: str
    interpretation: str
    hypothesis: str
    evidence_roots: tuple[str, ...]
    promotion_owner_id: str
    rights_current: bool
    privacy_allowed: bool
    expires_at: datetime

    def __post_init__(self) -> None:
        for name, value in (
            ("memory_id", self.memory_id), ("contract_version", self.contract_version),
            ("source_review_id", self.source_review_id),
            ("source_candidate_id", self.source_candidate_id),
            ("observation", self.observation), ("interpretation", self.interpretation),
            ("hypothesis", self.hypothesis), ("promotion_owner_id", self.promotion_owner_id),
        ):
            _text(value, name)
        if not isinstance(self.source_generation, int) or not isinstance(self.eligible_generation, int):
            raise E08ContractViolation("generation fields must be integers")
        if not isinstance(self.expires_at, datetime) or self.expires_at.tzinfo is None:
            raise E08ContractViolation("expires_at must be timezone-aware")
        if not isinstance(self.rights_current, bool) or not isinstance(self.privacy_allowed, bool):
            raise E08ContractViolation("memory governance flags must be boolean")

    @property
    def content_hash(self) -> str:
        material = json.dumps({
            "memory_id": self.memory_id,
            "contract_version": self.contract_version,
            "review": self.source_review_id,
            "candidate": self.source_candidate_id,
            "source_generation": self.source_generation,
            "observation": self.observation,
            "interpretation": self.interpretation,
            "hypothesis": self.hypothesis,
            "evidence": self.evidence_roots,
            "eligible_generation": self.eligible_generation,
            "promotion_owner_id": self.promotion_owner_id,
            "rights_current": self.rights_current,
            "privacy_allowed": self.privacy_allowed,
            "expires_at": self.expires_at.isoformat(),
        }, sort_keys=True, separators=(",", ":"))
        return sha256(material.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class MemoryAssessment:
    disposition: E08Disposition
    reasons: tuple[str, ...]
    memory_id: str
    content_hash: str

    @property
    def ready(self) -> bool:
        return self.disposition == "MEMORY_CANDIDATE_READY"


@dataclass(frozen=True, slots=True)
class StoredMemory:
    proposal: MemoryProposal
    content_hash: str
    state: str = "ACTIVE_CANDIDATE"
    deprecation_reason: str = ""


def assess_memory_candidate(
    visual: VisualAssessment,
    validation: ExternalValidationRecord,
    proposal: MemoryProposal,
    now: datetime | None = None,
) -> MemoryAssessment:
    """Check external validation and anti-loop semantics before storage."""

    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise E08ContractViolation("now must be timezone-aware")
    if not proposal.contract_version.startswith(_VERSION_PREFIX):
        return MemoryAssessment("UNSUPPORTED_VERSION", ("CONTRACT_VERSION_UNSUPPORTED",), proposal.memory_id, proposal.content_hash)
    if not visual.recommended_for_external_review:
        return MemoryAssessment("RETURN_TO_EVALUATION", ("VISUAL_REVIEW_NOT_RECOMMENDED",), proposal.memory_id, proposal.content_hash)
    upstream: list[str] = []
    if proposal.source_review_id != visual.review_id:
        upstream.append("SOURCE_REVIEW_MISMATCH")
    if proposal.source_candidate_id != visual.candidate_id:
        upstream.append("SOURCE_CANDIDATE_MISMATCH")
    if not validation.current:
        upstream.append("VALIDATION_NOT_CURRENT")
    if not validation.accepted_for_memory:
        upstream.append("MEMORY_NOT_EXTERNALLY_AUTHORIZED")
    if not validation.evidence_ids:
        upstream.append("VALIDATION_EVIDENCE_MISSING")
    if upstream:
        return MemoryAssessment("RETURN_UPSTREAM", tuple(upstream), proposal.memory_id, proposal.content_hash)

    quarantine: list[str] = []
    if not proposal.rights_current:
        quarantine.append("RIGHTS_NOT_CURRENT")
    if not proposal.privacy_allowed:
        quarantine.append("PRIVACY_NOT_ALLOWED")
    if proposal.expires_at <= now:
        quarantine.append("MEMORY_EXPIRED")
    if len(set(proposal.evidence_roots)) < 2:
        quarantine.append("INDEPENDENT_EVIDENCE_ROOTS_INSUFFICIENT")
    if proposal.eligible_generation <= proposal.source_generation:
        quarantine.append("SAME_GENERATION_FEEDBACK_FORBIDDEN")
    if quarantine:
        return MemoryAssessment("QUARANTINE_MEMORY", tuple(quarantine), proposal.memory_id, proposal.content_hash)
    return MemoryAssessment("MEMORY_CANDIDATE_READY", (), proposal.memory_id, proposal.content_hash)


class CreativeMemoryStore:
    """In-memory append-only reference store with collision and deprecation controls."""

    def __init__(self) -> None:
        self._records: dict[str, StoredMemory] = {}

    def write(self, assessment: MemoryAssessment, proposal: MemoryProposal) -> tuple[str, StoredMemory | None]:
        if not assessment.ready or assessment.memory_id != proposal.memory_id or assessment.content_hash != proposal.content_hash:
            return "REJECTED", None
        existing = self._records.get(proposal.memory_id)
        if existing is not None:
            if existing.content_hash == proposal.content_hash:
                return "IDEMPOTENT", existing
            return "IDENTITY_COLLISION", existing
        stored = StoredMemory(proposal, proposal.content_hash)
        self._records[proposal.memory_id] = stored
        return "STORED", stored

    def deprecate(self, memory_id: str, reason: str, *, at: datetime | None = None) -> StoredMemory:
        _text(reason, "reason")
        current = self._records[memory_id]
        updated = replace(current, state="DEPRECATED", deprecation_reason=reason)
        self._records[memory_id] = updated
        return updated

    def get(self, memory_id: str) -> StoredMemory | None:
        return self._records.get(memory_id)
