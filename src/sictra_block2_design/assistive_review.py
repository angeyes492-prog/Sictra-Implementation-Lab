"""Fail-closed receipt validation for the human assistive-review protocol.

This module records the shape and binding of a review supplied by a person. It
does not run NVDA/VoiceOver, verify a person's identity, or promote any gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


ReviewOutcome = Literal["PASS_LOCAL", "ISSUE_REPRODUCED", "INCONCLUSIVE", "RETURN_UPSTREAM"]
ReviewDisposition = Literal["REVIEW_RECORDED", "RETURN_UPSTREAM", "INVALID_REVIEW", "UNSUPPORTED_VERSION"]
_OUTCOMES = frozenset(ReviewOutcome.__args__)
_TECHNOLOGIES = frozenset({"NVDA", "VOICEOVER"})
_STEPS = frozenset({
    "SKIP_LINK", "VIEW_NAVIGATION", "CREATE_RETURN", "STUDIO_SELECTION",
    "PREFERENCES", "ZOOM_REFLOW",
})
_SEVERITIES = frozenset({"NONE", "MINOR", "MAJOR", "CRITICAL"})


class AssistiveReviewViolation(ValueError):
    """The candidate receipt cannot be structurally classified."""


def _required(**fields: str) -> None:
    missing = [key for key, value in fields.items() if not isinstance(value, str) or not value.strip()]
    if missing:
        raise AssistiveReviewViolation(f"missing required fields: {', '.join(missing)}")


def _sha256(value: str, label: str) -> None:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise AssistiveReviewViolation(f"{label} must be a lowercase SHA-256")


@dataclass(frozen=True, slots=True)
class AssistiveReviewTarget:
    """Pinned local console surface supplied to a human reviewer."""

    git_sha: str
    fixture_id: str
    console_url: str
    probe_sha256: str
    built_at: datetime

    def __post_init__(self) -> None:
        _required(git_sha=self.git_sha, fixture_id=self.fixture_id, console_url=self.console_url)
        if len(self.git_sha) != 40 or any(char not in "0123456789abcdef" for char in self.git_sha):
            raise AssistiveReviewViolation("git_sha must be a lowercase Git SHA")
        if not self.console_url.startswith("http://127.0.0.1:"):
            raise AssistiveReviewViolation("console_url must be a local loopback URL")
        _sha256(self.probe_sha256, "probe_sha256")
        if not isinstance(self.built_at, datetime) or self.built_at.tzinfo is None:
            raise AssistiveReviewViolation("built_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class AssistiveReviewReceipt:
    """One human-observed protocol step, bound to an exact review target."""

    receipt_id: str
    contract_version: str
    git_sha: str
    fixture_id: str
    console_url: str
    probe_sha256: str
    reviewer_id: str
    reviewer_role: str
    reviewer_authorized: bool
    technology: str
    technology_version: str
    operating_system: str
    browser: str
    browser_version: str
    zoom_percent: int
    contrast_mode: str
    step_id: str
    expected_observation: str
    observed_result: str
    outcome: str
    severity: str
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    reviewed_at: datetime

    def __post_init__(self) -> None:
        _required(
            receipt_id=self.receipt_id, contract_version=self.contract_version, git_sha=self.git_sha,
            fixture_id=self.fixture_id, console_url=self.console_url, probe_sha256=self.probe_sha256,
            reviewer_id=self.reviewer_id, reviewer_role=self.reviewer_role, technology=self.technology,
            technology_version=self.technology_version, operating_system=self.operating_system,
            browser=self.browser, browser_version=self.browser_version, contrast_mode=self.contrast_mode,
            step_id=self.step_id, expected_observation=self.expected_observation,
            observed_result=self.observed_result, outcome=self.outcome, severity=self.severity,
        )
        if not self.contract_version.startswith("0.1."):
            raise AssistiveReviewViolation("assistive review receipt version is unsupported")
        if not isinstance(self.reviewer_authorized, bool):
            raise AssistiveReviewViolation("reviewer_authorized must be boolean")
        if not isinstance(self.zoom_percent, int) or not 100 <= self.zoom_percent <= 500:
            raise AssistiveReviewViolation("zoom_percent must be an integer from 100 to 500")
        if self.technology not in _TECHNOLOGIES or self.step_id not in _STEPS:
            raise AssistiveReviewViolation("technology or protocol step is not governed")
        if self.outcome not in _OUTCOMES or self.severity not in _SEVERITIES:
            raise AssistiveReviewViolation("outcome or severity is not governed")
        _sha256(self.probe_sha256, "probe_sha256")
        if not self.evidence_refs or any(not isinstance(ref, str) or not ref.strip() for ref in self.evidence_refs):
            raise AssistiveReviewViolation("evidence_refs must be non-empty strings")
        if any(not isinstance(item, str) or not item.strip() for item in self.limitations):
            raise AssistiveReviewViolation("limitations must be strings")
        if not isinstance(self.reviewed_at, datetime) or self.reviewed_at.tzinfo is None:
            raise AssistiveReviewViolation("reviewed_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class AssistiveReviewAssessment:
    disposition: ReviewDisposition
    reasons: tuple[str, ...]
    receipt_id: str | None
    promotion_state: str = "NOT_PROMOTED"
    acceptance_state: str = "NOT_ACCEPTED"

    @property
    def recorded(self) -> bool:
        return self.disposition == "REVIEW_RECORDED"


def assess_assistive_review(
    target: AssistiveReviewTarget, receipt: AssistiveReviewReceipt,
) -> AssistiveReviewAssessment:
    """Classify a supplied review without treating it as accessibility acceptance."""

    upstream: list[str] = []
    for label, expected, actual in (
        ("GIT_SHA", target.git_sha, receipt.git_sha),
        ("FIXTURE", target.fixture_id, receipt.fixture_id),
        ("CONSOLE_URL", target.console_url, receipt.console_url),
        ("PROBE", target.probe_sha256, receipt.probe_sha256),
    ):
        if expected != actual:
            upstream.append(f"TARGET_{label}_MISMATCH")
    if receipt.reviewed_at < target.built_at:
        upstream.append("REVIEW_BEFORE_TARGET")
    if upstream:
        return AssistiveReviewAssessment("RETURN_UPSTREAM", tuple(upstream), None)

    failures: list[str] = []
    if not receipt.reviewer_authorized:
        failures.append("REVIEWER_AUTHORITY_UNVERIFIED")
    if receipt.outcome == "PASS_LOCAL" and receipt.severity != "NONE":
        failures.append("PASS_WITH_NONZERO_SEVERITY")
    if receipt.outcome == "ISSUE_REPRODUCED" and receipt.severity == "NONE":
        failures.append("ISSUE_WITHOUT_SEVERITY")
    if receipt.outcome == "RETURN_UPSTREAM":
        return AssistiveReviewAssessment("RETURN_UPSTREAM", ("REVIEWER_RETURNED_UPSTREAM",), None)
    if failures:
        return AssistiveReviewAssessment("INVALID_REVIEW", tuple(failures), None)
    return AssistiveReviewAssessment("REVIEW_RECORDED", (), receipt.receipt_id)
