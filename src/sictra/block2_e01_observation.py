"""Block 2 E01 observation admissibility boundary.

This module keeps observed evidence separate from acceptance authority. An
observation may be structurally admissible while still requiring a genuinely
external observation class before a claim can be accepted.
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
    external_authority = (
        observation.externally_observed
        and observation.source_class in EXTERNAL_SOURCE_CLASSES
    )
    accepted = admissible and (
        external_authority or not require_external_observation
    )
    if admissible and require_external_observation:
        if not observation.externally_observed:
            reasons.append("EXTERNAL_OBSERVATION_REQUIRED")
        elif observation.source_class not in EXTERNAL_SOURCE_CLASSES:
            reasons.append("EXTERNAL_SOURCE_CLASS_REQUIRED")
    return ObservationAssessment(admissible, accepted, tuple(reasons))
