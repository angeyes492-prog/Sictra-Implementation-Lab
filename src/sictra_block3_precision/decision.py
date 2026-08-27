"""M02 Decision Intelligence: evidence-bounded, falsifiable decision hypotheses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .behavioral import BehavioralEvidenceProfile
from .context import ContextRelevanceMap
from .contracts import (
    EngineAssessment,
    EvidenceRef,
    PrecisionContractViolation,
    fingerprint,
    validate_identity_set,
    weakest_confidence,
)
from .person import PersonProfile
from .relationship import RelationshipProfile


DecisionDimension = Literal["DRIVER", "HORIZON", "EVIDENCE_PREFERENCE", "FRAMING"]
DecisionBasisKind = Literal["OBSERVATION", "HYPOTHESIS"]
_VALUES: dict[str, frozenset[str]] = {
    "DRIVER": frozenset({"Risk", "Cost", "Growth", "Speed", "Control"}),
    "HORIZON": frozenset({"Now", "Quarter", "Year", "Long-term"}),
    "EVIDENCE_PREFERENCE": frozenset({
        "Data", "Case", "Benchmark", "Financial", "Scenario", "Practical",
    }),
    "FRAMING": frozenset({
        "Opportunity", "Risk", "Cost", "Efficiency", "Advantage", "Resilience",
        "Innovation", "Compliance",
    }),
}
_SIGNAL_SOURCES = frozenset({
    "M01", "M03", "M04", "M05", "ACCOUNT_INTELLIGENCE", "GOVERNED_RULE",
})


@dataclass(frozen=True, slots=True)
class DecisionSignal:
    signal_id: str
    person_id: str
    insight_id: str
    dimension: DecisionDimension
    value: str
    polarity: int
    basis_kind: DecisionBasisKind
    source_engine: str
    basis_reference: str
    evidence: EvidenceRef

    def __post_init__(self) -> None:
        for name in ("signal_id", "person_id", "insight_id", "value", "source_engine", "basis_reference"):
            item = getattr(self, name)
            if not isinstance(item, str) or not item.strip():
                raise PrecisionContractViolation(f"{name} must be non-empty")
        if self.dimension not in _VALUES:
            raise PrecisionContractViolation("decision dimension is not governed")
        if self.value not in _VALUES[self.dimension]:
            raise PrecisionContractViolation("decision value is not governed for its dimension")
        if self.polarity not in {-1, 1}:
            raise PrecisionContractViolation("decision signal polarity must be -1 or 1")
        if self.basis_kind not in {"OBSERVATION", "HYPOTHESIS"}:
            raise PrecisionContractViolation("decision basis kind is not governed")
        if self.source_engine not in _SIGNAL_SOURCES:
            raise PrecisionContractViolation("decision signal source is not governed")


@dataclass(frozen=True, slots=True)
class DecisionCandidate:
    dimension: DecisionDimension
    value: str
    positive_root_count: int
    negative_root_count: int
    evidence_ids: tuple[str, ...]
    basis_references: tuple[str, ...]
    confidence: str
    state: str


@dataclass(frozen=True, slots=True)
class DecisionHypothesis:
    hypothesis_id: str
    person_id: str
    insight_id: str
    primary_driver: str | None
    secondary_drivers: tuple[str, ...]
    horizon: str | None
    evidence_preference: str | None
    framing: str | None
    candidates: tuple[DecisionCandidate, ...]
    input_fingerprints: tuple[str, ...]
    omitted_evidence_ids: tuple[str, ...]
    restrictions: tuple[str, ...]

    @property
    def output_fingerprint(self) -> str:
        return fingerprint(self)


@dataclass(frozen=True, slots=True)
class DecisionResult:
    assessment: EngineAssessment
    hypothesis: DecisionHypothesis | None


class DecisionIntelligenceEngine:
    name = "M02"

    def __init__(self, *, max_signals: int = 1_000) -> None:
        if max_signals < 1:
            raise PrecisionContractViolation("max_signals must be positive")
        self._max_signals = max_signals

    @staticmethod
    def _select(
        dimension: str, candidates: tuple[DecisionCandidate, ...], reasons: list[str],
    ) -> str | None:
        eligible = [
            item for item in candidates
            if item.dimension == dimension and item.state == "SUPPORTED"
        ]
        if not eligible:
            reasons.append(f"{dimension}_INSUFFICIENT_EVIDENCE")
            return None
        maximum = max(item.positive_root_count for item in eligible)
        leaders = [item for item in eligible if item.positive_root_count == maximum]
        if len(leaders) != 1:
            reasons.append(f"{dimension}_AMBIGUOUS")
            return None
        return leaders[0].value

    def formulate(
        self, *, person: PersonProfile, context: ContextRelevanceMap,
        behavioral: BehavioralEvidenceProfile, relationship: RelationshipProfile,
        signals: tuple[DecisionSignal, ...], now: int,
    ) -> DecisionResult:
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise PrecisionContractViolation("now must be a non-negative integer")
        if not (person.person_id == behavioral.person_id == relationship.person_id):
            raise PrecisionContractViolation("M02 inputs do not share one person identity")
        signals = tuple(signals)
        validate_identity_set(signals, id_attribute="signal_id", limit=self._max_signals)
        if any(
            signal.person_id != person.person_id or signal.insight_id != context.insight_id
            for signal in signals
        ):
            raise PrecisionContractViolation("M02 signal identity does not match its input profiles")
        unique = {signal.signal_id: signal for signal in signals}
        usable = [signal for signal in unique.values() if signal.evidence.current_at(now)]
        omitted = tuple(sorted(
            signal.evidence.evidence_id for signal in unique.values()
            if not signal.evidence.current_at(now)
        ))
        if not usable:
            return DecisionResult(
                EngineAssessment(
                    self.name, "RETURN_UPSTREAM",
                    ("NO_CURRENT_DECISION_SIGNALS",) + (
                        ("NON_CURRENT_EVIDENCE_OMITTED",) if omitted else ()
                    ),
                    (), None,
                ),
                None,
            )

        grouped: dict[tuple[str, str], list[DecisionSignal]] = {}
        for signal in usable:
            grouped.setdefault((signal.dimension, signal.value), []).append(signal)
        candidates: list[DecisionCandidate] = []
        contradiction_found = False
        for (dimension, value), supporting in sorted(grouped.items()):
            positive = {
                signal.evidence.root_provenance for signal in supporting if signal.polarity == 1
            }
            negative = {
                signal.evidence.root_provenance for signal in supporting if signal.polarity == -1
            }
            if positive and negative:
                state = "CONTRADICTED"
                contradiction_found = True
            elif positive:
                state = "SUPPORTED"
            else:
                state = "NEGATIVE_ONLY"
            candidates.append(DecisionCandidate(
                dimension=dimension,  # type: ignore[arg-type]
                value=value,
                positive_root_count=len(positive),
                negative_root_count=len(negative),
                evidence_ids=tuple(sorted({signal.evidence.evidence_id for signal in supporting})),
                basis_references=tuple(sorted({signal.basis_reference for signal in supporting})),
                confidence=weakest_confidence(tuple(
                    signal.evidence.confidence for signal in supporting
                )),
                state=state,
            ))

        candidate_tuple = tuple(candidates)
        reasons: list[str] = []
        primary = self._select("DRIVER", candidate_tuple, reasons)
        horizon = self._select("HORIZON", candidate_tuple, reasons)
        preference = self._select("EVIDENCE_PREFERENCE", candidate_tuple, reasons)
        framing = self._select("FRAMING", candidate_tuple, reasons)
        secondary = tuple(
            item.value for item in sorted(
                (
                    candidate for candidate in candidates
                    if candidate.dimension == "DRIVER"
                    and candidate.state == "SUPPORTED"
                    and candidate.value != primary
                ),
                key=lambda item: (-item.positive_root_count, item.value),
            )
        )
        if person.contradictions:
            reasons.append("PERSON_PROFILE_CONTRADICTIONS_PRESERVED")
        if context.contradicted_claim_keys:
            reasons.append("CONTEXT_CONTRADICTIONS_PRESERVED")
        if relationship.unsubscribe_observed:
            reasons.append("UNSUBSCRIBE_OBSERVED_OUTSIDE_DECISION_AUTHORITY")
        if omitted:
            reasons.append("NON_CURRENT_EVIDENCE_OMITTED")
        if contradiction_found:
            reasons.append("DECISION_SIGNAL_CONTRADICTION")

        hypothesis = DecisionHypothesis(
            hypothesis_id=f"{person.person_id}:{context.insight_id}:decision-hypothesis:v0.1",
            person_id=person.person_id,
            insight_id=context.insight_id,
            primary_driver=primary,
            secondary_drivers=secondary,
            horizon=horizon,
            evidence_preference=preference,
            framing=framing,
            candidates=candidate_tuple,
            input_fingerprints=(
                person.output_fingerprint,
                context.output_fingerprint,
                behavioral.output_fingerprint,
                relationship.output_fingerprint,
            ),
            omitted_evidence_ids=omitted,
            restrictions=(
                "HYPOTHESIS_NOT_PERSONALITY",
                "HYPOTHESIS_NOT_FACT",
                "NO_CONFIDENCE_INFLATION",
                "NO_DELIVERY_AUTHORITY",
            ),
        )
        disposition = "CONTRADICTED" if contradiction_found else (
            "PARTIAL" if reasons else "ACCEPTED"
        )
        return DecisionResult(
            EngineAssessment(
                self.name,
                disposition,
                tuple(sorted(set(reasons))),
                tuple(sorted({signal.evidence.evidence_id for signal in usable})),
                hypothesis.output_fingerprint,
            ),
            hypothesis,
        )
