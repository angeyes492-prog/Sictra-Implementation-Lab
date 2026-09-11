"""M01 Person Intelligence: professional context without psychographic claims."""

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


FactKind = Literal["FACT", "HYPOTHESIS"]
DecisionProximity = Literal[
    "Observer", "Influencer", "Evaluator", "Recommender",
    "Decision Maker", "Economic Buyer", "Gatekeeper", "UNKNOWN",
]

_ALLOWED_FIELDS = frozenset({
    "name", "company", "title", "department", "seniority", "location",
    "tenure", "responsibility", "experience", "organization_role",
    "contact_kind", "contact_function", "decision_proximity",
})
_PROHIBITED_FIELDS = frozenset({
    "age", "gender", "sex", "ethnicity", "race", "religion", "health",
    "disability", "politics", "sexual_orientation", "personality",
})
_PROXIMITIES = frozenset(DecisionProximity.__args__) - {"UNKNOWN"}


@dataclass(frozen=True, slots=True)
class ProfessionalFact:
    fact_id: str
    person_id: str
    field: str
    value: str
    kind: FactKind
    evidence: EvidenceRef

    def __post_init__(self) -> None:
        for name in ("fact_id", "person_id", "field", "value"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise PrecisionContractViolation(f"{name} must be non-empty")
        normalized = self.field.strip().lower()
        object.__setattr__(self, "field", normalized)
        if normalized in _PROHIBITED_FIELDS:
            raise PrecisionContractViolation(f"prohibited persuasion attribute: {normalized}")
        if normalized not in _ALLOWED_FIELDS:
            raise PrecisionContractViolation(f"professional field is not governed: {normalized}")
        if self.kind not in {"FACT", "HYPOTHESIS"}:
            raise PrecisionContractViolation("professional fact kind is not governed")
        if normalized == "decision_proximity" and self.value not in _PROXIMITIES:
            raise PrecisionContractViolation("decision_proximity value is not governed")


@dataclass(frozen=True, slots=True)
class ProfessionalAttribute:
    field: str
    values: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    root_count: int
    epistemic_state: str
    confidence: str


@dataclass(frozen=True, slots=True)
class PersonProfile:
    profile_id: str
    person_id: str
    attributes: tuple[ProfessionalAttribute, ...]
    decision_proximity: DecisionProximity
    decision_proximity_evidence_ids: tuple[str, ...]
    decision_proximity_confidence: str
    contradictions: tuple[str, ...]
    omitted_evidence_ids: tuple[str, ...]
    restrictions: tuple[str, ...]

    @property
    def output_fingerprint(self) -> str:
        return fingerprint(self)

    @property
    def searchable_tokens(self) -> frozenset[str]:
        tokens: set[str] = set()
        for attribute in self.attributes:
            for value in attribute.values:
                tokens.update(part.casefold() for part in value.replace("/", " ").split())
        return frozenset(tokens)


@dataclass(frozen=True, slots=True)
class PersonResult:
    assessment: EngineAssessment
    profile: PersonProfile | None


class PersonIntelligenceEngine:
    name = "M01"

    def __init__(self, *, max_facts: int = 500) -> None:
        if max_facts < 1:
            raise PrecisionContractViolation("max_facts must be positive")
        self._max_facts = max_facts

    def build(self, *, person_id: str, facts: tuple[ProfessionalFact, ...], now: int) -> PersonResult:
        if not isinstance(person_id, str) or not person_id.strip():
            raise PrecisionContractViolation("person_id must be non-empty")
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise PrecisionContractViolation("now must be a non-negative integer")
        facts = tuple(facts)
        validate_identity_set(facts, id_attribute="fact_id", limit=self._max_facts)
        if any(item.person_id != person_id for item in facts):
            raise PrecisionContractViolation("M01 cannot combine different person identities")

        unique = {item.fact_id: item for item in facts}
        current = [item for item in unique.values() if item.evidence.current_at(now)]
        omitted = tuple(sorted(
            item.evidence.evidence_id for item in unique.values() if not item.evidence.current_at(now)
        ))
        if not current:
            reasons = ("NO_CURRENT_PROFESSIONAL_EVIDENCE",) + (
                ("NON_CURRENT_EVIDENCE_OMITTED",) if omitted else ()
            )
            return PersonResult(EngineAssessment(self.name, "RETURN_UPSTREAM", reasons, (), None), None)

        attributes: list[ProfessionalAttribute] = []
        contradictions: list[str] = []
        by_field: dict[str, list[ProfessionalFact]] = {}
        for item in current:
            if item.field != "decision_proximity":
                by_field.setdefault(item.field, []).append(item)
        for field, values in sorted(by_field.items()):
            distinct_values = tuple(sorted({item.value for item in values}))
            fact_values = {item.value for item in values if item.kind == "FACT"}
            state = "CONTRADICTED" if len(fact_values) > 1 else (
                "PROBABLE" if any(item.kind == "HYPOTHESIS" for item in values) else "VERIFIED"
            )
            if len(fact_values) > 1:
                contradictions.append(f"CONTRADICTORY_{field.upper()}")
            attributes.append(ProfessionalAttribute(
                field=field,
                values=distinct_values,
                evidence_ids=tuple(sorted({item.evidence.evidence_id for item in values})),
                root_count=len({item.evidence.root_provenance for item in values}),
                epistemic_state=state,
                confidence=weakest_confidence(tuple(item.evidence.confidence for item in values)),
            ))

        proximity_items = [item for item in current if item.field == "decision_proximity"]
        proximity_values = {item.value for item in proximity_items}
        if len(proximity_values) == 1:
            proximity: DecisionProximity = next(iter(proximity_values))  # type: ignore[assignment]
            proximity_evidence = tuple(sorted({
                item.evidence.evidence_id for item in proximity_items
            }))
            proximity_confidence = weakest_confidence(tuple(
                item.evidence.confidence for item in proximity_items
            ))
        else:
            proximity = "UNKNOWN"
            proximity_evidence = tuple(sorted({
                item.evidence.evidence_id for item in proximity_items
            }))
            proximity_confidence = "E"
            if len(proximity_values) > 1:
                contradictions.append("CONTRADICTORY_DECISION_PROXIMITY")

        restrictions = ("PROFESSIONAL_CONTEXT_ONLY", "NO_PSYCHOGRAPHIC_INFERENCE")
        if any(attribute.field == "contact_kind" for attribute in attributes):
            restrictions += ("CONTACT_KIND_IS_NOT_DECISION_AUTHORITY",)
        profile = PersonProfile(
            profile_id=f"{person_id}:person-profile:v0.1",
            person_id=person_id,
            attributes=tuple(attributes),
            decision_proximity=proximity,
            decision_proximity_evidence_ids=proximity_evidence,
            decision_proximity_confidence=proximity_confidence,
            contradictions=tuple(sorted(contradictions)),
            omitted_evidence_ids=omitted,
            restrictions=restrictions,
        )
        disposition = "CONTRADICTED" if contradictions else "ACCEPTED"
        reasons = tuple(sorted(contradictions)) + (
            ("NON_CURRENT_EVIDENCE_OMITTED",) if omitted else ()
        )
        evidence_ids = tuple(sorted({item.evidence.evidence_id for item in current}))
        return PersonResult(
            EngineAssessment(self.name, disposition, reasons, evidence_ids, profile.output_fingerprint),
            profile,
        )
