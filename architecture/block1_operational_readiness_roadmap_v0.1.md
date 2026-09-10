# Block 1 — Operational readiness roadmap v0.1

`PLANNED / PROBABLE / B`. This roadmap does not change any gate. It defines
the minimum path from the local research laboratory to a real internal pilot,
then to a corporate operational service.

## Operational boundary

An **internal pilot** may use a bounded, approved public source and an operator
to review every output. A **corporate operation** additionally requires durable
identity, tenancy, secrets, recovery, monitoring and independent validation.
Neither label follows from a passing test suite alone.

| Layer | Purpose | Current state | Pilot acceptance evidence | Corporate acceptance evidence |
| --- | --- | --- | --- | --- |
| 1. Source policy | Limit each source to a known asset, terms, host and claim vocabulary. | Durable control store reconstructs a locally bound gateway; production binding/key configuration absent. | Approval record and signed binding match exactly under retained pilot keys. | Periodic terms review, owner and expiry controls. |
| 2. Guided ingress | Accept operator-supplied files without arbitrary network access. | CSV/XLSX preflight implemented locally. | First file passes preflight and is mapped without data loss. | Authenticated upload, malware scanning, quotas and retention policy. |
| 3. Schema and quality | Map source fields and reject ambiguous, invalid or incomplete values. | Eurostat mapper implemented; mixed geography requires selection. | Explicit geography-level selection and coverage report. | Versioned mappers, drift alerts, reconciliation and rollback. |
| 4. Evidence ledger | Preserve provenance and transformations for every admitted observation. | Atomic local attested-evidence store verifies and retains gateway evidence across reopen; a temporary real-workbook exercise recovered one current record. | Signed binding, gateway attestation and immutable local record link file hash, filters and mapping. | Durable encrypted store, audit trail, retention and restore exercise. |
| 5. Intelligence runtime | Form research questions, detect changes, contradictions and bounded insights. | A durable dossier store converts an independently assembled synthetic attested-input delta into separately typed facts, empty interpretations/hypotheses, uncertainties and questions; the retained real workbook correctly remains a baseline. | The bounded behavior is complete; a later real release may exercise the same path without changing the gate. | Load/performance SLOs and continuous regression with real anonymised cases. |
| 6. Editorial decisioning | Select only relevant, attributable insight candidates and hand off to Design. | Durable dossiers enter the editorial contract through a conservative bridge and are visible in a separate integrity-verified UI panel; they remain `RESEARCH_NEEDED`. | One reviewed brief links every statement to evidence and abstains when weak. | Approval workflow, versioned outputs and publishing audit trail. |
| 7. Watchlists and cadence | Recheck approved sources and surface meaningful change without noise. | Atomic retained operator cycle admits exactly one current attested source record, supersedes a valid newer release and quarantines same-release conflicts as `SOURCE_REVIEW_REQUIRED`; no scheduler is present. | Complete for manual supervised operation; cadence remains operator-triggered. | Budgeted workers, rate limits, change detection, alerts, kill switch and incident runbook. |
| 8. Operating plane | Make the system safe for multiple people and sustained use. | Local launcher initializes a signed-reader key/store layout under `%LOCALAPPDATA%`; documented data-only backup/restore is verified under original keys, while ACL and disaster/key recovery remain absent. | Complete for named single-user laboratory operation, subject to human approval. | SSO/RBAC, tenancy, secret manager, deployment controls, observability, backups, security review and disaster recovery. |

## Required order

1. Bind the already approved Eurostat scope locally.
2. Assemble one explicitly selected Layer 3 result without changing its non-evidentiary state.
3. Retain and review one bounded Layer 4 → E01–E08 operator run.
4. Run Layer 6 editorial decisioning on that evidence, with an explicit human review.
5. Add a manual watchlist cycle before any scheduler.
6. Promote to an internal pilot only after a clean independent review; start
   Layer 8 only when sustained multi-user use is actually required.

## Non-claims and blockers

- The owner decision applies only to the selected Eurostat asset; it is not a
  reusable blanket license for the portfolio.
- The supplied XLSX passed local structural, schema, temporal and numerical
  validation. Runtime source admission, independent provenance review and
  operational acceptance remain incomplete.
- No layer authorizes network scraping, automatic publication, production
  identity or global Block 1 acceptance.
