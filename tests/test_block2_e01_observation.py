import unittest

from sictra.block2_e01_observation import Observation, assess_observation


AUTHORIZED = frozenset({"reviewer-2"})


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
    def assess(self, obs):
        return assess_observation(
            obs,
            required_conditions=frozenset({"identity", "visibility"}),
            authorized_observer_ids=AUTHORIZED,
        )

    def test_structural_admissibility_does_not_imply_external_acceptance(self):
        result = self.assess(specimen())
        self.assertTrue(result.admissible)
        self.assertFalse(result.accepted)
        self.assertEqual(result.reasons, ("EXTERNAL_OBSERVATION_REQUIRED",))

    def test_external_observation_can_close_bounded_acceptance(self):
        result = self.assess(specimen(externally_observed=True))
        self.assertTrue(result.admissible)
        self.assertTrue(result.accepted)
        self.assertEqual(result.reasons, ())

    def test_unauthorized_observer_cannot_close_acceptance(self):
        result = self.assess(
            specimen(externally_observed=True, observer_id="reviewer-unknown")
        )
        self.assertTrue(result.admissible)
        self.assertFalse(result.accepted)
        self.assertIn("OBSERVER_AUTHORITY_REQUIRED", result.reasons)

    def test_same_author_cannot_self_attest_external_observation(self):
        result = self.assess(
            specimen(
                externally_observed=True,
                observer_id="author-1",
                evidence_author_id="author-1",
            )
        )
        self.assertTrue(result.admissible)
        self.assertFalse(result.accepted)
        self.assertIn("INDEPENDENT_OBSERVER_REQUIRED", result.reasons)

    def test_missing_observer_identity_cannot_close_acceptance(self):
        result = self.assess(specimen(externally_observed=True, observer_id=""))
        self.assertTrue(result.admissible)
        self.assertFalse(result.accepted)
        self.assertIn("OBSERVER_IDENTITY_REQUIRED", result.reasons)

    def test_missing_provenance_is_rejected_even_if_external_flag_is_true(self):
        result = self.assess(specimen(provenance="", externally_observed=True))
        self.assertFalse(result.admissible)
        self.assertFalse(result.accepted)
        self.assertIn("PROVENANCE_MISSING", result.reasons)

    def test_contamination_prevents_acceptance(self):
        result = self.assess(
            specimen(contamination_flags=frozenset({"same-author"}), externally_observed=True)
        )
        self.assertFalse(result.admissible)
        self.assertFalse(result.accepted)
        self.assertIn("CONTAMINATED", result.reasons)

    def test_missing_required_condition_is_rejected(self):
        result = self.assess(
            specimen(observed_conditions=frozenset({"identity"}), externally_observed=True)
        )
        self.assertFalse(result.admissible)
        self.assertFalse(result.accepted)
        self.assertIn("REQUIRED_CONDITIONS_MISSING", result.reasons)


if __name__ == "__main__":
    unittest.main()
