import itertools
import unittest

from tests.test_block2_e03_design_system import proposal as system_profile
from sictra_block2_design.e04_information_design import (
    BlueprintElement, ChannelTarget, EncodingPlan, InformationBlueprint,
    InformationPayload, PayloadClaim, assess_information_blueprint,
)
from sictra_block2_design.e04_information_design_oracle import expected_information_blueprint


def payload(**changes):
    value = InformationPayload("PAYLOAD-001", "0.1.0", (
        PayloadClaim("CLAIM-001", ("EVIDENCE-001",), ("SOURCE-001",), ("LIMIT-001",), "COMPARISON", True, "%", "HIGHER_IS_BETTER"),
    ), ("Approved copy",))
    return InformationPayload(**{name: changes.get(name, getattr(value, name)) for name in value.__dataclass_fields__})


def target(**changes):
    value = ChannelTarget("NEWSLETTER", "EMAIL", "EXECUTIVE")
    return ChannelTarget(**{name: changes.get(name, getattr(value, name)) for name in value.__dataclass_fields__})


def blueprint(**changes):
    value = InformationBlueprint(
        "BLUEPRINT-001", "0.1.0", "PROFILE-001", "fingerprint:upstream-001", "NEWSLETTER", "EMAIL", "EXECUTIVE",
        ("CHART-001", "CTA-001"),
        (
            BlueprintElement("CHART-001", "CHART", ("CLAIM-001",), ("EVIDENCE-001",), (), False),
            BlueprintElement("CTA-001", "CTA", ("CLAIM-001",), ("EVIDENCE-001",), ("LIMIT-001",), False),
        ),
        (EncodingPlan("ENC-001", "CLAIM-001", "COMPARISON", "BAR", "%", "HIGHER_IS_BETTER", ("SOURCE-001",), True, True, 3, False, False, False),),
        ("PLAIN_TEXT",), (), "NOT_PUBLISHED",
    )
    return InformationBlueprint(**{name: changes.get(name, getattr(value, name)) for name in value.__dataclass_fields__})


class E04InformationDesignTests(unittest.TestCase):
    def assert_oracle(self, item, *, source=None, destination=None, profile=None, profile_state="SYSTEM_PROFILE_READY_FOR_BLUEPRINT"):
        source = source or payload(); destination = destination or target(); profile = profile or system_profile()
        actual = assess_information_blueprint("fingerprint:upstream-001", profile, profile_state, source, destination, item)
        expected = expected_information_blueprint("fingerprint:upstream-001", profile, profile_state, source, destination, item)
        self.assertEqual(expected, actual)
        return actual

    def test_clean_blueprint_is_only_ready_for_production_review(self):
        result = self.assert_oracle(blueprint())
        self.assertEqual("BLUEPRINT_READY_FOR_PRODUCTION_REVIEW", result.disposition)
        self.assertTrue(result.ready_for_production_review)

    def test_missing_evidence_attribution_or_copy_returns_upstream(self):
        claim = payload().claims[0]
        for source in (
            payload(approved_copy=()),
            payload(claims=(PayloadClaim(claim.claim_id, (), claim.attribution_ids, claim.limitation_ids, claim.relationship, True, claim.unit, claim.polarity),)),
            payload(claims=(PayloadClaim(claim.claim_id, claim.evidence_refs, (), claim.limitation_ids, claim.relationship, True, claim.unit, claim.polarity),)),
        ):
            self.assertEqual("RETURN_UPSTREAM", self.assert_oracle(blueprint(), source=source).disposition)

    def test_profile_and_channel_lineage_are_immutable(self):
        for item, kwargs in (
            (blueprint(profile_id="OTHER"), {}),
            (blueprint(envelope_fingerprint="other"), {}),
            (blueprint(channel="SOCIAL"), {}),
            (blueprint(), {"profile_state": "RETURN_TO_PREVIOUS"}),
        ):
            self.assertEqual("RETURN_TO_PREVIOUS", self.assert_oracle(item, **kwargs).disposition)

    def test_uncontracted_channel_or_fallback_is_unsupported(self):
        self.assertEqual("UNSUPPORTED_CHANNEL", self.assert_oracle(blueprint(accessibility_fallbacks=())).disposition)
        unknown = target(artifact_type="HOLOGRAM")
        self.assertEqual("UNSUPPORTED_CHANNEL", self.assert_oracle(blueprint(artifact_type="HOLOGRAM"), destination=unknown).disposition)

    def test_executable_or_published_output_is_scope_violation(self):
        for item in (blueprint(executable_artifacts=("email.html",)), blueprint(publication_state="PUBLISHED")):
            self.assertEqual("SCOPE_VIOLATION", self.assert_oracle(item).disposition)

    def test_claim_mapping_reading_order_and_cta_limits_are_enforced(self):
        for item in (
            blueprint(reading_order=("CHART-001",)),
            blueprint(elements=(BlueprintElement("DECOR-1", "DECORATION", ("CLAIM-001",), ("EVIDENCE-001",), (), True),)),
            blueprint(elements=(BlueprintElement("CTA-001", "CTA", ("CLAIM-001",), ("EVIDENCE-001",), (), False),), reading_order=("CTA-001",)),
            blueprint(elements=(BlueprintElement("TEXT-1", "TEXT", (), (), (), False),), reading_order=("TEXT-1",)),
        ):
            self.assertEqual("RETURN_TO_PREVIOUS", self.assert_oracle(item).disposition)

    def test_professional_encoding_rules_reject_misleading_charts(self):
        base = blueprint().encodings[0]
        variants = (
            {"chart_type": "LINE"}, {"baseline_at_zero": False}, {"color_only": True},
            {"is_3d": True}, {"dual_axis": True}, {"uncertainty_visible": False},
            {"unit": "USD"}, {"polarity": "LOWER_IS_BETTER"}, {"attribution_ids": ()},
        )
        for changes in variants:
            encoding = EncodingPlan(**{name: changes.get(name, getattr(base, name)) for name in base.__dataclass_fields__})
            self.assertEqual("CONTRADICTED", self.assert_oracle(blueprint(encodings=(encoding,))).disposition)

    def test_pie_is_limited_to_five_series(self):
        claim = PayloadClaim("CLAIM-001", ("EVIDENCE-001",), ("SOURCE-001",), (), "PART_TO_WHOLE", False, "%", "PARTS_SUM_TO_WHOLE")
        source = payload(claims=(claim,))
        base = blueprint().encodings[0]
        encoding = EncodingPlan(base.encoding_id, base.claim_id, "PART_TO_WHOLE", "PIE", "%", "PARTS_SUM_TO_WHOLE", base.attribution_ids, True, True, 6, False, False, False)
        self.assertEqual("CONTRADICTED", self.assert_oracle(blueprint(encodings=(encoding,)), source=source).disposition)

    def test_version_boundary_is_explicit(self):
        self.assertEqual("UNSUPPORTED_VERSION", self.assert_oracle(blueprint(contract_version="1.0.0")).disposition)

    def test_duplicate_identities_fail_closed(self):
        claim = payload().claims[0]
        self.assertEqual(
            "RETURN_UPSTREAM",
            self.assert_oracle(blueprint(), source=payload(claims=(claim, claim))).disposition,
        )
        element = blueprint().elements[0]
        self.assertEqual(
            "RETURN_TO_PREVIOUS",
            self.assert_oracle(blueprint(elements=(element, element), reading_order=(element.element_id,))).disposition,
        )
        encoding = blueprint().encodings[0]
        self.assertEqual(
            "CONTRADICTED",
            self.assert_oracle(blueprint(encodings=(encoding, encoding))).disposition,
        )

    def test_oracle_exhausts_chart_accessibility_uncertainty_and_scope_matrix(self):
        base = blueprint().encodings[0]
        for color_only, uncertainty_visible, is_3d, published in itertools.product((False, True), repeat=4):
            encoding = EncodingPlan(**{
                name: {"color_only": color_only, "uncertainty_visible": uncertainty_visible, "is_3d": is_3d}.get(name, getattr(base, name))
                for name in base.__dataclass_fields__
            })
            item = blueprint(encodings=(encoding,), publication_state="PUBLISHED" if published else "NOT_PUBLISHED")
            result = self.assert_oracle(item)
            expected = "SCOPE_VIOLATION" if published else ("CONTRADICTED" if color_only or not uncertainty_visible or is_3d else "BLUEPRINT_READY_FOR_PRODUCTION_REVIEW")
            self.assertEqual(expected, result.disposition)


if __name__ == "__main__":
    unittest.main()
