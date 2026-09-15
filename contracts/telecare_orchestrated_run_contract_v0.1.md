# Telecare orchestrated run contract v0.1

Status: `CANDIDATE / LOCAL IMPLEMENTATION / MAR REQUIRED`.
Date: 2026-09-14. Producer and authority: Block 4 Orchestrator. Consumers:
the local worker, Blocks 1–3 and the loopback Command Center.

## Purpose and scope

One authenticated loopback control request, `{"action":"execute"}`, records
an `ORCHESTRATION_REQUEST`, enables only the approved local dropbox monitor,
and begins the bounded route:

`approved local source → Block 1 dossier → Block 2 REVIEW_NEWSLETTER → Block 3 declared audience → Block 4 review queue`.

The request and result carry a random `run_id`, timestamp, explicit route,
source boundary, publication state and delivery state. The journal is signed
and append-only. The command is repeatable but does not duplicate an already
committed case/profile output.

## Preconditions, authority and invariants

The request is accepted only from loopback, same origin, with the process-local
control token and JSON schema exactly matching the control route. It may monitor
only the configured `APPROVED_LOCAL_DROPBOX`; only stable local XLSX files are
registered, hash-checked and sent to the current Block 1 pipeline.

The command respects an existing human pause or explicit STOP and never clears
either. It does not access a network source, choose an unapproved source,
identify a person, read a CRM, infer customer facts, accept a dossier, send a
newsletter, deliver content or publish. Every generated newsletter remains
`HUMAN_REVIEW_REQUIRED`, `BLOCKED`, and `NONE` for delivery.

## State, rejection and recovery

An active run reports `ORCHESTRATION_EXECUTED`; an existing pause returns
`PAUSED / HUMAN_PAUSE_PRESERVED`; an explicit STOP returns
`STOPPED / EXPLICIT_STOP_REQUIRES_RESTART`. Invalid origin/token/schema is
rejected before any journal write. A source mutation, incomplete evidence,
contradiction, profile expiry or fingerprint failure enters the existing
review/wait state. Recovery remains explicit and source-bound; a subsequent
run never promotes or silently retries a failed source.

## Compatibility, observability and non-claims

This is version 1. A future external collector, CRM/customer connector, mail
delivery provider or queue platform requires its own versioned contract, source
approval, identity/secret custody, privacy/retention decision, rate limit,
failure model and MAR. It is not compatible by implication with this local
route.

The snapshot exposes source monitor status and the last signed run. Tests cover
the positive route, malformed control rejection, immutable run history and
preservation of pause/STOP. Local test success is not independent acceptance,
production readiness or a claim that sources are true.
