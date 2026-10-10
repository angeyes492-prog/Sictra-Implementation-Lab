"""Read-only, source-specific assessment of a linked evidence candidate."""

from math import isfinite

from .common import ContractViolation
from .need_classification import classify_data_need


class NeedAssessmentViolation(ContractViolation):
    pass


_COMPARISON_STATUSES = frozenset({
    "NO_SHARED_MEASUREMENT", "PARTIAL_COVERAGE_REVIEW_REQUIRED",
    "VALUE_DIFFERENCE_REVIEW_REQUIRED", "EXACT_VALUE_AGREEMENT_REVIEW_REQUIRED",
})


def assess_linked_data_need(source_id: str, requirement: str, comparison: dict) -> dict:
    """Explain what the candidate can and cannot answer; never resolve a gap."""
    kind = classify_data_need(source_id, requirement)
    if (not isinstance(comparison, dict)
            or comparison.get("status") not in _COMPARISON_STATUSES
            or comparison.get("resolution") != "NOT_RESOLVED"
            or comparison.get("acceptance") != "NOT_ACCEPTED"
            or comparison.get("publication") != "BLOCKED"
            or not isinstance(comparison.get("primary_dossier_id"), str)
            or not comparison["primary_dossier_id"]
            or not isinstance(comparison.get("candidate_dossier_id"), str)
            or not comparison["candidate_dossier_id"]
            or comparison["primary_dossier_id"] == comparison["candidate_dossier_id"]
            or not isinstance(comparison.get("matched"), list)
            or not isinstance(comparison.get("unmatched_primary_fact_ids"), list)
            or not isinstance(comparison.get("unmatched_candidate_fact_ids"), list)):
        raise NeedAssessmentViolation("COMPARISON_BOUNDARY_INVALID")
    status = comparison["status"]
    unmatched = (comparison["unmatched_primary_fact_ids"]
                 + comparison["unmatched_candidate_fact_ids"])
    if any(not isinstance(fact_id, str) or not fact_id.strip() for fact_id in unmatched):
        raise NeedAssessmentViolation("COMPARISON_MATCH_STATUS_INVALID")
    has_difference = False
    for item in comparison["matched"]:
        if (not isinstance(item, dict)
                or type(item.get("primary_value")) not in (int, float)
                or type(item.get("candidate_value")) not in (int, float)
                or not isfinite(item["primary_value"])
                or not isfinite(item["candidate_value"])):
            raise NeedAssessmentViolation("COMPARISON_MATCH_STATUS_INVALID")
        different = item["primary_value"] != item["candidate_value"]
        if item.get("comparison") != ("DIFFERENT_AFTER_VALUE" if different else "EXACT_AFTER_VALUE"):
            raise NeedAssessmentViolation("COMPARISON_MATCH_STATUS_INVALID")
        has_difference = has_difference or different
    expected_status = (
        "NO_SHARED_MEASUREMENT" if not comparison["matched"] else
        "VALUE_DIFFERENCE_REVIEW_REQUIRED" if has_difference else
        "PARTIAL_COVERAGE_REVIEW_REQUIRED" if unmatched else
        "EXACT_VALUE_AGREEMENT_REVIEW_REQUIRED"
    )
    if status != expected_status:
        raise NeedAssessmentViolation("COMPARISON_MATCH_STATUS_INVALID")
    if kind == "UNCLASSIFIED":
        verdict, reason, action = ("INSUFFICIENT", "NEED_UNCLASSIFIED", "CLASSIFY_NEED_MANUALLY")
    elif kind != "INDEPENDENT_CORROBORATION":
        verdict, reason, action = ("INSUFFICIENT", "DIFFERENT_EVIDENCE_TYPE_REQUIRED",
                                   "REQUEST_NEED_SPECIFIC_EVIDENCE")
    elif status == "NO_SHARED_MEASUREMENT":
        verdict, reason, action = ("INSUFFICIENT", "NO_SHARED_MEASUREMENT",
                                   "REQUEST_COMPARABLE_APPROVED_SOURCE")
    elif status == "PARTIAL_COVERAGE_REVIEW_REQUIRED":
        verdict, reason, action = ("INSUFFICIENT", "PARTIAL_COVERAGE",
                                   "REQUEST_COMPARABLE_APPROVED_SOURCE")
    elif status == "VALUE_DIFFERENCE_REVIEW_REQUIRED":
        verdict, reason, action = ("MEASUREMENT_DISAGREEMENT", "REPORTED_AFTER_VALUES_DIFFER",
                                   "REVIEW_REVISIONS_AND_COVERAGE")
    else:
        verdict, reason, action = ("REVIEW_REQUIRED", "EXACT_AFTER_VALUES_NOT_CORROBORATION",
                                   "REQUEST_BLOCK1_HUMAN_REVIEW")
    return {
        "version": "0.1.0", "need_kind": kind,
        "primary_dossier_id": comparison["primary_dossier_id"],
        "candidate_dossier_id": comparison["candidate_dossier_id"],
        "comparison_status": status, "verdict": verdict,
        "reason_code": reason, "next_action": action,
        "resolution": "NOT_RESOLVED", "acceptance": "NOT_ACCEPTED",
        "publication": "BLOCKED",
    }
