import itertools
import unittest

from sictra_block2_design.e02_direction import (
    Direction,
    DirectionSet,
    E02Envelope,
    VisualThesis,
    assess_direction_set,
)
from sictra_block2_design.e02_direction_oracle import expected_direction_assessment


def envelope(**changes):
    value = E02Envelope("MESSAGE-001", "fingerprint:upstream-001", "CONTINUE", "CURRENT", True, True)
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


class E02DirectionOracleTests(unittest.TestCase):
    def assert_matches_oracle(self, context, visual_thesis, proposed):
        actual = assess_direction_set(context, visual_thesis, proposed)
        expected = expected_direction_assessment(context, visual_thesis, proposed)
        self.assertEqual(expected.disposition, actual.disposition)
        self.assertEqual(expected.reasons, actual.reasons)
        self.assertEqual(expected.material_differences, actual.material_differences)

    def test_clean_set_matches_independent_oracle(self):
        self.assert_matches_oracle(envelope(), thesis(), direction_set(*structurally_distinct_pair()))

    def test_upstream_failure_precedence_matches_independent_oracle(self):
        self.assert_matches_oracle(
            envelope(disposition="RETURN_UPSTREAM", references_allowed=False), thesis(), direction_set(*structurally_distinct_pair())
        )

    def test_cosmetic_and_claim_mutation_matrix_matches_independent_oracle(self):
        altered = direction("DIRECTION-B", certainty="VERIFIED", cosmetic_treatment="red")
        self.assert_matches_oracle(envelope(), thesis(), direction_set(direction("DIRECTION-A"), altered))

    def test_selection_and_quarantined_reference_match_independent_oracle(self):
        altered = direction(
            "DIRECTION-B", visual_metaphor="scenario-comparison", information_architecture="decision-matrix",
            reference_ids=("REF-QUARANTINED",),
        )
        self.assert_matches_oracle(
            envelope(quarantined_reference_ids=("REF-QUARANTINED",)), thesis(),
            direction_set(direction("DIRECTION-A"), altered, selected_direction_id="DIRECTION-A"),
        )

    def test_independent_oracle_exhausts_divergence_and_preservation_mutations(self):
        """Exercise combinations without sharing the production evaluator's helpers."""

        for mutate_claim, mutate_certainty, mutate_contradiction, one_axis_only, quarantined in itertools.product(
            (False, True), repeat=5
        ):
            changes = {}
            if mutate_claim:
                changes["claim_bindings"] = ("CLAIM-OTHER",)
            if mutate_certainty:
                changes["certainty"] = "VERIFIED"
            if mutate_contradiction:
                changes["contradictions"] = ()
            if one_axis_only:
                changes["visual_metaphor"] = "scenario-comparison"
            else:
                changes.update(
                    visual_metaphor="scenario-comparison",
                    information_architecture="decision-matrix",
                )
            if quarantined:
                changes["reference_ids"] = ("REF-QUARANTINED",)
            altered = direction("DIRECTION-B", **changes)
            context = envelope(quarantined_reference_ids=("REF-QUARANTINED",) if quarantined else ())
            self.assert_matches_oracle(context, thesis(), direction_set(direction("DIRECTION-A"), altered))

    def test_every_pair_in_three_direction_set_must_be_materially_distinct(self):
        third = direction(
            "DIRECTION-C",
            visual_metaphor="progression",
            information_architecture="causal-sequence",
            encoding="milestones",
            reading_sequence="linear",
            interaction_or_motion="static",
            cosmetic_treatment="different-only-cosmetics",
        )
        self.assert_matches_oracle(
            envelope(), thesis(), direction_set(*structurally_distinct_pair(), third),
        )


if __name__ == "__main__":
    unittest.main()
