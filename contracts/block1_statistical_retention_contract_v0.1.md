# Statistical retention consumer v0.1

Status CANDIDATE / MAR REQUIRED / LABORATORY_INTERNAL_SUPERVISED.
Producer/consumer: sictra_block1.statistical_retention.StatisticalEvidenceStore.
Dependencies: research_admission, current quarantine and signed source control,
and the existing AttestedEvidenceStore history/atomic-write primitive.
No installed-runtime adoption, shared acceptance or automatic source approval.

## Objective and inputs

Retain a statistical admission packet, recover it after restart and select its
exact identity only while current. Configuration requires a distinct store
path outside quarantine and source-control files, trusted evidence keys, a
separate >=32-byte integrity key, a trusted integer clock, freshness 0..86400
seconds and capacity 1..1000. Scope/claim are the exact admission bridge scope;
the existing XLSX store/validator is not widened or migrated.
The caller must also supply a trusted source-control history-head checkpoint.
Reopening an existing evidence file requires its externally retained history
checkpoint; loss of that file while a checkpoint exists cannot create a new
genesis. Each verified chain must contain the expected head or a descendant.
The live facade remembers newly observed signed heads and rejects subsequent
truncation/rollback, even when the restored older file has valid signatures.
checkpoint() returns the last observed public head hashes without reading or
claiming currentness; the caller must preserve them outside the data backup.
Do not derive a trusted recovery checkpoint from the very restored file being
challenged. Without external custody, fresh-start offline rollback remains
unproven, and installed activation must not be accepted on this mechanism.

When retain is called, verify the source signature and exact current raw data,
metadata, terms, reviewed scope and binding with research_admission. Persist
using the existing HMAC chain, config check, fsync and atomic replacement.
The record's signed admission time proves historical verification, not current
use. A slow write can retain valid admission-time history but must return
NOT_CURRENT rather than CURRENT after dependencies expire or authority changes.
Exact replay never appends; malformed, unapproved or signed forged packets
cannot enter the store. Capacity and monotonic admission time remain enforced.

## History versus controlled current selection

Every load verifies the chain and reconstructs each packet from its retained
dependencies at its integrity-protected admission time. Historical verification
may use that time internally; public APIs never accept a caller-supplied past
time. Missing/altered dependency or chain bytes fail closed; history requires
the original quarantine, source-control artifacts and separate original keys.
Full historical parsing/signature reconstruction may be memoized by the exact
packet, admission time, freshly rehashed dependency descriptors and verified
source-control history. Cache size is bounded by store capacity; it is never
persisted, never skips fresh byte/hash/chain checks and never authorizes current
selection. Current admission verification is not cached.

history returns receipts, not usable stale source bodies. select(evidence_id)
returns a defensive copy only for the current exact head; no implicit selection
by arbitrary path, source name, age override or list index. Current checks use
the configured clock and the dedicated independent admission verifier.
Superseded/expired source authority cannot be reinstated by replay or fallback.

Collection time is not release order. The candidate head is the greatest
timezone-aware publisher update normalized to UTC across retained history.
An unordered publisher timestamp withholds selection rather than assigning a
timezone. Different raw data hashes at the same greatest update are ambiguous
and withhold selection, even if only one is fresh. For the same release/hash,
only its latest collection may be selected; among equivalent certificates at
that collection, choose the last admission then deterministic evidence ID.
An expired or unapproved latest head cannot fall back to older evidence.
These are conservative candidate selection rules, not an explanation of a
statistical revision, source truth or independent corroboration.

Re-read history and current dependencies after slow reads; changed/expired
reads yield no selected result. Receipts explicitly distinguish CURRENT and
NOT_CURRENT and retain reason, raw candidate identity, binding, expiry,
publisher time, admission time and history hash. No receipt resolves a need.

## Recovery, effects and closure

Injected pre-replace OSError preserves the previous file and permits retry;
restart/replay preserves identities without duplicate records. Data-only
recovery restores history, quarantine and source control under original keys;
wrong keys, tampered content, missing dependencies or substituted old authority
cannot enable current selection relative to the supplied/observed checkpoints.
No secrets are persisted. Single-process
locking is inherited; cross-process writers, encryption/KMS, deletion and
installed backup integration remain out of scope and require review.

Runtime effect NONE; publication BLOCKED; resolution NOT_RESOLVED. No E01-E08,
dossier, scheduler, UI, delivery or network adapter consumes this port yet.
Rollback removes the facade; retained candidate files remain unreadable to the
legacy XLSX consumer. Positive oracle uses stated values and retained bytes;
adversarial closure requires tamper, expiry/rotation, ambiguity/no fallback,
failure injection, replay/restart, key/format isolation and data-only restore.
