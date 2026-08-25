import unittest

from sictra.block2_e01_observation import Observation, assess_observation


def specimen(**changes):
    values = dict(
        observation_id="obs-1",
        claim_id="claim-1",
        source_class="human-perception",
        provenance="external-review-1",
        observed_conditions=frozenset({"identity", "visibility"}),
        contamination_flags=frozenset(),
        externally_observed=False,
        observer_id="reviewer-2",
        evidence_author_id="author-1",
    )
    values.update(changes)
    return Observation(**values)


class ObservationBoundaryTests(unittest.TestCase):
    def test_structural_admissibility_does_not_imply_external_acceptance(self):
        result = assess_observation(
            specimen(), required_conditions=frozenset({"identity", "visibility"})
        )
        self.assertTrue(result.admissible)
        self.assertFalse(result.accepted)
        self.assertEqual(result.reasons, ("EXTERNAL_OBSERVATION_REQUIRED",))

    def test_external_observation_can_close_bounded_acceptance(self):
        result = assess_observation(
            specimen(externally_observed=True),
            required_conditions=frozenset({"identity", "visibility"}),
        )
        self.assertTrue(result.admissible)
        self.assertTrue(result.accepted)
        self.assertEqual(result.reasons, ())

    def test_same_author_cannot_self_attest_external_observation(self):
        result = assess_observation(
            specimen(
                externally_observed=True,
                observer_id="author-1",
                evidence_author_id="author-1",
            ),
            required_conditions=frozenset({"identity", "visibility"}),
        )
        self.assertTrue(result.admissible)
        self.assertFalse(result.accepted)
        self.assertIn("INDEPENDENT_OBSERVER_REQUIRED", result.reasons)

    def test_missing_observer_identity_cannot_close_acceptance(self):
        result = assess_observation(
            specimen(externally_observed=True, observer_id=""),
            required_conditions=frozenset({"identity", "visibility"}),
        )
        self.assertTrue(result.admissible)
        self.assertFalse(result.accepted)
        self.assertIn("OBSERVER_IDENTITY_REQUIRED", result.reasons)

    def test_missing_provenance_is_rejected_even_if_external_flag_is_true(self):
        result = assess_observation(
            specimen(provenance="", externally_observed=True),
            required_conditions=frozenset({"identity", "visibility"}),
        )
        self.assertFalse(result.admissible)
        self.assertFalse(result.accepted)
        self.assertIn("PROVENANCE_MISSING", result.reasons)

    def test_contamination_prevents_acceptance(self):
        result = assess_observation(
            specimen(contamination_flags=frozenset({"same-author"}), externally_observed=True),
            required_conditions=frozenset({"identity", "visibility"}),
        )
        self.assertFalse(result.admissible)
        self.assertFalse(result.accepted)
        self.assertIn("CONTAMINATED", result.reasons)

    def test_missing_required_condition_is_rejected(self):
        result = assess_observation(
            specimen(observed_conditions=frozenset({"identity"}), externally_observed=True),
            required_conditions=frozenset({"identity", "visibility"}),
        )
        self.assertFalse(result.admissible)
        self.assertFalse(result.accepted)
        self.assertIn("REQUIRED_CONDITIONS_MISSING", result.reasons)


if __name__ == "__main__":
    unittest.main()
