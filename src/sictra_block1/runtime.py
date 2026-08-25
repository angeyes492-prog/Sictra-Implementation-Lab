"""Deterministic end-to-end composition of the eight engines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .common import AuthorityContext, Envelope
from .engines import (AgentEngine, EvaluationRedTeamEngine, GovernanceEngine,
    IntegrationEngine, KnowledgeAcquisitionEngine, MemoryLearningEngine,
    PracticeExperimentEngine, StabilityEngine)


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

    @classmethod
    def reference(cls) -> "IntelligenceRuntime":
        return cls(AgentEngine(), KnowledgeAcquisitionEngine(), PracticeExperimentEngine(),
                   IntegrationEngine(), EvaluationRedTeamEngine(), MemoryLearningEngine(),
                   StabilityEngine(), GovernanceEngine())

    def run(self, *, task_id: str, run_id: str, objective: str,
            sources: Iterable[dict[str, Any]], authority: AuthorityContext | None,
            action: str = "store_candidate", now: int = 0, known_epoch: int = 1) -> Envelope:
        current = self.agent.request(task_id=task_id, run_id=run_id,
            objective=objective, sources=sources, authority=authority)
        self.integration.route(current, "E01")
        current = current.handoff("E01", "E02", current.payload)
        self.integration.route(current, "E02")
        current = self.acquisition.acquire(current).envelope
        self.integration.route(current, "E03")
        current = self.experiment.execute(current).envelope
        self.integration.route(current, "E05")
        current = self.evaluation.evaluate(current).envelope
        self.integration.route(current, "E06")
        current = self.memory.store_candidate(current).envelope
        self.integration.route(current, "E07")
        current = self.stability.assess(current).envelope
        self.integration.route(current, "E08")
        return self.governance.decide(current, action=action, now=now, known_epoch=known_epoch).envelope
