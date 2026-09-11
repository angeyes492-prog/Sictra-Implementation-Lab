"""Bounded E03 Design System contract validator.

The validator checks a proposed system profile.  It does not choose a creative
direction, render components, resolve legal rights, or certify real-world
accessibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from .e02_direction import Direction


E03Disposition = Literal[
    "SYSTEM_PROFILE_READY_FOR_BLUEPRINT",
    "RETURN_TO_PREVIOUS",
    "QUARANTINE_REFERENCE",
    "CONTRADICTED",
    "UNSUPPORTED_CHANNEL",
    "UNSUPPORTED_VERSION",
]
_SUPPORTED_VERSION_PREFIX = "0.1."
_INTERACTIVE_STATES = frozenset({"DEFAULT", "FOCUS", "DISABLED"})
_NON_COLOR_FALLBACKS = frozenset({"TEXT", "LABEL", "PATTERN", "SHAPE", "MONOCHROME"})
_ALLOWED_ASSET_DECISIONS = frozenset({"ALLOW_CONSTRAINT_ONLY", "ALLOW_LICENSED_ASSET"})


class E03ContractViolation(ValueError):
    """A malformed profile cannot be assessed safely."""


def _text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise E03ContractViolation(f"{name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class SelectionRecord:
    direction_id: str
    selector_id: str
    authority_reference: str
    current: bool

    def __post_init__(self) -> None:
        _text(self.direction_id, "direction_id")
        _text(self.selector_id, "selector_id")
        _text(self.authority_reference, "authority_reference")
        if not isinstance(self.current, bool):
            raise E03ContractViolation("selection current flag must be boolean")


@dataclass(frozen=True, slots=True)
class TokenRule:
    token_id: str
    semantic_role: str
    material: bool
    fallback_mode: str

    def __post_init__(self) -> None:
        _text(self.token_id, "token_id")
        _text(self.semantic_role, "semantic_role")
        if not isinstance(self.material, bool):
            raise E03ContractViolation("token material flag must be boolean")


@dataclass(frozen=True, slots=True)
class AssetReference:
    asset_id: str
    asset_type: str
    rights_decision: str
    allowed_channels: tuple[str, ...]
    rights_current: bool

    def __post_init__(self) -> None:
        _text(self.asset_id, "asset_id")
        _text(self.asset_type, "asset_type")
        _text(self.rights_decision, "rights_decision")
        if any(not isinstance(item, str) or not item.strip() for item in self.allowed_channels):
            raise E03ContractViolation("allowed channels must be non-empty strings")
        if not isinstance(self.rights_current, bool):
            raise E03ContractViolation("rights_current must be boolean")


@dataclass(frozen=True, slots=True)
class ComponentRule:
    component_id: str
    interactive: bool
    variants: tuple[str, ...]
    states: tuple[str, ...]
    accessibility_notes: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.component_id, "component_id")
        if not isinstance(self.interactive, bool):
            raise E03ContractViolation("component interactive flag must be boolean")


@dataclass(frozen=True, slots=True)
class ExceptionRule:
    exception_id: str
    owner_id: str
    reviewed_at: datetime
    review_expires_at: datetime
    rollback_profile_id: str

    def __post_init__(self) -> None:
        _text(self.exception_id, "exception_id")
        for name, value in (("reviewed_at", self.reviewed_at), ("review_expires_at", self.review_expires_at)):
            if not isinstance(value, datetime) or value.tzinfo is None:
                raise E03ContractViolation(f"{name} must be timezone-aware datetime")
        if self.review_expires_at <= self.reviewed_at:
            raise E03ContractViolation("review expiry must be after review date")


@dataclass(frozen=True, slots=True)
class SystemProfileProposal:
    profile_id: str
    contract_version: str
    envelope_fingerprint: str
    direction_id: str
    target_channel: str
    supported_channels: tuple[str, ...]
    selection: SelectionRecord
    claim_bindings: tuple[str, ...]
    certainty: str
    contradictions: tuple[str, ...]
    non_claims: tuple[str, ...]
    uncertainty_exposure: tuple[str, ...]
    tokens: tuple[TokenRule, ...]
    assets: tuple[AssetReference, ...]
    components: tuple[ComponentRule, ...]
    exceptions: tuple[ExceptionRule, ...]

    def __post_init__(self) -> None:
        for name, value in (
            ("profile_id", self.profile_id),
            ("contract_version", self.contract_version),
            ("envelope_fingerprint", self.envelope_fingerprint),
            ("direction_id", self.direction_id),
            ("target_channel", self.target_channel),
            ("certainty", self.certainty),
        ):
            _text(value, name)


@dataclass(frozen=True, slots=True)
class SystemProfileAssessment:
    disposition: E03Disposition
    reasons: tuple[str, ...]

    @property
    def ready_for_blueprint(self) -> bool:
        return self.disposition == "SYSTEM_PROFILE_READY_FOR_BLUEPRINT"


def assess_system_profile(
    expected_envelope_fingerprint: str,
    selected_direction: Direction,
    proposal: SystemProfileProposal,
    now: datetime | None = None,
) -> SystemProfileAssessment:
    """Validate professional-system constraints without rendering a design."""

    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise E03ContractViolation("now must be timezone-aware datetime")

    if not proposal.contract_version.startswith(_SUPPORTED_VERSION_PREFIX):
        return SystemProfileAssessment("UNSUPPORTED_VERSION", ("CONTRACT_VERSION_UNSUPPORTED",))

    selection_failures: list[str] = []
    if proposal.envelope_fingerprint != expected_envelope_fingerprint:
        selection_failures.append("ENVELOPE_FINGERPRINT_MISMATCH")
    if proposal.direction_id != selected_direction.direction_id:
        selection_failures.append("DIRECTION_ID_MISMATCH")
    if proposal.selection.direction_id != selected_direction.direction_id:
        selection_failures.append("SELECTION_DIRECTION_MISMATCH")
    if not proposal.selection.current:
        selection_failures.append("SELECTION_NOT_CURRENT")
    if selection_failures:
        return SystemProfileAssessment("RETURN_TO_PREVIOUS", tuple(selection_failures))

    if proposal.target_channel not in proposal.supported_channels:
        return SystemProfileAssessment("UNSUPPORTED_CHANNEL", ("TARGET_CHANNEL_NOT_SUPPORTED",))

    asset_failures = tuple(
        f"ASSET_{asset.asset_id}_NOT_ALLOWED"
        for asset in proposal.assets
        if asset.rights_decision not in _ALLOWED_ASSET_DECISIONS
        or not asset.rights_current
        or proposal.target_channel not in asset.allowed_channels
    )
    if asset_failures:
        return SystemProfileAssessment("QUARANTINE_REFERENCE", asset_failures)

    contradictions = tuple(
        f"TOKEN_{token.token_id}_MISSING_NON_COLOR_FALLBACK"
        for token in proposal.tokens
        if token.material and token.fallback_mode not in _NON_COLOR_FALLBACKS
    )
    if contradictions:
        return SystemProfileAssessment("CONTRADICTED", contradictions)

    failures: list[str] = []
    for label, actual, expected in (
        ("CLAIM_BINDINGS", proposal.claim_bindings, selected_direction.claim_bindings),
        ("CERTAINTY", proposal.certainty, selected_direction.certainty),
        ("CONTRADICTIONS", proposal.contradictions, selected_direction.contradictions),
        ("NON_CLAIMS", proposal.non_claims, selected_direction.non_claims),
        (
            "UNCERTAINTY_EXPOSURE",
            proposal.uncertainty_exposure,
            selected_direction.uncertainty_exposure,
        ),
    ):
        if actual != expected:
            failures.append(f"{label}_MUTATED")
    if not proposal.tokens:
        failures.append("TOKENS_MISSING")
    for component in proposal.components:
        if not component.variants:
            failures.append(f"COMPONENT_{component.component_id}_VARIANTS_MISSING")
        if component.interactive:
            missing = _INTERACTIVE_STATES - set(component.states)
            failures.extend(f"COMPONENT_{component.component_id}_STATE_{state}_MISSING" for state in sorted(missing))
            if not component.accessibility_notes:
                failures.append(f"COMPONENT_{component.component_id}_ACCESSIBILITY_NOTES_MISSING")
    for exception in proposal.exceptions:
        if not exception.owner_id.strip():
            failures.append(f"EXCEPTION_{exception.exception_id}_OWNER_MISSING")
        if exception.reviewed_at > now or exception.review_expires_at <= now:
            failures.append(f"EXCEPTION_{exception.exception_id}_REVIEW_STALE")
        if not exception.rollback_profile_id.strip():
            failures.append(f"EXCEPTION_{exception.exception_id}_ROLLBACK_MISSING")
    if failures:
        return SystemProfileAssessment("RETURN_TO_PREVIOUS", tuple(failures))

    return SystemProfileAssessment("SYSTEM_PROFILE_READY_FOR_BLUEPRINT", ())
