"""Independent declarative oracle for E01 observation admissibility."""


def expected_observation_state(observation, required_conditions, require_external=True):
    structural = bool(observation.observation_id and observation.claim_id)
    structural = structural and bool(observation.provenance)
    structural = structural and not bool(observation.contamination_flags)
    structural = structural and required_conditions.issubset(observation.observed_conditions)
    accepted = structural and (observation.externally_observed or not require_external)
    return structural, accepted
