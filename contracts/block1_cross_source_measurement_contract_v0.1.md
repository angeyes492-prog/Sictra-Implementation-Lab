# Block 1 cross-source measurement comparison v0.1

Status: CANDIDATE / LABORATORY_INTERNAL_SUPERVISED / MAR REQUIRED.
Producer: Block 1 `evidence_comparison`. Consumer: Block 4 evidence-task view.

## Purpose and authority

Compare two currently exportable, separately rooted Block 1 dossiers before a
local operator spends time on a candidate evidence link. The caller must verify
each signed producer package, exact dossier ID, source hash, currentness and
expiry at use time. This pure comparison has no source approval, task-resolution,
corroboration, interpretation, publication or delivery authority.

## Accepted measurements and result

Version 1 recognizes only maritime freight in thousand tonnes by geo code and
calendar year, and Honduras customs CIF import value in USD millions by customs
point and quarter. A match requires the same metric, unit, geographic key and
period, plus different root source identities. No conversions, geographic
inference, keyword matching or tolerance are assumed. Duplicate measurement
keys, missing provenance, unsupported or nonfinite values reject.

The output retains dossier IDs, source roots, matched fact IDs and literal
after-values, unmatched primary facts, explicit scope status and boundaries:
`NO_SHARED_MEASUREMENT`, `PARTIAL_COVERAGE_REVIEW_REQUIRED`,
`VALUE_DIFFERENCE_REVIEW_REQUIRED`, or `EXACT_VALUE_AGREEMENT_REVIEW_REQUIRED`.
Equality of two reported values is a comparison result, not independent truth.
Different values require review; they are not automatically a causal or source
contradiction. Every result is `NOT_RESOLVED`, `BLOCKED`, and `NOT_ACCEPTED`.

For existing task links lacking the comparison field, read-side revalidation
continues under the v0.1 task-link contract; the field is computed for new
links without rewriting history. On replay, changed evidence or comparison
rejects. An unavailable, expired or tampered producer is not comparable.

## Validation and recovery

Positive exact-scope fixture and negative metric/unit, geography, period,
duplicate, nonfinite, same-root and stale/tampered producer tests are required.
Block 4 may display this result but cannot close a need or promote a dossier.
Future new metrics require a versioned contract and Master Architecture Review.
