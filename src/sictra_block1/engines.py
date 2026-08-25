"""Eight bounded engines for the Block 1 Intelligence reference runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .common import AuthorityContext, ContractViolation, Envelope, IdentityCollision


@dataclass(frozen=True, slots=True)
class EngineResult:
    envelope: Envelope
    disposition: str


class AgentEngine:
    name = "E01"

    def request(self, *, task_id: str, run_id: str, objective: str,
                sources: Iterable[dict[str, Any]], authority: AuthorityContext | None = None) -> Envelope:
        if not objective.strip():
            raise ContractViolation("objective is required")
        return Envelope(
            message_id=f"{run_id}:0:E01", task_id=task_id, run_id=run_id,
            producer="USER", consumer="E01", contract_version="0.2.0",
            logical_time=0, payload={"objective": objective, "sources": list(sources)},
            root_provenance=f"request:{task_id}", lineage=(f"request:{task_id}",),
            authority=authority, restrictions=("NO_IMPLICIT_PROMOTION",),
        )


class KnowledgeAcquisitionEngine:
    name = "E02"

    def acquire(self, envelope: Envelope) -> EngineResult:
        sources = envelope.payload.get("sources", [])
        evidence, rejected = [], []
        for source in sources:
            if source.get("source_id") and source.get("content") and source.get("observed_at") is not None:
                evidence.append(dict(source))
            else:
                rejected.append(source.get("source_id", "UNKNOWN"))
        state = "UNCONFIRMED" if evidence else "INSUFFICIENT EVIDENCE"
        out = envelope.handoff("E02", "E03", {"objective": envelope.payload["objective"],
            "evidence": evidence, "rejected_sources": rejected}, state=state,
            uncertainty=tuple(envelope.uncertainty) + (("source gaps",) if rejected else ()))
        return EngineResult(out, "ACQUIRED" if evidence else "REJECTED")


class PracticeExperimentEngine:
    name = "E03"

    def execute(self, envelope: Envelope) -> EngineResult:
        evidence = envelope.payload.get("evidence", [])
        status = "COMPLETED" if evidence else "NOT_EXECUTED"
        payload = {**envelope.payload, "execution_status": status,
                   "outcome": {"evidence_count": len(evidence)},
                   "execution_is_validation": False}
        out = envelope.handoff("E03", "E05", payload,
            state="UNCONFIRMED" if evidence else "INSUFFICIENT EVIDENCE")
        return EngineResult(out, status)


class IntegrationEngine:
    name = "E04"

    def __init__(self) -> None:
        self._seen: dict[str, str] = {}
        self.audit: list[tuple[str, str, str]] = []

    def route(self, envelope: Envelope, expected_consumer: str) -> EngineResult:
        prior = self._seen.get(envelope.message_id)
        if prior and prior != envelope.fingerprint:
            raise IdentityCollision("same message identity has different material payload")
        if prior:
            self.audit.append((envelope.message_id, expected_consumer, "DUPLICATE"))
            return EngineResult(envelope, "DUPLICATE")
        if envelope.consumer != expected_consumer:
            raise ContractViolation("consumer route mismatch")
        self._seen[envelope.message_id] = envelope.fingerprint
        self.audit.append((envelope.message_id, expected_consumer, "ROUTED"))
        return EngineResult(envelope, "ROUTED")


class EvaluationRedTeamEngine:
    name = "E05"

    def evaluate(self, envelope: Envelope) -> EngineResult:
        evidence = envelope.payload.get("evidence", [])
        roots = {item.get("root_provenance", item.get("source_id")) for item in evidence}
        roots.discard(None)
        contradictions = [item["source_id"] for item in evidence if item.get("contradicts")]
        if not evidence:
            disposition, state = "INSUFFICIENT", "INSUFFICIENT EVIDENCE"
        elif contradictions:
            disposition, state = "CONTRADICTED", "CONTRADICTED"
        else:
            disposition, state = "CANDIDATE", "PROBABLE"
        assessment = {"disposition": disposition,
            "independent_root_count": len(roots), "contradictions": contradictions,
            "authorization": False, "limitations": list(envelope.uncertainty)}
        out = envelope.handoff("E05", "E06", {**envelope.payload, "assessment": assessment}, state=state)
        return EngineResult(out, disposition)


class MemoryLearningEngine:
    name = "E06"

    def __init__(self) -> None:
        self._memory: dict[str, tuple[dict[str, Any], ...]] = {}

    def store_candidate(self, envelope: Envelope) -> EngineResult:
        versions = self._memory.get(envelope.task_id, ())
        record = {"version": len(versions) + 1, "run_id": envelope.run_id,
                  "assessment": envelope.payload["assessment"], "promoted": False,
                  "source_fingerprint": envelope.fingerprint}
        self._memory[envelope.task_id] = versions + (record,)
        out = envelope.handoff("E06", "E07", {**envelope.payload, "memory_candidate": record},
            restrictions=envelope.restrictions + ("STORED_NOT_PROMOTED",))
        return EngineResult(out, "STORED_CANDIDATE")

    def history(self, task_id: str) -> tuple[dict[str, Any], ...]:
        return self._memory.get(task_id, ())


class StabilityEngine:
    name = "E07"

    def assess(self, envelope: Envelope) -> EngineResult:
        assessment = envelope.payload["assessment"]
        if assessment["disposition"] == "INSUFFICIENT":
            health, mode = "AT_RISK", "CONTAINING"
        elif assessment["disposition"] == "CONTRADICTED":
            health, mode = "DEGRADED", "CONTAINING"
        else:
            health, mode = "STABLE", "NORMAL"
        stability = {"health": health, "control_mode": mode,
                     "observation_sufficient": bool(envelope.payload.get("evidence")),
                     "action_completion_is_recovery": False}
        out = envelope.handoff("E07", "E08", {**envelope.payload, "stability": stability})
        return EngineResult(out, health)


class GovernanceEngine:
    name = "E08"

    def decide(self, envelope: Envelope, *, action: str, now: int, known_epoch: int) -> EngineResult:
        authority = envelope.authority
        assessment = envelope.payload["assessment"]
        stability = envelope.payload["stability"]
        permitted = bool(authority and authority.permits(action, now, known_epoch))
        if not permitted:
            decision = "QUARANTINE"
        elif assessment["disposition"] != "CANDIDATE" or stability["health"] != "STABLE":
            decision = "REVALIDATE"
        else:
            decision = "ALLOW_REFERENCE_ACTION"
        payload = {**envelope.payload, "governance": {"decision": decision,
            "action": action, "decision_is_enforcement": False,
            "runtime_effect_observed": False}}
        out = envelope.handoff("E08", "CALLER", payload,
            restrictions=envelope.restrictions + ("DECISION_NOT_ENFORCEMENT",))
        return EngineResult(out, decision)
