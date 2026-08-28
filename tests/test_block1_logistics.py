"""Contract, oracle, and adversarial tests for the logistics workspace."""

from __future__ import annotations

from copy import deepcopy
import unittest

from sictra_block1.logistics import (
    FIXTURE_CLASS,
    LogisticsContractViolation,
    StrategyObservation,
    compare_investigation_strategies,
    compare_strategies,
    get_investigation,
    validate_investigation,
    workspace_catalog,
)


class Block1LogisticsTests(unittest.TestCase):
    def test_catalog_preserves_synthetic_boundary_and_three_scales(self):
        catalog = workspace_catalog()
        self.assertEqual(catalog["fixture_class"], FIXTURE_CLASS)
        self.assertEqual(
            {item["scope"]["level"] for item in catalog["investigations"]},
            {"GLOBAL", "REGIONAL", "LOCAL"},
        )
        self.assertTrue(all("Datos sintéticos" in item["limitations"] for item in catalog["investigations"]))

    def test_catalog_is_a_defensive_copy(self):
        first = workspace_catalog()
        first["investigations"][0]["title"] = "MUTATED"
        second = workspace_catalog()
        self.assertNotEqual(second["investigations"][0]["title"], "MUTATED")

    def test_correlated_source_does_not_inflate_independent_roots(self):
        item = get_investigation("global-components-001")
        self.assertEqual(len(item["sources"]), 4)
        self.assertEqual(item["evidence_summary"]["independent_roots"], 3)
        claim = next(claim for claim in item["claims"] if claim["claim_id"] == "CLM-G-01")
        self.assertEqual(len(claim["source_ids"]), 3)
        self.assertEqual(claim["independent_roots"], 2)

    def test_pareto_dominance_prefers_strategy_without_scalar_score(self):
        result = compare_investigation_strategies(
            "global-components-001", "STR-G-A", "STR-G-B"
        )
        self.assertEqual(result["comparison"]["verdict"], "PREFER_LEFT")
        self.assertEqual(result["comparison"]["preferred_strategy_id"], "STR-G-A")
        self.assertNotIn("score", result["comparison"])

    def test_crossed_advantages_remain_incomparable(self):
        result = compare_investigation_strategies(
            "global-components-001", "STR-G-A", "STR-G-C"
        )
        self.assertEqual(result["comparison"]["verdict"], "INCOMPARABLE")
        self.assertIsNone(result["comparison"]["preferred_strategy_id"])

    def test_failed_red_team_prevents_preference(self):
        result = compare_investigation_strategies(
            "regional-ca-electronics-002", "STR-R-A", "STR-R-B"
        )
        self.assertEqual(result["comparison"]["verdict"], "INSUFFICIENT_EVIDENCE")

    def test_scope_mismatch_is_explicit(self):
        left = get_investigation("global-components-001")["strategies"][0]
        right = get_investigation("regional-ca-electronics-002")["strategies"][0]
        result = compare_strategies(left, right)
        self.assertEqual(result["verdict"], "SCOPE_MISMATCH")

    def test_unknown_and_self_comparisons_fail_closed(self):
        with self.assertRaises(LogisticsContractViolation):
            compare_investigation_strategies("missing", "A", "B")
        item = get_investigation("global-components-001")
        with self.assertRaises(LogisticsContractViolation):
            compare_strategies(item["strategies"][0], item["strategies"][0])

    def test_malformed_metric_and_unknown_fields_are_rejected(self):
        value = deepcopy(get_investigation("global-components-001")["strategies"][0])
        value["metrics"]["coverage_pct"] = 101
        with self.assertRaises(LogisticsContractViolation):
            StrategyObservation.from_mapping(value)
        value = deepcopy(get_investigation("global-components-001")["strategies"][0])
        value["uncontracted"] = True
        with self.assertRaises(LogisticsContractViolation):
            StrategyObservation.from_mapping(value)

    def test_non_finite_metrics_are_rejected(self):
        for metric, invalid in (("coverage_pct", float("nan")), ("independent_roots", float("inf"))):
            with self.subTest(metric=metric):
                value = deepcopy(get_investigation("global-components-001")["strategies"][0])
                value["metrics"][metric] = invalid
                with self.assertRaises(LogisticsContractViolation):
                    StrategyObservation.from_mapping(value)

    def test_fixture_lineage_and_strategy_roots_fail_closed(self):
        item = get_investigation("global-components-001")
        item["claims"][0]["independent_roots"] = 99
        with self.assertRaises(LogisticsContractViolation):
            validate_investigation(item)
        item = get_investigation("global-components-001")
        item["sources"][0]["supports"] = ["UNKNOWN-CLAIM"]
        with self.assertRaises(LogisticsContractViolation):
            validate_investigation(item)
        item = get_investigation("global-components-001")
        item["strategies"][0]["metrics"]["independent_roots"] = 4
        with self.assertRaises(LogisticsContractViolation):
            validate_investigation(item)


if __name__ == "__main__":
    unittest.main()
