from copy import deepcopy
import unittest

from sictra_block1.change_context import ChangeContextViolation, project_change_context
from sictra_block1.intelligence_dossier import build_intelligence_dossier
from test_block1_intelligence_dossier import reviewable_delta, BRIDGE_KEY


def dossier():
    return build_intelligence_dossier(reviewable_delta(), bridge_keys={"watchlist-bridge": BRIDGE_KEY})


class ChangeContextTests(unittest.TestCase):
    def test_same_period_value_is_not_causal_or_statistical_revision(self):
        value = dossier()
        before = deepcopy(value)
        result = project_change_context(value)
        self.assertEqual([{"fact_id": "FACT-001", "kind": "SAME_PERIOD_REPORTED_VALUE_CHANGE",
                          "geography": "BE", "before_period": "2021", "after_period": "2021",
                          "unit": "THOUSAND_TONNES"}], result["facts"])
        self.assertEqual("UNCONFIRMED", result["cause_certainty"])
        self.assertEqual("NOT_RESOLVED", result["resolution"])
        self.assertEqual("NOT_ACCEPTED", result["acceptance"])
        self.assertEqual("BLOCKED", result["publication"])
        self.assertEqual(before, value)
        self.assertEqual(result, project_change_context(value))

    def test_added_removed_and_flag_only_have_distinct_literal_contexts(self):
        cases = [("ADDED_OBSERVATION", None, 15.0, None, None, "OBSERVATION_COVERAGE_ADDED"),
                 ("REMOVED_OBSERVATION", 15.0, None, None, None, "OBSERVATION_COVERAGE_REMOVED"),
                 ("FLAG_CHANGED", 15.0, 15.0, None, "p", "SAME_PERIOD_STATUS_FLAG_CHANGE")]
        for kind, before, after, old_flag, flag, expected in cases:
            with self.subTest(kind=kind):
                value = dossier()
                value["facts"][0]["observed_change"].update(change_type=kind,
                    before_value_thousand_tonnes=before, after_value_thousand_tonnes=after,
                    absolute_delta_thousand_tonnes=0.0 if kind == "FLAG_CHANGED" else None,
                    before_status_flag=old_flag, after_status_flag=flag)
                self.assertEqual(expected, project_change_context(value)["facts"][0]["kind"])

    def test_bad_measurement_null_flag_or_scope_never_gets_a_context(self):
        changes = [{"before_value_thousand_tonnes": None}, {"after_value_thousand_tonnes": True},
                   {"after_value_thousand_tonnes": float("nan")}, {"absolute_delta_thousand_tonnes": 99},
                   {"after_value_thousand_tonnes": 13.5, "absolute_delta_thousand_tonnes": 0.0},
                   {"time_period": True}, {"before_status_flag": []}, {"change_type": "CAUSAL_CHANGE"},
                   {"change_type": "ADDED_OBSERVATION", "absolute_delta_thousand_tonnes": None},
                   {"change_type": "FLAG_CHANGED"}, {"after_value_thousand_tonnes": 10 ** 400},
                   {"absolute_delta_thousand_tonnes": 10 ** 400},
                   {"after_value_thousand_tonnes": -1}]
        for mutation in changes:
            with self.subTest(mutation=mutation):
                value = dossier()
                value["facts"][0]["observed_change"].update(mutation)
                with self.assertRaises(ChangeContextViolation):
                    project_change_context(value)

    def test_schema_lineage_authority_and_duplicate_rejection(self):
        for field, content in [("schema_version", "next"), ("scope", "PRODUCTION"),
                               ("publication_state", "ALLOWED"), ("interpretations", ["cause"]),
                               ("dossier_id", "eurostat:forged"), ("facts", [])]:
            value = dossier()
            value[field] = content
            with self.assertRaises(ChangeContextViolation):
                project_change_context(value)
        for mutate in (lambda d: d["source"].update(source_id="unknown"),
                       lambda d: d["facts"][0]["evidence_refs"].update(content_sha256="0" * 64),
                       lambda d: d["facts"][0]["observed_change"].pop("before_status_flag"),
                       lambda d: d["facts"].append(deepcopy(d["facts"][0]))):
            value = dossier()
            mutate(value)
            with self.assertRaises(ChangeContextViolation):
                project_change_context(value)

    def test_distinct_customs_periods_not_same_period_revision(self):
        value = dossier()
        value.update(schema_version="HN_CUSTOMS_DOSSIER_V1", scope="BLOCK1_LOCAL_HN_CUSTOMS_PERIOD_PIPELINE",
                     dossier_id="hn-customs:" + value["source"]["delta_sha256"])
        value["source"]["source_id"] = "HN_ADUANAS_BULLETINS"
        fact = value["facts"][0]
        fact["evidence_refs"] = {"source_id": "HN_ADUANAS_BULLETINS",
                                 "current_content_sha256": value["source"]["content_sha256"]}
        fact["observed_change"] = {"customs_point": "Puerto Cortes", "before_period": "2024Q1",
            "after_period": "2025Q1", "change_type": "VALUE_CHANGED", "before_value_usd_million": 10.0,
            "after_value_usd_million": 12.0, "absolute_delta_usd_million": 2.0, "relative_delta": 0.2}
        result = project_change_context(value)
        self.assertEqual("DISTINCT_PERIOD_VALUE_COMPARISON", result["facts"][0]["kind"])
        self.assertEqual("USD_MILLION", result["facts"][0]["unit"])
        bad = deepcopy(value)
        bad["facts"][0]["observed_change"]["relative_delta"] = 0.9
        with self.assertRaisesRegex(ChangeContextViolation, "RELATIVE_DELTA_INVALID"):
            project_change_context(bad)
        for before, after in [("2025Q1", "2025Q1"), ("2026Q1", "2025Q1"), ("2024Q2", "2025Q1"), (None, "2025Q1")]:
            with self.subTest(before=before, after=after):
                bad = deepcopy(value)
                bad["facts"][0]["observed_change"].update(before_period=before, after_period=after)
                with self.assertRaises(ChangeContextViolation):
                    project_change_context(bad)


if __name__ == "__main__":
    unittest.main()
