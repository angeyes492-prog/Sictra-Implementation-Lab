# Block 2 / E01 — Preflight Entrypoint Contract v0.1

> Status: `CANDIDATE / LOCAL BOUNDED INTEGRATION`. This is the local entry
> point that binds upstream normalization to Clean External Trial preflight. It
> does not collect an observation or grant implementation, promotion, memory,
> or acceptance authority.

## Flow and precedence

`UPSTREAM_RECORD → NORMALIZE → FIXTURE_CONSTRUCTION → PREFLIGHT_ASSESSMENT`

1. The raw upstream record is normalized first.
2. If normalization returns `RETURN_UPSTREAM`, no `Fixture` is constructed.
3. The same `RETURN_UPSTREAM` reasons and task claim quarantine are returned.
4. Only a normalized current record may enter fixture author identity,
   equivalence, leakage, observer, confounder, and composition checks.

This makes upstream insufficiency precede downstream trial invalidity. A
leaking task paired with missing evidence still returns upstream first; the
source owner must repair the handoff before an E01 trial can be assessed.

## Inputs, outputs, and recovery

- **Inputs:** `UpstreamRecord` and `TrialDraft`.
- **Output:** `EntrypointAssessment` containing both normalization and
  preflight results.
- **Recovery:** repair/version the upstream record at its owner, then submit a
  fresh request. If the fixture author is absent, identify and bind that author
  before preflight. Do not reuse a rejected normalized payload.

## Validation vectors

The contract is exercised against: clean normalized input, missing evidence
plus task leakage, stale upstream plus a semantic mismatch, and valid upstream
plus task leakage. The latter proves that a valid handoff does not hide a
downstream invalid trial.

An independently implemented declarative oracle additionally compares clean,
upstream-precedence, multi-failure, and claim-composition paths without calling
the production normalizer, preflight, or entrypoint functions.

## Non-claims

`READY_FOR_OBSERVATION` remains only a structural precondition. It is not a
human observation, perception result, visual selection, causal conclusion,
integration acceptance, or E01 gate promotion.
