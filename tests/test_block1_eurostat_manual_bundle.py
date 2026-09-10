import json
import unittest

from sictra_block1 import (
    EurostatManualBundleViolation,
    build_eurostat_manual_bundle,
)
from test_block1_eurostat_maritime_mapper import workbook


SOURCE_URL = "https://ec.europa.eu/eurostat/databrowser/view/tran_r_mago_nm/default/table?lang=en"


class EurostatManualBundleTests(unittest.TestCase):
    def test_assembly_preserves_one_explicit_selection_without_attesting_it(self):
        bundle = build_eurostat_manual_bundle(
            "eurostat.xlsx",
            workbook(rows=(
                ("BE", "Belgium", "12.5", None, "13.5"),
                ("BE2", "Vlaams Gewest", "10", None, "11"),
            )),
            "COUNTRY",
            source_url=SOURCE_URL,
            observed_at=10_000,
            correlation_id="eurostat-country-2026-09-05",
        )
        self.assertEqual(set(bundle), {
            "source_id", "source_url", "content", "observed_at",
            "claim_key", "polarity", "correlation_id",
        })
        self.assertEqual(bundle["claim_key"], "maritime_freight_weight_thousand_tonnes")
        self.assertEqual(bundle["polarity"], 1)
        content = json.loads(bundle["content"])
        self.assertEqual(content["bundle_state"], "UNATTESTED_MANUAL_BUNDLE")
        self.assertEqual(content["provenance"]["mapping_status"], "MAPPED_NOT_EVIDENCE")
        self.assertEqual(content["selection"]["selection_status"], "SELECTED_NOT_EVIDENCE")
        self.assertEqual(content["selection"]["geo_level"], "COUNTRY")
        self.assertEqual(len(content["observations"]), 2)
        self.assertLessEqual(len(bundle["content"].encode("utf-8")), 131_072)

    def test_invalid_source_and_gateway_boundary_inputs_fail_closed(self):
        args = ("eurostat.xlsx", workbook(), "COUNTRY")
        kwargs = {
            "source_url": SOURCE_URL,
            "observed_at": 10_000,
            "correlation_id": "eurostat-country-001",
        }
        for changed in (
            {"source_url": "http://ec.europa.eu/eurostat/databrowser/view/tran_r_mago_nm"},
            {"source_url": "https://ec.europa.eu/eurostat/databrowser/view/other_dataset"},
            {"source_url": "https://user@ec.europa.eu/eurostat/databrowser/view/tran_r_mago_nm"},
            {"observed_at": True},
            {"correlation_id": "contains space"},
        ):
            with self.subTest(changed=changed), self.assertRaises(EurostatManualBundleViolation):
                build_eurostat_manual_bundle(*args, **{**kwargs, **changed})

    def test_bundle_does_not_choose_or_collapse_geo_levels(self):
        with self.assertRaises(EurostatManualBundleViolation):
            build_eurostat_manual_bundle(
                "eurostat.xlsx", workbook(), "ALL",
                source_url=SOURCE_URL,
                observed_at=10_000,
                correlation_id="eurostat-all-001",
            )


if __name__ == "__main__":
    unittest.main()
