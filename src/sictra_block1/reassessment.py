"""Independent, non-promoting reassessment of a context pack."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .context import ContextPack, EvidenceClass


@dataclass(frozen=True, slots=True)
class ReassessmentResult:
    record_count: int
    independent_evidence_count: int
    runtime_evidence_admissible: bool
    status: Literal["LOCAL_ONLY", "RUNTIME_CANDIDATE", "REJECTED"]
    reasons: tuple[str, ...]


def _is_admissible_runtime_evidence(evidence_class: EvidenceClass) -> bool:
    return evidence_class == "OBSERVED"


def reassess(pack: ContextPack) -> ReassessmentResult:
    """Compute evidence independence without giving the result promotion authority.

    Independence is the number of distinct root-source identities among
    admissible observed records. Record count, repeated roots, derivatives,
    synthetic fixtures, and adversarial records do not inflate it.
    """
    if not pack.records:
        return ReassessmentResult(0, 0, False, "REJECTED", ("context pack is empty",))

    admissible = [
        record
        for record in pack.records
        if _is_admissible_runtime_evidence(record.evidence_class)
    ]
    independent_roots = {record.root_provenance for record in admissible}
    reasons: list[str] = []
    if len(admissible) != len(pack.records):
        reasons.append("synthetic, adversarial, or derived records are not runtime evidence")
    if pack.open_contradictions:
        reasons.append("open contradictions preserved for reassessment")
    if not admissible:
        return ReassessmentResult(
            len(pack.records), 0, False, "LOCAL_ONLY", tuple(reasons)
        )
    return ReassessmentResult(
        len(pack.records),
        len(independent_roots),
        True,
        "RUNTIME_CANDIDATE",
        tuple(reasons),
    )
