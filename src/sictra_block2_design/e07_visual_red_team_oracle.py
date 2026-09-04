"""Independent declarative oracle for the E07 rubric boundary."""

from __future__ import annotations


REQUIRED = {
    "COMPREHENSION", "HIERARCHY", "LEGIBILITY", "ACCESSIBILITY",
    "CLAIM_FIDELITY", "CHANNEL_ADAPTATION", "BRAND_AND_RIGHTS",
    "NON_DECEPTIVE_PERSUASION",
}


def expected_visual_disposition(candidate, production_state, review) -> str:
    """Evaluate serialized fields without importing E07 implementation helpers."""

    if not review.contract_version.startswith("0.1."):
        return "UNSUPPORTED_VERSION"
    if candidate is None or production_state != "PRODUCTION_CANDIDATE_READY_FOR_REVIEW":
        return "RETURN_TO_PREVIOUS"
    if (
        review.candidate_id != candidate.candidate_id
        or review.candidate_sha256 != candidate.artifact.sha256
        or not review.independent
        or review.reviewer_id == candidate.producer_id
    ):
        return "BLOCKED"
    if {item.criterion for item in review.observations} != REQUIRED:
        return "BLOCKED"
    if any(item.critical_failure or item.score < 60 for item in review.observations):
        return "BLOCKED"
    if any(item.score < 80 for item in review.observations):
        return "REVISE"
    return "PASS_RECOMMENDED_FOR_EXTERNAL_REVIEW"

