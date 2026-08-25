"""Block 2 E01 observation admissibility boundary.

This module keeps observed evidence separate from acceptance authority. An
observation may be structurally admissible while still requiring a genuinely
external, independently attributable, explicitly authorized observer before a
claim can be accepted.
"""
from dataclasses import dataclass
from typing import FrozenSet


EXTERNAL_SOURCE_CLASSES = frozenset(
    {"human-perception", "external-review", "production-observation"}
)


@dataclass(frozen=True)
class Observation:
    observation_id: str
    claim_id: str
    source_class: str
    provenance: str
    observed_conditions: FrozenSet[str]
    contamination_flags: FrozenSet[str] = frozenset()
    externally_observed: bool = False
    observer_id: str = ""
    evidence_author_id: str = ""


@dataclass(frozen=True)
class ObservationAssessment:
    admissible: bool
    accepted: bool
    reasons: tuple[str, ...]


def assess_observation(
    observation: Observation,
    *,
    required_conditions: FrozenSet[str],
    require_external_observation: bool = True,
    authorized_observer_ids: FrozenSet[str] = frozenset(),
) -> ObservationAssessment:
    reasons: list[str] = []
    if not observation.observation_id or not observation.claim_id:
        reasons.append("IDENTITY_INCOMPLETE")
    if not observation.provenance:
        reasons.append("PROVENANCE_MISSING")
    if observation.contamination_flags:
        reasons.append("CONTAMINATED")
    missing = required_conditions - observation.observed_conditions
    if missing:
        reasons.append("REQUIRED_CONDITIONS_MISSING")

    admissible = not reasons
    independent_observer = bool(
        observation.observer_id
        and observation.evidence_author_id
        and observation.observer_id != observation.evidence_author_id
    )
    observer_authorized = observation.observer_id in authorized_observer_ids
    external_authority = (
        observation.externally_observed
        and observation.source_class in EXTERNAL_SOURCE_CLASSES
        and independent_observer
        and observer_authorized
    )
    accepted = admissible and (
        external_authority or not require_external_observation
    )
    if admissible and require_external_observation:
        if not observation.externally_observed:
            reasons.append("EXTERNAL_OBSERVATION_REQUIRED")
        elif observation.source_class not in EXTERNAL_SOURCE_CLASSES:
            reasons.append("EXTERNAL_SOURCE_CLASS_REQUIRED")
        elif not observation.observer_id or not observation.evidence_author_id:
            reasons.append("OBSERVER_IDENTITY_REQUIRED")
        elif observation.observer_id == observation.evidence_author_id:
            reasons.append("INDEPENDENT_OBSERVER_REQUIRED")
        elif not observer_authorized:
            reasons.append("OBSERVER_AUTHORITY_REQUIRED")
    return ObservationAssessment(admissible, accepted, tuple(reasons))
