"""M05 Context Intelligence: evidence-preserving Global-to-Moment relevance map."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .contracts import (
    EngineAssessment,
    EvidenceRef,
    PrecisionContractViolation,
    fingerprint,
    validate_identity_set,
    weakest_confidence,
)


ContextScope = Literal["GLOBAL", "INDUSTRY", "ACCOUNT", "ROLE", "MOMENT"]
StatementKind = Literal["FACT", "HYPOTHESIS"]
_SCOPES = ContextScope.__args__
_KINDS = frozenset(StatementKind.__args__)


@dataclass(frozen=True, slots=True)
class ContextSignal:
    signal_id: str
    insight_id: str
    target_id: str
    scope: ContextScope
    claim_key: str
    statement: str
    kind: StatementKind
    polarity: int
    tags: tuple[str, ...]
    valid_from: int
    valid_until: int
    evidence: EvidenceRef

    def __post_init__(self) -> None:
        for name in ("signal_id", "insight_id", "target_id", "claim_key", "statement"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise PrecisionContractViolation(f"{name} must be non-empty")
        if self.scope not in _SCOPES:
            raise PrecisionContractViolation("context scope is not governed")
        if self.kind not in _KINDS:
            raise PrecisionContractViolation("context statement kind is not governed")
        if self.polarity not in {-1, 1}:
            raise PrecisionContractViolation("context polarity must be -1 or 1")
        if any(not isinstance(tag, str) or not tag.strip() for tag in self.tags):
            raise PrecisionContractViolation("context tags must be non-empty strings")
        object.__setattr__(self, "tags", tuple(self.tags))
        if any(
            not isinstance(value, int) or isinstance(value, bool)
            for value in (self.valid_from, self.valid_until)
        ):
            raise PrecisionContractViolation("context validity bounds must be integers")
        if self.valid_from < 0 or self.valid_until < self.valid_from:
            raise PrecisionContractViolation("context validity window is invalid")

    def active_at(self, now: int) -> bool:
        return self.evidence.current_at(now) and self.valid_from <= now <= self.valid_until


@dataclass(frozen=True, slots=True)
class ContextStage:
    scope: ContextScope
    statements: tuple[str, ...]
    fact_statements: tuple[str, ...]
    hypothesis_statements: tuple[str, ...]
    tags: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    root_provenance_ids: tuple[str, ...]
    independent_root_count: int
    confidence: str


@dataclass(frozen=True, slots=True)
class ContextRelevanceMap:
    map_id: str
    insight_id: str
    target_id: str
    stages: tuple[ContextStage, ...]
    missing_scopes: tuple[str, ...]
    contradicted_claim_keys: tuple[str, ...]
    omitted_evidence_ids: tuple[str, ...]
    restrictions: tuple[str, ...]

    @property
    def output_fingerprint(self) -> str:
        return fingerprint(self)

    @property
    def tags(self) -> frozenset[str]:
        return frozenset(tag.casefold() for stage in self.stages for tag in stage.tags)


@dataclass(frozen=True, slots=True)
class ContextResult:
    assessment: EngineAssessment
    relevance_map: ContextRelevanceMap | None


class ContextIntelligenceEngine:
    name = "M05"

    def __init__(self, *, max_signals: int = 2_000) -> None:
        if max_signals < 1:
            raise PrecisionContractViolation("max_signals must be positive")
        self._max_signals = max_signals

    def map_relevance(
        self, *, insight_id: str, target_id: str,
        signals: tuple[ContextSignal, ...], now: int,
    ) -> ContextResult:
        if not insight_id.strip() or not target_id.strip():
            raise PrecisionContractViolation("insight_id and target_id are required")
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise PrecisionContractViolation("now must be a non-negative integer")
        signals = tuple(signals)
        validate_identity_set(signals, id_attribute="signal_id", limit=self._max_signals)
        if any(item.insight_id != insight_id or item.target_id != target_id for item in signals):
            raise PrecisionContractViolation("M05 cannot combine different insight or target identities")
        unique = {item.signal_id: item for item in signals}
        active = [item for item in unique.values() if item.active_at(now)]
        omitted = tuple(sorted(
            item.evidence.evidence_id for item in unique.values() if not item.active_at(now)
        ))
        if not any(item.scope == "GLOBAL" for item in active):
            reasons = ("GLOBAL_INTELLIGENCE_MISSING_OR_NOT_CURRENT",) + (
                ("NON_CURRENT_OR_OUT_OF_WINDOW_EVIDENCE_OMITTED",) if omitted else ()
            )
            return ContextResult(
                EngineAssessment(self.name, "RETURN_UPSTREAM", reasons, (), None), None,
            )

        polarity_by_claim: dict[str, set[int]] = {}
        for item in active:
            polarity_by_claim.setdefault(item.claim_key, set()).add(item.polarity)
        contradicted = tuple(sorted(
            claim for claim, polarities in polarity_by_claim.items() if polarities == {-1, 1}
        ))

        stages: list[ContextStage] = []
        present_scopes: set[str] = set()
        for scope in _SCOPES:
            scoped = [item for item in active if item.scope == scope]
            if not scoped:
                continue
            present_scopes.add(scope)
            stages.append(ContextStage(
                scope=scope,
                statements=tuple(sorted({item.statement for item in scoped})),
                fact_statements=tuple(sorted({
                    item.statement for item in scoped if item.kind == "FACT"
                })),
                hypothesis_statements=tuple(sorted({
                    item.statement for item in scoped if item.kind == "HYPOTHESIS"
                })),
                tags=tuple(sorted({tag for item in scoped for tag in item.tags})),
                evidence_ids=tuple(sorted({item.evidence.evidence_id for item in scoped})),
                root_provenance_ids=tuple(sorted({
                    item.evidence.root_provenance for item in scoped
                })),
                independent_root_count=len({item.evidence.root_provenance for item in scoped}),
                confidence=weakest_confidence(tuple(item.evidence.confidence for item in scoped)),
            ))
        missing = tuple(scope for scope in _SCOPES if scope not in present_scopes)
        restrictions = (
            "CONTEXT_IS_NOT_DECISION_HYPOTHESIS",
            "ACCOUNT_ROLE_AND_TIMING_IMPLICATIONS_REQUIRE_OWN_EVIDENCE",
            "NO_UPSTREAM_CERTAINTY_UPGRADE",
        )
        relevance_map = ContextRelevanceMap(
            map_id=f"{insight_id}:{target_id}:context-map:v0.1",
            insight_id=insight_id,
            target_id=target_id,
            stages=tuple(stages),
            missing_scopes=missing,
            contradicted_claim_keys=contradicted,
            omitted_evidence_ids=omitted,
            restrictions=restrictions,
        )
        reasons: tuple[str, ...] = ()
        if missing:
            reasons += tuple(f"MISSING_{scope}_CONTEXT" for scope in missing)
        if contradicted:
            reasons += tuple(f"CONTRADICTED_CONTEXT_CLAIM:{claim}" for claim in contradicted)
        if omitted:
            reasons += ("NON_CURRENT_OR_OUT_OF_WINDOW_EVIDENCE_OMITTED",)
        disposition = "CONTRADICTED" if contradicted else ("PARTIAL" if reasons else "ACCEPTED")
        return ContextResult(
            EngineAssessment(
                self.name, disposition, reasons,
                tuple(sorted({item.evidence.evidence_id for item in active})),
                relevance_map.output_fingerprint,
            ),
            relevance_map,
        )

