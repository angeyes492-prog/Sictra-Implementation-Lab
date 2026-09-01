"""E01 clean-trial preflight boundary.

The module deliberately classifies fixture readiness before any observer is
exposed. It does not inspect visual output, rank candidates, or convert a
result into Design Memory, a local rule, or an implementation authorization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Disposition = Literal[
    "READY_FOR_OBSERVATION",
    "RETURN_UPSTREAM",
    "INVALID_TRIAL",
    "UNSUPPORTED_COMBINATION",
]
_EQUIVALENCE_FIELDS = (
    "content_id",
    "task_version",
    "labels",
    "scale",
    "uncertainty_object",
    "annotation_burden",
    "context_version",
    "attention_condition",
    "implementation_burden",
)


class E01PreflightViolation(ValueError):
    """Fixture structure cannot be assessed safely."""


def _required(**fields: str) -> None:
    missing = [name for name, value in fields.items() if not isinstance(value, str) or not value.strip()]
    if missing:
        raise E01PreflightViolation(f"missing required fields: {', '.join(missing)}")


@dataclass(frozen=True, slots=True)
class UpstreamIntelligence:
    """The minimum fidelity record required before E01 may begin a trial."""

    object_id: str
    source_identity: str
    evidence_status: str
    authority_reference: str
    audience_context: str
    decision_context: str

    def __post_init__(self) -> None:
        values = (
            self.object_id,
            self.source_identity,
            self.evidence_status,
            self.authority_reference,
            self.audience_context,
            self.decision_context,
        )
        if any(not isinstance(value, str) for value in values):
            raise E01PreflightViolation("upstream fidelity fields must be strings")


@dataclass(frozen=True, slots=True)
class TaskDefinition:
    claim_id: str
    target: str
    action: str
    scope: str
    version: str
    wording: str
    leakage_clear: bool

    def __post_init__(self) -> None:
        _required(
            claim_id=self.claim_id,
            target=self.target,
            action=self.action,
            scope=self.scope,
            version=self.version,
            wording=self.wording,
        )
        if not isinstance(self.leakage_clear, bool):
            raise E01PreflightViolation("leakage_clear must be boolean")


@dataclass(frozen=True, slots=True)
class Candidate:
    candidate_id: str
    mechanism: str
    content_id: str
    task_version: str
    labels: tuple[str, ...]
    scale: str
    uncertainty_object: str
    annotation_burden: str
    context_version: str
    attention_condition: str
    implementation_burden: str

    def __post_init__(self) -> None:
        _required(
            candidate_id=self.candidate_id,
            mechanism=self.mechanism,
            content_id=self.content_id,
            task_version=self.task_version,
            scale=self.scale,
            uncertainty_object=self.uncertainty_object,
            annotation_burden=self.annotation_burden,
            context_version=self.context_version,
            attention_condition=self.attention_condition,
            implementation_burden=self.implementation_burden,
        )
        if not self.labels or any(not isinstance(label, str) or not label.strip() for label in self.labels):
            raise E01PreflightViolation("candidate labels must be non-empty strings")


@dataclass(frozen=True, slots=True)
class ObserverProfile:
    observer_id: str
    external_to_e01: bool
    independence_reviewed: bool
    material_leakage: bool
    order_condition: Literal["COUNTERBALANCED", "RANDOMIZED", "UNCONTROLLED"]

    def __post_init__(self) -> None:
        _required(observer_id=self.observer_id)
        if not all(isinstance(value, bool) for value in (
            self.external_to_e01,
            self.independence_reviewed,
            self.material_leakage,
        )):
            raise E01PreflightViolation("observer flags must be boolean")
        if self.order_condition not in {"COUNTERBALANCED", "RANDOMIZED", "UNCONTROLLED"}:
            raise E01PreflightViolation("order_condition is not governed")


@dataclass(frozen=True, slots=True)
class Confounder:
    variable: str
    disposition: Literal["MANIPULATED", "CONTROLLED", "PROHIBITED", "TOLERATED", "DISCOVERED_POST_TRIAL"]
    material: bool

    def __post_init__(self) -> None:
        _required(variable=self.variable)
        if self.disposition not in {
            "MANIPULATED", "CONTROLLED", "PROHIBITED", "TOLERATED", "DISCOVERED_POST_TRIAL"
        }:
            raise E01PreflightViolation("confounder disposition is not governed")
        if not isinstance(self.material, bool):
            raise E01PreflightViolation("confounder material must be boolean")


@dataclass(frozen=True, slots=True)
class ClaimComposition:
    source_claim_ids: tuple[str, ...] = ()
    interaction_tested: bool = False

    def __post_init__(self) -> None:
        if any(not isinstance(value, str) or not value.strip() for value in self.source_claim_ids):
            raise E01PreflightViolation("source_claim_ids must be non-empty strings")
        if not isinstance(self.interaction_tested, bool):
            raise E01PreflightViolation("interaction_tested must be boolean")


@dataclass(frozen=True, slots=True)
class Fixture:
    fixture_id: str
    upstream: UpstreamIntelligence
    task: TaskDefinition
    candidate_a: Candidate
    candidate_b: Candidate
    intended_manipulation: str
    observer: ObserverProfile
    confounders: tuple[Confounder, ...]
    composition: ClaimComposition = ClaimComposition()

    def __post_init__(self) -> None:
        _required(fixture_id=self.fixture_id, intended_manipulation=self.intended_manipulation)
        if self.candidate_a.candidate_id == self.candidate_b.candidate_id:
            raise E01PreflightViolation("candidate identities must be distinct")
        if self.candidate_a.mechanism == self.candidate_b.mechanism:
            raise E01PreflightViolation("candidates must differ by the intended mechanism")


@dataclass(frozen=True, slots=True)
class PreflightAssessment:
    disposition: Disposition
    reasons: tuple[str, ...]
    quarantined_claim_ids: tuple[str, ...]

    @property
    def ready_for_observation(self) -> bool:
        return self.disposition == "READY_FOR_OBSERVATION"


def _equivalence_failures(a: Candidate, b: Candidate) -> tuple[str, ...]:
    return tuple(
        field.upper()
        for field in _EQUIVALENCE_FIELDS
        if getattr(a, field) != getattr(b, field)
    )


def assess_fixture(fixture: Fixture) -> PreflightAssessment:
    """Classify trial readiness without producing a perceptual claim.

    Precedence is intentional: missing upstream inputs force ``RETURN_UPSTREAM``;
    material contamination invalidates the trial; an unsupported combination is
    then kept separate from a clean single-claim fixture.
    """
    upstream_missing = tuple(
        name.upper()
        for name, value in (
            ("object_id", fixture.upstream.object_id),
            ("source_identity", fixture.upstream.source_identity),
            ("evidence_status", fixture.upstream.evidence_status),
            ("authority_reference", fixture.upstream.authority_reference),
            ("audience_context", fixture.upstream.audience_context),
            ("decision_context", fixture.upstream.decision_context),
        )
        if not value.strip()
    )
    if upstream_missing:
        return PreflightAssessment("RETURN_UPSTREAM", upstream_missing, (fixture.task.claim_id,))

    failures: list[str] = []
    if not fixture.task.leakage_clear:
        failures.append("TASK_LEAKAGE")
    failures.extend(f"SEMANTIC_EQUIVALENCE_{field}" for field in _equivalence_failures(
        fixture.candidate_a, fixture.candidate_b
    ))
    if not fixture.observer.external_to_e01:
        failures.append("OBSERVER_NOT_EXTERNAL")
    if not fixture.observer.independence_reviewed:
        failures.append("OBSERVER_INDEPENDENCE_UNREVIEWED")
    if fixture.observer.material_leakage:
        failures.append("OBSERVER_MATERIAL_LEAKAGE")
    if fixture.observer.order_condition == "UNCONTROLLED":
        failures.append("ORDER_UNCONTROLLED")
    failures.extend(
        f"MATERIAL_CONFOUNDER_{item.variable}"
        for item in fixture.confounders
        if item.material and item.disposition in {"PROHIBITED", "DISCOVERED_POST_TRIAL"}
    )
    if failures:
        return PreflightAssessment("INVALID_TRIAL", tuple(failures), (fixture.task.claim_id,))

    if fixture.composition.source_claim_ids and not fixture.composition.interaction_tested:
        return PreflightAssessment(
            "UNSUPPORTED_COMBINATION",
            ("EVIDENCE_CONJUNCTION_OVERREACH",),
            (fixture.task.claim_id,),
        )
    return PreflightAssessment("READY_FOR_OBSERVATION", (), ())
