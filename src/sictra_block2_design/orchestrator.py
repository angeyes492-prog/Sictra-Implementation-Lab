"""Currentness-checked orchestration for actual partial Block 2 execution."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from .checkpoint import ResumeDecision, RunCheckpoint, plan_resume, request_hash
from .document_evolution import InvalidationPlan
from .engine_registry import EngineRegistry, default_engine_registry
from .e08_creative_memory import CreativeMemoryStore
from .model_gateway import LocalDeterministicModelGateway
from .runtime import Block2RunInput, Block2RunResult, execute_block2_partial
from .canonical_document import canonical_json
from .project_graph import GraphEdge, GraphNode, ProjectGraphStore
from hashlib import sha256


@dataclass(frozen=True, slots=True)
class OrchestratedResume:
    decision: ResumeDecision
    run: Block2RunResult | None
    publication_state: str = "NOT_PUBLISHED"
    acceptance_state: str = "NOT_ACCEPTED"


def execute_resumed_block2(
    request: Block2RunInput,
    *,
    checkpoint: RunCheckpoint,
    previous_result: Block2RunResult,
    current_policy_hash: str,
    current_rights_hash: str,
    invalidation: InvalidationPlan | None = None,
    now: datetime | None = None,
    engine_registry: EngineRegistry | None = None,
    memory_store: CreativeMemoryStore | None = None,
    model_gateway: LocalDeterministicModelGateway | None = None,
) -> OrchestratedResume:
    """Plan and execute Resume without crossing any currentness boundary."""

    registry = engine_registry or default_engine_registry()
    registry.verify_bindings()
    decision = plan_resume(
        checkpoint,
        current_envelope_fingerprint=request.envelope.fingerprint,
        current_request_hash=request_hash(request),
        current_engine_registry_hash=registry.content_hash,
        current_policy_hash=current_policy_hash,
        current_rights_hash=current_rights_hash,
        invalidation=invalidation,
    )
    if decision.disposition == "RESUME_REJECTED":
        return OrchestratedResume(decision, None)

    run = execute_block2_partial(
        request,
        reused_engines=decision.reused_engines,
        previous_result=previous_result,
        now=now,
        memory_store=memory_store,
        model_gateway=model_gateway,
        engine_registry=registry,
    )
    decision = replace(decision, executed_engines=run.executed_engines)
    return OrchestratedResume(decision, run)


def persist_orchestrated_resume(
    graph: ProjectGraphStore,
    resume: OrchestratedResume,
    *,
    project_id: str,
    resume_id: str,
    checkpoint_id: str,
    created_at: datetime,
) -> str:
    """Journal a Resume decision and its reused/executed distinction."""

    if resume.run is None:
        raise ValueError("a rejected resume has no runtime trace to persist")
    digest = lambda value: sha256(canonical_json(value).encode("utf-8")).hexdigest()
    actions: list[str] = []
    try:
        actions.append(graph.append_node(GraphNode(
            project_id, resume_id, "ORCHESTRATOR_RESUME", digest(resume.decision),
            {
                "disposition": resume.decision.disposition,
                "reasons": list(resume.decision.reasons),
                "reused_engines": list(resume.run.reused_engines),
                "executed_engines": list(resume.run.executed_engines),
                "registry_hash": resume.run.engine_registry_hash,
                "publication_state": resume.publication_state,
                "acceptance_state": resume.acceptance_state,
            },
            created_at,
        )))
        actions.append(graph.append_edge(GraphEdge(
            project_id, resume_id, "DERIVED_FROM", checkpoint_id,
            resume.decision.disposition, created_at,
        )))
        for stage in resume.run.stages:
            stage_id = f"{resume_id}-{stage.engine}"
            actions.append(graph.append_node(GraphNode(
                project_id, stage_id, "ENGINE_STAGE_RESUME", digest(stage),
                {
                    "engine": stage.engine, "disposition": stage.disposition,
                    "reasons": list(stage.reasons), "execution_state": stage.execution_state,
                },
                created_at,
            )))
            actions.append(graph.append_edge(GraphEdge(
                project_id, stage_id, "DERIVED_FROM", resume_id,
                stage.execution_state, created_at,
            )))
        graph.commit()
    except Exception:
        graph.rollback()
        raise
    return "IDEMPOTENT" if actions and all(item == "IDEMPOTENT" for item in actions) else "APPENDED"
