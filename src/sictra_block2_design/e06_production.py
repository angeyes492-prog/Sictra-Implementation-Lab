"""Deterministic, side-effect-free E06 production adapters."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from html import escape
from typing import Literal

from .e03_design_system import SystemProfileProposal
from .e04_information_design import InformationBlueprint, InformationPayload
from .e05_reference_research import ReferenceResearchProposal


E06Disposition = Literal[
    "PRODUCTION_CANDIDATE_READY_FOR_REVIEW",
    "RETURN_TO_PREVIOUS",
    "QUARANTINE_REFERENCE",
    "UNSUPPORTED_ADAPTER",
    "SCOPE_VIOLATION",
    "UNSUPPORTED_VERSION",
]
_VERSION_PREFIX = "0.1."
_ADAPTERS = {"NEWSLETTER": "HTML_EMAIL", "GRAPHIC": "SVG", "INFOGRAPHIC": "SVG"}


class E06ContractViolation(ValueError):
    """Malformed production requests fail closed."""


def _text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise E06ContractViolation(f"{name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class ProductionContent:
    title: str
    claim_copy: tuple[tuple[str, str], ...]
    accessible_description: str

    def __post_init__(self) -> None:
        _text(self.title, "title")
        _text(self.accessible_description, "accessible_description")
        if not self.claim_copy or any(not claim.strip() or not copy.strip() for claim, copy in self.claim_copy):
            raise E06ContractViolation("claim_copy must contain non-empty claim and copy")
        if len({claim for claim, _ in self.claim_copy}) != len(self.claim_copy):
            raise E06ContractViolation("claim_copy identities must be distinct")


@dataclass(frozen=True, slots=True)
class ProductionRequest:
    candidate_id: str
    contract_version: str
    adapter: str
    envelope_fingerprint: str
    profile_id: str
    blueprint_id: str
    research_pack_id: str
    producer_id: str
    content: ProductionContent
    publish_requested: bool = False
    remote_resource_urls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("candidate_id", self.candidate_id), ("contract_version", self.contract_version),
            ("adapter", self.adapter), ("envelope_fingerprint", self.envelope_fingerprint),
            ("profile_id", self.profile_id), ("blueprint_id", self.blueprint_id),
            ("research_pack_id", self.research_pack_id), ("producer_id", self.producer_id),
        ):
            _text(value, name)
        if not isinstance(self.publish_requested, bool):
            raise E06ContractViolation("publish_requested must be boolean")


@dataclass(frozen=True, slots=True)
class RenderedArtifact:
    media_type: str
    content: bytes
    sha256: str
    accessibility_media_type: str
    accessibility_content: bytes
    accessibility_sha256: str


@dataclass(frozen=True, slots=True)
class ProductionCandidate:
    candidate_id: str
    contract_version: str
    adapter: str
    envelope_fingerprint: str
    profile_id: str
    blueprint_id: str
    research_pack_id: str
    producer_id: str
    claim_ids: tuple[str, ...]
    artifact: RenderedArtifact
    publication_state: str = "NOT_PUBLISHED"


@dataclass(frozen=True, slots=True)
class ProductionAssessment:
    disposition: E06Disposition
    reasons: tuple[str, ...]
    candidate: ProductionCandidate | None

    @property
    def ready_for_review(self) -> bool:
        return self.disposition == "PRODUCTION_CANDIDATE_READY_FOR_REVIEW"


def _artifact(media_type: str, content: str, description: str) -> RenderedArtifact:
    primary = content.encode("utf-8")
    accessible = description.encode("utf-8")
    return RenderedArtifact(
        media_type, primary, sha256(primary).hexdigest(), "text/plain", accessible,
        sha256(accessible).hexdigest(),
    )


def _render_html(content: ProductionContent) -> RenderedArtifact:
    blocks = "".join(
        f'<section data-claim="{escape(claim, quote=True)}"><p>{escape(copy)}</p></section>'
        for claim, copy in content.claim_copy
    )
    markup = (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{escape(content.title)}</title></head><body><main><h1>{escape(content.title)}</h1>'
        f'{blocks}</main></body></html>'
    )
    plain = content.title + "\n\n" + "\n\n".join(copy for _, copy in content.claim_copy) + "\n\n" + content.accessible_description
    return _artifact("text/html", markup, plain)


def _render_svg(content: ProductionContent) -> RenderedArtifact:
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1200" role="img"',
        f' aria-label="{escape(content.accessible_description, quote=True)}">',
        '<rect width="1200" height="1200" fill="#ffffff"/>',
        f'<text x="80" y="120" font-size="54" fill="#111111">{escape(content.title)}</text>',
    ]
    for index, (claim, copy) in enumerate(content.claim_copy, start=1):
        y = 120 + index * 120
        lines.append(f'<g data-claim="{escape(claim, quote=True)}"><text x="80" y="{y}" font-size="32" fill="#222222">{escape(copy)}</text></g>')
    lines.append('</svg>')
    return _artifact("image/svg+xml", "".join(lines), content.accessible_description)


def build_production_candidate(
    profile: SystemProfileProposal,
    blueprint: InformationBlueprint,
    blueprint_disposition: str,
    payload: InformationPayload,
    research: ReferenceResearchProposal,
    research_disposition: str,
    request: ProductionRequest,
) -> ProductionAssessment:
    """Render a bounded candidate in memory; no I/O or publication occurs."""

    if not request.contract_version.startswith(_VERSION_PREFIX):
        return ProductionAssessment("UNSUPPORTED_VERSION", ("CONTRACT_VERSION_UNSUPPORTED",), None)
    expected_adapter = _ADAPTERS.get(blueprint.artifact_type)
    if expected_adapter is None or request.adapter != expected_adapter:
        return ProductionAssessment("UNSUPPORTED_ADAPTER", ("ADAPTER_NOT_CONTRACTED_FOR_ARTIFACT",), None)
    if request.publish_requested or request.remote_resource_urls:
        reasons = []
        if request.publish_requested:
            reasons.append("PUBLICATION_OUT_OF_SCOPE")
        if request.remote_resource_urls:
            reasons.append("REMOTE_RESOURCES_OUT_OF_SCOPE")
        return ProductionAssessment("SCOPE_VIOLATION", tuple(reasons), None)
    lineage: list[str] = []
    if blueprint_disposition != "BLUEPRINT_READY_FOR_PRODUCTION_REVIEW":
        lineage.append("BLUEPRINT_NOT_READY")
    if research_disposition != "RESEARCH_PACK_READY_FOR_PRODUCTION":
        lineage.append("RESEARCH_NOT_READY")
    for label, actual, expected in (
        ("ENVELOPE", request.envelope_fingerprint, blueprint.envelope_fingerprint),
        ("PROFILE", request.profile_id, profile.profile_id),
        ("BLUEPRINT", request.blueprint_id, blueprint.blueprint_id),
        ("RESEARCH", request.research_pack_id, research.pack_id),
    ):
        if actual != expected:
            lineage.append(f"{label}_LINEAGE_MISMATCH")
    if lineage:
        return ProductionAssessment("RETURN_TO_PREVIOUS", tuple(lineage), None)

    payload_claims = {item.claim_id for item in payload.claims}
    content_claims = {claim for claim, _ in request.content.claim_copy}
    approved_copy = set(payload.approved_copy)
    content_failures: list[str] = []
    if content_claims != payload_claims:
        content_failures.append("CLAIM_MAPPING_MUTATED")
    if any(copy not in approved_copy for _, copy in request.content.claim_copy):
        content_failures.append("UNAPPROVED_COPY_PRESENT")
    if content_failures:
        return ProductionAssessment("RETURN_TO_PREVIOUS", tuple(content_failures), None)

    artifact = _render_html(request.content) if request.adapter == "HTML_EMAIL" else _render_svg(request.content)
    candidate = ProductionCandidate(
        request.candidate_id, request.contract_version, request.adapter,
        request.envelope_fingerprint, request.profile_id, request.blueprint_id,
        request.research_pack_id, request.producer_id,
        tuple(claim for claim, _ in request.content.claim_copy), artifact,
    )
    return ProductionAssessment("PRODUCTION_CANDIDATE_READY_FOR_REVIEW", (), candidate)

