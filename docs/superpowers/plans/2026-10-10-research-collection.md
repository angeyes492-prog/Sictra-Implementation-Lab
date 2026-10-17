# Finite research collection implementation plan

Goal: replace seven manual acquisition commands and copied IDs with a finite,
restart-safe candidate collection and exact offline selection.
Architecture: compose existing pinned acquisitions and read-only reviews; share
one budget; seal selection only after current-byte verification.
Tech stack: Python standard library, unittest, existing quarantine/recovery helpers.
Spec: contracts/block1_research_collection_contract_v0.1.md.

## Global constraints

Single backlog remains closure/closure_execution_queue_v0.1.md. No installed
runtime acquisition, admission, causal inference, promotion or publication.
Owner waived procedural approval checkpoints, not evidence requirements.

## Review Focus

Cross-publisher budgets, failed-cycle restart, selection/rights substitution,
clock drift during acquisition and handoff, resealed forged reports, filesystem
links and failure cleanup, raw-source parser failures, acquisition vs admission.

## Task 1 — Collect a bounded exact source closure

Write positive and denial/budget/restart tests; observe RED. Compose real collectors
with only transport/DNS substituted in tests. Shared counters and durable cycle
marker precede requests. Focused command: python -m unittest discover -s tests
-p test_research_collection.py -v. Observe GREEN.

## Task 2 — Reopen and fence offline selection

Write RED tamper/expiry/forgery and offline tests; implement bounded immutable
selection and read/verify/CLI. Observe GREEN; verify one real permitted cycle,
formal guard model, fresh final review, serial full regression, commit/push and
exact-SHA CI. Record material delta and remaining limits in canonical ledger.
