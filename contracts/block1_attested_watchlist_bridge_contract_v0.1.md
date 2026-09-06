# Contract — Attested watchlist bridge v0.1

Version `0.1`; producer/consumer:
`sictra_block1.attested_watchlist_bridge.AttestedWatchlistBridge`. Scope:
`BLOCK1_LOCAL_ATTESTED_WATCHLIST_BRIDGE`. Authority: admit a uniquely current
attested source into a manual watchlist checkpoint.

`ingest(source_id, now)` requires a non-empty source ID and non-negative
integer time. It reads current records from `AttestedEvidenceStore`; exactly
one must match. The bridge reconstructs the strict seven-field manual bundle
from signed evidence and invokes `ManualWatchlistCycle.ingest`. Its receipt
retains signed approval/binding fingerprints and the watchlist receipt.

An empty, stale or ambiguous matching set rejects before the cycle can append.
The output never elevates the watchlist delta beyond
`ATTESTED_INPUT_DELTA_NOT_EVIDENCE`; a detected delta has next state
`REQUIRES_REVIEW`. Non-claims: source truth, independent corroboration,
interpretation, scheduler, notification, human approval, publication and gate
promotion.
