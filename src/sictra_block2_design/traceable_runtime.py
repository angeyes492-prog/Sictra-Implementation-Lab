"""Explicit adapter from the bounded E01-E08 runtime into shared trace state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256

from .canonical_document import DesignDocumentVersion, document_from_completed_run
from .project_graph import GraphEdge, GraphNode, ProjectGraphStore
from .runtime import Block2RunInput, Block2RunResult, execute_block2
from .e08_creative_memory import CreativeMemoryStore
from .design_context import DesignContextEnvelope, assess_runtime_binding


@dataclass(frozen=True, slots=True)
class TraceableBlock2RunResult:
    run: Block2RunResult
    document: DesignDocumentVersion | None
    graph_action: str
    run_id: str


def _digest(*values: str) -> str:
    return sha256("\x1f".join(values).encode("utf-8")).hexdigest()


def execute_traceable_block2(
    request: Block2RunInput,
    *,
    graph: ProjectGraphStore,
    project_id: str,
    document_id: str,
    actor_id: str,
    run_id: str | None = None,
    now: datetime | None = None,
    memory_store: CreativeMemoryStore | None = None,
    design_context: DesignContextEnvelope | None = None,
) -> TraceableBlock2RunResult:
    """Execute and atomically append bounded stage lineage and an optional CDD."""

    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    run_id = run_id or "RUN-" + _digest(project_id, request.envelope.fingerprint, now.isoformat())[:20]
    if not isinstance(run_id, str) or not run_id.strip():
        raise ValueError("run_id must be a non-empty string")
    if design_context is not None:
        binding = assess_runtime_binding(design_context, request)
        if not binding.ready:
            raise ValueError(";".join(binding.reasons))
    result = execute_block2(request, now=now, memory_store=memory_store)
    actions: list[str] = []
    try:
        previous_id: str | None = None
        for stage in result.stages:
            node_id = f"{run_id}-{stage.engine}"
            payload = {
                "engine": stage.engine, "disposition": stage.disposition,
                "reasons": list(stage.reasons), "execution_state": stage.execution_state,
            }
            action = graph.append_node(GraphNode(
                project_id, node_id, "ENGINE_STAGE", _digest(stage.engine, stage.disposition, *stage.reasons), payload, now,
            ))
            actions.append(action)
            if stage.engine == "E01" and design_context is not None:
                actions.append(graph.append_edge(GraphEdge(
                    project_id, node_id, "DERIVED_FROM",
                    f"DESIGN-CONTEXT-{design_context.message_id}",
                    design_context.fingerprint, now,
                )))
            if previous_id is not None:
                actions.append(graph.append_edge(GraphEdge(
                    project_id, node_id, "DERIVED_FROM", previous_id, "BOUNDED_RUNTIME_STAGE_ORDER", now,
                )))
            previous_id = node_id

        document = None
        if result.completed and result.production and result.production.candidate:
            candidate = result.production.candidate
            artifact_id = f"ASSET-{candidate.artifact.sha256}"
            e06_id = f"{run_id}-E06"
            actions.append(graph.append_node(GraphNode(
                project_id,
                artifact_id,
                "ASSET_CANDIDATE",
                candidate.artifact.sha256,
                {"media_type": candidate.artifact.media_type, "publication_state": candidate.publication_state},
                now,
            )))
            receipt = result.gateway_receipt
            if receipt is None:
                raise ValueError("a completed E06 result requires a Model Gateway receipt")
            receipt_id = receipt.receipt_id
            actions.append(graph.append_node(GraphNode(
                project_id,
                receipt_id,
                "MODEL_GATEWAY_RECEIPT",
                _digest(receipt.input_hash, receipt.output_hash or "", receipt.outcome),
                {
                    "spec_id": receipt.spec_id, "provider_manifest_id": receipt.provider_manifest_id,
                    "adapter": receipt.adapter, "outcome": receipt.outcome,
                    "quarantine_state": receipt.quarantine_state, "cost_units": receipt.cost_units,
                    "latency_ms": receipt.latency_ms,
                    "cancel_state": receipt.cancel_state,
                    "budget_limit_units": receipt.budget_limit_units,
                    "timeout_ms": receipt.timeout_ms,
                    "policy_hash": receipt.policy_hash,
                    "rights_hash": receipt.rights_hash,
                },
                now,
            )))
            actions.append(graph.append_edge(GraphEdge(
                project_id, receipt_id, "DERIVED_FROM", e06_id, receipt.spec_id, now,
            )))
            actions.append(graph.append_edge(GraphEdge(
                project_id, artifact_id, "GENERATED_BY", receipt_id, candidate.candidate_id, now,
            )))
            document = document_from_completed_run(
                request, result, project_id=project_id, document_id=document_id, actor_id=actor_id, created_at=now,
            )
            actions.append(graph.append_document(document))
            document_node_id = f"DOCUMENT-{document.version_id}"
            actions.append(graph.append_node(GraphNode(
                project_id,
                document_node_id,
                "DESIGN_DOCUMENT_VERSION",
                document.content_hash,
                {"document_id": document.document_id, "version_id": document.version_id, "state": document.state},
                now,
            )))
            actions.append(graph.append_edge(GraphEdge(
                project_id, document_node_id, "DERIVED_FROM", artifact_id, document.version_id, now,
            )))
            review_id = f"{run_id}-E07"
            actions.append(graph.append_edge(GraphEdge(
                project_id, artifact_id, "VALIDATED_BY", review_id, request.visual_review.review_id, now,
            )))
        graph.commit()
    except Exception:
        graph.rollback()
        raise
    graph_action = "IDEMPOTENT" if actions and all(item == "IDEMPOTENT" for item in actions) else "APPENDED"
    return TraceableBlock2RunResult(result, document, graph_action, run_id)
