"""Contract, adversarial, and selection tests for the Editorial Engine."""

from __future__ import annotations

from copy import deepcopy
import unittest

from sictra_block1.editorial import (
    EditorialContractViolation,
    assess_editorial_candidate,
    editorial_cycle,
    editorial_fixture_cycle,
    select_flagship,
)


def candidate(candidate_id: str = "ED-C01", **changes):
    value = {
        "candidate_id": candidate_id,
        "event_id": f"EV-{candidate_id}",
        "title": f"Candidate {candidate_id}",
        "state": "DELIVERABLE_BOUNDED",
        "profile": {
            "impact": 80,
            "relevance": 75,
            "novelty": 70,
            "uncertainty": 25,
            "timeliness": 85,
            "actionability": 72,
            "evidence_strength": 80,
            "interpretive_value": 78,
        },
        "evidence": {
            "source_ids": [f"SRC-{candidate_id}-1", f"SRC-{candidate_id}-2"],
            "root_ids": [f"ROOT-{candidate_id}-1", f"ROOT-{candidate_id}-2"],
            "required_roots": 2,
            "provenance_integrity": True,
            "source_approved": True,
            "scope_authorized": True,
            "freshness": "CURRENT",
            "contradictions_bounded": True,
            "license_compatible": True,
            "sensitive_data": False,
        },
        "red_team": "PASS",
        "stability": "STABLE",
        "dimensions": {
            "geography": "GLOBAL",
            "mode": "MARITIME",
            "topic": "TRADE",
            "audience": "IMPORTER",
            "horizon": "30D",
        },
        "editorial": {
            "what_changed": "A synthetic logistics condition changed.",
            "why_it_matters": "It may alter a bounded planning assumption.",
            "who_is_affected": ["IMPORTER"],
            "interpretation": "The relative value of options may have changed.",
            "executive_question": "Which planning assumption needs revalidation?",
            "implicit_company_implication": "Review exposure before acting.",
            "alternatives": ["The signal may be temporary."],
            "limitations": ["Synthetic field fixture."],
        },
        "derivations": {
            "global_frame_id": f"GLOBAL-{candidate_id}",
            "segment_frame_ids": [f"SEGMENT-{candidate_id}"],
            "account_frame_ids": [],
        },
        "watchlist": [
            {"horizon": "7D", "observable": "Synthetic confirmation", "trigger": "2 roots"},
            {"horizon": "30D", "observable": "Synthetic persistence", "trigger": "2 cycles"},
            {"horizon": "90D", "observable": "Synthetic structural change", "trigger": "review"},
        ],
    }
    value.update(changes)
    return value


def contains_key(value, forbidden):
    if isinstance(value, dict):
        return forbidden in value or any(contains_key(item, forbidden) for item in value.values())
    if isinstance(value, list):
        return any(contains_key(item, forbidden) for item in value)
    return False


class EditorialEngineTests(unittest.TestCase):
    def test_high_uncertainty_increases_research_priority_but_blocks_readiness(self):
        value = candidate()
        value["profile"]["uncertainty"] = 90
        result = assess_editorial_candidate(value)
        self.assertEqual(result["research_priority"], "HIGH")
        self.assertEqual(result["editorial_readiness"], "BLOCKED")
        self.assertEqual(result["disposition"], "RESEARCH_NEEDED")
        self.assertIn("MATERIAL_UNCERTAINTY", result["reasons"])
        self.assertNotIn("score", result)

    def test_broken_provenance_quarantines_even_when_profile_is_strong(self):
        value = candidate()
        value["evidence"]["provenance_integrity"] = False
        result = assess_editorial_candidate(value)
        self.assertEqual(result["disposition"], "QUARANTINED")
        self.assertEqual(result["editorial_readiness"], "BLOCKED")

    def test_correlated_sources_count_as_one_root_and_require_more_research(self):
        value = candidate()
        value["evidence"]["source_ids"] = ["SRC-1", "SRC-2", "SRC-3"]
        value["evidence"]["root_ids"] = ["ROOT-A", "ROOT-A", "ROOT-A"]
        result = assess_editorial_candidate(value)
        self.assertEqual(result["independent_roots"], 1)
        self.assertEqual(result["disposition"], "RESEARCH_NEEDED")
        self.assertIn("INSUFFICIENT_INDEPENDENT_ROOTS", result["reasons"])

    def test_cycle_uses_pareto_frontier_without_universal_score(self):
        dominant = candidate("ED-A")
        dominated = candidate("ED-B")
        dominated["profile"].update({
            "impact": 70, "relevance": 65, "novelty": 60,
            "uncertainty": 30, "timeliness": 75, "actionability": 62,
            "evidence_strength": 70, "interpretive_value": 68,
        })
        crossed = candidate("ED-C")
        crossed["profile"].update({"impact": 95, "evidence_strength": 65})
        result = editorial_cycle([dominant, dominated, crossed], min_candidates=2, max_candidates=5)
        self.assertEqual(set(result["pareto_frontier_ids"]), {"ED-A", "ED-C"})
        self.assertNotIn("ED-B", result["pareto_frontier_ids"])
        self.assertFalse(contains_key(result, "score"))

    def test_shortlist_is_diverse_deterministic_and_bounded(self):
        values = []
        dimensions = [
            ("GLOBAL", "MARITIME", "TRADE", "IMPORTER", "30D"),
            ("AMERICAS", "AIR", "TECHNOLOGY", "EXPORTER", "7D"),
            ("EUROPE", "ROAD", "CUSTOMS", "PROCUREMENT", "90D"),
            ("ASIA", "RAIL", "RISK", "MANUFACTURER", "30D"),
            ("AFRICA", "PORT", "INFRASTRUCTURE", "IMPORTER", "90D"),
            ("GLOBAL", "MARITIME", "TRADE", "IMPORTER", "30D"),
        ]
        for index, dimension in enumerate(dimensions):
            value = candidate(f"ED-{index}")
            value["dimensions"] = dict(zip(
                ("geography", "mode", "topic", "audience", "horizon"), dimension
            ))
            values.append(value)
        first = editorial_cycle(values, min_candidates=3, max_candidates=5)
        second = editorial_cycle(deepcopy(values), min_candidates=3, max_candidates=5)
        self.assertEqual(first["shortlist_ids"], second["shortlist_ids"])
        self.assertEqual(len(first["shortlist_ids"]), 5)
        self.assertGreaterEqual(first["diversity"]["geographies"], 4)

    def test_fewer_than_minimum_candidates_returns_no_shortlist(self):
        result = editorial_cycle([candidate("ED-ONLY")], min_candidates=3, max_candidates=5)
        self.assertEqual(result["status"], "INSUFFICIENT_ELIGIBLE_CANDIDATES")
        self.assertEqual(result["shortlist_ids"], [])

    def test_human_selection_is_bounded_to_shortlist_and_never_publishes(self):
        cycle = editorial_fixture_cycle()
        selected_id = cycle["shortlist_ids"][0]
        dossier = select_flagship(cycle, selected_id, selected_by="LOCAL_HUMAN_OPERATOR")
        self.assertEqual(dossier["selected_candidate_id"], selected_id)
        self.assertEqual(dossier["selection"]["authority"], "HUMAN_EDITORIAL_CHOICE")
        self.assertNotIn("publish", str(dossier).lower())
        self.assertIn("BLOCK2_DESIGN_HANDOFF", dossier["handoff"]["type"])
        with self.assertRaises(EditorialContractViolation):
            select_flagship(cycle, "ED-NOT-SHORTLISTED", selected_by="LOCAL_HUMAN_OPERATOR")

    def test_forged_cycle_cannot_promote_a_blocked_candidate(self):
        cycle = editorial_fixture_cycle()
        blocked = next(
            item["candidate_id"] for item in cycle["assessments"]
            if item["disposition"] == "QUARANTINED"
        )
        cycle["shortlist_ids"].append(blocked)
        next(
            item for item in cycle["assessments"] if item["candidate_id"] == blocked
        )["editorial_readiness"] = "READY"
        with self.assertRaises(EditorialContractViolation):
            select_flagship(cycle, blocked, selected_by="LOCAL_HUMAN_OPERATOR")

    def test_cycle_rejects_unbounded_candidate_input(self):
        with self.assertRaises(EditorialContractViolation):
            editorial_cycle(
                (candidate(f"ED-{index}") for index in range(501)),
                min_candidates=3,
                max_candidates=5,
            )

    def test_contract_rejects_unknown_fields_bad_ranges_and_bad_watchlist(self):
        value = candidate()
        value["unexpected"] = True
        with self.assertRaises(EditorialContractViolation):
            assess_editorial_candidate(value)
        value = candidate()
        value["profile"]["impact"] = 101
        with self.assertRaises(EditorialContractViolation):
            assess_editorial_candidate(value)
        value = candidate()
        value["watchlist"][0]["horizon"] = "14D"
        with self.assertRaises(EditorialContractViolation):
            assess_editorial_candidate(value)

    def test_fixture_cycle_has_three_to_five_ready_and_explicit_blocks(self):
        cycle = editorial_fixture_cycle()
        self.assertEqual(cycle["fixture_class"], "SYNTHETIC_FIELD_TEST")
        self.assertIn(cycle["status"], {"SHORTLIST_READY", "INSUFFICIENT_ELIGIBLE_CANDIDATES"})
        self.assertGreaterEqual(len(cycle["shortlist_ids"]), 3)
        self.assertLessEqual(len(cycle["shortlist_ids"]), 5)
        dispositions = {item["disposition"] for item in cycle["assessments"]}
        self.assertIn("RESEARCH_NEEDED", dispositions)
        self.assertIn("QUARANTINED", dispositions)


if __name__ == "__main__":
    unittest.main()
