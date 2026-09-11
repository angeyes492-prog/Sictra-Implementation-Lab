"""Bounded E05 reference-research validator.

The engine turns governed references into abstract, attributable design
principles.  It neither downloads assets nor grants rights or permission to
imitate a protected identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from .e04_information_design import InformationBlueprint


E05Disposition = Literal[
    "RESEARCH_PACK_READY_FOR_PRODUCTION",
    "RETURN_TO_PREVIOUS",
    "QUARANTINE_REFERENCE",
    "CONTRADICTED",
    "UNSUPPORTED_CHANNEL",
    "UNSUPPORTED_VERSION",
]
_VERSION_PREFIX = "0.1."
_ALLOWED_DECISIONS = frozenset({
    "ALLOW_CONSTRAINT_ONLY", "ALLOW_LICENSED_ASSET", "ALLOW_METADATA_INDEX"
})
_DIMENSIONS = frozenset({
    "HIERARCHY", "RHYTHM", "GRID", "TYPOGRAPHY_ROLE", "DENSITY",
    "CONTRAST", "NARRATIVE", "ACCESSIBILITY", "MOTION", "INTERACTION",
})
_PROTECTED_USES = frozenset({
    "COPY_LOGO", "COPY_EXACT_FONT", "COPY_TRADE_DRESS",
    "COPY_DISTINCTIVE_COMPOSITION", "IMITATE_IDENTIFIABLE_STYLE",
})


class E05ContractViolation(ValueError):
    """Malformed research cannot be classified safely."""


def _text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise E05ContractViolation(f"{name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class GovernedReference:
    reference_id: str
    source_url: str
    asset_type: str
    rights_decision: str
    allowed_channels: tuple[str, ...]
    rights_current: bool
    evidence_ids: tuple[str, ...]
    requested_uses: tuple[str, ...] = ("ABSTRACT_PRINCIPLE",)

    def __post_init__(self) -> None:
        for name, value in (
            ("reference_id", self.reference_id), ("source_url", self.source_url),
            ("asset_type", self.asset_type), ("rights_decision", self.rights_decision),
        ):
            _text(value, name)
        if not isinstance(self.rights_current, bool):
            raise E05ContractViolation("rights_current must be boolean")
        if not self.evidence_ids or any(not item.strip() for item in self.evidence_ids):
            raise E05ContractViolation("reference evidence_ids are required")


@dataclass(frozen=True, slots=True)
class TransferablePrinciple:
    principle_id: str
    reference_id: str
    dimension: str
    observation: str
    abstract_rule: str
    evidence_ids: tuple[str, ...]
    identity_independent: bool

    def __post_init__(self) -> None:
        for name, value in (
            ("principle_id", self.principle_id), ("reference_id", self.reference_id),
            ("dimension", self.dimension), ("observation", self.observation),
            ("abstract_rule", self.abstract_rule),
        ):
            _text(value, name)
        if not isinstance(self.identity_independent, bool):
            raise E05ContractViolation("identity_independent must be boolean")


@dataclass(frozen=True, slots=True)
class ReferenceResearchProposal:
    pack_id: str
    contract_version: str
    blueprint_id: str
    profile_id: str
    envelope_fingerprint: str
    target_channel: str
    references: tuple[GovernedReference, ...]
    principles: tuple[TransferablePrinciple, ...]
    binary_payload_present: bool = False

    def __post_init__(self) -> None:
        for name, value in (
            ("pack_id", self.pack_id), ("contract_version", self.contract_version),
            ("blueprint_id", self.blueprint_id), ("profile_id", self.profile_id),
            ("envelope_fingerprint", self.envelope_fingerprint),
            ("target_channel", self.target_channel),
        ):
            _text(value, name)
        if not isinstance(self.binary_payload_present, bool):
            raise E05ContractViolation("binary_payload_present must be boolean")
        if len({item.reference_id for item in self.references}) != len(self.references):
            raise E05ContractViolation("reference identities must be distinct")
        if len({item.principle_id for item in self.principles}) != len(self.principles):
            raise E05ContractViolation("principle identities must be distinct")


@dataclass(frozen=True, slots=True)
class ReferenceResearchAssessment:
    disposition: E05Disposition
    reasons: tuple[str, ...]
    usable_reference_ids: tuple[str, ...]
    quarantined_reference_ids: tuple[str, ...]
    principle_ids: tuple[str, ...]
    assessed_at: datetime

    @property
    def ready_for_production(self) -> bool:
        return self.disposition == "RESEARCH_PACK_READY_FOR_PRODUCTION"


def assess_reference_research(
    blueprint: InformationBlueprint,
    blueprint_disposition: str,
    proposal: ReferenceResearchProposal,
    now: datetime | None = None,
) -> ReferenceResearchAssessment:
    """Classify reference research while preserving rights and identity limits."""

    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise E05ContractViolation("now must be timezone-aware")

    def result(disposition: E05Disposition, reasons: list[str] | tuple[str, ...], usable=(), quarantined=()):
        return ReferenceResearchAssessment(
            disposition, tuple(reasons), tuple(sorted(usable)), tuple(sorted(quarantined)),
            tuple(item.principle_id for item in proposal.principles), now,
        )

    if not proposal.contract_version.startswith(_VERSION_PREFIX):
        return result("UNSUPPORTED_VERSION", ("CONTRACT_VERSION_UNSUPPORTED",))

    lineage: list[str] = []
    if blueprint_disposition != "BLUEPRINT_READY_FOR_PRODUCTION_REVIEW":
        lineage.append("BLUEPRINT_NOT_READY")
    if proposal.blueprint_id != blueprint.blueprint_id:
        lineage.append("BLUEPRINT_ID_MISMATCH")
    if proposal.profile_id != blueprint.profile_id:
        lineage.append("PROFILE_ID_MISMATCH")
    if proposal.envelope_fingerprint != blueprint.envelope_fingerprint:
        lineage.append("ENVELOPE_FINGERPRINT_MISMATCH")
    if proposal.target_channel != blueprint.channel:
        lineage.append("CHANNEL_MUTATED")
    if lineage:
        return result("RETURN_TO_PREVIOUS", lineage)

    if proposal.binary_payload_present:
        return result("CONTRADICTED", ("BINARY_ASSET_STORAGE_OUT_OF_SCOPE",))
    if not proposal.references:
        return result("RETURN_TO_PREVIOUS", ("REFERENCES_MISSING",))

    usable: set[str] = set()
    quarantined: set[str] = set()
    rights_reasons: list[str] = []
    for reference in proposal.references:
        protected = _PROTECTED_USES.intersection(reference.requested_uses)
        allowed = reference.rights_decision in _ALLOWED_DECISIONS and reference.rights_current
        if reference.rights_decision == "ALLOW_LICENSED_ASSET" and proposal.target_channel not in reference.allowed_channels:
            allowed = False
            rights_reasons.append(f"REFERENCE_{reference.reference_id}_CHANNEL_OUT_OF_SCOPE")
        if protected:
            allowed = False
            rights_reasons.extend(
                f"REFERENCE_{reference.reference_id}_PROTECTED_USE_{item}" for item in sorted(protected)
            )
        if allowed:
            usable.add(reference.reference_id)
        else:
            quarantined.add(reference.reference_id)
            if not protected and not any(reference.reference_id in item for item in rights_reasons):
                rights_reasons.append(f"REFERENCE_{reference.reference_id}_RIGHTS_NOT_USABLE")
    if quarantined:
        return result("QUARANTINE_REFERENCE", rights_reasons, usable, quarantined)

    reference_map = {item.reference_id: item for item in proposal.references}
    principle_failures: list[str] = []
    dimensions: set[str] = set()
    for principle in proposal.principles:
        reference = reference_map.get(principle.reference_id)
        if reference is None:
            principle_failures.append(f"PRINCIPLE_{principle.principle_id}_UNKNOWN_REFERENCE")
            continue
        if principle.dimension not in _DIMENSIONS:
            principle_failures.append(f"PRINCIPLE_{principle.principle_id}_UNKNOWN_DIMENSION")
        else:
            dimensions.add(principle.dimension)
        if not principle.identity_independent:
            principle_failures.append(f"PRINCIPLE_{principle.principle_id}_IDENTITY_DEPENDENT")
        if not principle.evidence_ids or not set(principle.evidence_ids).issubset(reference.evidence_ids):
            principle_failures.append(f"PRINCIPLE_{principle.principle_id}_EVIDENCE_UNBOUND")
    if principle_failures:
        return result("CONTRADICTED", principle_failures, usable)

    coverage: list[str] = []
    if len(proposal.principles) < 4:
        coverage.append("MINIMUM_FOUR_PRINCIPLES_NOT_MET")
    if len(dimensions) < 3:
        coverage.append("MINIMUM_THREE_DIMENSIONS_NOT_MET")
    if coverage:
        return result("RETURN_TO_PREVIOUS", coverage, usable)

    return result("RESEARCH_PACK_READY_FOR_PRODUCTION", (), usable)

