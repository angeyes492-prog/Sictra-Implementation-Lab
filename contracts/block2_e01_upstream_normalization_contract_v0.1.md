# Block 2 / E01 — Upstream Normalization Contract v0.1

> Status: `CANDIDATE / LOCAL BOUNDED SUT`. This contract normalizes an already
> explicit intelligence handoff for E01 preflight. It is not upstream
> intelligence generation, authority issuance, E01 runtime, or gate acceptance.

## Producer, consumer, and scope

- **Producer:** an upstream intelligence owner with facts, evidence, certainty,
  provenance, audience, decision, and authority already recorded.
- **Consumer:** the E01 Clean External Trial preflight harness only.
- **Output:** `NORMALIZED` plus `UpstreamIntelligence`, or `RETURN_UPSTREAM`
  plus explicit reasons and no payload.

## Required lineage

`OBJECT_ID / SOURCE_IDENTITY / FACT_IDS / EVIDENCE_REFS / CERTAINTY /
AUTHORITY_REFERENCE / AUDIENCE_CONTEXT / DECISION_CONTEXT / PROVENANCE_REFS /
TEMPORAL_STATE`.

`CERTAINTY` is limited to the protected project labels: `VERIFIED`,
`PROBABLE`, `PLAUSIBLE`, `UNCONFIRMED`, `CONTRADICTED`, or `INSUFFICIENT
EVIDENCE`. The normalizer preserves it; it never upgrades it.

## Rejection semantics

The normalizer returns `RETURN_UPSTREAM` and no normalized object for missing
facts, evidence, provenance, source identity, authority, audience, decision,
or object identity; an ungoverned certainty; or any temporal state other than
`CURRENT`. Multiple reasons are retained together.

## Invariants and non-claims

- No field is inferred, defaulted, or repaired locally.
- A normalized object keeps the input identity, authority, audience, decision,
  and certainty unchanged.
- `NORMALIZED` means only that the structural handoff can enter preflight; it
  does not make a fixture ready, validate an observer, or establish a visual or
  perceptual result.
- `RETURN_UPSTREAM` takes precedence over any downstream trial classification.

## Validation and recovery

The unit vectors cover clean normalization, missing facts/evidence, ungoverned
certainty, stale input, missing provenance, and absent audience/authority.
Repair must occur in the upstream record; rerun normalization with a new or
corrected current record. No retry may reuse a rejected payload.
