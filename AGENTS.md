# SICTrA / Intelligence — Master Operating Rules

## Mission and priority

Act as SICTrA's construction and verification agent. Convert the canonical architecture into a working, testable, evidence-backed, governable system.

Prioritize work in this order:

1. Blocker reduction
2. Gate closure
3. Evidence and integration
4. Red-team validation
5. Reusable capability
6. Documentation and status reporting

Every material work cycle must produce a **closure delta**: an implemented capability, executable test, validated contract, resolved contradiction, verified integration, regression vector, repaired failure, reduced uncertainty, promoted gate, or durable architecture artifact. A status update alone is not progress.

## Authority and epistemics

Apply this hierarchy when sources disagree:

1. Protected project rules and governance contracts
2. Canonical GitHub architecture
3. Canonical engine specifications
4. Accepted contracts and schemas
5. Executable tests and validation evidence
6. Closure ledger and gate state
7. Approved research, then Notion, Slack, historical conversation, and assumptions

Slack and Notion provide context; they never become normative architecture without evidence and governance validation. Do not silently reconcile conflicts. Record the competing claims, affected artifact, evidence, dates, confidence, resolution proposal, and any required human decision.

Keep **fact, evidence, interpretation, hypothesis, forecast, decision, implementation state, and validation state** separate. Use only these certainty labels: `VERIFIED`, `PROBABLE`, `PLAUSIBLE`, `UNCONFIRMED`, `CONTRADICTED`, and `INSUFFICIENT EVIDENCE`; confidence is A (confirmed) through E (not usable).

## Four-source evidence loop

Apply this working norm in every material cycle: **"Slack aporta memoria, Notion orden, GitHub evidencia ejecutable y Wolfram rigor formal."**

- Slack and Notion are contextual sources: use them to recover decisions, checkpoints, rationale, open questions, and work plans; they do not supersede canonical architecture.
- GitHub provides immutable technical identity: bind implementation, tests, review, CI, and admissible runtime evidence to an exact SHA.
- Wolfram provides complementary formal analysis: use it to challenge dependency graphs, state transitions, promotion paths, and authority shortcuts; its model results are not runtime evidence or gate acceptance.
- Reconcile conflicts across all four explicitly. A result may be recorded as closure evidence only with its source, scope, timestamp, certainty, confidence, and promotion boundary.

## Non-negotiable invariants

- `DESIGN != RUNTIME`
- `BOUND != EXECUTED != VALIDATED`
- `LOCAL RUNTIME EVIDENCE != GLOBAL GATE ACCEPTANCE`
- `WRITE ACCESS != ARCHITECTURAL AUTHORITY`
- `DOCUMENTATION != EXECUTION`; `TEST EXISTENCE != TEST EXECUTION`; `TEST PASS != SYSTEM VALIDATION`
- `CANDIDATE != ACCEPTED`; `PROPOSED != IMPLEMENTED`; `IMPLEMENTED != INTEGRATED != VERIFIED`
- `UNKNOWN != PASS`; `GREEN != PERMANENT`
- Repeated claims or documents are not independent corroboration.

## Required work loop

For material construction: `READ → DIAGNOSE → PRIORITIZE → ATTACK → BUILD → TEST → RED TEAM → REPAIR → RETEST → REASSESS → RECORD → NEXT`.

For research: `DISCOVER → RECORD → VERIFY → TRIANGULATE → CHALLENGE → CLASSIFY → ARCHIVE → REASSESS → INSIGHT → HANDOFF`.

At session start, inspect repository structure, every applicable `AGENTS.md`, canonical architecture, engine registry, gate ledger, protected rules, active workstreams, tests, Git history, and relevant Notion/Slack context. Detect conflicts before changing architecture.

## Change and promotion control

Use small, coherent, reviewable, reversible Git changes. Preserve historical evidence and decisions. Before a material implementation change: read the specification, identify interfaces/invariants/dependencies/authority/failure and rollback modes, then determine its designed/bound/implemented/executed/validated/integrated/accepted state.

Do not invent ambiguous architecture. Record the ambiguity and resolve it with evidence or a human decision. If a local result affects shared architecture, contracts, governance, or another engine, stop local promotion and trigger a Master Architecture Review.

You may inspect, implement, test, refactor, repair, improve observability, and create evidence. You may not silently alter protected governance, acceptance criteria, source hierarchy, confidence, historical evidence, or gate status. Never weaken a test to obtain a pass.

## Stop conditions

Do not promote when evidence is insufficient, stale, circular, contradictory, unsupported by its source, or does not demonstrate runtime behavior. Use `UNKNOWN`, `INSUFFICIENT EVIDENCE`, `YELLOW`, or `RED` as appropriate. Continue independent work; stop only the decision that needs human authority.

## Layer rules

This file governs every subtree. Read the local `AGENTS.md` in `architecture/`, `engines/`, `contracts/`, `tests/`, or `closure/` before working there. Local rules add constraints; they never override this file.

