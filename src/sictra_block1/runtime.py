"""Recoverable, observable composition of the eight Block 1 engines."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any, Callable, Iterable, Mapping

from .common import (
    AuthorityContext, AuthorityVerifier, ContractViolation, Envelope,
    IdentityCollision, plain_copy,
)
from .evidence import EvidenceVerifier
from .engines import (
    AgentEngine, EvaluationRedTeamEngine, GovernanceEngine, IntegrationEngine,
    KnowledgeAcquisitionEngine, MemoryLearningEngine, PracticeExperimentEngine,
    StabilityEngine,
)
from .storage import OperationalStore


@dataclass(slots=True)
class IntelligenceRuntime:
    agent: AgentEngine
    acquisition: KnowledgeAcquisitionEngine
    experiment: PracticeExperimentEngine
    integration: IntegrationEngine
    evaluation: EvaluationRedTeamEngine
    memory: MemoryLearningEngine
    stability: StabilityEngine
    governance: GovernanceEngine
    store: OperationalStore
    clock: Callable[[], int]

    @classmethod
    def operational(cls, *, store_path: str | Path = ":memory:",
                    authority_keys: Mapping[str, bytes], authority_audience: str,
                    authority_epoch: int, evidence_keys: Mapping[str, bytes],
                    evidence_scope: str, evidence_max_age: int,
                    evidence_claims: frozenset[str], execution_key: bytes,
                    decision_key: bytes,
                    max_records: int = 100_000, max_attempts: int | None = None,
                    clock: Callable[[], int] | None = None) -> "IntelligenceRuntime":
        store = OperationalStore(
            store_path, max_records=max_records, max_attempts=max_attempts
        )
        authority_verifier = AuthorityVerifier(authority_keys, authority_audience, authority_epoch)
        evidence_verifier = EvidenceVerifier(
            evidence_keys, evidence_scope, evidence_max_age, evidence_claims
        )
        return cls(
            AgentEngine(), KnowledgeAcquisitionEngine(evidence_verifier),
            PracticeExperimentEngine(execution_key), IntegrationEngine(),
            EvaluationRedTeamEngine(execution_key),
            MemoryLearningEngine(store, authority_verifier, decision_key), StabilityEngine(),
            GovernanceEngine(authority_verifier, decision_key),
            store, clock or (lambda: int(time.time())),
        )

    def _route(self, envelope: Envelope, consumer: str) -> None:
        result = self.integration.route(envelope, consumer)
        if result.disposition not in {"ROUTED", "DUPLICATE"}:
            raise ContractViolation(f"unhandled routing disposition at {consumer}")

    def _trusted_now(self) -> int:
        now = self.clock()
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise ContractViolation("now must be a non-negative integer from the trusted adapter")
        return now

    def run(self, *, task_id: str, run_id: str, objective: str,
            sources: Iterable[Mapping[str, Any]], authority: AuthorityContext | None,
            action: str = "store_candidate") -> Envelope:
        now = self._trusted_now()
        if action != "store_candidate":
            raise ContractViolation("unsupported action has no bounded operational handler")
        request = self.agent.request(
            task_id=task_id, run_id=run_id, objective=objective,
            sources=sources, authority=authority,
        )
        request_fingerprint = request.fingerprint
        terminal = self.store.get_terminal(run_id, request_fingerprint)
        if terminal:
            prior_request_fingerprint, prior_result = terminal
            if prior_request_fingerprint != request_fingerprint:
                raise IdentityCollision("run identity reused with different request")
            replay = prior_result.to_dict()
            replay["payload"] = {
                **plain_copy(prior_result.payload),
                "replay": {
                    "mode": "HISTORICAL_TERMINAL",
                    "current_authority_revalidated": False,
                    "new_effect": False,
                },
            }
            replay["restrictions"] = list(prior_result.restrictions) + [
                "HISTORICAL_REPLAY_NOT_REAUTHORIZATION"
            ]
            replay["message_id"] = f"{prior_result.message_id}:historical-replay"
            replay["logical_time"] = prior_result.logical_time + 1
            replay["lineage"] = list(prior_result.lineage) + [prior_result.message_id]
            replay["trace"] = list(prior_result.trace) + ["CALLER->CALLER:HISTORICAL_REPLAY"]
            return Envelope.from_dict(replay)
        committed_terminal = self.store.get_committed_terminal(run_id)
        if committed_terminal is not None:
            raise IdentityCollision("run identity reused with different committed request")

        self.store.record_state(request_fingerprint, run_id, "STARTED", "VALIDATED_REQUEST", now)
        try:
            self._route(request, "E01")
            current = request.handoff("E01", "E02", request.payload)
            self._route(current, "E02")
            current = self.acquisition.acquire(current, now=now).envelope
            self._route(current, "E03")
            current = self.experiment.execute(current).envelope
            self._route(current, "E05")
            current = self.evaluation.evaluate(current).envelope
            self._route(current, "E06")
            current = self.memory.prepare_candidate(current).envelope
            self._route(current, "E07")
            current = self.stability.assess(
                current, store_available=self.store.healthcheck(write_required=True)
            ).envelope
            self._route(current, "E08")
            decision_now = self._trusted_now()
            decision = self.governance.decide(current, action=action, now=decision_now)
            current = decision.envelope
            self._route(current, "RUNTIME")

            if decision.disposition == "ALLOW_BOUNDED_ACTION":
                commit_now = self._trusted_now()
                candidate = self.memory.authorize_commit(
                    current, action=action, now=commit_now
                )
                final = self.store.commit_effect_and_terminal(
                    request_fingerprint=request_fingerprint,
                    decision_envelope=current,
                    candidate_fingerprint=current.fingerprint,
                    record=candidate,
                    action=action,
                )
                self._route(final, "CALLER")
                return final
            enforcement = {
                "action": action, "status": "NOT_EXECUTED", "effect_engine": None,
                "record_version": None, "runtime_effect_observed": False,
            }
            final = current.handoff("RUNTIME", "CALLER", {
                **current.payload, "enforcement": enforcement,
            }, restrictions=current.restrictions + ("NO_EFFECT_EXECUTED",))
            self._route(final, "CALLER")
            return self.store.commit_no_effect_terminal(
                request_fingerprint=request_fingerprint, envelope=final,
            )
        except Exception as exc:
            terminal_after_failure = self.store.get_terminal(run_id, request_fingerprint)
            if (terminal_after_failure is None
                    or terminal_after_failure[0] != request_fingerprint):
                self.store.record_state(
                    request_fingerprint, run_id, "FAILED",
                    f"{type(exc).__name__}:{exc}", now,
                )
            raise

    def close(self) -> None:
        self.store.close()

