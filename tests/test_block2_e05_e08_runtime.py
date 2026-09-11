import unittest
from dataclasses import replace
from datetime import datetime, timezone

from tests.test_block2_e01_preflight import fixture
from tests.test_block2_e02_direction import envelope, thesis, direction_set, structurally_distinct_pair
from tests.test_block2_e03_design_system import proposal as system_profile
from tests.test_block2_e04_information_design import blueprint, payload, target

from sictra_block2_design.e03_design_system import assess_system_profile
from sictra_block2_design.e04_information_design import assess_information_blueprint
from sictra_block2_design.e05_reference_research import (
    GovernedReference, ReferenceResearchProposal, TransferablePrinciple,
    assess_reference_research,
)
from sictra_block2_design.e06_production import (
    ProductionContent, ProductionRequest, build_production_candidate,
)
from sictra_block2_design.e07_visual_red_team import (
    RubricObservation, VisualReview, assess_visual_candidate,
)
from sictra_block2_design.e07_visual_red_team_oracle import expected_visual_disposition
from sictra_block2_design.e08_creative_memory import (
    CreativeMemoryStore, ExternalValidationRecord, MemoryProposal,
    assess_memory_candidate,
)
from sictra_block2_design.runtime import Block2RunInput, execute_block2


NOW = datetime(2026, 8, 30, tzinfo=timezone.utc)
CRITERIA = (
    "COMPREHENSION", "HIERARCHY", "LEGIBILITY", "ACCESSIBILITY",
    "CLAIM_FIDELITY", "CHANNEL_ADAPTATION", "BRAND_AND_RIGHTS",
    "NON_DECEPTIVE_PERSUASION",
)


def reference(reference_id="REF-1", **changes):
    value = GovernedReference(
        reference_id, f"https://example.test/{reference_id}", "IMAGE",
        "ALLOW_CONSTRAINT_ONLY", ("EMAIL",), True, (f"EVIDENCE-{reference_id}",),
    )
    return replace(value, **changes)


def research(**changes):
    refs = (reference("REF-1"), reference("REF-2"))
    principles = (
        TransferablePrinciple("P-1", "REF-1", "HIERARCHY", "clear lead", "one dominant entry point", ("EVIDENCE-REF-1",), True),
        TransferablePrinciple("P-2", "REF-1", "GRID", "stable alignment", "align related evidence", ("EVIDENCE-REF-1",), True),
        TransferablePrinciple("P-3", "REF-2", "ACCESSIBILITY", "redundant labels", "encode meaning beyond color", ("EVIDENCE-REF-2",), True),
        TransferablePrinciple("P-4", "REF-2", "RHYTHM", "group spacing", "use spacing to expose groups", ("EVIDENCE-REF-2",), True),
    )
    value = ReferenceResearchProposal(
        "PACK-001", "0.1.0", "BLUEPRINT-001", "PROFILE-001",
        "fingerprint:upstream-001", "EMAIL", refs, principles,
    )
    return replace(value, **changes)


def production_request(**changes):
    value = ProductionRequest(
        "CANDIDATE-001", "0.1.0", "HTML_EMAIL", "fingerprint:upstream-001",
        "PROFILE-001", "BLUEPRINT-001", "PACK-001", "PRODUCER-001",
        ProductionContent("Executive brief", (("CLAIM-001", "Approved copy"),), "Accessible executive brief"),
    )
    return replace(value, **changes)


def build_candidate(request=None, research_proposal=None):
    profile = system_profile()
    bp = blueprint()
    rp = research_proposal or research()
    e03 = assess_system_profile("fingerprint:upstream-001", structurally_distinct_pair()[0], profile, NOW)
    e04 = assess_information_blueprint("fingerprint:upstream-001", profile, e03.disposition, payload(), target(), bp)
    e05 = assess_reference_research(bp, e04.disposition, rp, NOW)
    e06 = build_production_candidate(profile, bp, e04.disposition, payload(), rp, e05.disposition, request or production_request())
    return e06


def visual_review(candidate, *, score=90, independent=True, reviewer="REVIEWER-001", criteria=CRITERIA):
    observations = tuple(
        RubricObservation(item, score, (f"AUDIT-{item}",), "bounded fixture measurement", "criterion observed")
        for item in criteria
    )
    return VisualReview(
        "REVIEW-001", "0.1.0", candidate.candidate_id, candidate.artifact.sha256,
        reviewer, independent, observations,
    )


def validation(**changes):
    value = ExternalValidationRecord(
        "VALIDATION-001", "HUMAN-002", "AUTHORITY-REVIEW-001", True, True,
        ("ROOT-EXTERNAL",),
    )
    return replace(value, **changes)


def memory(**changes):
    value = MemoryProposal(
        "MEMORY-001", "0.1.0", "REVIEW-001", "CANDIDATE-001", 1, 2,
        "Readers located the claim", "Hierarchy may have supported scanning",
        "Test this hierarchy on a distinct audience", ("ROOT-VISUAL", "ROOT-EXTERNAL"),
        "OWNER-001", True, True, datetime(2027, 8, 30, tzinfo=timezone.utc),
    )
    return replace(value, **changes)


def complete_run_input(**changes):
    directions = direction_set(*structurally_distinct_pair())
    rp = research()
    e06 = build_candidate(research_proposal=rp)
    review = visual_review(e06.candidate)
    value = Block2RunInput(
        fixture(), envelope(), thesis(), directions, directions.directions[0],
        system_profile(), payload(), target(), blueprint(), rp, production_request(),
        review, validation(), memory(),
    )
    return replace(value, **changes)


class E05ReferenceResearchTests(unittest.TestCase):
    def test_professional_abstract_pack_is_ready(self):
        result = assess_reference_research(blueprint(), "BLUEPRINT_READY_FOR_PRODUCTION_REVIEW", research(), NOW)
        self.assertEqual("RESEARCH_PACK_READY_FOR_PRODUCTION", result.disposition)
        self.assertEqual(("REF-1", "REF-2"), result.usable_reference_ids)

    def test_identifiable_imitation_is_quarantined(self):
        refs = (reference(requested_uses=("IMITATE_IDENTIFIABLE_STYLE",)), reference("REF-2"))
        result = assess_reference_research(blueprint(), "BLUEPRINT_READY_FOR_PRODUCTION_REVIEW", research(references=refs), NOW)
        self.assertEqual("QUARANTINE_REFERENCE", result.disposition)
        self.assertIn("REF-1", result.quarantined_reference_ids)

    def test_identity_dependent_or_unbound_principle_is_contradicted(self):
        bad = replace(research().principles[0], identity_independent=False, evidence_ids=("OTHER",))
        result = assess_reference_research(blueprint(), "BLUEPRINT_READY_FOR_PRODUCTION_REVIEW", research(principles=(bad,) + research().principles[1:]), NOW)
        self.assertEqual("CONTRADICTED", result.disposition)
        self.assertEqual(2, len(result.reasons))

    def test_insufficient_professional_coverage_returns_to_previous(self):
        result = assess_reference_research(blueprint(), "BLUEPRINT_READY_FOR_PRODUCTION_REVIEW", research(principles=research().principles[:2]), NOW)
        self.assertEqual("RETURN_TO_PREVIOUS", result.disposition)


class E06ProductionTests(unittest.TestCase):
    def test_html_adapter_is_deterministic_and_accessible(self):
        first = build_candidate()
        second = build_candidate()
        self.assertEqual("PRODUCTION_CANDIDATE_READY_FOR_REVIEW", first.disposition)
        self.assertEqual(first.candidate.artifact.sha256, second.candidate.artifact.sha256)
        self.assertEqual("text/plain", first.candidate.artifact.accessibility_media_type)
        self.assertEqual("NOT_PUBLISHED", first.candidate.publication_state)

    def test_publication_and_remote_resources_are_scope_violations(self):
        result = build_candidate(production_request(publish_requested=True, remote_resource_urls=("https://remote.test/a.png",)))
        self.assertEqual("SCOPE_VIOLATION", result.disposition)

    def test_unapproved_copy_is_rejected(self):
        request = production_request(content=ProductionContent("Brief", (("CLAIM-001", "Invented copy"),), "Description"))
        self.assertEqual("RETURN_TO_PREVIOUS", build_candidate(request).disposition)

    def test_approved_markup_is_escaped_instead_of_executed(self):
        hostile = "<script>alert('x')</script>"
        source = replace(payload(), approved_copy=(hostile,))
        profile = system_profile()
        bp = blueprint()
        rp = research()
        e03 = assess_system_profile("fingerprint:upstream-001", structurally_distinct_pair()[0], profile, NOW)
        e04 = assess_information_blueprint("fingerprint:upstream-001", profile, e03.disposition, source, target(), bp)
        e05 = assess_reference_research(bp, e04.disposition, rp, NOW)
        request = production_request(content=ProductionContent("<img onerror=x>", (("CLAIM-001", hostile),), "<unsafe>"))
        result = build_production_candidate(profile, bp, e04.disposition, source, rp, e05.disposition, request)
        rendered = result.candidate.artifact.content.decode("utf-8")
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("<img onerror=x>", rendered)
        self.assertIn("&lt;script&gt;", rendered)

    def test_svg_adapter_materializes_a_graphic_with_text_alternative(self):
        profile = replace(
            system_profile(), target_channel="WEB", supported_channels=("WEB",),
            assets=(replace(system_profile().assets[0], allowed_channels=("WEB",)),),
        )
        destination = replace(target(), artifact_type="GRAPHIC", channel="WEB")
        bp = replace(
            blueprint(), artifact_type="GRAPHIC", channel="WEB",
            accessibility_fallbacks=("ALT_TEXT", "LEGEND"),
        )
        rp = replace(research(), target_channel="WEB")
        request = replace(production_request(), adapter="SVG")
        e03 = assess_system_profile("fingerprint:upstream-001", structurally_distinct_pair()[0], profile, NOW)
        e04 = assess_information_blueprint("fingerprint:upstream-001", profile, e03.disposition, payload(), destination, bp)
        e05 = assess_reference_research(bp, e04.disposition, rp, NOW)
        result = build_production_candidate(profile, bp, e04.disposition, payload(), rp, e05.disposition, request)
        self.assertEqual("image/svg+xml", result.candidate.artifact.media_type)
        self.assertIn(b"<svg", result.candidate.artifact.content)
        self.assertTrue(result.candidate.artifact.accessibility_content)


class E07VisualRedTeamTests(unittest.TestCase):
    def test_complete_independent_review_matches_oracle(self):
        production = build_candidate()
        review = visual_review(production.candidate)
        result = assess_visual_candidate(production.candidate, production.disposition, review)
        self.assertEqual(expected_visual_disposition(production.candidate, production.disposition, review), result.disposition)
        self.assertEqual("PASS_RECOMMENDED_FOR_EXTERNAL_REVIEW", result.disposition)
        self.assertEqual("NOT_ACCEPTED", result.acceptance_state)

    def test_self_review_and_missing_criterion_are_blocked(self):
        production = build_candidate()
        self.assertEqual("BLOCKED", assess_visual_candidate(
            production.candidate, production.disposition,
            visual_review(production.candidate, reviewer="PRODUCER-001"),
        ).disposition)
        self.assertEqual("BLOCKED", assess_visual_candidate(
            production.candidate, production.disposition,
            visual_review(production.candidate, criteria=CRITERIA[:-1]),
        ).disposition)

    def test_score_thresholds_do_not_collapse_revision_into_pass(self):
        production = build_candidate()
        self.assertEqual("REVISE", assess_visual_candidate(production.candidate, production.disposition, visual_review(production.candidate, score=79)).disposition)
        self.assertEqual("BLOCKED", assess_visual_candidate(production.candidate, production.disposition, visual_review(production.candidate, score=59)).disposition)


class E08CreativeMemoryTests(unittest.TestCase):
    def visual(self):
        production = build_candidate()
        return assess_visual_candidate(production.candidate, production.disposition, visual_review(production.candidate))

    def test_validated_future_generation_record_is_idempotent_and_deprecatable(self):
        proposal = memory()
        assessment = assess_memory_candidate(self.visual(), validation(), proposal, NOW)
        self.assertTrue(assessment.ready)
        store = CreativeMemoryStore()
        self.assertEqual("STORED", store.write(assessment, proposal)[0])
        self.assertEqual("IDEMPOTENT", store.write(assessment, proposal)[0])
        self.assertEqual("DEPRECATED", store.deprecate(proposal.memory_id, "out-of-sample failure").state)

    def test_same_generation_and_single_evidence_root_are_quarantined(self):
        result = assess_memory_candidate(self.visual(), validation(), memory(eligible_generation=1, evidence_roots=("ONE",)), NOW)
        self.assertEqual("QUARANTINE_MEMORY", result.disposition)
        self.assertIn("SAME_GENERATION_FEEDBACK_FORBIDDEN", result.reasons)

    def test_identity_collision_does_not_overwrite_history(self):
        store = CreativeMemoryStore()
        first = memory()
        first_assessment = assess_memory_candidate(self.visual(), validation(), first, NOW)
        store.write(first_assessment, first)
        conflicting = replace(first, hypothesis="Different material hypothesis")
        conflicting_assessment = assess_memory_candidate(self.visual(), validation(), conflicting, NOW)
        self.assertEqual("IDENTITY_COLLISION", store.write(conflicting_assessment, conflicting)[0])
        self.assertEqual(first.content_hash, store.get(first.memory_id).content_hash)


class Block2RuntimeTests(unittest.TestCase):
    def test_eight_engine_run_produces_candidate_without_publishing_or_accepting(self):
        store = CreativeMemoryStore()
        result = execute_block2(complete_run_input(), now=NOW, memory_store=store)
        self.assertTrue(result.completed)
        self.assertEqual(tuple(f"E0{i}" for i in range(1, 9)), tuple(stage.engine for stage in result.stages))
        self.assertEqual("NOT_PUBLISHED", result.publication_state)
        self.assertEqual("NOT_ACCEPTED", result.acceptance_state)
        self.assertEqual("STORED", result.memory_store_action)

    def test_runtime_stops_at_e05_on_rights_quarantine(self):
        bad_research = research(references=(reference(rights_decision="QUARANTINE"), reference("REF-2")))
        result = execute_block2(complete_run_input(research=bad_research), now=NOW)
        self.assertFalse(result.completed)
        self.assertEqual("E05", result.stopped_at)
        self.assertNotIn("E06", {stage.engine for stage in result.stages})

    def test_runtime_stops_at_e07_without_independent_pass(self):
        data = complete_run_input()
        bad_review = replace(data.visual_review, independent=False)
        result = execute_block2(replace(data, visual_review=bad_review), now=NOW)
        self.assertEqual("E07", result.stopped_at)
        self.assertIsNone(result.memory)


if __name__ == "__main__":
    unittest.main()
