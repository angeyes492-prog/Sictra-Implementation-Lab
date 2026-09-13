# Block 4 — Federated Orchestrator v0.1

Status: `CANDIDATE / LOCAL BOUNDED IMPLEMENTATION / MAR REQUIRED`.
Date: 2026-09-12. Authority: owner direction to build a supervised federation.

## Purpose and scope

Block 4 coordinates typed local handoffs from Blocks 1, 2 and 3. It owns the
federated run journal, checkpoint/retry policy, recovery and operator queue. It
does not own source truth, creative decisions, precision signals, publication,
delivery, CRM writes, gate promotion or human approval.

## Route

`controlled Block 1 package → Block 1 attestation → Block 2 candidate → Block 3 governed signal → human review or abstention`.

A case may advance only through the declared successor. The orchestrator can
automatically process a current, internally consistent package up to the human
review boundary. It stops on contradiction, expiry, missing lineage, unsupported
version, retry exhaustion or any authority-requesting action.

## Shared identity and invariants

Each handoff carries immutable `case_id`, `run_id`, `message_id`, `evidence_id`,
`dossier_id`, producer block, contract version, source hash, provenance root,
currentness, certainty, uncertainty, disposition and expiry. The local journal
is append-only and HMAC-attested. Exact replay is idempotent; identity with a
different fingerprint is a collision. A consumer may view a block console but
does not fetch another block's API or inherit its authority.

## State machine and recovery

`INGESTED → BLOCK1_ATTESTED → BLOCK2_CANDIDATE → BLOCK3_GOVERNED → HUMAN_REVIEW_REQUIRED`

Terminal safe states are `ABSTAINED`, `RETURN_UPSTREAM` and `REJECTED`.
The journal checkpoint records the last successful state and counter. On reopen,
the store verifies the entire chain and rehydrates only that checkpoint. A retry
never skips a failed state, is bounded to three attempts, and reuses the exact
input fingerprint. Invalidating evidence turns the case `RETURN_UPSTREAM`; it
does not alter historical events.

## Dependencies and failure boundary

The first slice consumes only an operator-supplied, signed local package. It
does not attach to Block 1's internal key stores or perform network acquisition.
This deliberately avoids secret sharing and preserves each block's storage
boundary. Real adapters, a common key service, tenancy, scheduling infrastructure
and production promotion require the open Master Architecture Review.

## Observability and validation

The local console exposes cases, state, restrictions, failures, review queue,
checkpoints and links to independent consoles. Tests cover successful progression,
tamper, expiry, lineage substitution, illegal transition, collision, retry cap
and restart recovery. Fixture execution is laboratory evidence only.

## Downstream impact / Master Architecture Review

This candidate introduces common identity and coordination semantics across all
three blocks. The MAR must decide contract ownership, adapter/key authority,
compatibility/migration, durable operational identity, production scheduler,
retention, human-review authentication and promotion conditions. No local test
can accept those decisions.
