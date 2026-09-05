# Block 1 — Durable manual watchlist cycle v0.1

`IMPLEMENTED CANDIDATE / LOCAL-TESTED / B`. The cycle owns a bounded local
history of Eurostat manual bundle checkpoints and the exact delta from each
predecessor. Checkpoint, comparison and event are written as one atomic JSON
replacement; a restart recomputes every delta and HMAC link before returning
history.

The first valid bundle establishes `BASELINE_ESTABLISHED_NOT_EVIDENCE`.
A newer release produces `DELTA_DETECTED_NOT_EVIDENCE` or
`NO_DELTA_NOT_EVIDENCE`. Replaying the same source-file hash does not create a
new cycle. Same-release content drift, time regression, malformed bundles,
capacity exhaustion, identity collision or any persisted mutation fail closed
without advancing the checkpoint.

The cycle has no scheduler, network client, notification channel, source
binding, evidence issuer, interpretation or promotion authority. It preserves
reviewable change rather than deciding whether that change matters.

Dependencies: manual bundle validator, Eurostat bundle comparator and a
caller-held integrity key. Downstream: a future scheduler may invoke this
cycle, and the intelligence/editorial layers may consume only separately
attested and reviewed deltas. Cross-process locking, encryption, retention,
backup and operator identity remain operating-plane requirements.
