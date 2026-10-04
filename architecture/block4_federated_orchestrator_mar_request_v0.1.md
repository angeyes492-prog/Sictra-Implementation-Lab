# Master Architecture Review Request — Block 4 Federation

Date: 2026-09-12. Status: `OPEN / NO PROMOTION`.

## Candidate change

Block 4 now provides a local HMAC-attested journal and Command Center for
typed, supervised coordination of Block 1 → Block 2 → Block 3 cases. It
introduces common case/run/evidence/dossier identity and a bounded state machine
that stops at `HUMAN_REVIEW_REQUIRED`.

## Decisions still requiring human architecture authority

1. Ownership/versioning and migration policy for the federated contract.
2. Whether a verified Block 1 store may produce signed exports for Block 4,
   and the identity/key boundary for that adapter.
3. Which Block 2 and Block 3 outputs count as executable receipts rather than
   the current local coordination records.
4. Tenancy, reviewer identity, retention, secret management, backup and
   restoration requirements for any sustained operation.
5. Scheduler budget, retry policy, incident/kill-switch ownership and
   production observability.
6. Conditions under which a human review receipt can be authenticated without
   turning it into publication, delivery or global gate acceptance.
7. Whether the candidate local evidence-task link/reassessment contract may
   become a shared cross-block contract. The current local reviewer identifier
   is self-declared; even a request for Block 1 reassessment cannot close a
   source gap, accept content, or establish corroboration.
8. Whether the new Block 1 comparison projection can become a shared
   measurement contract. It compares only exact typed metric, unit, geography
   and period without resolving any task. The two currently admitted source
   types have no shared metric. New metric mapping or tolerance, if needed,
   requires source-specific evidence and an explicit architectural decision.
9. Whether Block 1's candidate per-need read-only assessment can become a
   shared cross-block contract. Its insufficient/disagreement/review verdicts
   guide research, but never resolve a task or promote a dossier; source-specific
   acceptance semantics and independently validated comparable inputs are
   still absent.
10. Whether the candidate twelve-arista composition and bounded local research
    cycle may become accepted cross-block interfaces. Block 4 only schedules
    current admitted dossiers and journals Block 1 comparisons/assessments;
    its automatic search cannot close a task, mint approval, infer causal
    intelligence, or activate network acquisition/delivery. Review ownership,
    budget, retention, migration and source-specific resolution separately.
11. Owner exception dated 2026-10-03 permits agent-assisted official public
    research collection. The standalone candidate acquisition/quarantine and
    exact methodology-review contracts do not activate B4 networking or source
    admission. Before a runtime consumer adopts them, review recipe ownership,
    verified endpoints/terms, per-cycle budgets, DNS/TLS isolation, quarantine
    retention/recovery, approval/binding lineage and compatibility. A collected
    metadata document is not an attested measurement or a resolved need. No
    installed activation or shared-contract acceptance is inferred from the
    owner research exception or local tests.
    The subsequent fixed Belgium 2023-2024 statistical recipe/JSON-stat
    inspection preserves the same quarantine boundary. Query validation,
    category position, missingness, flags and publisher update parsing are
    technical inputs, not runtime adoption, corroboration or source approval.

12. Candidate statistical admission bridge v0.1 introduces the explicit scope
    BLOCK1_EUROSTAT_STATISTICS_BE_2023_2024 and a distinct statistical media
    type. It requires exact current terms/methodology lineage and separately
    supplied signed source control; the legacy XLSX approval cannot authorize
    it. Consumer verification recomputes content/lineage independently of the
    producer signature, with read-time expiry/rotation checks. Review scope,
    format compatibility, exclusive binding expiry, retention and the required
    dedicated consumer before adoption. The actual prepared review remains
    PENDING / NOT_ADMITTED; fixture authority is not a real reviewer decision.
    No accepted shared contract, existing pipeline migration or installed
    runtime effect follows from this candidate port.
    The subsequent dedicated statistical retention facade reuses the existing
    evidence-store HMAC/atomic-write primitive without relaxing XLSX validation.
    Review its publisher-time head/ambiguity policy, format-specific history,
    full current consumer verification, memoized historical reconstruction and
    external checkpoint custody. It requires a trusted control-head checkpoint
    and an external history checkpoint on reopening. Known signed heads cannot
    be rolled back, but authentic custody cannot be inferred from a hash read
    from the restored file itself. Original keys/quarantine/control are required
    for data-only recovery. No installed backup/scheduler adoption, independent
    custody validation or acceptance follows from the fixture tests.

## Evidence available

The bounded SUT has positive progression/recovery coverage and adversarial
vectors for altered signatures/journals, expiry, contradiction, lineage
substitution, identity collision and retry exhaustion. It has no external
adapter, common KMS, real-source handoff, independent review or production
authority. The only recommended decision today is acceptance or rejection of
the laboratory contract boundary; all production adapters remain blocked.
