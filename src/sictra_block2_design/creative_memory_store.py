"""Durable event-sourced adapter for E08 Creative Memory."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json

from .e08_creative_memory import (
    E08ContractViolation, MemoryAssessment, MemoryProposal, StoredMemory,
)
from .project_graph import (
    GraphEdge, GraphMemoryEvent, GraphMemoryRecord, GraphNode,
    ProjectGraphStore, ProjectGraphViolation,
)


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise E08ContractViolation(f"{name} must be a non-empty string")


def _proposal_payload(proposal: MemoryProposal) -> dict[str, object]:
    return {
        "memory_id": proposal.memory_id,
        "contract_version": proposal.contract_version,
        "source_review_id": proposal.source_review_id,
        "source_candidate_id": proposal.source_candidate_id,
        "source_generation": proposal.source_generation,
        "eligible_generation": proposal.eligible_generation,
        "observation": proposal.observation,
        "interpretation": proposal.interpretation,
        "hypothesis": proposal.hypothesis,
        "evidence_roots": list(proposal.evidence_roots),
        "promotion_owner_id": proposal.promotion_owner_id,
        "rights_current": proposal.rights_current,
        "privacy_allowed": proposal.privacy_allowed,
        "expires_at": proposal.expires_at.isoformat(),
    }


def _proposal_from_payload(payload: dict[str, object]) -> MemoryProposal:
    required = {
        "memory_id", "contract_version", "source_review_id", "source_candidate_id",
        "source_generation", "eligible_generation", "observation", "interpretation",
        "hypothesis", "evidence_roots", "promotion_owner_id", "rights_current",
        "privacy_allowed", "expires_at",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise E08ContractViolation("durable memory payload schema is invalid")
    text_fields = required - {
        "source_generation", "eligible_generation", "evidence_roots",
        "rights_current", "privacy_allowed",
    }
    if any(not isinstance(payload[name], str) for name in text_fields):
        raise E08ContractViolation("durable memory text fields are invalid")
    if any(
        not isinstance(payload[name], int) or isinstance(payload[name], bool)
        for name in ("source_generation", "eligible_generation")
    ):
        raise E08ContractViolation("durable memory generation fields are invalid")
    evidence = payload["evidence_roots"]
    if not isinstance(evidence, list) or any(not isinstance(item, str) for item in evidence):
        raise E08ContractViolation("durable memory evidence roots are invalid")
    if any(not isinstance(payload[name], bool) for name in ("rights_current", "privacy_allowed")):
        raise E08ContractViolation("durable memory governance flags are invalid")
    try:
        expires_at = datetime.fromisoformat(payload["expires_at"])
    except ValueError as error:
        raise E08ContractViolation("durable memory expiry is invalid") from error
    return MemoryProposal(
        payload["memory_id"], payload["contract_version"], payload["source_review_id"],
        payload["source_candidate_id"], payload["source_generation"],
        payload["eligible_generation"], payload["observation"],
        payload["interpretation"], payload["hypothesis"], tuple(evidence),
        payload["promotion_owner_id"], payload["rights_current"],
        payload["privacy_allowed"], expires_at,
    )


class ProjectGraphCreativeMemoryStore:
    """Durable E08 store that participates in the caller's graph transaction."""

    def __init__(
        self, graph: ProjectGraphStore, project_id: str, *, recorded_at: datetime,
    ) -> None:
        _text(project_id, "project_id")
        if not isinstance(recorded_at, datetime) or recorded_at.tzinfo is None:
            raise E08ContractViolation("recorded_at must be timezone-aware")
        self.graph = graph
        self.project_id = project_id
        self.recorded_at = recorded_at

    @staticmethod
    def node_id(memory_id: str) -> str:
        return f"CREATIVE-MEMORY-{memory_id}"

    def write(
        self, assessment: MemoryAssessment, proposal: MemoryProposal,
    ) -> tuple[str, StoredMemory | None]:
        if (
            not assessment.ready or assessment.memory_id != proposal.memory_id
            or assessment.content_hash != proposal.content_hash
        ):
            return "REJECTED", None
        existing = self.get(proposal.memory_id)
        if existing is not None:
            if existing.content_hash == proposal.content_hash:
                return "IDEMPOTENT", existing
            return "IDENTITY_COLLISION", existing
        payload = _proposal_payload(proposal)
        record = GraphMemoryRecord(
            self.project_id, proposal.memory_id, proposal.content_hash, payload,
            self.recorded_at,
        )
        node = GraphNode(
            self.project_id, self.node_id(proposal.memory_id),
            "CREATIVE_MEMORY_CANDIDATE", proposal.content_hash,
            {
                "memory_id": proposal.memory_id,
                "state": "ACTIVE_CANDIDATE",
                "source_candidate_id": proposal.source_candidate_id,
                "eligible_generation": proposal.eligible_generation,
            },
            self.recorded_at,
        )
        try:
            record_action = self.graph.append_memory_record(record)
            node_action = self.graph.append_node(node)
        except ProjectGraphViolation:
            current = self.get(proposal.memory_id)
            if current is not None and current.content_hash == proposal.content_hash:
                return "IDEMPOTENT", current
            if current is not None:
                return "IDENTITY_COLLISION", current
            raise
        action = "IDEMPOTENT" if record_action == node_action == "IDEMPOTENT" else "STORED"
        return action, StoredMemory(proposal, proposal.content_hash)

    def deprecate(
        self, memory_id: str, reason: str, *, at: datetime | None = None,
    ) -> StoredMemory:
        _text(reason, "reason")
        current = self.get(memory_id)
        if current is None:
            raise KeyError(memory_id)
        event_at = at or self.recorded_at
        if not isinstance(event_at, datetime) or event_at.tzinfo is None:
            raise E08ContractViolation("deprecation time must be timezone-aware")
        event_material = {
            "memory_id": memory_id, "event_type": "DEPRECATED", "reason": reason,
        }
        event_hash = sha256(_canonical(event_material).encode("utf-8")).hexdigest()
        event_id = "MEMORY-EVENT-" + event_hash[:24]
        self.graph.append_memory_event(GraphMemoryEvent(
            self.project_id, event_id, memory_id, "DEPRECATED", event_hash,
            {"reason": reason}, event_at,
        ))
        self.graph.append_node(GraphNode(
            self.project_id, event_id, "CREATIVE_MEMORY_DEPRECATION", event_hash,
            {"memory_id": memory_id, "reason": reason}, event_at,
        ))
        self.graph.append_edge(GraphEdge(
            self.project_id, event_id, "SUPERSEDES", self.node_id(memory_id),
            event_hash, event_at,
        ))
        return StoredMemory(current.proposal, current.content_hash, "DEPRECATED", reason)

    def get(self, memory_id: str) -> StoredMemory | None:
        record = self.graph.load_memory_record(self.project_id, memory_id)
        if record is None:
            return None
        proposal = _proposal_from_payload(record["payload"])
        if proposal.memory_id != memory_id or proposal.content_hash != record["content_hash"]:
            raise E08ContractViolation("durable memory integrity check failed")
        event = record["latest_event"]
        if event is None:
            return StoredMemory(proposal, record["content_hash"])
        if event["event_type"] != "DEPRECATED":
            raise E08ContractViolation("durable memory event type is unsupported")
        event_payload = event["payload"]
        if (
            not isinstance(event_payload, dict) or set(event_payload) != {"reason"}
            or not isinstance(event_payload["reason"], str)
            or not event_payload["reason"].strip()
        ):
            raise E08ContractViolation("durable memory deprecation payload is invalid")
        expected_event_hash = sha256(_canonical({
            "memory_id": memory_id, "event_type": "DEPRECATED",
            "reason": event_payload["reason"],
        }).encode("utf-8")).hexdigest()
        if (
            event["content_hash"] != expected_event_hash
            or event["event_id"] != "MEMORY-EVENT-" + expected_event_hash[:24]
        ):
            raise E08ContractViolation("durable memory event integrity check failed")
        return StoredMemory(
            proposal, record["content_hash"], "DEPRECATED", event_payload["reason"],
        )
