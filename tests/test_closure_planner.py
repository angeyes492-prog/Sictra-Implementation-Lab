import unittest

from tools.closure_planner import ClosureItem, plan, render_markdown


def item(identifier, state="READY_FOR_TECHNICAL_WORK", **dimensions):
    values = {"risk": 1, "dependency_impact": 1, "evidence_gap": 1, "irreversibility": 1}
    values.update(dimensions)
    return ClosureItem(identifier, identifier, state, next_action="act", evidence="evidence", **values)


class ClosurePlannerTests(unittest.TestCase):
    def test_higher_risk_technical_work_is_ranked_first_deterministically(self):
        low = item("LOW")
        high = item("HIGH", risk=5, dependency_impact=5, evidence_gap=4, irreversibility=3)
        self.assertEqual(["HIGH", "LOW"], [value.identifier for value in plan([low, high])["TECHNICAL"]])

    def test_human_gate_never_appears_as_autonomous_technical_work(self):
        gate = item("REVIEW", state="HUMAN_REVIEW_REQUIRED", risk=5)
        lanes = plan([gate])
        self.assertEqual([], lanes["TECHNICAL"])
        self.assertEqual([gate], lanes["HUMAN_GATE"])

    def test_invalid_priority_dimension_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "risk"):
            ClosureItem.from_mapping({"identifier": "BAD", "title": "bad", "state": "READY", "risk": 0, "dependency_impact": 1, "evidence_gap": 1, "irreversibility": 1, "next_action": "x", "evidence": "x"})

    def test_render_exposes_evidence_and_never_claims_gate_promotion(self):
        rendered = render_markdown([item("REVIEW", state="HUMAN_REVIEW_REQUIRED", risk=5)])
        self.assertIn("Human / architecture gates", rendered)
        self.assertIn("evidence", rendered)
        self.assertNotIn("APPROVED", rendered)

