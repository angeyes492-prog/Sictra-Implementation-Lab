"""Fail-closed compiler for a Block 2 Design Context Envelope."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256

from .canonical_document import canonical_json
from .project_graph import GraphEdge, GraphNode, ProjectGraphStore


CERTAINTY_VALUES = frozenset({
    "VERIFIED", "PROBABLE", "PLAUSIBLE", "UNCONFIRMED", "CONTRADICTED",
    "INSUFFICIENT EVIDENCE",
})
SUPPORTED_CHANNELS = frozenset({"EMAIL", "WEB", "SOCIAL", "PRESENTATION", "PRINT"})


class DesignContextViolation(ValueError):
    """A Create request or its identity is structurally unsafe."""


def _ids(values: tuple[str, ...]) -> bool:
    return bool(values) and len(values) <= 64 and all(
        isinstance(value, str) and value.strip() and len(value) <= 256 for value in values
    )


@dataclass(frozen=True, slots=True)
class CreateDesignRequest:
    request_id: str
    contract_version: str
    project_id: str
    message_id: str
    task_id: str
    run_id: str
    producer: str
    consumer: str
    actor_id: str
    logical_time: datetime
    object_id: str
    source_identity: str
    fact_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    certainty: str
    contradictions: tuple[str, ...]
    authority_reference: str
    temporal_state: str
    provenance_refs: tuple[str, ...]
    audience: str
    decision: str
    task: str
    channel_set: tuple[str, ...]
    success_criterion: str
    accessibility_requirements: tuple[str, ...]
    legal_constraints: tuple[str, ...]
    channel_constraints: tuple[str, ...]
    references_declared: bool
    brand_manifest_ref: str | None = None
    reference_rights_manifest_ref: str | None = None
    uncertainty: tuple[str, ...] = ()
    non_claims: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.logical_time, datetime) or self.logical_time.tzinfo is None:
            raise DesignContextViolation("logical_time must be timezone-aware")
        if not isinstance(self.references_declared, bool):
            raise DesignContextViolation("references_declared must be boolean")

    @property
    def content_hash(self) -> str:
        return sha256(canonical_json(self).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class DesignContextEnvelope:
    message_id: str
    task_id: str
    run_id: str
    contract_version: str
    producer: str
    consumer: str
    logical_time: datetime
    object_id: str
    source_identity: str
    fact_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    certainty: str
    contradictions: tuple[str, ...]
    authority_reference: str
    temporal_state: str
    provenance_refs: tuple[str, ...]
    audience: str
    decision: str
    task: str
    channel_set: tuple[str, ...]
    success_criterion: str
    accessibility_requirements: tuple[str, ...]
    brand_manifest_ref: str | None
    reference_rights_manifest_ref: str | None
    legal_constraints: tuple[str, ...]
    channel_constraints: tuple[str, ...]
    uncertainty: tuple[str, ...]
    non_claims: tuple[str, ...]
    parent_fingerprint: str | None
    transformation_id: str
    added_by: str
    state: str = "CANDIDATE_NOT_ACCEPTED"

    @property
    def fingerprint(self) -> str:
        return sha256(canonical_json(self).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class CreateAssessment:
    request_id: str
    project_id: str
    request_hash: str
    disposition: str
    reasons: tuple[str, ...]
    envelope: DesignContextEnvelope | None
    publication_state: str = "NOT_PUBLISHED"
    acceptance_state: str = "NOT_ACCEPTED"

    @property
    def content_hash(self) -> str:
        return sha256(canonical_json(self).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class RuntimeBindingAssessment:
    disposition: str
    reasons: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return self.disposition == "BOUND_FOR_E01"


def compile_design_context(request: CreateDesignRequest) -> CreateAssessment:
    """Compile explicit inputs without supplying missing upstream semantics."""

    reasons: list[str] = []
    required = {
        "REQUEST_ID": request.request_id, "PROJECT_ID": request.project_id,
        "MESSAGE_ID": request.message_id, "TASK_ID": request.task_id,
        "RUN_ID": request.run_id, "PRODUCER": request.producer,
        "CONSUMER": request.consumer, "ACTOR_ID": request.actor_id,
        "OBJECT_ID": request.object_id, "SOURCE_IDENTITY": request.source_identity,
        "AUTHORITY_REFERENCE": request.authority_reference,
        "AUDIENCE": request.audience, "DECISION": request.decision,
        "TASK": request.task, "SUCCESS_CRITERION": request.success_criterion,
    }
    reasons.extend(
        f"{name}_MISSING" for name, value in required.items()
        if not isinstance(value, str) or not value.strip() or len(value) > 4000
    )
    if not request.contract_version.startswith("0.1."):
        reasons.append("UNSUPPORTED_VERSION")
    for name, values in (
        ("FACTS", request.fact_ids), ("EVIDENCE", request.evidence_refs),
        ("PROVENANCE", request.provenance_refs), ("CHANNELS", request.channel_set),
    ):
        if not _ids(values):
            reasons.append(f"{name}_MISSING")
    if request.certainty not in CERTAINTY_VALUES:
        reasons.append("CERTAINTY_UNGOVERNED")
    if request.temporal_state != "CURRENT":
        reasons.append("UPSTREAM_NOT_CURRENT")
    unsupported = sorted(set(request.channel_set) - SUPPORTED_CHANNELS)
    reasons.extend(f"UNSUPPORTED_CHANNEL_{channel}" for channel in unsupported)
    if request.references_declared and not (
        isinstance(request.reference_rights_manifest_ref, str)
        and request.reference_rights_manifest_ref.strip()
    ):
        reasons.append("REFERENCE_RIGHTS_MANIFEST_MISSING")
    if any(not isinstance(item, str) or not item.strip() for values in (
        request.contradictions, request.accessibility_requirements,
        request.legal_constraints, request.channel_constraints,
        request.uncertainty, request.non_claims,
    ) for item in values):
        reasons.append("OPTIONAL_COLLECTION_MALFORMED")
    if reasons:
        unique = tuple(dict.fromkeys(reasons))
        return CreateAssessment(
            request.request_id or "UNIDENTIFIED", request.project_id or "UNIDENTIFIED",
            request.content_hash, "RETURN_UPSTREAM", unique, None,
        )

    envelope = DesignContextEnvelope(
        request.message_id, request.task_id, request.run_id, request.contract_version,
        request.producer, request.consumer, request.logical_time, request.object_id,
        request.source_identity, request.fact_ids, request.evidence_refs,
        request.certainty, request.contradictions, request.authority_reference,
        request.temporal_state, request.provenance_refs, request.audience,
        request.decision, request.task, request.channel_set, request.success_criterion,
        request.accessibility_requirements, request.brand_manifest_ref,
        request.reference_rights_manifest_ref, request.legal_constraints,
        request.channel_constraints, request.uncertainty, request.non_claims, None,
        f"CREATE-{request.request_id}", request.actor_id,
    )
    return CreateAssessment(
        request.request_id, request.project_id, request.content_hash,
        "CONTINUE", (), envelope,
    )


def assess_runtime_binding(envelope: DesignContextEnvelope, request) -> RuntimeBindingAssessment:
    """Verify that a runtime input preserves the compiled handoff exactly."""

    upstream = request.fixture.upstream
    failures: list[str] = []
    for label, expected, actual in (
        ("FINGERPRINT", envelope.fingerprint, request.envelope.fingerprint),
        ("MESSAGE", envelope.message_id, request.envelope.message_id),
        ("OBJECT", envelope.object_id, upstream.object_id),
        ("SOURCE", envelope.source_identity, upstream.source_identity),
        ("CERTAINTY", envelope.certainty, upstream.evidence_status),
        ("AUTHORITY", envelope.authority_reference, upstream.authority_reference),
        ("AUDIENCE", envelope.audience, upstream.audience_context),
        ("DECISION", envelope.decision, upstream.decision_context),
    ):
        if expected != actual:
            failures.append(f"CREATE_RUNTIME_{label}_MISMATCH")
    if request.envelope.disposition != "CONTINUE":
        failures.append("CREATE_RUNTIME_ENVELOPE_NOT_CONTINUE")
    if request.envelope.temporal_state != "CURRENT":
        failures.append("CREATE_RUNTIME_ENVELOPE_NOT_CURRENT")
    return RuntimeBindingAssessment(
        "RETURN_TO_CREATE" if failures else "BOUND_FOR_E01", tuple(failures),
    )


def persist_create_assessment(graph: ProjectGraphStore, assessment: CreateAssessment, *, created_at: datetime) -> str:
    """Append the assessment and, only on CONTINUE, its candidate envelope."""

    actions: list[str] = []
    assessment_id = f"CREATE-ASSESSMENT-{assessment.request_id}"
    try:
        actions.append(graph.append_node(GraphNode(
            assessment.project_id, assessment_id, "CREATE_ASSESSMENT",
            assessment.content_hash,
            {
                "request_hash": assessment.request_hash,
                "disposition": assessment.disposition,
                "reasons": list(assessment.reasons),
                "publication_state": assessment.publication_state,
                "acceptance_state": assessment.acceptance_state,
            }, created_at,
        )))
        if assessment.envelope is not None:
            envelope_id = f"DESIGN-CONTEXT-{assessment.envelope.message_id}"
            actions.append(graph.append_node(GraphNode(
                assessment.project_id, envelope_id, "DESIGN_CONTEXT_ENVELOPE",
                assessment.envelope.fingerprint,
                {
                    "task_id": assessment.envelope.task_id,
                    "run_id": assessment.envelope.run_id,
                    "channels": list(assessment.envelope.channel_set),
                    "certainty": assessment.envelope.certainty,
                    "state": assessment.envelope.state,
                    "fingerprint": assessment.envelope.fingerprint,
                }, created_at,
            )))
            actions.append(graph.append_edge(GraphEdge(
                assessment.project_id, assessment_id, "REPRESENTS", envelope_id,
                assessment.envelope.transformation_id, created_at,
            )))
        graph.commit()
    except Exception:
        graph.rollback()
        raise
    return "IDEMPOTENT" if actions and all(action == "IDEMPOTENT" for action in actions) else "APPENDED"
