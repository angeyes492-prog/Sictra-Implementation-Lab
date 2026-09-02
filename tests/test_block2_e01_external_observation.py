import unittest
from dataclasses import replace
from datetime import datetime, timezone

from sictra_block2_design.e01_external_observation import (
    ExternalObservationReceipt, assess_external_observation, fixture_fingerprint,
)
from sictra_block2_design.preflight import assess_fixture
from tests.test_block2_e01_preflight import fixture


NOW = datetime(2026, 9, 1, 15, tzinfo=timezone.utc)


def receipt(value=None, **changes):
    value = value or fixture()
    base = ExternalObservationReceipt(
        "RECEIPT-001", "0.1.0", value.fixture_id, fixture_fingerprint(value), "FIXTURE-AUTHOR",
        value.upstream.object_id, value.upstream.authority_reference, "CURRENT",
        "INDEPENDENT-REVIEWER", "EXTERNAL-OBSERVER", True, True, False, False, False,
        "OBSERVATION-001", "A_SUPPORTED", ("EVIDENCE-OBS-001",), NOW,
    )
    return replace(base, **changes)


class E01ExternalObservationTests(unittest.TestCase):
    def test_valid_receipt_is_atomic_observation_not_promotion(self):
        value = fixture()
        result = assess_external_observation(value, assess_fixture(value), receipt(value))
        self.assertTrue(result.recorded)
        self.assertEqual("NOT_PROMOTED", result.promotion_state)
        self.assertEqual("NOT_ACCEPTED", result.acceptance_state)

    def test_self_review_exposure_and_confounder_invalidate(self):
        value = fixture()
        result = assess_external_observation(value, assess_fixture(value), receipt(
            value, reviewer_id="FIXTURE-AUTHOR", thesis_exposed_before_observation=True,
            material_confounder_discovered=True,
        ))
        self.assertEqual("INVALID_TRIAL", result.disposition)
        self.assertEqual(
            ("REVIEWER_IS_FIXTURE_AUTHOR", "THESIS_EXPOSED_BEFORE_OBSERVATION", "MATERIAL_CONFOUNDER_DISCOVERED"),
            result.reasons,
        )

    def test_fixture_or_authority_substitution_does_not_record_observation(self):
        value = fixture()
        substituted = assess_external_observation(value, assess_fixture(value), receipt(value, fixture_hash="a" * 64))
        stale = assess_external_observation(value, assess_fixture(value), receipt(value, upstream_temporal_state="STALE"))
        self.assertEqual(("FIXTURE_HASH_MISMATCH",), substituted.reasons)
        self.assertEqual("RETURN_UPSTREAM", stale.disposition)
        self.assertEqual(("UPSTREAM_NOT_CURRENT",), stale.reasons)

    def test_preflight_return_upstream_precedes_a_well_formed_receipt(self):
        value = fixture()
        incomplete = replace(value, upstream=replace(value.upstream, authority_reference=""))
        result = assess_external_observation(incomplete, assess_fixture(incomplete), receipt(value))
        self.assertEqual("RETURN_UPSTREAM", result.disposition)
        self.assertIn("AUTHORITY_REFERENCE", result.reasons)


if __name__ == "__main__":
    unittest.main()
