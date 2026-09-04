# Engine Layer Rules

Inherits the root and architecture `AGENTS.md` rules.

## Engine model

Treat each engine as: `ENGINE → CONTRACT → IMPLEMENTATION → TESTS → EVIDENCE → INTEGRATION → GATE`.

Maintain its dependencies explicitly. Do not optimize a single engine in a way that violates an accepted common contract or creates cross-engine inconsistency.

## Required engine dossier

Before implementing or modifying an engine, identify and record:

- purpose and owned semantics
- inputs, outputs, interfaces, and dependencies
- preconditions, postconditions, invariants, and authority boundary
- state model, error/failure/recovery behavior, observability, and rollback needs
- designed, bound, implemented, executed, validated, integrated, and accepted states separately
- required tests, evidence, red-team attacks, gate linkage, and unresolved contradictions

## Promotion discipline

- Engine-local success is not common-architecture or project-gate acceptance.
- An engine may emit a typed result, constraint, or observation, but cannot silently reinterpret it as global authority or runtime enforcement proof.
- Contract impact, ownership ambiguity, or multi-engine consequences require Master Architecture Review before local promotion.
- Preserve `UNKNOWN` when required runtime, integration, or independent evidence is absent.

## Implementation boundary

Do not begin implementation merely because an engine design is detailed. Confirm that the relevant gate and authority permit it, and keep design, executable fixture, bounded SUT, actual runtime, and validation evidence distinct.
