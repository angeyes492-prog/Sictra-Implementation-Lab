from itertools import product

from sictra.block2_e01_observation import Observation, assess_observation
from sictra.block2_e01_observation_oracle import expected_observation_state


def test_observation_evaluator_matches_independent_oracle_across_mutations():
    required = frozenset({"identity", "visibility"})
    for provenance, contaminated, complete, external in product(
        ("p1", ""), (False, True), (False, True), (False, True)
    ):
        observed = required if complete else frozenset({"identity"})
        obs = Observation(
            observation_id="obs-1",
            claim_id="claim-1",
            source_class="human-perception",
            provenance=provenance,
            observed_conditions=observed,
            contamination_flags=frozenset({"leak"}) if contaminated else frozenset(),
            externally_observed=external,
        )
        actual = assess_observation(obs, required_conditions=required)
        expected = expected_observation_state(obs, required)
        assert (actual.admissible, actual.accepted) == expected
