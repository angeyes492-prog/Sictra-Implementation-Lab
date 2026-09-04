"""Bounded receipt validation for a human E01 external trial observation.

This is deliberately a record validator, not an experiment runner.  It cannot
turn a locally constructed fixture or synthetic receipt into an accepted design
rule.  Its purpose is to make the still-human E01 review gate attributable and
fail closed when its preconditions are absent or contaminated.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
from hashlib import sha256
import json
from typing import Literal

from .preflight import Fixture, PreflightAssessment


Outcome = Literal["A_SUPPORTED", "B_SUPPORTED", "NO_DISCRIMINATION"]
ObservationDisposition = Literal[
    "OBSERVATION_RECORDED", "RETURN_UPSTREAM", "INVALID_TRIAL", "UNSUPPORTED_VERSION",
]
_OUTCOMES = frozenset(Outcome.__args__)


class E01ObservationViolation(ValueError):
    """A receipt is structurally malformed before it can be classified."""


def _canonical(value: object) -> str:
    def default(item: object) -> object:
        if is_dataclass(item):
            return asdict(item)
        raise TypeError(f"unsupported canonical value: {type(item)!r}")

    return json.dumps(value, default=default, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def fixture_fingerprint(fixture: Fixture) -> str:
    """Bind a review receipt to the exact preflight fixture material."""

    return sha256(_canonical(fixture).encode("utf-8")).hexdigest()


def _required(**fields: str) -> None:
    missing = [name for name, value in fields.items() if not isinstance(value, str) or not value.strip()]
    if missing:
        raise E01ObservationViolation(f"missing required fields: {', '.join(missing)}")


@dataclass(frozen=True, slots=True)
class ExternalObservationReceipt:
    """A human-supplied statement about one already preflighted E01 fixture."""

    receipt_id: str
    contract_version: str
    fixture_id: str
    fixture_hash: str
    fixture_author_id: str
    upstream_object_id: str
    upstream_authority_reference: str
    upstream_temporal_state: str
    reviewer_id: str
    reviewer_role: str
    reviewer_external_to_fixture: bool
    reviewer_independence_reviewed: bool
    reviewer_material_leakage: bool
    thesis_exposed_before_observation: bool
    material_confounder_discovered: bool
    observation_id: str
    outcome: str
    evidence_refs: tuple[str, ...]
    reviewed_at: datetime

    def __post_init__(self) -> None:
        _required(
            receipt_id=self.receipt_id, contract_version=self.contract_version,
            fixture_id=self.fixture_id, fixture_hash=self.fixture_hash,
            fixture_author_id=self.fixture_author_id, upstream_object_id=self.upstream_object_id,
            upstream_authority_reference=self.upstream_authority_reference,
            upstream_temporal_state=self.upstream_temporal_state,
            reviewer_id=self.reviewer_id, reviewer_role=self.reviewer_role,
            observation_id=self.observation_id, outcome=self.outcome,
        )
        if not self.contract_version.startswith("0.1."):
            raise E01ObservationViolation("observation receipt version is unsupported")
        if len(self.fixture_hash) != 64 or any(char not in "0123456789abcdef" for char in self.fixture_hash):
            raise E01ObservationViolation("fixture_hash must be a lowercase SHA-256")
        if self.outcome not in _OUTCOMES:
            raise E01ObservationViolation("observation outcome is not governed")
        if not self.evidence_refs or any(not isinstance(item, str) or not item.strip() for item in self.evidence_refs):
            raise E01ObservationViolation("observation evidence_refs must be non-empty")
        if not isinstance(self.reviewed_at, datetime) or self.reviewed_at.tzinfo is None:
            raise E01ObservationViolation("reviewed_at must be timezone-aware")
        if not all(isinstance(value, bool) for value in (
            self.reviewer_external_to_fixture, self.reviewer_independence_reviewed,
            self.reviewer_material_leakage, self.thesis_exposed_before_observation,
            self.material_confounder_discovered,
        )):
            raise E01ObservationViolation("reviewer and contamination flags must be boolean")


@dataclass(frozen=True, slots=True)
class ExternalObservationAssessment:
    disposition: ObservationDisposition
    reasons: tuple[str, ...]
    receipt_id: str | None
    promotion_state: str = "NOT_PROMOTED"
    acceptance_state: str = "NOT_ACCEPTED"

    @property
    def recorded(self) -> bool:
        return self.disposition == "OBSERVATION_RECORDED"


def assess_external_observation(
    fixture: Fixture,
    preflight: PreflightAssessment,
    receipt: ExternalObservationReceipt,
) -> ExternalObservationAssessment:
    """Validate a bounded external observation without promoting it.

    Upstream insufficiency keeps its existing precedence.  All other violations
    are invalid-trial states because their outcome can no longer support the
    declared perceptual comparison.
    """

    if preflight.disposition == "RETURN_UPSTREAM":
        return ExternalObservationAssessment("RETURN_UPSTREAM", preflight.reasons, None)
    if preflight.disposition != "READY_FOR_OBSERVATION":
        return ExternalObservationAssessment(
            "INVALID_TRIAL", ("PREFLIGHT_NOT_READY", *preflight.reasons), None,
        )

    upstream_failures: list[str] = []
    if receipt.upstream_object_id != fixture.upstream.object_id:
        upstream_failures.append("UPSTREAM_OBJECT_MISMATCH")
    if receipt.upstream_authority_reference != fixture.upstream.authority_reference:
        upstream_failures.append("UPSTREAM_AUTHORITY_MISMATCH")
    if receipt.upstream_temporal_state != "CURRENT":
        upstream_failures.append("UPSTREAM_NOT_CURRENT")
    if upstream_failures:
        return ExternalObservationAssessment("RETURN_UPSTREAM", tuple(upstream_failures), None)

    failures: list[str] = []
    if receipt.fixture_id != fixture.fixture_id:
        failures.append("FIXTURE_ID_MISMATCH")
    if receipt.fixture_hash != fixture_fingerprint(fixture):
        failures.append("FIXTURE_HASH_MISMATCH")
    if receipt.fixture_author_id != fixture.fixture_author_id:
        failures.append("FIXTURE_AUTHOR_MISMATCH")
    if receipt.reviewer_id == fixture.fixture_author_id:
        failures.append("REVIEWER_IS_FIXTURE_AUTHOR")
    if not receipt.reviewer_external_to_fixture:
        failures.append("REVIEWER_NOT_EXTERNAL")
    if not receipt.reviewer_independence_reviewed:
        failures.append("REVIEWER_INDEPENDENCE_UNREVIEWED")
    if receipt.reviewer_material_leakage:
        failures.append("REVIEWER_MATERIAL_LEAKAGE")
    if receipt.thesis_exposed_before_observation:
        failures.append("THESIS_EXPOSED_BEFORE_OBSERVATION")
    if receipt.material_confounder_discovered:
        failures.append("MATERIAL_CONFOUNDER_DISCOVERED")
    if failures:
        return ExternalObservationAssessment("INVALID_TRIAL", tuple(failures), None)
    return ExternalObservationAssessment("OBSERVATION_RECORDED", (), receipt.receipt_id)
