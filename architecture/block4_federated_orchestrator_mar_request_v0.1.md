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

## Evidence available

The bounded SUT has positive progression/recovery coverage and adversarial
vectors for altered signatures/journals, expiry, contradiction, lineage
substitution, identity collision and retry exhaustion. It has no external
adapter, common KMS, real-source handoff, independent review or production
authority. The only recommended decision today is acceptance or rejection of
the laboratory contract boundary; all production adapters remain blocked.
