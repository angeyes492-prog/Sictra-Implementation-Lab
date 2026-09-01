import unittest

from sictra_block2_design.preflight import (
    Candidate,
    ClaimComposition,
    Confounder,
    Fixture,
    ObserverProfile,
    TaskDefinition,
    UpstreamIntelligence,
    assess_fixture,
)


def fixture(**changes):
    upstream = UpstreamIntelligence(
        object_id="INTEL-001",
        source_identity="source:INTEL-001:v1",
        evidence_status="VERIFIED",
        authority_reference="authority:INTEL-001:v1",
        audience_context="export-operations-lead",
        decision_context="prioritize outreach segments",
    )
    task = TaskDefinition(
        claim_id="CLAIM-001",
        target="rank export-operation roles by fit",
        action="compare",
        scope="one audience and one decision",
        version="TASK-v1",
        wording="Which role group is most directly responsible for export coordination?",
        leakage_clear=True,
    )
    common = dict(
        content_id="INTEL-001", task_version="TASK-v1", labels=("role", "fit"),
        scale="ordinal-3", uncertainty_object="evidence-status", annotation_burden="one-caption",
        context_version="CONTEXT-v1", attention_condition="first-view", implementation_burden="static",
    )
    candidate_a = Candidate(candidate_id="A", mechanism="aligned-position", **common)
    candidate_b = Candidate(candidate_id="B", mechanism="grouped-table", **common)
    observer = ObserverProfile("observer-001", True, True, False, "COUNTERBALANCED")
    value = Fixture(
        fixture_id="FIXTURE-001", upstream=upstream, task=task,
        candidate_a=candidate_a, candidate_b=candidate_b,
        intended_manipulation="visual mechanism", observer=observer,
        confounders=(Confounder("mechanism", "MANIPULATED", True),),
    )
    return Fixture(**{name: changes.get(name, getattr(value, name)) for name in value.__dataclass_fields__})


class E01PreflightTests(unittest.TestCase):
    def test_clean_fixture_is_ready_but_not_observed(self):
        result = assess_fixture(fixture())
        self.assertEqual(result.disposition, "READY_FOR_OBSERVATION")
        self.assertTrue(result.ready_for_observation)
        self.assertEqual(result.reasons, ())

    def test_missing_upstream_authority_returns_upstream(self):
        upstream = fixture().upstream
        incomplete = UpstreamIntelligence(
            upstream.object_id, upstream.source_identity, upstream.evidence_status,
            "", upstream.audience_context, upstream.decision_context,
        )
        result = assess_fixture(fixture(upstream=incomplete))
        self.assertEqual(result.disposition, "RETURN_UPSTREAM")
        self.assertIn("AUTHORITY_REFERENCE", result.reasons)

    def test_task_leakage_invalidates_claim(self):
        task = fixture().task
        result = assess_fixture(fixture(task=TaskDefinition(**{
            field: (False if field == "leakage_clear" else getattr(task, field))
            for field in task.__dataclass_fields__
        })))
        self.assertEqual(result.disposition, "INVALID_TRIAL")
        self.assertIn("TASK_LEAKAGE", result.reasons)

    def test_label_asymmetry_is_not_attributed_to_mechanism(self):
        candidate = fixture().candidate_b
        unequal = Candidate(**{
            field: (("role", "fit", "hint") if field == "labels" else getattr(candidate, field))
            for field in candidate.__dataclass_fields__
        })
        result = assess_fixture(fixture(candidate_b=unequal))
        self.assertEqual(result.disposition, "INVALID_TRIAL")
        self.assertIn("SEMANTIC_EQUIVALENCE_LABELS", result.reasons)

    def test_uncertainty_object_mismatch_is_invalid(self):
        candidate = fixture().candidate_b
        unequal = Candidate(**{
            field: ("forecast-interval" if field == "uncertainty_object" else getattr(candidate, field))
            for field in candidate.__dataclass_fields__
        })
        result = assess_fixture(fixture(candidate_b=unequal))
        self.assertIn("SEMANTIC_EQUIVALENCE_UNCERTAINTY_OBJECT", result.reasons)

    def test_material_observer_leakage_is_invalid(self):
        observer = fixture().observer
        contaminated = ObserverProfile(
            observer.observer_id, observer.external_to_e01, observer.independence_reviewed,
            True, observer.order_condition,
        )
        result = assess_fixture(fixture(observer=contaminated))
        self.assertEqual(result.disposition, "INVALID_TRIAL")
        self.assertIn("OBSERVER_MATERIAL_LEAKAGE", result.reasons)

    def test_uncontrolled_order_is_invalid(self):
        observer = fixture().observer
        result = assess_fixture(fixture(observer=ObserverProfile(
            observer.observer_id, True, True, False, "UNCONTROLLED"
        )))
        self.assertIn("ORDER_UNCONTROLLED", result.reasons)

    def test_post_trial_material_confounder_is_invalid(self):
        result = assess_fixture(fixture(confounders=(
            Confounder("familiarity", "DISCOVERED_POST_TRIAL", True),
        )))
        self.assertIn("MATERIAL_CONFOUNDER_familiarity", result.reasons)

    def test_unverified_claim_composition_stays_separate(self):
        result = assess_fixture(fixture(composition=ClaimComposition(("CLAIM-A", "CLAIM-B"), False)))
        self.assertEqual(result.disposition, "UNSUPPORTED_COMBINATION")
        self.assertIn("EVIDENCE_CONJUNCTION_OVERREACH", result.reasons)

    def test_invalidity_precedes_unsupported_composition(self):
        task = fixture().task
        leaking_task = TaskDefinition(**{
            field: (False if field == "leakage_clear" else getattr(task, field))
            for field in task.__dataclass_fields__
        })
        result = assess_fixture(fixture(
            task=leaking_task,
            composition=ClaimComposition(("CLAIM-A", "CLAIM-B"), False),
        ))
        self.assertEqual(result.disposition, "INVALID_TRIAL")


if __name__ == "__main__":
    unittest.main()
