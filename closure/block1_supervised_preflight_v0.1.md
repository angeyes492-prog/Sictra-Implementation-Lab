# Block 1 Intelligence — Supervised Laboratory Preflight v0.1

## Scope and verdict

Target: `LABORATORY_INTERNAL_SUPERVISED` only.

Verdict: `YELLOW / TECHNICAL IMPLEMENTATION COMPLETE / HUMAN APPROVAL
PENDING`. The code and local runtime meet the bounded laboratory sequence.
This file does not claim production,
independent validation, commercial reuse rights, automatic acquisition,
publication, delivery, or integration of Blocks 2–4.

## Preflight record

| Area | Evidence | State and limit |
| --- | --- | --- |
| Scope | Local UI binds only to `127.0.0.1`; source ingress has no HTTP client or scheduler. | `VERIFIED / B`; local, single-user boundary. |
| Provenance | Retained Eurostat baseline has source binding, approval lineage, hash and manual selection. | `VERIFIED / B`; one governed source path. |
| Evidence and epistemics | Attested evidence, watchlist and dossier chain separate baseline, facts, interpretation, hypotheses and publication. | `VERIFIED / B`; real baseline creates no insight. |
| Adversarial controls | Stale/altered/ambiguous evidence, tampered stores, invalid source role and reference-host mismatch reject. | `VERIFIED / B`; local tests are not independent review. |
| Source registry | 18 candidates expose role/license/access/cadence/revision metadata; all remain `PROPOSED` with zero admissibility. | `VERIFIED / B`; terms are not approved except the pre-existing bounded Eurostat path. |
| Editorial and handoff | Review or abstention remains bounded; no send/publication authority is present. | `VERIFIED / B`; independent corroboration and human interpretation are still external. |
| Reproducibility and recovery | Windows launcher, controlled XLSX intake, data-only backup and original-key recovery are tested. | `VERIFIED / B`; no cross-device key recovery. |
| Regression | 282 local tests passed on 2026-09-09. Exact implementation SHA `e73cc427f7dd55983916cbe5b06cc59624fe45da` passed GitHub Actions runs `34303522368` and `34303518680`. | `VERIFIED / A` for that SHA; the ledger commit is subject to the same exact-SHA workflow. |

## Residual risks and abstention conditions

- `AWAIT_NEWER_SOURCE`: a real second governed Eurostat release is needed
  before a real delta/dossier exists during operation; this is an expected
  abstention state, not a technical closure blocker.
- `WAITING_FOR_CORROBORATION`: an editorial-ready real candidate needs an
  independent root and human interpretation.
- `LICENSE_UNCLEAR`: public accessibility does not allow redistribution until
  the candidate-specific terms review is bound.
- `INDEPENDENT_REVIEW_DEFERRED`: owner approval is not independent validation;
  independent review and final owner approval are the remaining gate actions.

## Exact promotion condition

The implementation is technically complete at the stated boundary once CI
succeeds on the exact commit containing this preflight. Gate promotion still
requires independent human review and final owner approval. Any production,
external distribution, network acquisition, automatic scheduling, new source
binding or cross-block claim requires a separate review and gate.
