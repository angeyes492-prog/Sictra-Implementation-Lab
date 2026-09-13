# Block 4 Local Worker Recovery Contract v0.1

Status: `CANDIDATE / LOCAL BOUNDED SUT / NOT ACCEPTED`.
Date: 2026-09-13. Producer: configured recovery operator. Consumer: Block 4
local intake worker.

## Scope, identity and authority

A recovery receipt may reconcile only an existing `RUNNING` or
`REVIEW_REQUIRED` job. It binds the immutable job ID, source SHA-256, current
verified Block 1 pipeline snapshot, explicit decision, actor ID, reason and
issue time. It is signed with a recovery key distinct from the queue integrity
key and expires after 15 minutes.

Allowed decisions are `ABSTAIN`, `CONFIRM_COMPLETED` and
`REQUEUE_EXACT_INPUT`. `REQUEUE_EXACT_INPUT` rechecks the allowlisted inbox path
and exact source hash. None of the decisions grants publication, delivery,
source approval, content acceptance or gate-promotion authority.

## Failure and recovery semantics

Wrong type, key, signature, actor, reason, source, job state, time window or
pipeline fingerprint fails closed. Receipt material and its actor remain in the
HMAC-bound queue audit. A recovery decision never erases the interrupted state
or earlier events.

Queue backups contain no keys. A signed manifest binds the SQLite bytes and
the current pipeline fingerprint. Verification checks the manifest signature,
byte hash, embedded queue HMAC and pipeline boundary. Restore writes only to a
new path and reopens the restored queue before returning success. It never
overwrites the live queue.

## Compatibility and non-claims

This is a local v0.1 candidate over the existing worker queue schema. It does
not provide external identity federation, quorum approval, an external
monotonic rollback anchor, cross-host secret custody or production disaster
recovery. Replacing both state and its local evidence with an older valid set
remains outside the detectable boundary.
