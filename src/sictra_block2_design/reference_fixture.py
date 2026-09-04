"""Deterministic synthetic fixture for exercising all eight Block 2 engines."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .preflight import (
    Candidate, Confounder, Fixture, ObserverProfile, TaskDefinition, UpstreamIntelligence,
)
from .e02_direction import Direction, DirectionSet, E02Envelope, VisualThesis
from .e03_design_system import (
    AssetReference, ComponentRule, SelectionRecord, SystemProfileProposal, TokenRule,
    assess_system_profile,
)
from .e04_information_design import (
    BlueprintElement, ChannelTarget, EncodingPlan, InformationBlueprint,
    InformationPayload, PayloadClaim, assess_information_blueprint,
)
from .e05_reference_research import (
    GovernedReference, ReferenceResearchProposal, TransferablePrinciple,
    assess_reference_research,
)
from .e06_production import ProductionContent, ProductionRequest, build_production_candidate
from .e07_visual_red_team import RubricObservation, VisualReview
from .e08_creative_memory import ExternalValidationRecord, MemoryProposal
from .runtime import Block2RunInput, Block2RunResult, execute_block2
from .design_context import CreateDesignRequest, DesignContextEnvelope


def reference_create_request(now: datetime | None = None) -> CreateDesignRequest:
    """Build the explicit synthetic Create handoff used by integrated tests."""

    now = now or datetime.now(timezone.utc)
    return CreateDesignRequest(
        "CREATE-DEMO", "0.1.0", "PROJECT-DEMO", "MESSAGE-DEMO", "TASK-v1",
        "RUN-CREATE-DEMO", "INTELLIGENCE-ADAPTER-DEMO", "BLOCK2-E01",
        "HUMAN-DEMO", now, "INTEL-DEMO", "synthetic:demo:v1", ("CLAIM-001",),
        ("EVIDENCE-001",), "VERIFIED", ("CONTRADICTION-001",),
        "authority:demo:v1", "CURRENT", ("PROVENANCE-DEMO",),
        "design-runtime-reviewer", "exercise bounded design pipeline",
        "show a bounded claim", ("EMAIL",), "claim and limitation are locatable",
        ("WCAG-AA",), (), ("EMAIL-600PX",), False, "BRAND-DEMO", None,
        ("synthetic fixture only",), ("NO-CAUSAL-CLAIM",),
    )


def reference_run_input(
    now: datetime | None = None,
    design_context: DesignContextEnvelope | None = None,
) -> Block2RunInput:
    """Build a fully attributable synthetic input; no real-world claims are implied."""

    now = now or datetime.now(timezone.utc)
    upstream = UpstreamIntelligence(
        "INTEL-DEMO" if design_context is None else design_context.object_id,
        "synthetic:demo:v1" if design_context is None else design_context.source_identity,
        "VERIFIED" if design_context is None else design_context.certainty,
        "authority:demo:v1" if design_context is None else design_context.authority_reference,
        "design-runtime-reviewer" if design_context is None else design_context.audience,
        "exercise bounded design pipeline" if design_context is None else design_context.decision,
    )
    task = TaskDefinition("CLAIM-001", "show a bounded claim", "compare", "synthetic", "TASK-v1", "Which layout exposes the claim clearly?", True)
    common = dict(
        content_id="INTEL-DEMO", task_version="TASK-v1", labels=("claim", "limit"),
        scale="ordinal-3", uncertainty_object="claim-limit", annotation_burden="one-caption",
        context_version="CONTEXT-v1", attention_condition="first-view", implementation_burden="static",
    )
    trial = Fixture(
        "FIXTURE-DEMO", upstream, task,
        Candidate("A", "aligned-position", **common), Candidate("B", "grouped-table", **common),
        "visual mechanism", ObserverProfile("OBSERVER-DEMO", True, True, False, "COUNTERBALANCED"),
        (Confounder("mechanism", "MANIPULATED", True),),
        fixture_author_id="FIXTURE-AUTHOR-DEMO",
    )
    envelope = E02Envelope(
        "MESSAGE-DEMO" if design_context is None else design_context.message_id,
        "fingerprint:demo" if design_context is None else design_context.fingerprint,
        "CONTINUE", "CURRENT", True, True,
    )
    thesis = VisualThesis("THESIS-DEMO", ("CLAIM-001",), "PLAUSIBLE", ("CONTRADICTION-001",), ("NO-CAUSAL-CLAIM",), ("show-limit",))
    direction_a = Direction("DIRECTION-A", "progression", "causal-sequence", "milestones", "linear", "static", thesis.claim_bindings, thesis.certainty, thesis.contradictions, thesis.non_claims, thesis.uncertainty_exposure)
    direction_b = Direction("DIRECTION-B", "comparison", "decision-matrix", "annotated-bars", "matrix", "static", thesis.claim_bindings, thesis.certainty, thesis.contradictions, thesis.non_claims, thesis.uncertainty_exposure)
    directions = DirectionSet("DIRECTION-SET-DEMO", thesis.thesis_id, envelope.fingerprint, (direction_a, direction_b))
    profile = SystemProfileProposal(
        "PROFILE-DEMO", "0.1.0", envelope.fingerprint, direction_a.direction_id, "EMAIL", ("EMAIL",),
        SelectionRecord(direction_a.direction_id, "HUMAN-DEMO", "AUTHORITY-SELECTION-DEMO", True),
        thesis.claim_bindings, thesis.certainty, thesis.contradictions, thesis.non_claims, thesis.uncertainty_exposure,
        (TokenRule("certainty-low", "certainty_low", True, "LABEL"),),
        (AssetReference("FONT-DEMO", "FONT", "ALLOW_LICENSED_ASSET", ("EMAIL",), True),),
        (ComponentRule("CTA", True, ("PRIMARY",), ("DEFAULT", "FOCUS", "DISABLED"), ("announces action",)),), (),
    )
    claim = PayloadClaim("CLAIM-001", ("EVIDENCE-001",), ("SOURCE-001",), ("LIMIT-001",), "COMPARISON", True, "%", "HIGHER_IS_BETTER")
    payload = InformationPayload("PAYLOAD-DEMO", "0.1.0", (claim,), ("Synthetic approved copy",))
    channel = ChannelTarget("NEWSLETTER", "EMAIL", "EXECUTIVE")
    blueprint = InformationBlueprint(
        "BLUEPRINT-DEMO", "0.1.0", profile.profile_id, envelope.fingerprint,
        channel.artifact_type, channel.channel, channel.audience_path, ("CHART-001", "CTA-001"),
        (
            BlueprintElement("CHART-001", "CHART", (claim.claim_id,), claim.evidence_refs, (), False),
            BlueprintElement("CTA-001", "CTA", (claim.claim_id,), claim.evidence_refs, claim.limitation_ids, False),
        ),
        (EncodingPlan("ENC-001", claim.claim_id, claim.relationship, "BAR", claim.unit, claim.polarity, claim.attribution_ids, True, True, 3, False, False, False),),
        ("PLAIN_TEXT",), (), "NOT_PUBLISHED",
    )
    references = (
        GovernedReference("REF-1", "https://example.test/one", "IMAGE", "ALLOW_CONSTRAINT_ONLY", ("EMAIL",), True, ("REF-EVIDENCE-1",)),
        GovernedReference("REF-2", "https://example.test/two", "IMAGE", "ALLOW_CONSTRAINT_ONLY", ("EMAIL",), True, ("REF-EVIDENCE-2",)),
    )
    principles = (
        TransferablePrinciple("P-1", "REF-1", "HIERARCHY", "clear lead", "one dominant entry", ("REF-EVIDENCE-1",), True),
        TransferablePrinciple("P-2", "REF-1", "GRID", "aligned evidence", "align related evidence", ("REF-EVIDENCE-1",), True),
        TransferablePrinciple("P-3", "REF-2", "ACCESSIBILITY", "redundant labels", "encode beyond color", ("REF-EVIDENCE-2",), True),
        TransferablePrinciple("P-4", "REF-2", "RHYTHM", "group spacing", "space by semantic group", ("REF-EVIDENCE-2",), True),
    )
    research = ReferenceResearchProposal("PACK-DEMO", "0.1.0", blueprint.blueprint_id, profile.profile_id, envelope.fingerprint, "EMAIL", references, principles)
    production_request = ProductionRequest(
        "CANDIDATE-DEMO", "0.1.0", "HTML_EMAIL", envelope.fingerprint,
        profile.profile_id, blueprint.blueprint_id, research.pack_id, "PRODUCER-DEMO",
        ProductionContent("SICTrA bounded design brief", ((claim.claim_id, "Synthetic approved copy"),), "Synthetic claim with its visible limitation"),
    )
    e03 = assess_system_profile(envelope.fingerprint, direction_a, profile, now)
    e04 = assess_information_blueprint(envelope.fingerprint, profile, e03.disposition, payload, channel, blueprint)
    e05 = assess_reference_research(blueprint, e04.disposition, research, now)
    e06 = build_production_candidate(profile, blueprint, e04.disposition, payload, research, e05.disposition, production_request)
    criteria = (
        "COMPREHENSION", "HIERARCHY", "LEGIBILITY", "ACCESSIBILITY",
        "CLAIM_FIDELITY", "CHANNEL_ADAPTATION", "BRAND_AND_RIGHTS", "NON_DECEPTIVE_PERSUASION",
    )
    visual = VisualReview(
        "REVIEW-DEMO", "0.1.0", e06.candidate.candidate_id, e06.candidate.artifact.sha256,
        "REVIEWER-DEMO", True,
        tuple(RubricObservation(item, 90, (f"AUDIT-{item}",), "synthetic bounded check", "fixture passes") for item in criteria),
    )
    validation = ExternalValidationRecord("VALIDATION-DEMO", "HUMAN-DEMO-2", "AUTHORITY-MEMORY-DEMO", True, True, ("ROOT-EXTERNAL",))
    memory = MemoryProposal(
        "MEMORY-DEMO", "0.1.0", visual.review_id, e06.candidate.candidate_id, 1, 2,
        "Synthetic fixture passed", "Constraints may be coherent", "Retest out of sample",
        ("ROOT-VISUAL", "ROOT-EXTERNAL"), "OWNER-DEMO", True, True, now + timedelta(days=365),
    )
    return Block2RunInput(trial, envelope, thesis, directions, direction_a, profile, payload, channel, blueprint, research, production_request, visual, validation, memory)


def run_reference_fixture(now: datetime | None = None) -> Block2RunResult:
    now = now or datetime.now(timezone.utc)
    return execute_block2(reference_run_input(now), now=now)
