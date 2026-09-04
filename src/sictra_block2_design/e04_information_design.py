"""Bounded E04 information-design validator.

E04 turns an approved payload and an E03 system profile into a composition
blueprint.  It never renders, serializes, publishes, or invents content.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .e03_design_system import SystemProfileProposal


E04Disposition = Literal[
    "BLUEPRINT_READY_FOR_PRODUCTION_REVIEW",
    "RETURN_UPSTREAM",
    "RETURN_TO_PREVIOUS",
    "UNSUPPORTED_CHANNEL",
    "CONTRADICTED",
    "SCOPE_VIOLATION",
    "UNSUPPORTED_VERSION",
]
_SUPPORTED_VERSION_PREFIX = "0.1."
_READY_PROFILE = "SYSTEM_PROFILE_READY_FOR_BLUEPRINT"
_CHARTS_BY_RELATIONSHIP = {
    "TREND": frozenset({"LINE"}),
    "COMPARISON": frozenset({"BAR", "HORIZONTAL_BAR", "DOT"}),
    "RANKING": frozenset({"HORIZONTAL_BAR", "DOT"}),
    "PART_TO_WHOLE": frozenset({"STACKED_BAR", "PIE"}),
    "DISTRIBUTION": frozenset({"HISTOGRAM", "BOX", "VIOLIN", "STRIP"}),
    "CORRELATION": frozenset({"SCATTER"}),
    "FLOW": frozenset({"SANKEY", "FUNNEL"}),
    "NETWORK": frozenset({"NETWORK"}),
    "PERFORMANCE_TARGET": frozenset({"BULLET"}),
    "MULTI_KPI": frozenset({"SMALL_MULTIPLES"}),
    "GEOGRAPHIC": frozenset({"CHOROPLETH", "BUBBLE_MAP", "HEX_MAP"}),
}
_BAR_CHARTS = frozenset({"BAR", "HORIZONTAL_BAR"})
_FALLBACKS_BY_ARTIFACT = {
    "NEWSLETTER": frozenset({"PLAIN_TEXT"}),
    "MULTIMEDIA": frozenset({"TRANSCRIPT", "MATERIAL_DESCRIPTION"}),
    "VIDEO": frozenset({"TRANSCRIPT", "MATERIAL_DESCRIPTION"}),
    "GRAPHIC": frozenset({"ALT_TEXT", "LEGEND"}),
    "INFOGRAPHIC": frozenset({"ALT_TEXT", "LEGEND"}),
}


class E04ContractViolation(ValueError):
    """A malformed blueprint cannot be assessed safely."""


def _text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise E04ContractViolation(f"{name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class PayloadClaim:
    claim_id: str
    evidence_refs: tuple[str, ...]
    attribution_ids: tuple[str, ...]
    limitation_ids: tuple[str, ...]
    relationship: str
    uncertainty_required: bool
    unit: str
    polarity: str

    def __post_init__(self) -> None:
        for name, value in (
            ("claim_id", self.claim_id),
            ("relationship", self.relationship),
            ("unit", self.unit),
            ("polarity", self.polarity),
        ):
            _text(value, name)
        if not isinstance(self.uncertainty_required, bool):
            raise E04ContractViolation("uncertainty_required must be boolean")


@dataclass(frozen=True, slots=True)
class InformationPayload:
    payload_id: str
    contract_version: str
    claims: tuple[PayloadClaim, ...]
    approved_copy: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.payload_id, "payload_id")
        _text(self.contract_version, "contract_version")


@dataclass(frozen=True, slots=True)
class ChannelTarget:
    artifact_type: str
    channel: str
    audience_path: str

    def __post_init__(self) -> None:
        _text(self.artifact_type, "artifact_type")
        _text(self.channel, "channel")
        _text(self.audience_path, "audience_path")


@dataclass(frozen=True, slots=True)
class BlueprintElement:
    element_id: str
    element_type: str
    claim_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    limitation_ids: tuple[str, ...]
    decorative: bool

    def __post_init__(self) -> None:
        _text(self.element_id, "element_id")
        _text(self.element_type, "element_type")
        if not isinstance(self.decorative, bool):
            raise E04ContractViolation("decorative must be boolean")


@dataclass(frozen=True, slots=True)
class EncodingPlan:
    encoding_id: str
    claim_id: str
    relationship: str
    chart_type: str
    unit: str
    polarity: str
    attribution_ids: tuple[str, ...]
    baseline_at_zero: bool
    uncertainty_visible: bool
    series_count: int
    color_only: bool
    is_3d: bool
    dual_axis: bool

    def __post_init__(self) -> None:
        for name, value in (
            ("encoding_id", self.encoding_id),
            ("claim_id", self.claim_id),
            ("relationship", self.relationship),
            ("chart_type", self.chart_type),
            ("unit", self.unit),
            ("polarity", self.polarity),
        ):
            _text(value, name)
        if not isinstance(self.series_count, int) or self.series_count < 1:
            raise E04ContractViolation("series_count must be a positive integer")


@dataclass(frozen=True, slots=True)
class InformationBlueprint:
    blueprint_id: str
    contract_version: str
    profile_id: str
    envelope_fingerprint: str
    artifact_type: str
    channel: str
    audience_path: str
    reading_order: tuple[str, ...]
    elements: tuple[BlueprintElement, ...]
    encodings: tuple[EncodingPlan, ...]
    accessibility_fallbacks: tuple[str, ...]
    executable_artifacts: tuple[str, ...]
    publication_state: str

    def __post_init__(self) -> None:
        for name, value in (
            ("blueprint_id", self.blueprint_id),
            ("contract_version", self.contract_version),
            ("profile_id", self.profile_id),
            ("envelope_fingerprint", self.envelope_fingerprint),
            ("artifact_type", self.artifact_type),
            ("channel", self.channel),
            ("audience_path", self.audience_path),
            ("publication_state", self.publication_state),
        ):
            _text(value, name)


@dataclass(frozen=True, slots=True)
class InformationBlueprintAssessment:
    disposition: E04Disposition
    reasons: tuple[str, ...]

    @property
    def ready_for_production_review(self) -> bool:
        return self.disposition == "BLUEPRINT_READY_FOR_PRODUCTION_REVIEW"


def assess_information_blueprint(
    expected_envelope_fingerprint: str,
    profile: SystemProfileProposal,
    profile_disposition: str,
    payload: InformationPayload,
    target: ChannelTarget,
    blueprint: InformationBlueprint,
) -> InformationBlueprintAssessment:
    """Assess traceability and visual-encoding integrity without production."""

    if not payload.contract_version.startswith(_SUPPORTED_VERSION_PREFIX) or not blueprint.contract_version.startswith(
        _SUPPORTED_VERSION_PREFIX
    ):
        return InformationBlueprintAssessment("UNSUPPORTED_VERSION", ("CONTRACT_VERSION_UNSUPPORTED",))

    lineage_failures: list[str] = []
    if profile_disposition != _READY_PROFILE:
        lineage_failures.append("PROFILE_NOT_READY")
    if profile.profile_id != blueprint.profile_id:
        lineage_failures.append("PROFILE_ID_MISMATCH")
    if expected_envelope_fingerprint != profile.envelope_fingerprint or expected_envelope_fingerprint != blueprint.envelope_fingerprint:
        lineage_failures.append("ENVELOPE_FINGERPRINT_MISMATCH")
    if target.channel != blueprint.channel or target.artifact_type != blueprint.artifact_type or target.audience_path != blueprint.audience_path:
        lineage_failures.append("CHANNEL_TARGET_MUTATED")
    if lineage_failures:
        return InformationBlueprintAssessment("RETURN_TO_PREVIOUS", tuple(lineage_failures))

    if target.channel not in profile.supported_channels:
        return InformationBlueprintAssessment("UNSUPPORTED_CHANNEL", ("CHANNEL_NOT_SUPPORTED_BY_PROFILE",))

    upstream_failures: list[str] = []
    if not payload.claims:
        upstream_failures.append("CLAIMS_MISSING")
    if not payload.approved_copy:
        upstream_failures.append("APPROVED_COPY_MISSING")
    claim_ids = [claim.claim_id for claim in payload.claims]
    if len(set(claim_ids)) != len(claim_ids):
        upstream_failures.append("DUPLICATE_CLAIM_ID")
    for claim in payload.claims:
        if not claim.evidence_refs:
            upstream_failures.append(f"CLAIM_{claim.claim_id}_EVIDENCE_MISSING")
        if not claim.attribution_ids:
            upstream_failures.append(f"CLAIM_{claim.claim_id}_ATTRIBUTION_MISSING")
    if upstream_failures:
        return InformationBlueprintAssessment("RETURN_UPSTREAM", tuple(upstream_failures))

    if blueprint.executable_artifacts or blueprint.publication_state != "NOT_PUBLISHED":
        reasons = []
        if blueprint.executable_artifacts:
            reasons.append("EXECUTABLE_ARTIFACT_PRESENT")
        if blueprint.publication_state != "NOT_PUBLISHED":
            reasons.append("PUBLICATION_STATE_OUT_OF_SCOPE")
        return InformationBlueprintAssessment("SCOPE_VIOLATION", tuple(reasons))

    required_fallbacks = _FALLBACKS_BY_ARTIFACT.get(target.artifact_type)
    if required_fallbacks is None:
        return InformationBlueprintAssessment("UNSUPPORTED_CHANNEL", ("ARTIFACT_TYPE_NOT_CONTRACTED",))
    missing_fallbacks = required_fallbacks - set(blueprint.accessibility_fallbacks)
    if missing_fallbacks:
        return InformationBlueprintAssessment(
            "UNSUPPORTED_CHANNEL",
            tuple(f"FALLBACK_{item}_MISSING" for item in sorted(missing_fallbacks)),
        )

    claims = {claim.claim_id: claim for claim in payload.claims}
    failures: list[str] = []
    covered_claims: set[str] = set()
    element_ids = {element.element_id for element in blueprint.elements}
    if len(element_ids) != len(blueprint.elements):
        failures.append("DUPLICATE_ELEMENT_ID")
    if set(blueprint.reading_order) != element_ids or len(blueprint.reading_order) != len(element_ids):
        failures.append("READING_ORDER_INCOMPLETE_OR_DUPLICATED")
    for element in blueprint.elements:
        if element.decorative and (element.claim_ids or element.evidence_refs or element.limitation_ids):
            failures.append(f"ELEMENT_{element.element_id}_DECORATIVE_AS_EVIDENCE")
        if not element.decorative and not element.claim_ids:
            failures.append(f"ELEMENT_{element.element_id}_CLAIM_MAP_MISSING")
        for claim_id in element.claim_ids:
            claim = claims.get(claim_id)
            if claim is None:
                failures.append(f"ELEMENT_{element.element_id}_UNKNOWN_CLAIM")
                continue
            covered_claims.add(claim_id)
            if not set(element.evidence_refs).issubset(claim.evidence_refs):
                failures.append(f"ELEMENT_{element.element_id}_EVIDENCE_MUTATED")
            if element.element_type == "CTA" and not set(claim.limitation_ids).issubset(element.limitation_ids):
                failures.append(f"ELEMENT_{element.element_id}_CTA_LIMITATION_MISSING")
    for claim_id in sorted(set(claims) - covered_claims):
        failures.append(f"CLAIM_{claim_id}_NOT_MAPPED")
    if failures:
        return InformationBlueprintAssessment("RETURN_TO_PREVIOUS", tuple(failures))

    encoding_failures: list[str] = []
    encoding_ids = [encoding.encoding_id for encoding in blueprint.encodings]
    if len(set(encoding_ids)) != len(encoding_ids):
        encoding_failures.append("DUPLICATE_ENCODING_ID")
    for encoding in blueprint.encodings:
        claim = claims.get(encoding.claim_id)
        if claim is None:
            encoding_failures.append(f"ENCODING_{encoding.encoding_id}_UNKNOWN_CLAIM")
            continue
        if encoding.relationship != claim.relationship:
            encoding_failures.append(f"ENCODING_{encoding.encoding_id}_RELATIONSHIP_MUTATED")
        if encoding.unit != claim.unit or encoding.polarity != claim.polarity:
            encoding_failures.append(f"ENCODING_{encoding.encoding_id}_MEANING_MUTATED")
        if not set(claim.attribution_ids).issubset(encoding.attribution_ids):
            encoding_failures.append(f"ENCODING_{encoding.encoding_id}_ATTRIBUTION_MISSING")
        if encoding.chart_type not in _CHARTS_BY_RELATIONSHIP.get(claim.relationship, frozenset()):
            encoding_failures.append(f"ENCODING_{encoding.encoding_id}_CHART_RELATIONSHIP_MISMATCH")
        if encoding.is_3d:
            encoding_failures.append(f"ENCODING_{encoding.encoding_id}_THREE_D_FORBIDDEN")
        if encoding.dual_axis:
            encoding_failures.append(f"ENCODING_{encoding.encoding_id}_DUAL_AXIS_FORBIDDEN")
        if encoding.color_only:
            encoding_failures.append(f"ENCODING_{encoding.encoding_id}_COLOR_ONLY")
        if encoding.chart_type in _BAR_CHARTS and not encoding.baseline_at_zero:
            encoding_failures.append(f"ENCODING_{encoding.encoding_id}_ZERO_BASELINE_MISSING")
        if encoding.chart_type == "PIE" and encoding.series_count > 5:
            encoding_failures.append(f"ENCODING_{encoding.encoding_id}_PIE_TOO_MANY_SERIES")
        if claim.uncertainty_required and not encoding.uncertainty_visible:
            encoding_failures.append(f"ENCODING_{encoding.encoding_id}_UNCERTAINTY_HIDDEN")
    if encoding_failures:
        return InformationBlueprintAssessment("CONTRADICTED", tuple(encoding_failures))

    return InformationBlueprintAssessment("BLUEPRINT_READY_FOR_PRODUCTION_REVIEW", ())
