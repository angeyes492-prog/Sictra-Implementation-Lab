# Candidate contract — literal change context v0.1

Producer: Block 1 `change_context`; consumer: Block 4 read-only operations
view. Scope: `LOCAL_LITERAL_CHANGE_CONTEXT`. Shared acceptance requires MAR.
Version `0.1.0`; this is not a replacement for a retained dossier contract.

The pure projection accepts the two existing, blocked, uninterpreted dossier
schemas only, with unique fact IDs, source/delta identity, finite nonnegative
measurements and fact-to-source hash lineage. It does not attest an arbitrary
dictionary. The consumer must obtain it from the integrity-verified producer,
validate the current signed package, bind ID/hash, then recheck the identical
package and dossier and exact expiry immediately before returning the view.

Each fact produces exactly one literal context:

- Eurostat `VALUE_CHANGED`: `SAME_PERIOD_REPORTED_VALUE_CHANGE`;
- Eurostat added/removed observation: `OBSERVATION_COVERAGE_ADDED`/`REMOVED`;
- Eurostat flags only: `SAME_PERIOD_STATUS_FLAG_CHANGE`;
- HN customs: `DISTINCT_PERIOD_VALUE_COMPARISON`, with ordered Q1 periods.

An observation coverage change is not proof of changed statistical methodology.
A reported-value change is not proof of statistical revision or operational
change. Cause remains `UNCONFIRMED`, resolution `NOT_RESOLVED`, acceptance
`NOT_ACCEPTED`, publication `BLOCKED`. No fact, task, stored artifact, gate,
interpretation or hypothesis is modified.

Unknown schema/source/change type, ambiguous nulls, inconsistent values/delta,
unchanged values advertised as a value change, malformed periods, duplicate
facts, broken lineage or authority escape reject. Stale, altered, unavailable
or changing input yields no context in the operations view. Existing journals
remain unchanged; the new nullable field is additive. Rollback omits the field
without rewriting old events. Read errors do not stop unrelated current sources.

Evidence: independent literal fixture expectations plus real local retained
Eurostat/HN pipeline integration, expiry/tamper/change-during-read and replay
tests. This proves classification and rejection, not real-world causality,
source approval, editorial quality, task closure or product completion.
