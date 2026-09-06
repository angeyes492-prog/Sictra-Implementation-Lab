# Block 1 — Attested evidence to runtime bridge v0.1

`IMPLEMENTED CANDIDATE / LOCAL-TESTED / B`. This Layer 5 adapter is the only
new bounded path defined here from retained Layer 4 evidence into the E01–E08
runtime. It obtains defensive copies exclusively through
`AttestedEvidenceStore.runtime_records(now)` and never accepts a caller-owned
source list.

Inputs are a configured evidence store, an `IntelligenceRuntime`, explicit
task/run/objective/authority values and one trusted integer time. The bridge
requires the runtime clock to agree with that time before starting. Its output
contains the ordinary runtime envelope plus defensive receipt summaries for
the exact admitted evidence set.

Invariants: at least one record must be current; every supplied runtime source
is from the current durable-store read; receipts must also report `CURRENT`;
and a clock disagreement rejects before the runtime request or durable effect.
The runtime remains owner of E01–E08 behavior, authority enforcement and its
own durable effect. The store remains owner of evidence retention and
freshness. The bridge owns only the boundary between them.

Failure/recovery: empty/stale evidence and clock disagreement fail before
runtime invocation. Store signature/integrity errors propagate fail-closed.
Runtime errors retain their existing journal semantics; this adapter neither
retries nor changes gate status. A stable shared clock is a required local
configuration condition; this reference adapter is not a distributed-time,
transactional two-store, production scheduler or multi-writer protocol.
