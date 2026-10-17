# Finite official research collection — candidate contract v0.1

Status: CANDIDATE implementation contract, not architecture or gate promotion.
Scope: agent-operated LABORATORY_INTERNAL_SUPERVISED research. Depends on the
existing Eurostat/Statbel acquisition, read-only review and quarantine contracts.

One explicit new cycle root obtains the seven already specified recipes: Eurostat
reuse notice, general/national/regional maritime methodology, fixed Belgian
2023–2024 statistics; Statbel reuse notice and sea transport page. Rights precede
dependent data. Both collectors share the same request/byte budget; no retries,
new endpoints, arbitrary queries, runtime scheduler or activation are introduced.
The existing stricter timeout, per-file, public-IP and publisher constraints apply.

Write an exclusive cycle-start marker before requesting anything. A root cannot
silently restart a spent or failed cycle, including across process restart. Retain
partial candidates on failure, persist budget/error outcome, and never publish a
complete selection on failure. A successful selection is immutable and identified
by SHA-256 of its exact canonical manifest, with all seven IDs and byte hashes,
original freshness boundaries and the accumulated budget. No latest-file selection.
Public reading also requires the exact matching durable COLLECTED cycle outcome;
published directories left by interruption or failed cleanup remain unusable.
Failure outcomes retain the exact identities of candidates already collected,
failed recipe and exception kind, including malformed HTTP and HTML parser faults.
Safe errno/Windows error codes are recorded without copying potentially private
exception messages. JSON handoff must preserve original Unicode even through a
legacy Windows pipe; ASCII JSON escapes are a lossless representation.

Offline reading requires an explicit existing root and selection ID, validates
exact schema/recipe/terms/hash closure, rejects links/junctions and bounded-file
violations, and recomputes both existing reviews from originals. Reject clock
rollback, expiry, changed inputs and forged/resealed report conclusions at final
handoff. New capture timestamps are not publisher revisions or independent roots.

Output remains NOT_ADMITTED / NOT_RESOLVED / NOT_ACCEPTED, runtime effect NONE,
publication BLOCKED. Arithmetic discrepancy has no inferred cause. Source admission,
attestation, semantic resolution, independent acceptance and installation are not
part of this change. Failure leaves originals recoverable; unpublished staging may
be removed only under the validated cycle root.

Observable closure: one call retains seven rights-linked originals and yields the
independently stated numeric gaps; offline reopen has zero requests; denial,
shared-budget exhaustion, tamper, expiry and restart do not produce a usable
selection or promoted result. Full regression and exact-SHA CI are required.
