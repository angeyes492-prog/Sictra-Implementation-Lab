# Block 4 Local Control Plane Contract v0.1

Status: `CANDIDATE / LOCAL BOUNDED SUT / NOT ACCEPTED`.

## Scope and ownership

Producer and consumer: `BLOCK4` local loopback runtime only. The control plane
owns its processing availability and the auditable request receipts for that
runtime. It does not own Block 1 source selection, Block 2 design, Block 3
profiles, human approval, publication, delivery, CRM, network acquisition or
global gate promotion.

## Control state

The initial state is `RUNNING`. Valid transitions are:

```text
RUNNING --PAUSE--> PAUSED --RESUME--> RUNNING
RUNNING|PAUSED --STOP--> STOPPED --START--> RUNNING
```

`PAUSED` and `STOPPED` fail closed for local case progression and retries.
They do not delete or mutate retained case evidence. Ingestion and integrity
verification remain available so an operator can preserve and diagnose a local
package without progressing it.

## Request schema

Each mutating request has exactly `action`, `request_id` and `reason`; a retry
also has `case_id`.

- `action`: one of `PAUSE`, `RESUME`, `STOP`, `START`, `RETRY_CASE`.
- `request_id`: 8–96 ASCII letters, digits, `_` or `-`; it is unique per
  canonical request.
- `reason`: one of `OPERATOR_REQUEST`, `REVIEW_REQUIRED`, `RECOVERY_CHECK` or
  `SAFETY_STOP`. This bounded vocabulary prevents sensitive free text entering
  the operational journal.
- `case_id`: required only for `RETRY_CASE`; it must name an existing,
  returnable case and does not substitute its immutable fingerprint.

`VERIFY_JOURNAL` is a read-only operation and has no request receipt or state
transition.

## Idempotency, audit and recovery

The runtime stores the canonical request fingerprint for each request ID. An
identical repeat returns the original result without creating an additional
event. Reuse of an ID with a different action, reason or case is rejected as a
collision. Every successful mutation appends an HMAC-attested `CONTROL_*` or
existing `RETRY` event to the same journal chain as the case events.

On reopen, the runtime verifies that entire chain before reading the persisted
control state or a request receipt. Any altered journal fails closed. The
control state and idempotency records are local recovery state only; neither
proves that a producer, a human reviewer or an external system acted.

## Rejection and non-claims

Unknown/malformed action, request, reason or case; invalid state transition;
request collision; retry cap; paused/stopped processing; invalid journal; and
hostile web origin reject with a non-sensitive error and no downstream effect.

No action can publish, deliver, approve, accept, contact a third party, invoke
a provider, access another block's store/key, acquire network data, alter
source evidence or promote a gate. The control plane is not a production
scheduler or an authorization mechanism. Contract conformance is not cross
block execution, independent review or global acceptance.

## Compatibility and validation

The control plane is additive to Federated Handoff Contract v0.1: handoff
envelope validation and case identity stay unchanged. It applies only to
newly-created local journals; existing local journals receive the deterministic
initial `RUNNING` state on first open.

Validate successful pause/resume/stop/start and retry; replay and request-ID
collision; blocked progression/retry while paused or stopped; restart recovery;
HMAC tampering; malformed input; hostile origin; and absence of publication or
delivery paths.
