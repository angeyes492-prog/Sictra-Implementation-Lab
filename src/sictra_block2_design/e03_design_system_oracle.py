"""Declarative differential oracle for the bounded E03 profile validator."""

from __future__ import annotations

from datetime import datetime, timezone

from .e02_direction import Direction
from .e03_design_system import SystemProfileAssessment, SystemProfileProposal


def expected_system_profile(
    expected_fingerprint: str,
    selected: Direction,
    proposal: SystemProfileProposal,
    now: datetime | None = None,
) -> SystemProfileAssessment:
    now = now or datetime.now(timezone.utc)
    if not proposal.contract_version.startswith("0.1."):
        return SystemProfileAssessment("UNSUPPORTED_VERSION", ("CONTRACT_VERSION_UNSUPPORTED",))
    reasons = tuple(
        label for label, failed in (
            ("ENVELOPE_FINGERPRINT_MISMATCH", proposal.envelope_fingerprint != expected_fingerprint),
            ("DIRECTION_ID_MISMATCH", proposal.direction_id != selected.direction_id),
            ("SELECTION_DIRECTION_MISMATCH", proposal.selection.direction_id != selected.direction_id),
            ("SELECTION_NOT_CURRENT", not proposal.selection.current),
        ) if failed
    )
    if reasons:
        return SystemProfileAssessment("RETURN_TO_PREVIOUS", reasons)
    if proposal.target_channel not in proposal.supported_channels:
        return SystemProfileAssessment("UNSUPPORTED_CHANNEL", ("TARGET_CHANNEL_NOT_SUPPORTED",))
    asset_reasons = tuple(
        f"ASSET_{item.asset_id}_NOT_ALLOWED" for item in proposal.assets
        if item.rights_decision not in {"ALLOW_CONSTRAINT_ONLY", "ALLOW_LICENSED_ASSET"}
        or not item.rights_current
        or proposal.target_channel not in item.allowed_channels
    )
    if asset_reasons:
        return SystemProfileAssessment("QUARANTINE_REFERENCE", asset_reasons)
    token_reasons = tuple(
        f"TOKEN_{item.token_id}_MISSING_NON_COLOR_FALLBACK" for item in proposal.tokens
        if item.material and item.fallback_mode not in {"TEXT", "LABEL", "PATTERN", "SHAPE", "MONOCHROME"}
    )
    if token_reasons:
        return SystemProfileAssessment("CONTRADICTED", token_reasons)
    failures = []
    for name, actual, expected in (
        ("CLAIM_BINDINGS", proposal.claim_bindings, selected.claim_bindings),
        ("CERTAINTY", proposal.certainty, selected.certainty),
        ("CONTRADICTIONS", proposal.contradictions, selected.contradictions),
        ("NON_CLAIMS", proposal.non_claims, selected.non_claims),
        (
            "UNCERTAINTY_EXPOSURE",
            proposal.uncertainty_exposure,
            selected.uncertainty_exposure,
        ),
    ):
        if actual != expected:
            failures.append(f"{name}_MUTATED")
    if len(proposal.tokens) == 0:
        failures.append("TOKENS_MISSING")
    required_states = {"DEFAULT", "FOCUS", "DISABLED"}
    for component in proposal.components:
        if len(component.variants) == 0:
            failures.append(f"COMPONENT_{component.component_id}_VARIANTS_MISSING")
        if component.interactive:
            for state in sorted(required_states - set(component.states)):
                failures.append(f"COMPONENT_{component.component_id}_STATE_{state}_MISSING")
            if len(component.accessibility_notes) == 0:
                failures.append(f"COMPONENT_{component.component_id}_ACCESSIBILITY_NOTES_MISSING")
    for exception in proposal.exceptions:
        if exception.owner_id.strip() == "":
            failures.append(f"EXCEPTION_{exception.exception_id}_OWNER_MISSING")
        if exception.reviewed_at > now or exception.review_expires_at <= now:
            failures.append(f"EXCEPTION_{exception.exception_id}_REVIEW_STALE")
        if exception.rollback_profile_id.strip() == "":
            failures.append(f"EXCEPTION_{exception.exception_id}_ROLLBACK_MISSING")
    if failures:
        return SystemProfileAssessment("RETURN_TO_PREVIOUS", tuple(failures))
    return SystemProfileAssessment("SYSTEM_PROFILE_READY_FOR_BLUEPRINT", ())
