"""Independent-observation boundary for E07 visual red-team evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .e06_production import ProductionCandidate


E07Disposition = Literal[
    "PASS_RECOMMENDED_FOR_EXTERNAL_REVIEW",
    "REVISE",
    "BLOCKED",
    "RETURN_TO_PREVIOUS",
    "UNSUPPORTED_VERSION",
]
_VERSION_PREFIX = "0.1."
_CRITERIA = frozenset({
    "COMPREHENSION", "HIERARCHY", "LEGIBILITY", "ACCESSIBILITY",
    "CLAIM_FIDELITY", "CHANNEL_ADAPTATION", "BRAND_AND_RIGHTS",
    "NON_DECEPTIVE_PERSUASION",
})


class E07ContractViolation(ValueError):
    """Malformed audits cannot be interpreted as a visual assessment."""


def _text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise E07ContractViolation(f"{name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class RubricObservation:
    criterion: str
    score: int
    evidence_ids: tuple[str, ...]
    method: str
    finding: str
    critical_failure: bool = False

    def __post_init__(self) -> None:
        for name, value in (
            ("criterion", self.criterion), ("method", self.method), ("finding", self.finding),
        ):
            _text(value, name)
        if not isinstance(self.score, int) or not 0 <= self.score <= 100:
            raise E07ContractViolation("score must be an integer from 0 to 100")
        if not self.evidence_ids or any(not value.strip() for value in self.evidence_ids):
            raise E07ContractViolation("each observation needs attributable evidence")
        if not isinstance(self.critical_failure, bool):
            raise E07ContractViolation("critical_failure must be boolean")

    @property
    def severity(self) -> str:
        if self.critical_failure or self.score < 60:
            return "CRITICAL"
        if self.score < 80:
            return "MAJOR"
        return "PASS"


@dataclass(frozen=True, slots=True)
class VisualReview:
    review_id: str
    contract_version: str
    candidate_id: str
    candidate_sha256: str
    reviewer_id: str
    independent: bool
    observations: tuple[RubricObservation, ...]

    def __post_init__(self) -> None:
        for name, value in (
            ("review_id", self.review_id), ("contract_version", self.contract_version),
            ("candidate_id", self.candidate_id), ("candidate_sha256", self.candidate_sha256),
            ("reviewer_id", self.reviewer_id),
        ):
            _text(value, name)
        if not isinstance(self.independent, bool):
            raise E07ContractViolation("independent must be boolean")
        if len({item.criterion for item in self.observations}) != len(self.observations):
            raise E07ContractViolation("rubric criteria must be unique")


@dataclass(frozen=True, slots=True)
class VisualFinding:
    criterion: str
    score: int
    severity: str
    finding: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class VisualAssessment:
    disposition: E07Disposition
    reasons: tuple[str, ...]
    review_id: str
    candidate_id: str
    findings: tuple[VisualFinding, ...]
    acceptance_state: str = "NOT_ACCEPTED"

    @property
    def recommended_for_external_review(self) -> bool:
        return self.disposition == "PASS_RECOMMENDED_FOR_EXTERNAL_REVIEW"


def assess_visual_candidate(
    candidate: ProductionCandidate | None,
    production_disposition: str,
    review: VisualReview,
) -> VisualAssessment:
    """Aggregate independent observations without accepting or repairing output."""

    findings = tuple(
        VisualFinding(item.criterion, item.score, item.severity, item.finding, item.evidence_ids)
        for item in review.observations
    )
    if not review.contract_version.startswith(_VERSION_PREFIX):
        return VisualAssessment("UNSUPPORTED_VERSION", ("CONTRACT_VERSION_UNSUPPORTED",), review.review_id, review.candidate_id, findings)
    if production_disposition != "PRODUCTION_CANDIDATE_READY_FOR_REVIEW" or candidate is None:
        return VisualAssessment("RETURN_TO_PREVIOUS", ("PRODUCTION_CANDIDATE_NOT_READY",), review.review_id, review.candidate_id, findings)

    lineage: list[str] = []
    if review.candidate_id != candidate.candidate_id:
        lineage.append("CANDIDATE_ID_MISMATCH")
    if review.candidate_sha256 != candidate.artifact.sha256:
        lineage.append("CANDIDATE_HASH_MISMATCH")
    if not review.independent:
        lineage.append("REVIEW_NOT_INDEPENDENT")
    if review.reviewer_id == candidate.producer_id:
        lineage.append("REVIEWER_EQUALS_PRODUCER")
    if lineage:
        return VisualAssessment("BLOCKED", tuple(lineage), review.review_id, review.candidate_id, findings)

    observed = {item.criterion for item in review.observations}
    missing = sorted(_CRITERIA - observed)
    unknown = sorted(observed - _CRITERIA)
    if missing or unknown:
        reasons = tuple([f"CRITERION_{item}_MISSING" for item in missing] + [f"CRITERION_{item}_UNKNOWN" for item in unknown])
        return VisualAssessment("BLOCKED", reasons, review.review_id, review.candidate_id, findings)

    critical = tuple(item.criterion for item in review.observations if item.severity == "CRITICAL")
    if critical:
        return VisualAssessment("BLOCKED", tuple(f"CRITICAL_{item}" for item in critical), review.review_id, review.candidate_id, findings)
    major = tuple(item.criterion for item in review.observations if item.severity == "MAJOR")
    if major:
        return VisualAssessment("REVISE", tuple(f"MAJOR_{item}" for item in major), review.review_id, review.candidate_id, findings)
    return VisualAssessment("PASS_RECOMMENDED_FOR_EXTERNAL_REVIEW", (), review.review_id, review.candidate_id, findings)

