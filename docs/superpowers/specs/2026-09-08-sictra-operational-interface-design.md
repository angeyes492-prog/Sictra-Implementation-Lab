# SICTrA Operational — Interface redesign

Status: `APPROVED DIRECTION / WRITTEN SPEC PENDING OWNER REVIEW`

## Purpose

Redesign the existing Block 1 Intelligence laboratory as a polished daily-use
workspace inspired by the clarity of the supplied Bouncer reference while
remaining unmistakably SICTrA. The redesign changes presentation and operator
orientation only. It preserves every current runtime, evidence, source,
dossier, editorial and publication boundary.

The primary user is a non-technical logistics-intelligence operator. The
interface's single job is to make it obvious where to begin research, where
retained evidence lives, what the system currently knows, and why a result is
ready, blocked or awaiting review.

## Design direction

`SICTrA Operational` uses a light operational shell:

- fixed pale-mint navigation rail;
- white workspace with generous horizontal rhythm;
- compact top status bar;
- soft neutral cards and restrained rounded corners;
- deep navy for identity and authority;
- turquoise for active navigation and verified operational signals;
- amber and red reserved for uncertainty, review and failure.

It borrows the reference's information architecture—not its brand, mascot,
copy or proprietary visual assets. The supplied SICTrA logo is displayed on a
deep-navy brand plate because the provided artwork is white and transparent.

## Visual tokens

| Role | Token |
| --- | --- |
| Authority navy | `#172557` |
| Active turquoise | `#20B89A` |
| Navigation mint | `#EDF8F5` |
| Workspace white | `#FFFFFF` |
| Quiet surface | `#F6F8F8` |
| Primary ink | `#17202A` |
| Secondary ink | `#66727A` |
| Boundary line | `#DDE7E4` |
| Review amber | `#F2A65A` |
| Failure red | `#C94C4C` |

Typography remains local and dependency-free. `Bahnschrift` provides compact
display authority; `Aptos`/`Segoe UI` carries interface copy; `Consolas` is
reserved for hashes, engine identifiers and evidence lineage.

## Shell and navigation

The desktop shell has a 272 px rail and a fluid workspace. The rail contains:

1. SICTrA logo plate and `Intelligence / Bloque 1` product label.
2. `Inicio`: Panorama.
3. `Investigación`: Investigaciones, Fuentes, Strategy Lab.
4. `Inteligencia`: Evidencia, Dossiers, Watchlists, Mesa editorial.
5. `Control`: Validación.
6. A persistent runtime-status footer.

The active destination uses a white capsule, turquoise icon and subtle shadow.
Every destination keeps its plain-language action subtitle. On narrow screens,
the rail becomes a horizontal navigation strip without hiding functionality.

The top bar shows the current destination, the laboratory boundary, pipeline
state and a single explicit `Actualizar` action. It never displays fictional
credits, accounts, alerts or cloud connectivity.

## Panorama

Panorama becomes an operational briefing rather than a decorative dashboard:

- a compact `Intelligence pulse` header shows global/regional/local scope;
- four honest metrics summarize visible investigations, retained source
  packets, independent roots and explicit contradictions;
- the primary panel lists active investigations with status and geography;
- a secondary panel explains the current epistemic distribution;
- the source → evidence → dossier → editorial path appears as a thin connected
  operational rail, the signature visual element of the product.

The rail is memorable because it represents a real system invariant. It does
not imply automation or completion.

## Working views

### Investigaciones

Lead with one prominent research-entry card. Fields remain unchanged but are
grouped into `Pregunta`, `Cobertura` and `Referencia`. The result appears as a
clear local-draft receipt. Existing investigations render below as expandable
records.

### Fuentes

Filters occupy one horizontal command card. Candidate sources render as a
structured table/card hybrid with publisher, region, role, terms status,
access posture and admissibility. `PROPOSED` must never look approved.

### Strategy Lab

The comparison controls read left-to-right and the result emphasizes dominance,
trade-offs and abstention. It never manufactures a universal score.

### Evidencia and Dossiers

Evidencia uses the connected lineage rail. Dossiers use a master-detail layout
with signed facts, limitations, contradictions, uncertainty and executive
questions visually separated. Hashes remain secondary but accessible.

### Watchlists and Mesa editorial

Watchlists use 7/30/90-day columns with explicit triggers. The editorial desk
shows shortlist, blocked candidates and human rationale as separate zones.
Publishing remains unavailable.

### Validación

Validation resembles a controlled test console: scenario cards on the left,
plain-language result and technical receipt on the right. Success, expected
rejection and unexpected failure use distinct semantics and colors.

## Interaction behavior

- View transitions use one restrained 180–240 ms fade/translate sequence.
- Hover reinforces clickability without moving layout.
- Keyboard focus is always visible.
- Reduced-motion preferences disable transitions.
- Loading, empty, review-required and integrity-error states explain the next
  valid operator action.
- All existing element IDs and API contracts are preserved unless a test-backed
  implementation change explicitly updates them.

## Responsive behavior

- Desktop: fixed rail, spacious command area, two-column analytical layouts.
- Tablet: compact icon rail and single-column detail views.
- Mobile: horizontal navigation, stacked forms, full-width controls, no hidden
  operational state, minimum 44 px touch targets.

## Logo handling

The supplied PNG is copied into the packaged web assets under a stable name.
It is displayed with `object-fit: contain`, meaningful alternative text and no
distortion. The original attachment is not modified. A text fallback preserves
product identity if the asset cannot load.

## Security and epistemic constraints

- No new network client, upload surface, credential field or publication path.
- No visual state may elevate `PROPOSED`, `DRAFT`, `NOT_EVIDENCE`, `UNKNOWN` or
  `SOURCE_REVIEW_REQUIRED` into an accepted state.
- The laboratory boundary remains visible on every view.
- Errors never expose source content, secrets, filesystem paths or raw keys.

## Validation

Implementation acceptance requires:

- all existing behavioral tests passing;
- tests for logo delivery, semantic navigation groups and preserved controls;
- keyboard and responsive inspection;
- browser inspection of Panorama, Investigaciones, Evidencia, Dossiers and
  Validación;
- no console errors;
- exact final SHA and successful CI.

## Non-goals

This redesign does not add autonomous Internet research, multi-user identity,
commercial publication, newsletter delivery, production security or a claim
of independent validation.
