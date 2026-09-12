# SICTrA Blocks 2 and 3 — Balanced Interface Polish

Status: `OWNER-APPROVED DESIGN BASE / WRITTEN SPEC PENDING OWNER REVIEW`

## Purpose

Refine the local interfaces for Blocks 2 and 3 so that a supervised operator
can understand current state, authority, the next valid action, and recovery
steps without sacrificing the distinct identity of either block. This cycle
balances visual finish with operational clarity and remains inside
`LABORATORY_INTERNAL_SUPERVISED`.

The work is presentation and bounded interaction refinement. It does not
change engine ownership, contracts, API schemas, source authority, gates,
session sharing, or the prohibition on publication, CRM writes, delivery, and
automatic acceptance.

## Audience and jobs

The primary user is the SICTrA owner operating locally.

- Block 2 is a **traceable design workshop**. Its single job is to help the
  operator move from a verifiable brief to an inspectable local candidate
  while seeing lineage, invalidation, rights limits, and execution state.
- Block 3 is a **commercial precision desk**. Its single job is to help the
  operator inspect an approved account, determine whether context is
  admissible, distinguish signals from hypotheses, and stop at human review.

## Chosen approach

Use a balanced operational refinement rather than a cosmetic patch or a full
redesign. Existing DOM hooks, endpoints, tokens, stores, and domain behavior
remain stable. Markup, CSS, and client-side presentation logic may be improved
where the change is covered by positive and rejection/recovery tests.

## Shared visual system

Both blocks retain the approved SICTrA Operational shell and dependency-free
fonts. The common palette is intentionally quiet so semantic states carry the
weight:

| Token | Value | Use |
| --- | --- | --- |
| Authority navy | `#172557` | identity, headings, bounded actions |
| Active turquoise | `#20B89A` | current route and verified local activity |
| Navigation mint | `#EDF8F5` | suite navigation and quiet orientation |
| Workspace white | `#FFFFFF` | primary work surface |
| Quiet surface | `#F6F8F8` | explanations, empty states, secondary evidence |
| Primary ink | `#17202A` | body text |
| Secondary ink | `#66727A` | metadata and supporting explanations |
| Review amber | `#F2A65A` | uncertainty, review, return upstream |
| Failure red | `#C94C4C` | integrity failure and rejected state |

Typography continues to use Bahnschrift for restrained display text, Aptos or
Segoe UI for interface prose, and Consolas for IDs, hashes, reason codes, and
lineage. No remote asset or font is introduced.

The shared signature is an **evidence route** that shows where the current
object is in its block-owned transformation and where authority stops. It is
not a progress meter and never aggregates health across blocks.

## Block 2 design

### Information structure

The current Create, Studio, and Ops modes remain. Each mode gains a compact
orientation header with three stable answers: what is being inspected, what
the operator may do here, and what condition prevents promotion.

```text
┌──────────── rail ────────────┬──────────── command + boundary ────────────┐
│ Create / Studio / Ops        │ project · local runtime · refresh          │
│ Separate suite links         ├─────────────────────────────────────────────┤
│ Local runtime condition      │ brief → system → CDD → review → candidate  │
└──────────────────────────────┤ primary workspace                           │
                               │ contextual next step / recovery             │
                               └─────────────────────────────────────────────┘
```

The evidence route changes emphasis by mode without changing its terms:

`brief → direction/system → document version → review receipt → export candidate`

### Refinements

- Replace mixed English/Spanish operator labels where a stable Spanish term is
  clearer, while retaining canonical codes such as `CDD`, engine IDs, and raw
  dispositions.
- Show a mode-specific explanation and next valid action near the boundary,
  rather than requiring the operator to infer it from the entire canvas.
- Make loading, unavailable project, failed refresh, empty history, missing CDD,
  `RETURN_UPSTREAM`, and controlled edit failures visually distinct and
  actionable.
- Preserve raw reason codes next to plain-language explanations.
- Improve selected, hover, keyboard-focus, and disabled states without relying
  on color alone.
- Reduce visual density in Studio and Ops through grouping and spacing, not by
  removing evidence.
- Keep Create submissions bounded and keep the handoff seal separate from the
  live announcement region.

## Block 3 design

### Information structure

Accounts, Admission, Signals, and Control remain separate views. A persistent
account context strip shows tenant/account identity, fixture or evidence class,
and current disposition. It provides context only; it does not create a global
score.

```text
┌──────────── rail ────────────┬──────────── account context ────────────────┐
│ Accounts / Admission         │ tenant · account · evidence class           │
│ Signals / Control            ├─────────────────────────────────────────────┤
│ Separate suite links         │ account → dossier → admission → signal      │
│ Local read-only runtime      ├─────────────────────────────────────────────┤
└──────────────────────────────┤ selected view + next human decision          │
                               └─────────────────────────────────────────────┘
```

The evidence route remains:

`approved account seed → official-site dossier → attested context → governed signal → human review`

### Refinements

- Turn the synthetic fixture label, account identity, and authority boundary
  into visible context rather than metadata hidden in the API response.
- In Admission, display disposition, reason/explanation, issuer, policy,
  attestation, and evidence freshness with an explicit next step.
- In Signals, separate governed signal, observation, hypothesis, and review
  state through labels and structure; never introduce a universal score.
- In Control, group prohibited actions, integrity conditions, expiry, and
  abstention so expected blocking behavior is recognizable.
- Provide meaningful empty states for no signals, no limitations, and no
  control declarations.
- On loader or health failure, keep stale content from appearing current and
  tell the operator to retry locally without exposing internal paths or traces.

## Interaction and state model

- Each block continues to fetch only its same-origin, block-owned API.
- Refresh enters a visible busy state, disables only the affected refresh
  action, and restores it on success or failure.
- A successful refresh announces that evidence was refreshed; it does not say
  the evidence was accepted or validated.
- A failed refresh marks runtime state as unavailable, hides or marks prior
  content as stale, and exposes a retry action.
- View selection updates `aria-current`, the visible panel, the page heading,
  and focus destination without changing domain data.
- Federated links remain ordinary links to separate loopback addresses. No
  cross-block API probing, iframes, token reuse, or implied availability is
  added.

## Error, empty, and abstention language

Every non-success state answers:

1. What happened in plain language.
2. The raw reason or disposition when one exists.
3. What the operator can do next.
4. What the interface deliberately did not do.

Expected abstention and `RETURN_UPSTREAM` use review amber; integrity failure
or rejected hostile input uses failure red. `UNKNOWN` and
`INSUFFICIENT EVIDENCE` never appear as neutral success.

## Accessibility and responsive behavior

- Preserve semantic landmarks, headings, labels, live regions, and skip links.
- Maintain at least 44 px targets, visible keyboard focus, and text/pattern in
  addition to color.
- Move focus to the selected view heading after keyboard or pointer navigation
  without stealing focus during initial load.
- Use `aria-busy` during refresh and atomic, concise status announcements.
- At 200% zoom or narrow widths, navigation becomes a horizontal strip and
  operational context remains visible rather than disappearing entirely.
- Respect reduced motion and forced-colors modes. Any transition is restrained
  to one 180–220 ms state change and is nonessential.

## Security and authority constraints

- Keep loopback-only binding, allowlisted paths/methods/hosts/origins, CSP,
  no-store, nosniff, no-referrer, and same-origin isolation.
- Render untrusted values through existing escaping boundaries; no inline
  executable code or remote dependency.
- Do not expose edit tokens, local paths, source bodies, credentials, or
  exception traces.
- Do not convert UI state into gate promotion, publication, delivery,
  acceptance, CRM mutation, or cross-block authority.

## Validation

Implementation must add or update tests that establish behavior rather than
only matching decorative strings:

- positive tests for mode/view navigation, refresh state, context visibility,
  actionable empty states, and raw-code preservation;
- rejection/recovery tests for loader failure, failed refresh, absent CDD,
  empty signal/control collections, stale presentation, and unsafe text;
- structural accessibility assertions for headings, focus targets, live
  regions, `aria-busy`, forced colors, reduced motion, and 44 px targets;
- browser inspection at desktop and narrow widths for both primary and failure
  paths, with no console errors;
- focused Block 2 and Block 3 suites, then full clean regression;
- commit and GitHub CI evidence on the exact final SHA before any closure
  claim.

## Delivery sequence

1. Establish the shared presentation primitives independently in each block.
2. Refine Block 2 orientation, states, and recovery without changing its APIs.
3. Refine Block 3 context, admission, signals, controls, and recovery.
4. Run accessibility and responsive inspection; repair observed defects.
5. Run focused and full regression, record evidence, push a reviewable branch,
   and obtain CI on the exact SHA.

## Completion and non-claims

This polish cycle is complete only when both interfaces implement the specified
states, focused and full tests pass, browser inspection is recorded, and CI is
green on the final SHA. The highest claim remains
`LABORATORY_INTERNAL_SUPERVISED`.

It does not prove production readiness, real provider or CRM integration,
commercial effectiveness, legal compliance, accessibility certification,
global gate acceptance, permission to contact third parties, or authorization
to publish.
