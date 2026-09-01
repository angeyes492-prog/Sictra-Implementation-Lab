"""Independent declarative oracle for the bounded E02 DirectionSet contract.

The oracle does not import or call ``assess_direction_set`` or its helpers.
It validates serialized proposal fields directly for differential tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from .e02_direction import DirectionSet, E02Envelope, VisualThesis


@dataclass(frozen=True, slots=True)
class ExpectedDirectionAssessment:
    disposition: str
    reasons: tuple[str, ...]
    material_differences: tuple[tuple[str, str, tuple[str, ...]], ...]


def expected_direction_assessment(
    envelope: E02Envelope,
    thesis: VisualThesis,
    proposed: DirectionSet,
) -> ExpectedDirectionAssessment:
    if envelope.disposition != "CONTINUE" or envelope.temporal_state != "CURRENT":
        reasons = tuple(
            name for name, condition in (
                ("ENVELOPE_NOT_CONTINUE", envelope.disposition != "CONTINUE"),
                ("ENVELOPE_NOT_CURRENT", envelope.temporal_state != "CURRENT"),
            ) if condition
        )
        return ExpectedDirectionAssessment("RETURN_UPSTREAM", reasons, ())
    lineage = tuple(
        name for name, condition in (
            ("ENVELOPE_FINGERPRINT_MISMATCH", proposed.envelope_fingerprint != envelope.fingerprint),
            ("PARENT_THESIS_MISMATCH", proposed.parent_thesis_id != thesis.thesis_id),
        ) if condition
    )
    if lineage:
        return ExpectedDirectionAssessment("RETURN_UPSTREAM", lineage, ())
    if not envelope.references_allowed:
        return ExpectedDirectionAssessment("QUARANTINE_REFERENCE", ("REFERENCES_NOT_ALLOWED",), ())
    if not envelope.channel_supported:
        return ExpectedDirectionAssessment("UNSUPPORTED_CHANNEL", ("CHANNEL_UNSUPPORTED",), ())

    failures: list[str] = []
    if not thesis.claim_bindings:
        failures.append("THESIS_CLAIM_BINDINGS_MISSING")
    if proposed.selected_direction_id is not None:
        failures.append("SELECTION_OUTSIDE_E02_SCOPE")
    if len(proposed.directions) not in (2, 3):
        failures.append("DIRECTION_COUNT_OUT_OF_RANGE")

    quarantined = set(envelope.quarantined_reference_ids)
    quarantined_failures: list[str] = []
    axis_names = (
        "visual_metaphor", "information_architecture", "encoding",
        "reading_sequence", "interaction_or_motion",
    )
    material: list[tuple[str, str, tuple[str, ...]]] = []
    for direction in proposed.directions:
        for label, actual, expected in (
            ("CLAIM_BINDINGS", direction.claim_bindings, thesis.claim_bindings),
            ("CERTAINTY", direction.certainty, thesis.certainty),
            ("CONTRADICTIONS", direction.contradictions, thesis.contradictions),
            ("NON_CLAIMS", direction.non_claims, thesis.non_claims),
            ("UNCERTAINTY_EXPOSURE", direction.uncertainty_exposure, thesis.uncertainty_exposure),
        ):
            if actual != expected:
                failures.append(f"{direction.direction_id}_{label}_MUTATED")
        failures.extend(f"{direction.direction_id}_PROHIBITED_ADAPTATION_{item}" for item in direction.prohibited_adaptations)
        quarantined_failures.extend(
            f"{direction.direction_id}_QUARANTINED_REFERENCE_{item}"
            for item in direction.reference_ids if item in quarantined
        )
    if quarantined_failures:
        return ExpectedDirectionAssessment("QUARANTINE_REFERENCE", tuple(quarantined_failures), ())

    for left, right in combinations(proposed.directions, 2):
        axes = tuple(axis for axis in axis_names if getattr(left, axis) != getattr(right, axis))
        material.append((left.direction_id, right.direction_id, axes))
        if len(axes) < 2:
            failures.append(f"INSUFFICIENT_DIVERGENCE_{left.direction_id}_{right.direction_id}")
    if failures:
        return ExpectedDirectionAssessment("RETURN_TO_PREVIOUS", tuple(failures), tuple(material))
    return ExpectedDirectionAssessment("DIRECTION_SET_READY_FOR_SELECTION", (), tuple(material))

