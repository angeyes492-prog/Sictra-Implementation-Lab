"""Canonical local entry point for an E01 clean-trial preflight request.

The entry point binds upstream normalization to fixture assessment so an
incomplete raw handoff cannot be accidentally treated as a preflight input.
It remains a bounded structural guard: no observation is collected and no
creative or acceptance decision is made here.
"""

from __future__ import annotations

from dataclasses import dataclass

from .preflight import (
    Candidate,
    ClaimComposition,
    Confounder,
    Fixture,
    ObserverProfile,
    PreflightAssessment,
    TaskDefinition,
    assess_fixture,
)
from .upstream import NormalizationAssessment, UpstreamRecord, normalize_upstream


@dataclass(frozen=True, slots=True)
class TrialDraft:
    """Fixture fields supplied alongside a raw upstream handoff."""

    fixture_id: str
    task: TaskDefinition
    candidate_a: Candidate
    candidate_b: Candidate
    intended_manipulation: str
    observer: ObserverProfile
    confounders: tuple[Confounder, ...]
    composition: ClaimComposition = ClaimComposition()


@dataclass(frozen=True, slots=True)
class EntrypointAssessment:
    upstream: NormalizationAssessment
    preflight: PreflightAssessment

    @property
    def ready_for_observation(self) -> bool:
        return self.preflight.ready_for_observation


def assess_trial(upstream: UpstreamRecord, draft: TrialDraft) -> EntrypointAssessment:
    """Normalize first, then assess a fixture only when normalization succeeds.

    A rejected upstream record is intentionally never converted into a
    ``Fixture``. This makes missing authority, facts, evidence, provenance,
    audience, decision context, certainty, or currentness a terminal return to
    the upstream owner for this request.
    """

    normalized = normalize_upstream(upstream)
    if not normalized.ready_for_preflight:
        return EntrypointAssessment(
            upstream=normalized,
            preflight=PreflightAssessment(
                "RETURN_UPSTREAM",
                normalized.reasons,
                (draft.task.claim_id,),
            ),
        )
    fixture = Fixture(
        fixture_id=draft.fixture_id,
        upstream=normalized.normalized,
        task=draft.task,
        candidate_a=draft.candidate_a,
        candidate_b=draft.candidate_b,
        intended_manipulation=draft.intended_manipulation,
        observer=draft.observer,
        confounders=draft.confounders,
        composition=draft.composition,
    )
    return EntrypointAssessment(upstream=normalized, preflight=assess_fixture(fixture))
