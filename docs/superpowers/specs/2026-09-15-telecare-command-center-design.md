# Telecare OS — Command Center federado del Orchestrator

Status: `APPROVED DESIGN / LOCAL CONTROL PLANE IMPLEMENTATION AUTHORIZED`
Date: 2026-09-15
Owner decision: Block 4 is the Telecare OS home and operational control panel, not a separate product tab.

## Objective

Replace the landing view with a compact Command Center inspired by the supplied logistics dashboard reference. It surfaces the week's intelligence, trends, reports, review queue and operational state. Every card is actionable and opens the owning block and same case in the current browser tab.

The shell does not merge runtimes, transfer authority, aggregate acceptance or let the UI decide operational state.

## Selected architecture

Use same-window federated navigation, not an embedded iframe or cross-block data proxy.

- Block 4 is the default home.
- Blocks 1–3 remain independently runnable and retain their stores, sessions and authority.
- Cards carry an explicit destination URL plus optional `case_id` and `correlation_id`; the destination validates what it may display.
- Returning to Command Center preserves only an allowlisted, non-sensitive case reference.
- A destination link is not evidence that its runtime is available or executed.

## Layout and contents

### Header and hero

The compact header contains Telecare OS identity, current operational boundary, current period, search/filter entrypoint, accessibility controls and visible pause/stop state.

The hero contains the most relevant weekly item, review-queue count, concise evidence/uncertainty statement and one safe action to open the item or review queue. It must never invent a success metric.

### Intelligence row

Four cards:
1. **Top noticias de la semana** — bounded, current Block 1 items.
2. **Tendencias de mercado** — change observations with evidence disposition; a technical delta is not a confirmed trend.
3. **Informes y dossiers** — traceable current dossiers and design candidates.
4. **Insights que requieren revisión** — only review-required, abstained or return-upstream cases.

Each card has title, source/evidence identity, observation time, certainty/uncertainty, owner block and a text action. The complete card uses that same action.

### Operations grid

- Current work and queue from Block 4.
- Evidence coverage/currentness; never a fabricated global health score.
- Pipeline distribution by explicit state.
- Recent audit, recovery and retry events.
- Pause, stop and resume controls only where the runtime admits them.

Charts require observed data. Empty or insufficient states explain the next valid operator action rather than rendering invented values.

### Navigation rail

Command Center is active home. The rail exposes Intelligence, Design, Precision, Review queue, Reports and Configuration. Each item identifies its block and opens in the current tab without shared credentials or cross-block API fetch.

## Interaction contract

A card uses this read-only descriptor:

```text
{ card_id, case_id?, correlation_id?, owner_block,
  destination_url, title, evidence_refs[], observed_at?,
  currentness, certainty, uncertainty[], disposition }
```

- IDs travel only in an allowlisted route/query representation.
- Every action is keyboard reachable, has visible focus, accessible name and text label.
- Text/pattern supplements every color state.
- Unknown target, stale evidence or malformed identity creates a non-sensitive error with no implicit retry.
- Visual controls never substitute same-origin or authority checks.

## Local operational control plane

The owner authorized functional controls only inside the existing loopback
Block 4 runtime. This is a bounded orchestration capability, not authority to
operate any producer, adapter, destination or external system.

### State model

`RUNNING → PAUSED → RUNNING` and `RUNNING|PAUSED → STOPPED → RUNNING`.

- **RUNNING** permits local bounded processing of an already retained package.
- **PAUSED** retains the journal and allows its inspection, but rejects a new
  processing transition or retry.
- **STOPPED** fails closed for processing and retries until an explicit local
  operator selects **Start**.
- Ingestion and journal verification remain available in all three states so
  evidence is never silently discarded and recovery can be diagnosed.

The state is stored in the same HMAC-attested append-only journal as the case
events. A restart rehydrates it only after chain verification. A pause, resume,
stop or start request includes an allowlisted action, bounded reason and unique
request ID; repeating the identical request is idempotent, while reusing its
ID for a different request is rejected. The design intentionally does not add
an approval, publish, delivery, CRM or cross-block command.

### Control interface

`POST /api/controls` accepts only local same-origin JSON actions:

| Action | Preconditions | Effect | Non-claim |
| --- | --- | --- | --- |
| `PAUSE` | `RUNNING` | Stops local case progression; records `CONTROL_PAUSED`. | Does not stop any producer or external service. |
| `RESUME` | `PAUSED` | Restores local progression; records `CONTROL_RESUMED`. | Does not approve queued cases. |
| `STOP` | `RUNNING` or `PAUSED` | Fails closed for local progression; records `CONTROL_STOPPED`. | Does not delete the journal or cancel external work. |
| `START` | `STOPPED` | Explicitly re-enables local progression; records `CONTROL_STARTED`. | Does not replay work automatically. |
| `RETRY_CASE` | Current runtime is `RUNNING`; case is returnable and below retry cap | Reuses the exact stored input fingerprint and records the existing bounded retry. | Does not create a new source claim. |
| `VERIFY_JOURNAL` | None | Revalidates the HMAC chain without mutation. | Is not recovery, acceptance or external validation. |

An unknown action, malformed payload, hostile origin, request-ID collision,
unsafe state transition, unavailable journal or prohibited retry must report a
non-sensitive error and create no downstream effect.

## Visual direction

Take the reference's qualities, not its literal assets: calm high-information field, compact white cards, deep navy/quiet-slate canvas, turquoise for current activity, amber for review, red for fail-closed state, restrained contextual logistics imagery, 12-column desktop grid and responsive one-column layout.

No remote fonts, remote images, analytics, embedded frames or unbounded dependencies.

### Revised composition

The page becomes an **Evidence Atlas** rather than a logistics simulation. A
quiet ice-blue field carries a CSS/SVG-like route lattice for the selected
case: evidence enters at Block 1, passes through bounded receipts for Blocks 2
and 3, and terminates visibly at the human gate. The lattice is the signature
element: it reflects actual lineage and stops rather than animating an invented
flow.

- A slim top bar mirrors the reference's confident control surface: Telecare
  identity, in-page federation navigation, laboratory boundary and live local
  control state.
- The stage pairs the selected case's real route with a compact control deck.
  The deck exposes only actions admitted in the current state, has an explicit
  reason, confirmation and a polite live result; dangerous-looking red is
  reserved for the fail-closed `STOPPED` condition.
- Four small readouts are computed from the returned journal: registered
  cases, human-review cases, selected-case route progress and external effects
  (always explicitly `0 / PROHIBITED` for this scope). They are not goals,
  performance scores or market metrics.
- The lower deck joins the case queue, evidence inspector and event timeline.
  The selected case controls all three; every event names its origin and time.
- Icy surfaces (`#F2F7FB`), deep navigation blue (`#102A43`), graphite
  (`#263238`), verified teal (`#087F72`), review amber (`#B7791F`) and
  fail-closed red (`#B42318`) form the palette. System UI fonts remain local.
  Motion is limited to a single route-progress transition and respects reduced
  motion.

## Failure and recovery

| Condition | Required behavior |
| --- | --- |
| No current evidence | Useful empty state and controlled input/review route. |
| Stale or contradicted evidence | Show reason, suppress downstream action, route upstream/review. |
| Unknown/malformed target | Reject descriptor and show non-sensitive error. |
| Destination unavailable | User-triggered local navigation failure; no inferred status badge. |
| Paused/stopped runtime | Display state and suppress only prohibited action. |
| Retry/recovery | Expose event/checkpoint without claiming success. |

## Validation and completion

Test descriptor validation, allowed same-window route, unknown/malformed case rejection, correlation preservation, pause/stop/start/retry state, request replay/collision, restart recovery, hostile origin, keyboard/focus/reduced-motion/forced-colors/CSP, responsive layout and no browser errors. Inspect current, empty, paused, stopped, review-required and fail-closed fixtures.

The interface is complete when all cards are actionable, block ownership remains explicit, errors/empty states are implemented, tests and visual inspection pass, full regression passes and CI succeeds on the exact SHA. This does not promote Telecare OS to production or prove external autonomy.
