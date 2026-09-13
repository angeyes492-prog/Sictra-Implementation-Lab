# Contract — Attested evidence to runtime bridge v0.1

Version `0.1`; producer/consumer:
`sictra_block1.attested_runtime_bridge.AttestedRuntimeBridge`. Scope:
`BLOCK1_LOCAL_ATTESTED_RUNTIME_BRIDGE`. Authority: bounded selection and
handoff of current locally at-tested evidence; no authority to create,
reinterpret, approve or promote evidence.

`run` requires non-empty string task ID, run ID and objective; a non-negative
integer `now`; and the runtime authority object required by the underlying
runtime. Before it can call E01, the bridge obtains a current evidence list and
receipt history from its evidence store. It filters the history to exactly the
`CURRENT` receipt subset, then rejects an empty list, a count mismatch between
that subset and the current evidence list, or a mismatch between `now` and the
runtime's trusted clock. Expired retained releases remain available for
lineage, but never enter runtime input or block a newer current release. It
passes precisely that current evidence list to `IntelligenceRuntime.run`.

The returned result has the runtime envelope and a tuple of defensive receipt
copies. Compatibility is exact for v0.1 store receipts and the existing
runtime source schema. The bridge does not turn `SOURCE_VERIFIED` into a truth
claim, independent corroboration, editorial approval, production identity or
global gate acceptance.
