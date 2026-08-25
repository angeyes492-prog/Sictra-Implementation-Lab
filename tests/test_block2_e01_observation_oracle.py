import unittest
from itertools import product

from sictra.block2_e01_observation import Observation, assess_observation
from sictra.block2_e01_observation_oracle import expected_observation_state


class ObservationOracleDifferentialTests(unittest.TestCase):
    def test_observation_evaluator_matches_independent_oracle_across_mutations(self):
        required = frozenset({"identity", "visibility"})
        for provenance, contaminated, complete, external, source_class, independent in product(
            ("p1", ""),
            (False, True),
            (False, True),
            (False, True),
            ("human-perception", "synthetic", "internal-agent"),
            (False, True),
        ):
            observed = required if complete else frozenset({"identity"})
            observer_id = "reviewer-2" if independent else "author-1"
            evidence_author_id = "author-1"
            obs = Observation(
                observation_id="obs-1",
                claim_id="claim-1",
                source_class=source_class,
                provenance=provenance,
                observed_conditions=observed,
                contamination_flags=frozenset({"leak"}) if contaminated else frozenset(),
                externally_observed=external,
                observer_id=observer_id,
                evidence_author_id=evidence_author_id,
            )
            actual = assess_observation(obs, required_conditions=required)
            expected = expected_observation_state(obs, required)
            with self.subTest(
                provenance=provenance,
                contaminated=contaminated,
                complete=complete,
                external=external,
                source_class=source_class,
                independent=independent,
            ):
                self.assertEqual((actual.admissible, actual.accepted), expected)


if __name__ == "__main__":
    unittest.main()
