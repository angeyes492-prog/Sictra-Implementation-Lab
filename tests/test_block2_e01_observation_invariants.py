import unittest
from itertools import combinations

from sictra.block2_e01_observation import Observation, assess_observation


REQUIRED = frozenset({"identity", "visibility"})


def specimen(**changes):
    values = dict(
        observation_id="obs-invariant",
        claim_id="claim-1",
        source_class="human-perception",
        provenance="external-review-1",
        observed_conditions=REQUIRED,
        contamination_flags=frozenset(),
        externally_observed=True,
        observer_id="reviewer-2",
        evidence_author_id="author-1",
    )
    values.update(changes)
    return Observation(**values)


class ObservationInvariantTests(unittest.TestCase):
    def test_acceptance_implies_admissibility(self):
        result = assess_observation(specimen(), required_conditions=REQUIRED)
        self.assertTrue(result.accepted)
        self.assertTrue(result.admissible)

    def test_any_single_required_gate_failure_blocks_acceptance(self):
        mutations = (
            dict(provenance=""),
            dict(contamination_flags=frozenset({"leak"})),
            dict(observed_conditions=frozenset({"identity"})),
            dict(externally_observed=False),
            dict(observer_id=""),
            dict(observer_id="author-1", evidence_author_id="author-1"),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                result = assess_observation(specimen(**mutation), required_conditions=REQUIRED)
                self.assertFalse(result.accepted)

    def test_external_flag_cannot_promote_synthetic_or_internal_source(self):
        for source_class in ("synthetic", "internal-agent", "simulation"):
            with self.subTest(source_class=source_class):
                result = assess_observation(
                    specimen(source_class=source_class, externally_observed=True),
                    required_conditions=REQUIRED,
                )
                self.assertTrue(result.admissible)
                self.assertFalse(result.accepted)
                self.assertIn("EXTERNAL_SOURCE_CLASS_REQUIRED", result.reasons)

    def test_same_identity_cannot_self_attest(self):
        result = assess_observation(
            specimen(observer_id="author-1", evidence_author_id="author-1"),
            required_conditions=REQUIRED,
        )
        self.assertFalse(result.accepted)
        self.assertIn("INDEPENDENT_OBSERVER_REQUIRED", result.reasons)

    def test_multiple_simultaneous_failures_never_restore_acceptance(self):
        failures = (
            ("provenance", ""),
            ("contamination_flags", frozenset({"same-author"})),
            ("observed_conditions", frozenset({"identity"})),
            ("externally_observed", False),
            ("observer_id", ""),
        )
        for size in range(2, len(failures) + 1):
            for combo in combinations(failures, size):
                with self.subTest(combo=combo):
                    result = assess_observation(
                        specimen(**dict(combo)), required_conditions=REQUIRED
                    )
                    self.assertFalse(result.accepted)

    def test_extra_observed_conditions_do_not_bypass_required_gates(self):
        result = assess_observation(
            specimen(
                observed_conditions=REQUIRED | {"salience", "contrast"},
                externally_observed=False,
            ),
            required_conditions=REQUIRED,
        )
        self.assertTrue(result.admissible)
        self.assertFalse(result.accepted)
        self.assertIn("EXTERNAL_OBSERVATION_REQUIRED", result.reasons)


if __name__ == "__main__":
    unittest.main()
