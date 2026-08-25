"""Eight independently bounded engines for operational Block 1."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from hashlib import sha256
import hmac
from itertools import islice
import json
from threading import RLock
from typing import Any, Iterable, Mapping

from .common import (
    AuthorityContext, AuthorityVerifier, CapacityExceeded, ContractViolation, Envelope,
    IdentityCollision, plain_copy,
)
from .evidence import EvidenceVerifier
from .storage import OperationalStore

MAX_SOURCES = 1_000
_ROUTES = {
    ("USER", "E01"), ("E01", "E02"), ("E02", "E03"), ("E03", "E05"),
    ("E05", "E06"), ("E06", "E07"), ("E07", "E08"), ("E08", "RUNTIME"),
    ("RUNTIME", "CALLER"),
}
_EXPECTED_PRODUCER = {
    "E01": "USER", "E02": "E01", "E03": "E02", "E05": "E03",
    "E06": "E05", "E07": "E06", "E08": "E07",
}


@dataclass(frozen=True, slots=True)
class EngineResult:
    envelope: Envelope
    disposition: str


def _require_consumer(envelope: Envelope, engine: str) -> None:
    if envelope.consumer != engine:
        raise ContractViolation(f"{engine} received envelope for {envelope.consumer}")
    expected = _EXPECTED_PRODUCER.get(engine)
    if expected is not None and envelope.producer != expected:
        raise ContractViolation(f"{engine} received envelope from {envelope.producer}, expected {expected}")


def _execution_fingerprint(payload: Mapping[str, Any]) -> str:
    material = {
        "execution_status": payload.get("execution_status"),
        "method_version": payload.get("method_version"),
        "input_fingerprint": payload.get("input_fingerprint"),
        "outcome": plain_copy(payload.get("outcome")),
        "validation_status": payload.get("validation_status"),
        "execution_is_validation": payload.get("execution_is_validation"),
        "evidence_fingerprint": payload.get("evidence_fingerprint"),
        "task_id": payload.get("execution_task_id"),
        "run_id": payload.get("execution_run_id"),
    }
    return sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _evidence_fingerprint(evidence: Any) -> str:
    return sha256(json.dumps(
        plain_copy(evidence), sort_keys=True, separators=(",", ":"),
    ).encode()).hexdigest()


def _candidate_fingerprint(candidate: Mapping[str, Any]) -> str:
    return sha256(json.dumps(
        plain_copy(candidate), sort_keys=True, separators=(",", ":"),
    ).encode()).hexdigest()


def _decision_material(governance: Mapping[str, Any]) -> bytes:
    fields = {
        key: plain_copy(governance.get(key)) for key in (
            "decision_issuer", "task_id", "run_id", "action", "decision",
            "input_fingerprint", "candidate_fingerprint",
        )
    }
    return json.dumps(fields, sort_keys=True, separators=(",", ":")).encode()


def _prior_fingerprint(envelope: Envelope, *, producer: str, consumer: str,
                       payload: Mapping[str, Any], restrictions: tuple[str, ...]) -> str:
    if not envelope.lineage or not envelope.trace or envelope.logical_time < 1:
        raise ContractViolation("handoff history is incomplete")
    prior = Envelope(
        message_id=envelope.lineage[-1], task_id=envelope.task_id,
        run_id=envelope.run_id, producer=producer, consumer=consumer,
        contract_version=envelope.contract_version,
        logical_time=envelope.logical_time - 1, payload=payload,
        root_provenance=envelope.root_provenance, lineage=envelope.lineage[:-1],
        epistemic_state=envelope.epistemic_state, uncertainty=envelope.uncertainty,
        restrictions=restrictions, authority=envelope.authority,
        trace=envelope.trace[:-1],
    )
    return prior.fingerprint


class AgentEngine:
    name = "E01"

    def request(self, *, task_id: str, run_id: str, objective: str,
                sources: Iterable[Mapping[str, Any]],
                authority: AuthorityContext | None = None) -> Envelope:
        if not isinstance(objective, str) or not objective.strip():
            raise ContractViolation("objective must be a non-empty string")
        try:
            bounded = list(islice(iter(sources), MAX_SOURCES + 1))
        except TypeError as error:
            raise ContractViolation("sources must be an iterable of mappings") from error
        if len(bounded) > MAX_SOURCES:
            raise ContractViolation(f"source count exceeds {MAX_SOURCES}")
        if any(not isinstance(item, Mapping) for item in bounded):
            raise ContractViolation("every source must be a mapping")
        attempt = authority.nonce if authority else "untrusted"
        root = f"request:{task_id}:{run_id}:{attempt}"
        return Envelope(
            message_id=(
                f"{task_id}:{run_id}:{sha256(root.encode()).hexdigest()[:16]}:0:E01"
            ), task_id=task_id, run_id=run_id,
            producer="USER", consumer="E01", contract_version="0.3.0",
            logical_time=0, payload={"objective": objective.strip(), "sources": bounded},
            root_provenance=root, lineage=(root,), authority=authority,
            restrictions=("NO_IMPLICIT_PROMOTION",),
        )


class KnowledgeAcquisitionEngine:
    name = "E02"

    def __init__(self, verifier: EvidenceVerifier) -> None:
        self._verifier = verifier

    def acquire(self, envelope: Envelope, *, now: int) -> EngineResult:
        _require_consumer(envelope, self.name)
        sources = envelope.payload.get("sources")
        if not isinstance(sources, tuple):
            raise ContractViolation("sources collection is required")
        evidence: list[dict[str, Any]] = []
        rejected: list[str] = []
        seen: dict[str, str] = {}
        for source in sources:
            if not isinstance(source, Mapping):
                raise ContractViolation("source must be a mapping")
            source_id = source.get("source_id")
            valid, rejection_reason = self._verifier.verify(source, now=now)
            if not valid:
                identity = source_id if isinstance(source_id, str) and source_id else "UNKNOWN"
                rejected.append(f"{identity}:{rejection_reason}")
                continue
            material = json.dumps(plain_copy(source), sort_keys=True, separators=(",", ":"))
            digest = sha256(material.encode()).hexdigest()
            if source_id in seen and seen[source_id] != digest:
                raise IdentityCollision("source identity reused for materially different evidence")
            seen[source_id] = digest
            evidence.append(dict(source))
        state = "UNCONFIRMED" if evidence else "INSUFFICIENT EVIDENCE"
        uncertainty = envelope.uncertainty + (("source gaps",) if rejected else ())
        output = envelope.handoff("E02", "E03", {
            "objective": envelope.payload["objective"], "evidence": evidence,
            "rejected_sources": rejected, "acquisition_time": now,
        }, state=state, uncertainty=uncertainty)
        return EngineResult(output, "ACQUIRED" if evidence else "REJECTED")


class PracticeExperimentEngine:
    name = "E03"

    def __init__(self, execution_key: bytes) -> None:
        if len(execution_key) < 32:
            raise ContractViolation("E03 requires a 32-byte execution signing key")
        self._execution_key = bytes(execution_key)

    def execute(self, envelope: Envelope) -> EngineResult:
        _require_consumer(envelope, self.name)
        evidence = envelope.payload.get("evidence", ())
        if not isinstance(evidence, tuple) or any(not isinstance(item, Mapping) for item in evidence):
            raise ContractViolation("E03 evidence must be a tuple of records")
        status = "COMPLETED" if evidence else "NOT_EXECUTED"
        execution = {
            "execution_status": status,
            "method_version": "block1-reference-method/0.3.0",
            "input_fingerprint": envelope.fingerprint,
            "outcome": {"evidence_count": len(evidence)},
            "validation_status": "NOT_VALIDATED",
            "execution_is_validation": False,
            "evidence_fingerprint": _evidence_fingerprint(evidence),
            "execution_task_id": envelope.task_id,
            "execution_run_id": envelope.run_id,
        }
        execution["outcome_fingerprint"] = _execution_fingerprint(execution)
        execution["execution_attestation"] = hmac.new(
            self._execution_key, execution["outcome_fingerprint"].encode(), sha256
        ).hexdigest()
        output = envelope.handoff("E03", "E05", {**envelope.payload, **execution},
            state="UNCONFIRMED" if evidence else "INSUFFICIENT EVIDENCE")
        return EngineResult(output, status)


class IntegrationEngine:
    name = "E04"

    def __init__(self, audit_limit: int = 10_000, seen_limit: int = 100_000) -> None:
        if audit_limit < 1 or seen_limit < 1:
            raise ContractViolation("integration limits must be positive")
        self._seen: OrderedDict[str, str] = OrderedDict()
        self.audit: list[tuple[str, str, str]] = []
        self._lock = RLock()
        self._audit_limit = audit_limit
        self._seen_limit = seen_limit

    def _audit(self, envelope: Envelope, consumer: str, disposition: str) -> None:
        self.audit.append((envelope.message_id, consumer, disposition))
        if len(self.audit) > self._audit_limit:
            del self.audit[:len(self.audit) - self._audit_limit]

    def route(self, envelope: Envelope, expected_consumer: str) -> EngineResult:
        with self._lock:
            if envelope.consumer != expected_consumer:
                self._audit(envelope, expected_consumer, "REJECTED_ROUTE_MISMATCH")
                raise ContractViolation("consumer route mismatch")
            if (envelope.producer, envelope.consumer) not in _ROUTES:
                self._audit(envelope, expected_consumer, "REJECTED_TOPOLOGY")
                raise ContractViolation("producer-consumer transition is not allowed")
            fingerprint = envelope.fingerprint
            prior = self._seen.get(envelope.message_id)
            if prior and prior != fingerprint:
                self._audit(envelope, expected_consumer, "REJECTED_IDENTITY_COLLISION")
                raise IdentityCollision("same message identity has different material payload")
            if prior:
                self._seen.move_to_end(envelope.message_id)
                self._audit(envelope, expected_consumer, "DUPLICATE")
                return EngineResult(envelope, "DUPLICATE")
            if len(self._seen) >= self._seen_limit:
                self._audit(envelope, expected_consumer, "REJECTED_CAPACITY")
                raise CapacityExceeded("E04 idempotency window exhausted; restart/recovery required")
            self._seen[envelope.message_id] = fingerprint
            self._audit(envelope, expected_consumer, "ROUTED")
            return EngineResult(envelope, "ROUTED")


class EvaluationRedTeamEngine:
    name = "E05"

    def __init__(self, execution_key: bytes) -> None:
        if len(execution_key) < 32:
            raise ContractViolation("E05 requires a 32-byte execution verification key")
        self._execution_key = bytes(execution_key)

    def evaluate(self, envelope: Envelope) -> EngineResult:
        _require_consumer(envelope, self.name)
        evidence = envelope.payload.get("evidence", ())
        if not isinstance(evidence, tuple) or any(not isinstance(item, Mapping) for item in evidence):
            raise ContractViolation("E05 evidence must be a tuple of records")
        outcome_fingerprint = envelope.payload.get("outcome_fingerprint")
        execution_attestation = envelope.payload.get("execution_attestation")
        acquisition_payload = {
            key: envelope.payload[key] for key in (
                "objective", "evidence", "rejected_sources", "acquisition_time"
            ) if key in envelope.payload
        }
        declared_input_matches = envelope.payload.get("input_fingerprint") == _prior_fingerprint(
            envelope, producer="E02", consumer="E03",
            payload=acquisition_payload, restrictions=envelope.restrictions,
        )
        execution_valid = (
            envelope.payload.get("execution_status") == "COMPLETED"
            and envelope.payload.get("validation_status") == "NOT_VALIDATED"
            and envelope.payload.get("execution_is_validation") is False
            and envelope.payload.get("evidence_fingerprint") == _evidence_fingerprint(evidence)
            and envelope.payload.get("execution_task_id") == envelope.task_id
            and envelope.payload.get("execution_run_id") == envelope.run_id
            and declared_input_matches
            and envelope.payload.get("method_version") == "block1-reference-method/0.3.0"
            and plain_copy(envelope.payload.get("outcome")) == {"evidence_count": len(evidence)}
            and outcome_fingerprint == _execution_fingerprint(envelope.payload)
            and isinstance(outcome_fingerprint, str)
            and isinstance(execution_attestation, str)
            and hmac.compare_digest(
                hmac.new(self._execution_key, outcome_fingerprint.encode(), sha256).hexdigest(),
                execution_attestation,
            )
        )
        parent: dict[str, str] = {}
        def find(node: str) -> str:
            parent.setdefault(node, node)
            while parent[node] != node:
                parent[node] = parent[parent[node]]
                node = parent[node]
            return node
        def union(left: str, right: str) -> None:
            left_root, right_root = find(left), find(right)
            if left_root != right_root:
                parent[right_root] = left_root
        roots: set[str] = set()
        polarities: dict[str, set[int]] = {}
        contradictions: list[str] = []
        if execution_valid:
            for item in evidence:
                required = ("root_provenance", "correlation_id", "claim_key", "source_id")
                if any(not isinstance(item.get(field), str) or not item[field] for field in required):
                    raise ContractViolation("E05 evidence identity fields are invalid")
                if item.get("polarity") not in (-1, 1):
                    raise ContractViolation("E05 evidence polarity is invalid")
                union(f"root:{item['root_provenance']}", f"correlation:{item['correlation_id']}")
            roots = {find(f"root:{item['root_provenance']}") for item in evidence}
            for item in evidence:
                polarities.setdefault(item["claim_key"], set()).add(item["polarity"])
            contradicted_claims = {
                claim for claim, values in polarities.items() if values == {-1, 1}
            }
            contradictions = [
                item["source_id"] for item in evidence
                if item["claim_key"] in contradicted_claims
            ]
        if not execution_valid or not evidence:
            disposition, state = "INSUFFICIENT", "INSUFFICIENT EVIDENCE"
        elif contradictions:
            disposition, state = "CONTRADICTED", "CONTRADICTED"
        else:
            disposition, state = "CANDIDATE", "PROBABLE"
        assessment = {
            "disposition": disposition, "independent_root_count": len(roots),
            "contradictions": contradictions, "authorization": False,
            "execution_evidence_valid": execution_valid,
            "limitations": list(envelope.uncertainty),
        }
        output = envelope.handoff("E05", "E06", {**envelope.payload, "assessment": assessment}, state=state)
        return EngineResult(output, disposition)


class MemoryLearningEngine:
    name = "E06"

    def __init__(self, store: OperationalStore, verifier: AuthorityVerifier,
                 decision_key: bytes) -> None:
        if len(decision_key) < 32:
            raise ContractViolation("E06 requires a 32-byte E08 decision verification key")
        self._store = store
        self._verifier = verifier
        self._decision_key = bytes(decision_key)

    def prepare_candidate(self, envelope: Envelope) -> EngineResult:
        _require_consumer(envelope, self.name)
        record = {
            "candidate_id": f"{envelope.task_id}:{envelope.run_id}:memory-candidate",
            "record_schema_version": "0.3.0", "contract_version": envelope.contract_version,
            "task_id": envelope.task_id, "run_id": envelope.run_id,
            "lineage": list(envelope.lineage), "assessment": envelope.payload["assessment"],
            "promoted": False, "source_fingerprint": envelope.fingerprint,
        }
        output = envelope.handoff("E06", "E07", {**envelope.payload, "memory_candidate": record},
            restrictions=envelope.restrictions + ("PREPARED_NOT_STORED", "STORED_NOT_PROMOTED"))
        return EngineResult(output, "PREPARED_CANDIDATE")

    def authorize_commit(self, envelope: Envelope, *, action: str, now: int) -> Mapping[str, Any]:
        if envelope.producer != "E08" or envelope.consumer != "RUNTIME":
            raise ContractViolation("E06 commit boundary requires E08 decision addressed to runtime")
        governance = envelope.payload.get("governance")
        if not isinstance(governance, Mapping):
            raise ContractViolation("governance decision is required")
        if action != "store_candidate" or governance.get("action") != action:
            raise ContractViolation("unsupported action cannot dispatch E06 effect")
        if governance.get("decision") != "ALLOW_BOUNDED_ACTION":
            raise ContractViolation("E06 cannot commit without ALLOW_BOUNDED_ACTION")
        signature = governance.get("decision_attestation")
        if not isinstance(signature, str) or len(signature) != 64:
            raise ContractViolation("E08 decision attestation is required")
        expected = hmac.new(self._decision_key, _decision_material(governance), sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise ContractViolation("E08 decision attestation is invalid")
        candidate = envelope.payload.get("memory_candidate")
        if not isinstance(candidate, Mapping):
            raise ContractViolation("memory candidate is required")
        if (
            governance.get("decision_issuer") != "E08"
            or governance.get("task_id") != envelope.task_id
            or governance.get("run_id") != envelope.run_id
            or governance.get("candidate_fingerprint") != _candidate_fingerprint(candidate)
            or governance.get("input_fingerprint") != _prior_fingerprint(
                envelope, producer="E07", consumer="E08",
                payload={
                    key: value for key, value in envelope.payload.items()
                    if key != "governance"
                },
                restrictions=(
                    envelope.restrictions[:-1]
                    if envelope.restrictions
                    and envelope.restrictions[-1] == "DECISION_NOT_ENFORCEMENT"
                    else envelope.restrictions
                ),
            )
        ):
            raise ContractViolation("E08 decision binding is invalid")
        permitted, reason = self._verifier.verify(envelope.authority, envelope, action, now)
        if not permitted:
            raise ContractViolation(f"E06 authority revalidation failed: {reason}")
        return candidate

    def history(self, task_id: str) -> tuple[Mapping[str, Any], ...]:
        return self._store.history(task_id)


class StabilityEngine:
    name = "E07"

    def assess(self, envelope: Envelope, *, store_available: bool) -> EngineResult:
        _require_consumer(envelope, self.name)
        if not isinstance(store_available, bool):
            raise ContractViolation("store_available must be a trusted boolean observation")
        assessment = envelope.payload["assessment"]
        execution_complete = envelope.payload.get("execution_status") == "COMPLETED"
        observations_sufficient = bool(envelope.payload.get("evidence")) and not envelope.uncertainty
        if assessment["disposition"] == "CONTRADICTED":
            health, mode = "DEGRADED", "CONTAINING"
        elif (assessment["disposition"] != "CANDIDATE" or not execution_complete
              or not observations_sufficient or not store_available):
            health, mode = "AT_RISK", "CONTAINING"
        else:
            health, mode = "STABLE", "NORMAL"
        stability = {
            "health": health, "control_mode": mode,
            "observation_sufficient": observations_sufficient,
            "execution_complete": execution_complete,
            "store_available": store_available,
            "action_completion_is_recovery": False,
        }
        output = envelope.handoff("E07", "E08", {**envelope.payload, "stability": stability})
        return EngineResult(output, health)


class GovernanceEngine:
    name = "E08"

    def __init__(self, verifier: AuthorityVerifier, decision_key: bytes) -> None:
        if len(decision_key) < 32:
            raise ContractViolation("E08 requires a 32-byte decision signing key")
        self._verifier = verifier
        self._decision_key = bytes(decision_key)

    def decide(self, envelope: Envelope, *, action: str, now: int) -> EngineResult:
        _require_consumer(envelope, self.name)
        assessment = envelope.payload["assessment"]
        stability = envelope.payload["stability"]
        permitted, authority_reason = self._verifier.verify(envelope.authority, envelope, action, now)
        if not permitted:
            decision = "QUARANTINE"
        elif assessment["disposition"] != "CANDIDATE" or stability["health"] != "STABLE":
            decision = "REVALIDATE"
        else:
            decision = "ALLOW_BOUNDED_ACTION"
        governance = {
            "decision_issuer": "E08", "task_id": envelope.task_id,
            "run_id": envelope.run_id,
            "decision": decision, "action": action, "authority_reason": authority_reason,
            "decision_is_enforcement": False, "runtime_effect_observed": False,
            "input_fingerprint": envelope.fingerprint,
            "candidate_fingerprint": _candidate_fingerprint(envelope.payload["memory_candidate"]),
        }
        governance["decision_attestation"] = hmac.new(
            self._decision_key, _decision_material(governance), sha256
        ).hexdigest()
        payload = {**envelope.payload, "governance": governance}
        output = envelope.handoff("E08", "RUNTIME", payload,
            restrictions=envelope.restrictions + ("DECISION_NOT_ENFORCEMENT",))
        return EngineResult(output, decision)

