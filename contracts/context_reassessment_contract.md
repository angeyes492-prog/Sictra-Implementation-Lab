# Context → Reassessment Contract v0.1

**Scope:** Local bounded SICTrA Block 1 execution slice.

## Producer and consumer

- Producer: Context assembly
- Consumer: Independent reassessment
- Authority: This contract has no promotion authority.

## Immutable provenance payload

Every record must retain `source_identity`, `root_provenance`,
`derivation_graph`, `temporal_scope`, and `evidence_class`. Transformations may
select records but may not merge, replace, or rewrite these fields.

## Selection

The current pack contains only records that match the target agent, are
selectable, current, and not explicitly out of scope or blocked. Open
contradictions remain visible; selection is not resolution.

## Reassessment

Independent evidence count is the number of distinct admissible observed root
sources, never record count. Synthetic, adversarial, and derived records are
not runtime evidence. A local result is never a global gate promotion.

## Known non-claims

This contract does not prove external runtime behavior, CI execution,
cross-engine integration, or global acceptance.
