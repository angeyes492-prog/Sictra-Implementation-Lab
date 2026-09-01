import unittest

from sictra_block2_design.entrypoint import TrialDraft, assess_trial
from sictra_block2_design.preflight import Candidate, Confounder, ObserverProfile, TaskDefinition
from sictra_block2_design.upstream import UpstreamRecord


def upstream(**changes):
    value = UpstreamRecord(
        object_id="INTEL-001",
        source_identity="source:INTEL-001:v1",
        fact_ids=("FACT-001",),
        evidence_refs=("EVIDENCE-001",),
        certainty="VERIFIED",
        authority_reference="AUTHORITY-001",
        audience_context="export-operations-lead",
        decision_context="prioritize outreach segments",
        provenance_refs=("PROVENANCE-001",),
        temporal_state="CURRENT",
    )
    return UpstreamRecord(**{
        field: changes.get(field, getattr(value, field))
        for field in value.__dataclass_fields__
    })


def draft(**changes):
    task = TaskDefinition("CLAIM-001", "role fit", "compare", "one audience", "TASK-v1", "Which role owns coordination?", True)
    common = dict(
        content_id="INTEL-001", task_version="TASK-v1", labels=("role", "fit"),
        scale="ordinal-3", uncertainty_object="evidence-status", annotation_burden="one-caption",
        context_version="CONTEXT-v1", attention_condition="first-view", implementation_burden="static",
    )
    value = TrialDraft(
        fixture_id="FIXTURE-001", task=task,
        candidate_a=Candidate("A", "position", **common),
        candidate_b=Candidate("B", "table", **common),
        intended_manipulation="visual mechanism",
        observer=ObserverProfile("observer-001", True, True, False, "COUNTERBALANCED"),
        confounders=(Confounder("mechanism", "MANIPULATED", True),),
    )
    return TrialDraft(**{
        field: changes.get(field, getattr(value, field))
        for field in value.__dataclass_fields__
    })


class E01EntrypointTests(unittest.TestCase):
    def test_normalized_clean_request_is_ready_but_not_observed(self):
        result = assess_trial(upstream(), draft())
        self.assertEqual("NORMALIZED", result.upstream.disposition)
        self.assertEqual("READY_FOR_OBSERVATION", result.preflight.disposition)
        self.assertTrue(result.ready_for_observation)

    def test_missing_evidence_blocks_before_a_leaking_task_is_classified(self):
        leaking = TaskDefinition("CLAIM-001", "role fit", "compare", "one audience", "TASK-v1", "Which role owns coordination?", False)
        result = assess_trial(upstream(evidence_refs=()), draft(task=leaking))
        self.assertEqual("RETURN_UPSTREAM", result.preflight.disposition)
        self.assertEqual(("EVIDENCE_MISSING",), result.preflight.reasons)
        self.assertNotIn("TASK_LEAKAGE", result.preflight.reasons)

    def test_stale_upstream_cannot_reach_fixture_equivalence_logic(self):
        unequal = draft().candidate_b
        broken = Candidate(**{
            field: ("different" if field == "scale" else getattr(unequal, field))
            for field in unequal.__dataclass_fields__
        })
        result = assess_trial(upstream(temporal_state="STALE"), draft(candidate_b=broken))
        self.assertEqual("RETURN_UPSTREAM", result.preflight.disposition)
        self.assertEqual(("UPSTREAM_NOT_CURRENT",), result.preflight.reasons)
        self.assertFalse(result.ready_for_observation)

    def test_valid_upstream_allows_downstream_trial_rejection_to_remain_visible(self):
        task = draft().task
        leaking = TaskDefinition(**{
            field: (False if field == "leakage_clear" else getattr(task, field))
            for field in task.__dataclass_fields__
        })
        result = assess_trial(upstream(), draft(task=leaking))
        self.assertEqual("NORMALIZED", result.upstream.disposition)
        self.assertEqual("INVALID_TRIAL", result.preflight.disposition)
        self.assertEqual(("TASK_LEAKAGE",), result.preflight.reasons)


if __name__ == "__main__":
    unittest.main()
