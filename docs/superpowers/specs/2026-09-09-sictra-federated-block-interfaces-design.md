# SICTrA Federated Block Interfaces

Status: `OWNER-APPROVED DESIGN / IMPLEMENTATION PENDING`

## Purpose

Create a coherent local operator interface for Blocks 1, 2, and 3 while
preserving a separate address, runtime, data boundary, and authority boundary
for every block. The interfaces form a visual suite, not a unified execution
plane.

The primary user is the SICTrA owner operating the system locally under the
`LABORATORY_INTERNAL_SUPERVISED` boundary. The suite must make it easy to move
between intelligence, design, and precision work without suggesting that one
block validates, accepts, or promotes another.

## Approved architecture

The suite is **federated**:

| Block | Default local address | Operator job | Existing state |
| --- | --- | --- | --- |
| Block 1 | `http://127.0.0.1:8765/` | Research, retained evidence, dossiers, watchlists, editorial review | Operational interface implemented on the Block 1 workstream |
| Block 2 | `http://127.0.0.1:8766/` | Create and inspect traceable design candidates | Local Design Console implemented; visual alignment required |
| Block 3 | `http://127.0.0.1:8767/` | Review admitted account context and governed decision signals | Domain runtime implemented; interface not yet implemented |

Each server binds only to `127.0.0.1`. Navigation links may open another
block's local address, but no interface fetches another block's API, shares a
session token, embeds another block in a frame, or treats availability as
evidence. A missing neighboring block is a navigational condition, not a
runtime failure.

This is a presentation and operator-access increment. It does not alter the
canonical engine ownership, source hierarchy, contracts, gate criteria, or
promotion state.

## Shared presentation profile

`SICTrA Operational` is the presentation profile. It is implemented within
each block's packaged static assets so a block remains independently runnable.
The profile is not a shared runtime authority and cannot normalize domain
states across blocks.

### Color

| Role | Value | Meaning |
| --- | --- | --- |
| Authority navy | `#172557` | identity, boundaries, primary text |
| Active turquoise | `#20B89A` | current navigation and verified activity |
| Navigation mint | `#EDF8F5` | local product rail |
| Workspace white | `#FFFFFF` | primary work surface |
| Quiet surface | `#F6F8F8` | secondary evidence and context |
| Primary ink | `#17202A` | body text |
| Secondary ink | `#66727A` | metadata and explanations |
| Boundary line | `#DDE7E4` | grouping and separation |
| Review amber | `#F2A65A` | review, uncertainty, incomplete evidence |
| Failure red | `#C94C4C` | rejection, integrity failure, blocked state |

Typography remains dependency-free: Bahnschrift for compact display text,
Aptos or Segoe UI for interface text, and Consolas only for hashes, IDs, and
lineage. No remote font, icon, script, analytics, or asset dependency is
introduced.

### Shell

Every block uses the same orientation pattern:

```text
┌────────────────────────┬───────────────────────────────────────────┐
│ SICTrA                 │ Block identity / current destination      │
│ Block identity         │ Local + supervised + explicit authority  │
│                        ├───────────────────────────────────────────┤
│ Block-owned navigation │ Block-owned working surface               │
│                        │                                           │
│ Open Block 1 ↗         │ Domain evidence, actions, and receipts    │
│ Open Block 2 ↗         │                                           │
│ Open Block 3 ↗         │                                           │
│ Runtime local          │                                           │
└────────────────────────┴───────────────────────────────────────────┘
```

The links identify the destination and open it separately. They do not use
status colors and never claim that the destination is running. The signature
element inside each workspace is a thin, block-specific route that exposes the
real transformation and its stopping boundary.

## Block-specific experience

### Block 1 — Intelligence Operational

Block 1 remains the visual reference and retains its current work route:

`question → retained source → evidence → dossier → editorial review`

Only a navigation group for the three local block addresses is added if the
Block 1 workstream accepts the presentation increment. Existing API contracts,
element IDs, evidence semantics, publication prohibition, and manual approval
boundary remain unchanged. Block 1 is not reopened technically merely to make
the suite symmetrical.

### Block 2 — Design Operational

The existing Create, Studio, Ops, History, Evidence Inspector, and Lineage
Ribbon capabilities remain. The interface is aligned to the Operational shell
without changing the Project Graph, CDD, edit token, or API schemas.

Its route is:

`brief → direction/system → document version → review receipt → export candidate`

The UI must keep `CANDIDATE_NOT_ACCEPTED`, invalidation, reused checkpoints,
rights limits, and missing upstream evidence visually explicit. Export remains
a local candidate action and never implies publication or acceptance.

### Block 3 — Precision Operational

Block 3 receives a new local console with four initial views:

1. **Accounts** — select tenant/account and inspect available dossiers without
   exposing secrets or unrestricted source content.
2. **Context admission** — show receipt, evidence freshness, issuer,
   attestation state, policy binding, exclusions, and the exact reason for
   admission or return upstream.
3. **Decision signals** — show only signals derived by the governed catalog,
   separated from hypotheses and raw observations. No universal score is
   introduced.
4. **Control** — show local scope, integrity, expiry, quarantine, abstention,
   and prohibited actions.

Its route is:

`approved account seed → official-site dossier → attested context → governed signal → human review`

The first version is a bounded read model with a deterministic synthetic demo.
Any action that evaluates an admission uses allowlisted input and an
unpredictable local session token. It cannot crawl the Internet, import Excel,
write CRM data, contact a person, deliver a message, promote learning, or mint
acceptance.

## Data and authority flow

Each UI reads only its block-owned durable store or deterministic demo fixture.
Presentation objects preserve source identity, hashes, timestamps, certainty,
limitations, contradictions, expiry, and disposition. The UI may translate an
engine reason into plain language, but the raw reason code remains available.

The interfaces distinguish:

- observation from fact;
- hypothesis from governed decision signal;
- candidate from accepted artifact;
- bound from executed from validated;
- local runtime evidence from global gate acceptance;
- expected abstention from system failure.

No aggregate cross-block health score or completion percentage is created.

## Failure, empty, and degraded states

- Missing database or account: explain which controlled setup step is needed;
  never render a synthetic success in its place.
- Missing neighboring server: the link remains a link; no false offline badge
  is inferred without a direct, user-initiated navigation.
- Stale, expired, altered, quarantined, contradictory, or out-of-policy
  evidence: show the blocking reason and suppress downstream effects.
- Unknown issuer, invalid attestation, policy substitution, tenant mismatch,
  or identity collision: reject fail-closed and expose no sensitive payload.
- Unsupported method, host, origin, schema, or cross-site request: return an
  explicit local error with security headers.
- Empty state: identify the next valid local step and the action the interface
  deliberately cannot perform.

## Accessibility and responsive behavior

- Semantic landmarks, labels, headings, status and alert regions.
- Full keyboard operation, visible focus, 44 px minimum touch targets.
- Text or pattern in addition to color for every material state.
- WCAG 2.1 AA contrast, 200% zoom/reflow, forced-colors support.
- Reduced-motion support; one restrained 180–240 ms transition sequence.
- Desktop rail becomes a horizontal, scrollable navigation strip on narrow
  screens without hiding operational state.

## Security boundaries

- Static files are packaged locally and served with CSP, `no-store`,
  `nosniff`, no-referrer, same-origin resource and opener policies.
- Hosts, origins, paths, methods, schemas, body sizes, IDs, and collection
  sizes are allowlisted or bounded.
- No remote resources, inline executable code, arbitrary paths, credentials,
  secrets, raw keys, unrestricted HTML, or cross-origin API calls.
- Human-readable errors do not expose filesystem paths, source bodies, keys,
  or internal exception traces.
- UI state never promotes a gate or substitutes owner/independent approval.

## Implementation sequence

1. Record this approved specification and baseline the current interfaces.
2. Align Block 2 to the Operational presentation profile while preserving all
   existing behavior and accessibility evidence.
3. Implement the Block 3 local read model, static interface, deterministic
   demo, and adversarial request boundaries.
4. Add the federated navigation links to Blocks 2 and 3.
5. Prepare the equivalent navigation-only increment for the Block 1
   workstream without reopening its completed technical closure.
6. Inspect all three at desktop and narrow widths; repair visual, console, and
   keyboard defects.
7. Run focused tests, full regression, commit coherent increments, push, and
   obtain CI on each exact final SHA.

## Validation and evidence

Every material increment requires a positive behavior test and at least one
rejection, tamper, stale, replay, recovery, or boundary test. Acceptance
includes:

- existing Block 1 and Block 2 interface tests remain green;
- Block 2 preserves Create, controlled editing, history, Ops, and lineage;
- Block 3 serves only on loopback and rejects hostile host/origin, cross-site
  requests, unsupported mutations, malformed schemas, invalid attestations,
  tenant mismatch, stale evidence, and unknown accounts;
- deterministic fixtures never become an oracle for their own conclusions;
- markup, keyboard focus, reduced motion, forced colors, and responsive layout
  are tested and inspected;
- browser console has no errors on primary and failure paths;
- full regression passes before material commits;
- CI succeeds on each recorded exact SHA.

## Completion and non-claims

An interface is technically complete when its owned views, error states,
security boundaries, accessibility requirements, focused tests, full
regression, browser inspection, exact-SHA commit, and CI evidence are present.

This design does not prove production readiness, global integration,
independent validation, commercial value, legal compliance, real CRM access,
real delivery, autonomous research, or authorization to publish or contact a
third party. Human and Master Architecture Review gates remain explicit where
the underlying contracts require them.

