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
| 4. Evidence ledger | Preserve provenance and transformations for every admitted observation. | A temporary durable control record rebuilt the gateway and emitted one local attestation; attested evidence is not yet retained. | Signed binding, gateway attestation and immutable local record link file hash, filters and mapping. | Durable encrypted store, audit trail, retention and restore exercise. |
| 5. Intelligence runtime | Form research questions, detect changes, contradictions and bounded insights. | E01–E08 completed one ephemeral local-reference run from the supplied workbook; no durable operational source. | A durably bound real-source run produces facts, interpretations and uncertainties separately. | Load/performance SLOs and continuous regression with real anonymised cases. |
| 6. Editorial decisioning | Select only relevant, attributable insight candidates and hand off to Design. | Bounded editorial engine runs on fixtures. | One reviewed brief links every statement to evidence and abstains when weak. | Approval workflow, versioned outputs and publishing audit trail. |
| 7. Watchlists and cadence | Recheck approved sources and surface meaningful change without noise. | Atomic manual cycle persists checkpoints and recomputable deltas; no scheduler or attested checkpoint. | Defined cadence and a manually triggered, attested delta report for one source. | Budgeted workers, rate limits, change detection, alerts, kill switch and incident runbook. |
| 8. Operating plane | Make the system safe for multiple people and sustained use. | Local single-user service only. | Named operator, documented local backup and access boundary. | SSO/RBAC, tenancy, secret manager, deployment controls, observability, backups, security review and disaster recovery. |

## Required order

1. Bind the already approved Eurostat scope locally.
2. Assemble one explicitly selected Layer 3 result without changing its non-evidentiary state.
3. Bind, attest and durably persist one evidence bundle under Layer 4.
4. Run Layers 5 and 6 on that evidence, with an explicit human review.
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
