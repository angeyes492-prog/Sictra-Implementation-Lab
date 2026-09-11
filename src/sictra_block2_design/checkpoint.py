"""Checkpoint currentness and safe resume planning for Block 2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256

from .canonical_document import canonical_json
from .document_evolution import InvalidationPlan
from .project_graph import GraphNode, ProjectGraphStore
from .runtime import Block2RunInput, Block2RunResult


_ENGINES = tuple(f"E0{number}" for number in range(1, 9))


class CheckpointViolation(ValueError):
    """Checkpoint identity or state cannot be trusted."""


@dataclass(frozen=True, slots=True)
class RunCheckpoint:
    checkpoint_id: str
    contract_version: str
    project_id: str
    run_id: str
    envelope_fingerprint: str
    request_hash: str
    completed_engines: tuple[str, ...]
    document_version_id: str | None
    asset_hash: str | None
    receipt_id: str | None
    engine_registry_hash: str
    policy_hash: str
    rights_hash: str
    created_at: datetime
    state: str = "CURRENT"

    def __post_init__(self) -> None:
        if not self.contract_version.startswith("0.1."):
            raise CheckpointViolation("checkpoint version is unsupported")
        if not isinstance(self.created_at, datetime) or self.created_at.tzinfo is None:
            raise CheckpointViolation("checkpoint timestamp must be timezone-aware")
        if len(set(self.completed_engines)) != len(self.completed_engines):
            raise CheckpointViolation("completed engines cannot repeat")
        if any(engine not in _ENGINES for engine in self.completed_engines):
            raise CheckpointViolation("checkpoint contains an unknown engine")
        expected_prefix = _ENGINES[:len(self.completed_engines)]
        if self.completed_engines != expected_prefix:
            raise CheckpointViolation("completed engines must be a contiguous prefix")

    @property
    def content_hash(self) -> str:
        return sha256(canonical_json(self).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ResumeDecision:
    disposition: str
    reasons: tuple[str, ...]
    reused_engines: tuple[str, ...]
    reexecute_engines: tuple[str, ...]
    next_engine: str | None
    executed_engines: tuple[str, ...] = ()


def request_hash(request: Block2RunInput) -> str:
    return sha256(canonical_json(request).encode("utf-8")).hexdigest()


def checkpoint_from_run(
    request: Block2RunInput,
    result: Block2RunResult,
    *,
    checkpoint_id: str,
    project_id: str,
    run_id: str,
    document_version_id: str | None,
    engine_registry_hash: str,
    policy_hash: str,
    rights_hash: str,
    created_at: datetime,
) -> RunCheckpoint:
    candidate = None if result.production is None else result.production.candidate
    successful_engines: list[str] = []
    for stage in result.stages:
        if stage.engine == result.stopped_at:
            break
        if stage.engine not in successful_engines:
            successful_engines.append(stage.engine)
    return RunCheckpoint(
        checkpoint_id, "0.1.0", project_id, run_id, request.envelope.fingerprint,
        request_hash(request), tuple(successful_engines),
        document_version_id, None if candidate is None else candidate.artifact.sha256,
        None if result.gateway_receipt is None else result.gateway_receipt.receipt_id,
        engine_registry_hash, policy_hash, rights_hash, created_at,
        "CURRENT" if result.stages else "UNKNOWN",
    )


def plan_resume(
    checkpoint: RunCheckpoint,
    *,
    current_envelope_fingerprint: str,
    current_request_hash: str,
    current_engine_registry_hash: str,
    current_policy_hash: str,
    current_rights_hash: str,
    invalidation: InvalidationPlan | None = None,
) -> ResumeDecision:
    failures: list[str] = []
    if checkpoint.state != "CURRENT":
        failures.append("CHECKPOINT_NOT_CURRENT")
    for label, expected, actual in (
        ("ENVELOPE", checkpoint.envelope_fingerprint, current_envelope_fingerprint),
        ("REQUEST", checkpoint.request_hash, current_request_hash),
        ("ENGINE_REGISTRY", checkpoint.engine_registry_hash, current_engine_registry_hash),
        ("POLICY", checkpoint.policy_hash, current_policy_hash),
        ("RIGHTS", checkpoint.rights_hash, current_rights_hash),
    ):
        if expected != actual:
            failures.append(f"{label}_HASH_MISMATCH")
    if failures:
        return ResumeDecision("RESUME_REJECTED", tuple(failures), (), (), None)

    if invalidation is not None:
        reusable = tuple(engine for engine in checkpoint.completed_engines if engine in invalidation.preserved_engines)
        reexecute = tuple(engine for engine in _ENGINES if engine not in reusable)
        next_engine = reexecute[0] if reexecute else None
        return ResumeDecision(
            "RESUMED_COMPLETE" if next_engine is None else f"REEXECUTE_FROM_{next_engine}",
            tuple(f"INVALIDATED_{domain}" for domain in invalidation.reason_domains),
            reusable, reexecute, next_engine,
        )

    if checkpoint.completed_engines == _ENGINES:
        return ResumeDecision("RESUMED_COMPLETE", (), _ENGINES, (), None)
    next_engine = _ENGINES[len(checkpoint.completed_engines)]
    return ResumeDecision(
        f"REEXECUTE_FROM_{next_engine}", ("CHECKPOINT_PARTIAL",),
        checkpoint.completed_engines, _ENGINES[len(checkpoint.completed_engines):], next_engine,
    )


def persist_checkpoint(graph: ProjectGraphStore, checkpoint: RunCheckpoint) -> str:
    action = graph.append_node(GraphNode(
        checkpoint.project_id, checkpoint.checkpoint_id, "RUN_CHECKPOINT",
        checkpoint.content_hash,
        {
            "run_id": checkpoint.run_id, "state": checkpoint.state,
            "completed_engines": list(checkpoint.completed_engines),
            "document_version_id": checkpoint.document_version_id,
            "asset_hash": checkpoint.asset_hash, "receipt_id": checkpoint.receipt_id,
            "engine_registry_hash": checkpoint.engine_registry_hash,
            "policy_hash": checkpoint.policy_hash, "rights_hash": checkpoint.rights_hash,
        },
        checkpoint.created_at,
    ))
    graph.commit()
    return action
