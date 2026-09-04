import unittest

from sictra_block2_design.e02_direction import (
    Direction,
    DirectionSet,
    E02ContractViolation,
    E02Envelope,
    VisualThesis,
    assess_direction_set,
)


def envelope(**changes):
    value = E02Envelope(
        "MESSAGE-001", "fingerprint:upstream-001", "CONTINUE", "CURRENT", True, True,
    )
    return E02Envelope(**{name: changes.get(name, getattr(value, name)) for name in value.__dataclass_fields__})


def thesis(**changes):
    value = VisualThesis(
        "THESIS-001", ("CLAIM-001",), "PLAUSIBLE", ("CONTRADICTION-001",),
        ("NO-CAUSAL-CLAIM",), ("headline-limit",),
    )
    return VisualThesis(**{name: changes.get(name, getattr(value, name)) for name in value.__dataclass_fields__})


def direction(direction_id, **changes):
    value = Direction(
        direction_id, "progression", "causal-sequence", "milestones", "linear", "static",
        ("CLAIM-001",), "PLAUSIBLE", ("CONTRADICTION-001",), ("NO-CAUSAL-CLAIM",), ("headline-limit",),
    )
    return Direction(**{name: changes.get(name, getattr(value, name)) for name in value.__dataclass_fields__})


def direction_set(*directions, **changes):
    value = DirectionSet("DIRECTION-SET-001", "THESIS-001", "fingerprint:upstream-001", directions)
    return DirectionSet(**{name: changes.get(name, getattr(value, name)) for name in value.__dataclass_fields__})


def structurally_distinct_pair():
    return (
        direction("DIRECTION-A"),
        direction(
            "DIRECTION-B",
            visual_metaphor="scenario-comparison",
            information_architecture="decision-matrix",
            encoding="annotated-comparison",
        ),
    )


class E02DirectionContractTests(unittest.TestCase):
    def test_clean_materially_distinct_set_is_ready_for_external_selection(self):
        result = assess_direction_set(envelope(), thesis(), direction_set(*structurally_distinct_pair()))
        self.assertEqual("DIRECTION_SET_READY_FOR_SELECTION", result.disposition)
        self.assertTrue(result.ready_for_selection)
        self.assertEqual(("visual_metaphor", "information_architecture", "encoding"), result.material_differences[0][2])

    def test_upstream_precedence_blocks_even_when_references_are_disallowed(self):
        result = assess_direction_set(
            envelope(disposition="RETURN_UPSTREAM", references_allowed=False), thesis(), direction_set(*structurally_distinct_pair())
        )
        self.assertEqual("RETURN_UPSTREAM", result.disposition)
        self.assertEqual(("ENVELOPE_NOT_CONTINUE",), result.reasons)

    def test_stale_envelope_returns_upstream(self):
        result = assess_direction_set(envelope(temporal_state="STALE"), thesis(), direction_set(*structurally_distinct_pair()))
        self.assertEqual("RETURN_UPSTREAM", result.disposition)
        self.assertIn("ENVELOPE_NOT_CURRENT", result.reasons)

    def test_lineage_mismatch_returns_upstream(self):
        result = assess_direction_set(envelope(), thesis(), direction_set(*structurally_distinct_pair(), parent_thesis_id="OTHER"))
        self.assertEqual("RETURN_UPSTREAM", result.disposition)
        self.assertEqual(("PARENT_THESIS_MISMATCH",), result.reasons)

    def test_references_not_allowed_are_quarantined_before_creative_evaluation(self):
        result = assess_direction_set(envelope(references_allowed=False), thesis(), direction_set(*structurally_distinct_pair()))
        self.assertEqual("QUARANTINE_REFERENCE", result.disposition)
        self.assertEqual(("REFERENCES_NOT_ALLOWED",), result.reasons)

    def test_unsupported_channel_stops_before_direction_evaluation(self):
        result = assess_direction_set(envelope(channel_supported=False), thesis(), direction_set(*structurally_distinct_pair()))
        self.assertEqual("UNSUPPORTED_CHANNEL", result.disposition)

    def test_cosmetic_only_variation_is_not_divergence(self):
        result = assess_direction_set(
            envelope(), thesis(), direction_set(direction("DIRECTION-A", cosmetic_treatment="blue"), direction("DIRECTION-B", cosmetic_treatment="red"))
        )
        self.assertEqual("RETURN_TO_PREVIOUS", result.disposition)
        self.assertIn("INSUFFICIENT_DIVERGENCE_DIRECTION-A_DIRECTION-B", result.reasons)

    def test_one_material_axis_is_not_divergence(self):
        result = assess_direction_set(
            envelope(), thesis(), direction_set(direction("DIRECTION-A"), direction("DIRECTION-B", visual_metaphor="scenario-comparison"))
        )
        self.assertEqual("RETURN_TO_PREVIOUS", result.disposition)
        self.assertIn("INSUFFICIENT_DIVERGENCE_DIRECTION-A_DIRECTION-B", result.reasons)

    def test_claim_and_certainty_mutation_are_rejected(self):
        altered = direction("DIRECTION-B", claim_bindings=("CLAIM-OTHER",), certainty="VERIFIED")
        result = assess_direction_set(envelope(), thesis(), direction_set(direction("DIRECTION-A"), altered))
        self.assertEqual("RETURN_TO_PREVIOUS", result.disposition)
        self.assertIn("DIRECTION-B_CLAIM_BINDINGS_MUTATED", result.reasons)
        self.assertIn("DIRECTION-B_CERTAINTY_MUTATED", result.reasons)

    def test_lost_contradiction_and_non_claim_are_rejected(self):
        altered = direction("DIRECTION-B", contradictions=(), non_claims=())
        result = assess_direction_set(envelope(), thesis(), direction_set(direction("DIRECTION-A"), altered))
        self.assertEqual("RETURN_TO_PREVIOUS", result.disposition)
        self.assertIn("DIRECTION-B_CONTRADICTIONS_MUTATED", result.reasons)
        self.assertIn("DIRECTION-B_NON_CLAIMS_MUTATED", result.reasons)

    def test_e02_cannot_select_winner(self):
        result = assess_direction_set(
            envelope(), thesis(), direction_set(*structurally_distinct_pair(), selected_direction_id="DIRECTION-A")
        )
        self.assertEqual("RETURN_TO_PREVIOUS", result.disposition)
        self.assertIn("SELECTION_OUTSIDE_E02_SCOPE", result.reasons)

    def test_prohibited_adaptation_is_rejected(self):
        altered = direction(
            "DIRECTION-B", visual_metaphor="scenario-comparison", information_architecture="decision-matrix",
            prohibited_adaptations=("sensitive-attribute-proxy",),
        )
        result = assess_direction_set(envelope(), thesis(), direction_set(direction("DIRECTION-A"), altered))
        self.assertEqual("RETURN_TO_PREVIOUS", result.disposition)
        self.assertIn("DIRECTION-B_PROHIBITED_ADAPTATION_sensitive-attribute-proxy", result.reasons)

    def test_quarantined_reference_is_not_usable(self):
        altered = direction(
            "DIRECTION-B", visual_metaphor="scenario-comparison", information_architecture="decision-matrix",
            reference_ids=("REF-UNLICENSED",),
        )
        result = assess_direction_set(
            envelope(quarantined_reference_ids=("REF-UNLICENSED",)), thesis(), direction_set(direction("DIRECTION-A"), altered)
        )
        self.assertEqual("QUARANTINE_REFERENCE", result.disposition)
        self.assertIn("DIRECTION-B_QUARANTINED_REFERENCE_REF-UNLICENSED", result.reasons)

    def test_duplicate_direction_identity_is_malformed(self):
        with self.assertRaises(E02ContractViolation):
            direction_set(direction("DIRECTION-A"), direction("DIRECTION-A"))


if __name__ == "__main__":
    unittest.main()

