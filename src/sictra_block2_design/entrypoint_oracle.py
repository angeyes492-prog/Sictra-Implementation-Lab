"""Independent declarative oracle for the bounded E01 preflight entry point.

This module intentionally does not import ``assess_trial``, ``normalize_upstream``
or ``assess_fixture``. It expresses the contract outcome directly for
differential tests; it is not an alternative runtime entry point.
"""

from __future__ import annotations

from dataclasses import dataclass

from .entrypoint import TrialDraft
from .upstream import UpstreamRecord


_CERTAINTY = {
    "VERIFIED", "PROBABLE", "PLAUSIBLE", "UNCONFIRMED", "CONTRADICTED", "INSUFFICIENT EVIDENCE"
}
_EQUIVALENCE = (
    "content_id", "task_version", "labels", "scale", "uncertainty_object",
    "annotation_burden", "context_version", "attention_condition", "implementation_burden",
)


@dataclass(frozen=True, slots=True)
class ExpectedEntrypoint:
    upstream_disposition: str
    preflight_disposition: str
    reasons: tuple[str, ...]
    quarantined_claim_ids: tuple[str, ...]


def _ids_present(values: tuple[str, ...]) -> bool:
    return bool(values) and all(isinstance(value, str) and value.strip() for value in values)


def expected_entrypoint(upstream: UpstreamRecord, draft: TrialDraft) -> ExpectedEntrypoint:
    """Compute contract outcomes without calling the production evaluators."""

    upstream_reasons: list[str] = []
    for name, value in (
        ("OBJECT_ID", upstream.object_id),
        ("SOURCE_IDENTITY", upstream.source_identity),
        ("AUTHORITY_REFERENCE", upstream.authority_reference),
        ("AUDIENCE_CONTEXT", upstream.audience_context),
        ("DECISION_CONTEXT", upstream.decision_context),
    ):
        if not isinstance(value, str) or not value.strip():
            upstream_reasons.append(name)
    if not _ids_present(upstream.fact_ids):
        upstream_reasons.append("FACTS_MISSING")
    if not _ids_present(upstream.evidence_refs):
        upstream_reasons.append("EVIDENCE_MISSING")
    if not _ids_present(upstream.provenance_refs):
        upstream_reasons.append("PROVENANCE_MISSING")
    if upstream.certainty not in _CERTAINTY:
        upstream_reasons.append("CERTAINTY_UNGOVERNED")
    if upstream.temporal_state != "CURRENT":
        upstream_reasons.append("UPSTREAM_NOT_CURRENT")
    if upstream_reasons:
        return ExpectedEntrypoint(
            "RETURN_UPSTREAM", "RETURN_UPSTREAM", tuple(upstream_reasons), (draft.task.claim_id,)
        )

    failures: list[str] = []
    if not draft.task.leakage_clear:
        failures.append("TASK_LEAKAGE")
    failures.extend(
        f"SEMANTIC_EQUIVALENCE_{field.upper()}"
        for field in _EQUIVALENCE
        if getattr(draft.candidate_a, field) != getattr(draft.candidate_b, field)
    )
    if not draft.observer.external_to_e01:
        failures.append("OBSERVER_NOT_EXTERNAL")
    if not draft.observer.independence_reviewed:
        failures.append("OBSERVER_INDEPENDENCE_UNREVIEWED")
    if draft.observer.material_leakage:
        failures.append("OBSERVER_MATERIAL_LEAKAGE")
    if draft.observer.order_condition == "UNCONTROLLED":
        failures.append("ORDER_UNCONTROLLED")
    failures.extend(
        f"MATERIAL_CONFOUNDER_{item.variable}"
        for item in draft.confounders
        if item.material and item.disposition in {"PROHIBITED", "DISCOVERED_POST_TRIAL"}
    )
    if failures:
        return ExpectedEntrypoint("NORMALIZED", "INVALID_TRIAL", tuple(failures), (draft.task.claim_id,))
    if draft.composition.source_claim_ids and not draft.composition.interaction_tested:
        return ExpectedEntrypoint(
            "NORMALIZED", "UNSUPPORTED_COMBINATION", ("EVIDENCE_CONJUNCTION_OVERREACH",), (draft.task.claim_id,)
        )
    return ExpectedEntrypoint("NORMALIZED", "READY_FOR_OBSERVATION", (), ())
