import itertools
import unittest
from datetime import datetime, timezone

from sictra_block2_design.e02_direction import Direction
from sictra_block2_design.e03_design_system import (
    AssetReference,
    ComponentRule,
    ExceptionRule,
    SelectionRecord,
    SystemProfileProposal,
    TokenRule,
    assess_system_profile,
)
from sictra_block2_design.e03_design_system_oracle import expected_system_profile


NOW = datetime(2026, 8, 28, tzinfo=timezone.utc)


def selected_direction(**changes):
    value = Direction(
        "DIRECTION-A", "progression", "causal-sequence", "milestones", "linear", "static",
        ("CLAIM-001",), "PLAUSIBLE", ("CONTRADICTION-001",), ("NO-CAUSAL-CLAIM",), ("headline-limit",),
    )
    return Direction(**{name: changes.get(name, getattr(value, name)) for name in value.__dataclass_fields__})


def proposal(**changes):
    value = SystemProfileProposal(
        "PROFILE-001", "0.1.0", "fingerprint:upstream-001", "DIRECTION-A", "EMAIL", ("EMAIL", "PDF"),
        SelectionRecord("DIRECTION-A", "REVIEWER-001", "AUTHORITY-001", True),
        ("CLAIM-001",), "PLAUSIBLE", ("CONTRADICTION-001",), ("NO-CAUSAL-CLAIM",),
        ("headline-limit",),
        (TokenRule("certainty-low", "certainty_low", True, "LABEL"),),
        (AssetReference("FONT-001", "FONT", "ALLOW_LICENSED_ASSET", ("EMAIL",), True),),
        (ComponentRule("CTA", True, ("PRIMARY", "SECONDARY"), ("DEFAULT", "FOCUS", "DISABLED"), ("announces action",)),),
        (ExceptionRule("EX-001", "OWNER-001", datetime(2026, 8, 1, tzinfo=timezone.utc), datetime(2026, 12, 31, tzinfo=timezone.utc), "PROFILE-000"),),
    )
    return SystemProfileProposal(**{name: changes.get(name, getattr(value, name)) for name in value.__dataclass_fields__})


class E03DesignSystemTests(unittest.TestCase):
    def assert_matches_oracle(self, item):
        actual = assess_system_profile("fingerprint:upstream-001", selected_direction(), item, NOW)
        expected = expected_system_profile("fingerprint:upstream-001", selected_direction(), item, NOW)
        self.assertEqual(expected, actual)
        return actual

    def test_complete_profile_is_ready_for_blueprint_not_rendering(self):
        result = self.assert_matches_oracle(proposal())
        self.assertEqual("SYSTEM_PROFILE_READY_FOR_BLUEPRINT", result.disposition)
        self.assertTrue(result.ready_for_blueprint)

    def test_unlicensed_asset_is_quarantined(self):
        result = self.assert_matches_oracle(proposal(assets=(AssetReference("FONT-X", "FONT", "QUARANTINE", ("EMAIL",), True),)))
        self.assertEqual("QUARANTINE_REFERENCE", result.disposition)

    def test_asset_license_scope_is_channel_specific(self):
        result = self.assert_matches_oracle(proposal(assets=(AssetReference("FONT-X", "FONT", "ALLOW_LICENSED_ASSET", ("WEB",), True),)))
        self.assertEqual("QUARANTINE_REFERENCE", result.disposition)
        revoked = self.assert_matches_oracle(
            proposal(assets=(AssetReference("FONT-X", "FONT", "ALLOW_LICENSED_ASSET", ("EMAIL",), False),))
        )
        self.assertEqual("QUARANTINE_REFERENCE", revoked.disposition)

    def test_material_token_needs_non_color_fallback(self):
        result = self.assert_matches_oracle(proposal(tokens=(TokenRule("warning", "warning", True, "COLOR_ONLY"),)))
        self.assertEqual("CONTRADICTED", result.disposition)

    def test_interactive_component_needs_focus_disabled_and_accessibility_notes(self):
        item = ComponentRule("CTA", True, ("PRIMARY",), ("DEFAULT",), ())
        result = self.assert_matches_oracle(proposal(components=(item,)))
        self.assertEqual("RETURN_TO_PREVIOUS", result.disposition)
        self.assertIn("COMPONENT_CTA_STATE_FOCUS_MISSING", result.reasons)
        self.assertIn("COMPONENT_CTA_STATE_DISABLED_MISSING", result.reasons)
        self.assertIn("COMPONENT_CTA_ACCESSIBILITY_NOTES_MISSING", result.reasons)

    def test_exception_requires_owner_current_review_and_rollback(self):
        item = ExceptionRule("EX-X", "", datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 2, 1, tzinfo=timezone.utc), "")
        result = self.assert_matches_oracle(proposal(exceptions=(item,)))
        self.assertEqual("RETURN_TO_PREVIOUS", result.disposition)
        self.assertEqual(3, len(result.reasons))

    def test_selection_cannot_be_inherited_or_stale(self):
        item = SelectionRecord("DIRECTION-B", "REVIEWER-001", "AUTHORITY-001", False)
        result = self.assert_matches_oracle(proposal(selection=item))
        self.assertEqual("RETURN_TO_PREVIOUS", result.disposition)

    def test_unsupported_channel_and_version_fail_explicitly(self):
        self.assertEqual("UNSUPPORTED_CHANNEL", self.assert_matches_oracle(proposal(target_channel="VIDEO")).disposition)
        self.assertEqual("UNSUPPORTED_VERSION", self.assert_matches_oracle(proposal(contract_version="0.2.0")).disposition)

    def test_claim_certainty_contradiction_and_non_claim_mutations_are_rejected(self):
        for field, changed in (
            ("claim_bindings", ("CLAIM-X",)),
            ("certainty", "VERIFIED"),
            ("contradictions", ()),
            ("non_claims", ()),
            ("uncertainty_exposure", ()),
        ):
            result = self.assert_matches_oracle(proposal(**{field: changed}))
            self.assertEqual("RETURN_TO_PREVIOUS", result.disposition)

    def test_oracle_exhausts_rights_fallback_selection_and_state_matrix(self):
        for rights_ok, fallback_ok, selection_current, states_ok in itertools.product((False, True), repeat=4):
            item = proposal(
                assets=(AssetReference("FONT-M", "FONT", "ALLOW_LICENSED_ASSET" if rights_ok else "QUARANTINE", ("EMAIL",), True),),
                tokens=(TokenRule("critical", "critical", True, "TEXT" if fallback_ok else "COLOR_ONLY"),),
                selection=SelectionRecord("DIRECTION-A", "REVIEWER", "AUTH", selection_current),
                components=(ComponentRule(
                    "CTA", True, ("PRIMARY",),
                    ("DEFAULT", "FOCUS", "DISABLED") if states_ok else ("DEFAULT",),
                    ("accessible action",),
                ),),
            )
            self.assert_matches_oracle(item)


if __name__ == "__main__":
    unittest.main()
