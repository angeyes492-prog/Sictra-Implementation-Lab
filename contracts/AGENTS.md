# Contract Layer Rules

Inherits the root and architecture `AGENTS.md` rules.

## Contract-first discipline

Contracts are more authoritative than implementation convenience. Before implementation or a material contract change, validate:

- schema and types
- preconditions and postconditions
- invariants and state transitions
- ownership and authority boundaries
- error, retry, stale, degraded, recovery, and rejection semantics
- versioning, compatibility, and migration behavior
- observability and evidence requirements

## Change control

When implementation and contract disagree, do not silently edit either. Determine whether the implementation is wrong, the contract is obsolete, architecture changed, or evidence invalidated the contract; then record and resolve that result explicitly.

Every executable contract must declare version, producer/consumer identity, scope, authority, required lineage/provenance, accepted and rejected inputs, compatibility rules, and known non-claims. Undefined value semantics remain `UNSPECIFIED`; do not fabricate them to make a test pass.

## Validation

Validate each material contract with clean reference cases and adversarial mutations, including malformed data, identity substitution, lineage breakage, version mismatch, missing evidence, stale data, authority violation, and consumer rejection behavior where applicable. Contract conformance alone is not runtime validation or gate closure.
