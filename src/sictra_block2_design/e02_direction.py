"""Bounded E02 Creative Direction contract validator.

This module validates a *proposed* synthetic direction set.  It intentionally
does not generate creative directions, select a winner, render assets, change
upstream claims, or write creative memory.  Its output is a local contract
classification only.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Literal


E02Disposition = Literal[
    "DIRECTION_SET_READY_FOR_SELECTION",
    "RETURN_UPSTREAM",
    "RETURN_TO_PREVIOUS",
    "QUARANTINE_REFERENCE",
    "UNSUPPORTED_CHANNEL",
]
_AXES = (
    "visual_metaphor",
    "information_architecture",
    "encoding",
    "reading_sequence",
    "interaction_or_motion",
)


class E02ContractViolation(ValueError):
    """A malformed candidate cannot be classified safely."""


def _required_ids(values: tuple[str, ...], label: str) -> None:
    if not values or any(not isinstance(value, str) or not value.strip() for value in values):
        raise E02ContractViolation(f"{label} must contain non-empty identifiers")


def _required_text(**fields: str) -> None:
    missing = [name for name, value in fields.items() if not isinstance(value, str) or not value.strip()]
    if missing:
        raise E02ContractViolation(f"missing required fields: {', '.join(missing)}")


@dataclass(frozen=True, slots=True)
class E02Envelope:
    """Minimal, already-validated view of the Design Context Envelope."""

    message_id: str
    fingerprint: str
    disposition: str
    temporal_state: str
    references_allowed: bool
    channel_supported: bool
    quarantined_reference_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _required_text(message_id=self.message_id, fingerprint=self.fingerprint)
        if not isinstance(self.references_allowed, bool) or not isinstance(self.channel_supported, bool):
            raise E02ContractViolation("envelope flags must be boolean")
        if any(not isinstance(value, str) or not value.strip() for value in self.quarantined_reference_ids):
            raise E02ContractViolation("quarantined references must be non-empty identifiers")


@dataclass(frozen=True, slots=True)
class VisualThesis:
    thesis_id: str
    claim_bindings: tuple[str, ...]
    certainty: str
    contradictions: tuple[str, ...]
    non_claims: tuple[str, ...]
    uncertainty_exposure: tuple[str, ...]

    def __post_init__(self) -> None:
        _required_text(thesis_id=self.thesis_id, certainty=self.certainty)
        _required_ids(self.claim_bindings, "claim_bindings")


@dataclass(frozen=True, slots=True)
class Direction:
    """A proposal whose five structural axes can be compared directly."""

    direction_id: str
    visual_metaphor: str
    information_architecture: str
    encoding: str
    reading_sequence: str
    interaction_or_motion: str
    claim_bindings: tuple[str, ...]
    certainty: str
    contradictions: tuple[str, ...]
    non_claims: tuple[str, ...]
    uncertainty_exposure: tuple[str, ...]
    reference_ids: tuple[str, ...] = ()
    prohibited_adaptations: tuple[str, ...] = ()
    cosmetic_treatment: str = ""

    def __post_init__(self) -> None:
        _required_text(
            direction_id=self.direction_id,
            visual_metaphor=self.visual_metaphor,
            information_architecture=self.information_architecture,
            encoding=self.encoding,
            reading_sequence=self.reading_sequence,
            interaction_or_motion=self.interaction_or_motion,
            certainty=self.certainty,
        )
        _required_ids(self.claim_bindings, "claim_bindings")
        for label, values in (
            ("reference_ids", self.reference_ids),
            ("prohibited_adaptations", self.prohibited_adaptations),
        ):
            if any(not isinstance(value, str) or not value.strip() for value in values):
                raise E02ContractViolation(f"{label} must contain non-empty identifiers")

    def axis_values(self) -> tuple[str, ...]:
        return tuple(getattr(self, axis) for axis in _AXES)


@dataclass(frozen=True, slots=True)
class DirectionSet:
    direction_set_id: str
    parent_thesis_id: str
    envelope_fingerprint: str
    directions: tuple[Direction, ...]
    selected_direction_id: str | None = None

    def __post_init__(self) -> None:
        _required_text(
            direction_set_id=self.direction_set_id,
            parent_thesis_id=self.parent_thesis_id,
            envelope_fingerprint=self.envelope_fingerprint,
        )
        if len({item.direction_id for item in self.directions}) != len(self.directions):
            raise E02ContractViolation("direction identities must be distinct")


@dataclass(frozen=True, slots=True)
class DirectionAssessment:
    disposition: E02Disposition
    reasons: tuple[str, ...]
    material_differences: tuple[tuple[str, str, tuple[str, ...]], ...]

    @property
    def ready_for_selection(self) -> bool:
        return self.disposition == "DIRECTION_SET_READY_FOR_SELECTION"


def _material_axes(left: Direction, right: Direction) -> tuple[str, ...]:
    return tuple(axis for axis in _AXES if getattr(left, axis) != getattr(right, axis))


def _preservation_failures(thesis: VisualThesis, direction: Direction) -> tuple[str, ...]:
    checks = (
        ("CLAIM_BINDINGS", direction.claim_bindings, thesis.claim_bindings),
        ("CERTAINTY", direction.certainty, thesis.certainty),
        ("CONTRADICTIONS", direction.contradictions, thesis.contradictions),
        ("NON_CLAIMS", direction.non_claims, thesis.non_claims),
        ("UNCERTAINTY_EXPOSURE", direction.uncertainty_exposure, thesis.uncertainty_exposure),
    )
    return tuple(f"{direction.direction_id}_{name}_MUTATED" for name, actual, expected in checks if actual != expected)


def assess_direction_set(
    envelope: E02Envelope,
    thesis: VisualThesis,
    proposed: DirectionSet,
) -> DirectionAssessment:
    """Classify a proposed E02 set without generating or selecting a direction.

    Upstream insufficiency has precedence.  All later failures are aggregated so
    the producer can repair one candidate set rather than retrying around a
    hidden failure.
    """

    upstream_reasons: list[str] = []
    if envelope.disposition != "CONTINUE":
        upstream_reasons.append("ENVELOPE_NOT_CONTINUE")
    if envelope.temporal_state != "CURRENT":
        upstream_reasons.append("ENVELOPE_NOT_CURRENT")
    if proposed.envelope_fingerprint != envelope.fingerprint:
        upstream_reasons.append("ENVELOPE_FINGERPRINT_MISMATCH")
    if proposed.parent_thesis_id != thesis.thesis_id:
        upstream_reasons.append("PARENT_THESIS_MISMATCH")
    if upstream_reasons:
        return DirectionAssessment("RETURN_UPSTREAM", tuple(upstream_reasons), ())

    if not envelope.references_allowed:
        return DirectionAssessment("QUARANTINE_REFERENCE", ("REFERENCES_NOT_ALLOWED",), ())
    if not envelope.channel_supported:
        return DirectionAssessment("UNSUPPORTED_CHANNEL", ("CHANNEL_UNSUPPORTED",), ())

    failures: list[str] = []
    if not thesis.claim_bindings:
        failures.append("THESIS_CLAIM_BINDINGS_MISSING")
    if proposed.selected_direction_id is not None:
        failures.append("SELECTION_OUTSIDE_E02_SCOPE")
    if not 2 <= len(proposed.directions) <= 3:
        failures.append("DIRECTION_COUNT_OUT_OF_RANGE")

    quarantined = set(envelope.quarantined_reference_ids)
    reference_failures: list[str] = []
    for direction in proposed.directions:
        failures.extend(_preservation_failures(thesis, direction))
        failures.extend(f"{direction.direction_id}_PROHIBITED_ADAPTATION_{item}" for item in direction.prohibited_adaptations)
        reference_failures.extend(
            f"{direction.direction_id}_QUARANTINED_REFERENCE_{item}"
            for item in direction.reference_ids
            if item in quarantined
        )
    if reference_failures:
        return DirectionAssessment("QUARANTINE_REFERENCE", tuple(reference_failures), ())

    material_differences = tuple(
        (left.direction_id, right.direction_id, _material_axes(left, right))
        for left, right in combinations(proposed.directions, 2)
    )
    failures.extend(
        f"INSUFFICIENT_DIVERGENCE_{left}_{right}"
        for left, right, axes in material_differences
        if len(axes) < 2
    )
    if failures:
        return DirectionAssessment("RETURN_TO_PREVIOUS", tuple(failures), material_differences)

    return DirectionAssessment("DIRECTION_SET_READY_FOR_SELECTION", (), material_differences)

