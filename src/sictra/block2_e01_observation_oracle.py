"""Independent declarative oracle for E01 observation admissibility."""

EXTERNAL_SOURCE_CLASSES = frozenset(
    {"human-perception", "external-review", "production-observation"}
)


def expected_observation_state(observation, required_conditions, require_external=True):
    structural = bool(observation.observation_id and observation.claim_id)
    structural = structural and bool(observation.provenance)
    structural = structural and not bool(observation.contamination_flags)
    structural = structural and required_conditions.issubset(observation.observed_conditions)
    independent_observer = bool(
        observation.observer_id
        and observation.evidence_author_id
        and observation.observer_id != observation.evidence_author_id
    )
    external_authority = (
        observation.externally_observed
        and observation.source_class in EXTERNAL_SOURCE_CLASSES
        and independent_observer
    )
    accepted = structural and (external_authority or not require_external)
    return structural, accepted
