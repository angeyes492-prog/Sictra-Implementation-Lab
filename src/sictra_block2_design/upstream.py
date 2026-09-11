"""Normalization boundary for an E01 upstream intelligence object.

This is a fail-closed adapter.  It does not infer facts, upgrade evidence,
choose an audience, or grant authority.  It only turns an already explicit,
current upstream record into the small fidelity object used by the E01
preflight harness.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .preflight import UpstreamIntelligence


Certainty = Literal[
    "VERIFIED",
    "PROBABLE",
    "PLAUSIBLE",
    "UNCONFIRMED",
    "CONTRADICTED",
    "INSUFFICIENT EVIDENCE",
]
TemporalState = Literal["CURRENT", "STALE", "HISTORICAL", "SUPERSEDED"]
NormalizationDisposition = Literal["NORMALIZED", "RETURN_UPSTREAM"]

_CERTAINTY_VALUES = frozenset(Certainty.__args__)
_CURRENT = "CURRENT"


def _valid_ids(values: tuple[str, ...]) -> bool:
    return bool(values) and all(isinstance(value, str) and value.strip() for value in values)


@dataclass(frozen=True, slots=True)
class UpstreamRecord:
    """An explicit, atomic intelligence handoff for one E01 trial claim."""

    object_id: str
    source_identity: str
    fact_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    certainty: str
    authority_reference: str
    audience_context: str
    decision_context: str
    provenance_refs: tuple[str, ...]
    temporal_state: str


@dataclass(frozen=True, slots=True)
class NormalizationAssessment:
    disposition: NormalizationDisposition
    reasons: tuple[str, ...]
    normalized: UpstreamIntelligence | None

    @property
    def ready_for_preflight(self) -> bool:
        return self.disposition == "NORMALIZED"


def normalize_upstream(record: UpstreamRecord) -> NormalizationAssessment:
    """Return an E01-compatible object only when the handoff is usable as-is.

    The function deliberately aggregates all structural omissions so the caller
    can repair the source record in one upstream cycle.  A rejected record has
    no normalized payload, preventing partial or guessed handoff.
    """

    reasons: list[str] = []
    scalar_fields = {
        "OBJECT_ID": record.object_id,
        "SOURCE_IDENTITY": record.source_identity,
        "AUTHORITY_REFERENCE": record.authority_reference,
        "AUDIENCE_CONTEXT": record.audience_context,
        "DECISION_CONTEXT": record.decision_context,
    }
    reasons.extend(
        field for field, value in scalar_fields.items()
        if not isinstance(value, str) or not value.strip()
    )
    if not _valid_ids(record.fact_ids):
        reasons.append("FACTS_MISSING")
    if not _valid_ids(record.evidence_refs):
        reasons.append("EVIDENCE_MISSING")
    if not _valid_ids(record.provenance_refs):
        reasons.append("PROVENANCE_MISSING")
    if record.certainty not in _CERTAINTY_VALUES:
        reasons.append("CERTAINTY_UNGOVERNED")
    if record.temporal_state != _CURRENT:
        reasons.append("UPSTREAM_NOT_CURRENT")
    if reasons:
        return NormalizationAssessment("RETURN_UPSTREAM", tuple(reasons), None)

    return NormalizationAssessment(
        "NORMALIZED",
        (),
        UpstreamIntelligence(
            object_id=record.object_id,
            source_identity=record.source_identity,
            evidence_status=record.certainty,
            authority_reference=record.authority_reference,
            audience_context=record.audience_context,
            decision_context=record.decision_context,
        ),
    )
