import unittest

from sictra_block2_design.entrypoint import TrialDraft, assess_trial
from sictra_block2_design.entrypoint_oracle import expected_entrypoint
from sictra_block2_design.preflight import Candidate, ClaimComposition, Confounder, ObserverProfile, TaskDefinition
from sictra_block2_design.upstream import UpstreamRecord


def upstream(**changes):
    value = UpstreamRecord(
        "INTEL-001", "source:INTEL-001:v1", ("FACT-001",), ("EVIDENCE-001",), "VERIFIED",
        "AUTHORITY-001", "export-operations-lead", "prioritize outreach segments", ("PROVENANCE-001",), "CURRENT",
    )
    return UpstreamRecord(**{field: changes.get(field, getattr(value, field)) for field in value.__dataclass_fields__})


def draft(**changes):
    task = TaskDefinition("CLAIM-001", "role fit", "compare", "one audience", "TASK-v1", "Which role owns coordination?", True)
    common = dict(
        content_id="INTEL-001", task_version="TASK-v1", labels=("role", "fit"),
        scale="ordinal-3", uncertainty_object="evidence-status", annotation_burden="one-caption",
        context_version="CONTEXT-v1", attention_condition="first-view", implementation_burden="static",
    )
    value = TrialDraft(
        "FIXTURE-001", task, Candidate("A", "position", **common), Candidate("B", "table", **common),
        "visual mechanism", ObserverProfile("observer-001", True, True, False, "COUNTERBALANCED"),
        (Confounder("mechanism", "MANIPULATED", True),),
    )
    return TrialDraft(**{field: changes.get(field, getattr(value, field)) for field in value.__dataclass_fields__})


class E01EntrypointOracleTests(unittest.TestCase):
    def assert_matches_oracle(self, record, trial):
        actual = assess_trial(record, trial)
        expected = expected_entrypoint(record, trial)
        self.assertEqual(expected.upstream_disposition, actual.upstream.disposition)
        self.assertEqual(expected.preflight_disposition, actual.preflight.disposition)
        self.assertEqual(expected.reasons, actual.preflight.reasons)
        self.assertEqual(expected.quarantined_claim_ids, actual.preflight.quarantined_claim_ids)

    def test_clean_request_matches_declarative_oracle(self):
        self.assert_matches_oracle(upstream(), draft())

    def test_upstream_precedence_matches_declarative_oracle(self):
        leaking = TaskDefinition("CLAIM-001", "role fit", "compare", "one audience", "TASK-v1", "Which role owns coordination?", False)
        self.assert_matches_oracle(upstream(evidence_refs=()), draft(task=leaking))

    def test_downstream_multi_failure_matches_declarative_oracle(self):
        candidate = draft().candidate_b
        unequal = Candidate(**{
            field: ("different" if field == "scale" else getattr(candidate, field))
            for field in candidate.__dataclass_fields__
        })
        observer = ObserverProfile("observer-001", True, False, True, "UNCONTROLLED")
        self.assert_matches_oracle(upstream(), draft(candidate_b=unequal, observer=observer))

    def test_claim_composition_boundary_matches_declarative_oracle(self):
        self.assert_matches_oracle(upstream(), draft(composition=ClaimComposition(("A", "B"), False)))


if __name__ == "__main__":
    unittest.main()
