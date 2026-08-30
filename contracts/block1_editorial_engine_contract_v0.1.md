# Contract — Block 1 Governed Editorial Engine v0.1

## Identity, producer and authority

Contract `BLOCK1_EDITORIAL_ENGINE_V0.1`. E01 coordinates a composition of E02–E08;
no component gains another engine's semantics. The producer is Block 1 and the
only current consumer is the bounded local Workspace. A selected dossier may
declare a candidate handoff to `BLOCK2_DESIGN`, but cannot publish, distribute,
contact, promote a gate or mutate external systems.

## Inputs

Each candidate requires exact identities, existing lifecycle state, eight-axis
priority profile, evidence controls, red-team and stability states, five
diversity dimensions, editorial interpretation, three-layer derivation IDs and
a complete 7/30/90 watchlist.

Profile axes are finite values in `[0, 100]`: impact, relevance, novelty,
uncertainty, timeliness, actionability, evidence strength and interpretive
value. They remain separate; no scalar score is accepted or emitted.

Evidence declares aligned source and root IDs, minimum independent roots,
provenance integrity, source approval, scope authority, freshness,
contradiction bounding, license compatibility and sensitive-data presence.
Repeated root IDs are valid correlation and count once.

## Dispositions and invariants

- Broken provenance, source approval, scope, license or sensitive-data boundary
  yields `QUARANTINED`.
- Stale/unknown evidence, insufficient independent roots, open material
  contradiction, non-passing red team, unstable state, evidence strength below
  60 or uncertainty above 40 yields `RESEARCH_NEEDED`.
- Only an otherwise valid `DELIVERABLE_BOUNDED` candidate is `READY`.
- High uncertainty may produce `HIGH` research priority while readiness remains
  `BLOCKED`.
- `SUPERSEDED` remains historical and cannot re-enter the shortlist.
- Unknown fields, values, states, horizons and malformed collections fail
  closed.
- A cycle accepts at most 500 candidates. Flagship selection recomputes the
  contract, assessments and shortlist from candidate payloads and rejects any
  integrity mismatch; a consumer cannot elevate a blocked candidate by editing
  the returned cycle.

## Selection

Eligible candidates form a Pareto frontier: maximize every axis except
uncertainty, which is minimized. A candidate dominates another only when it is
no worse on all axes and strictly better on at least one. Crossed advantages
remain incomparable.

The deterministic shortlist selects at most five non-dominated candidates and
prefers new geography, mode, topic, audience and horizon values. Evidence
strength, timeliness, interpretive value and identity are visible tie-breakers.
If fewer than the configured minimum survive, no shortlist is emitted.

Only a human-labelled selection from the shortlist can create a bounded Block
2 handoff candidate. It requires a rationale of 20–1000 characters. A human may
instead record `NO_FLAGSHIP_SELECTED` with the same rationale requirement; that
decision emits no handoff. Both decisions are ephemeral in v0.1. Selection does
not change evidence, readiness or gate.

## Compatibility, recovery and non-claims

Version `0.1` is additive and local. Inputs are reconstructed from governed
records; the current API stores no selection. Repetition is deterministic and
defensive copies prevent shared mutation. This contract does not acquire real
sources, persist users, identify real accounts, infer causal truth or establish
production readiness.
