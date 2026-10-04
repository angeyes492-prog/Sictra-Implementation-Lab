# Statistical review dossier and candidate archive v0.1

Status CANDIDATE / MAR REQUIRED / LABORATORY_INTERNAL_SUPERVISED.
Producer: B1 StatisticalDossierProducer. Persistence owner: B4
StatisticalReviewArchive, using an injected existing OperationsStore.

Observable closure: current checkpoint-verified statistical input produces an
epistemically separated dossier, stored and recovered without duplicate writes.
Rehashed, signed-but-forged, stale, superseded or changed content cannot be read
as current. No new approval, key, journal implementation or installed route.

The producer accepts only a configured StatisticalWatchlist, never arbitrary
source dictionaries. It recomputes/verifies the projection and binds its exact
ID, custody checkpoints, current/historical evidence refs, facts, comparison,
uncertainty, contradictions, limits, scope, questions and next-data needs.
Interpretations/hypotheses stay empty, certainty UNCONFIRMED / C, resolution
NOT_RESOLVED, editorial RESEARCH_NEEDED, runtime NONE, publication BLOCKED,
acceptance NOT_ACCEPTED. Missing observations remain uncertainties. Existing
admission rejects an all-missing release before it can produce a dossier.
Storage changes no source truth or substantive interpretation semantics.
Producer reads capture trusted time before composition and reject a final
time earlier than that start, including rollback after source verification.
The editorial view applies the same start/final monotonicity fence after its
last dossier verification; an expiry-only comparison is insufficient.

editorial_candidate() rechecks the dossier before and after the existing
editorial engine assessment. It preserves literal current publisher measurements
and exact dossier/evidence/expiry lineage, counts only the one Eurostat root
(historical releases add no root), and must assess RESEARCH_NEEDED / BLOCKED.
Numeric profile fields use conservative zero utility and maximum uncertainty,
not measured quality or an accepted scoring rubric. Cause, business/account
impact and interpretations remain unspecified. No selection, handoff or
publication effect. Changed/expired evidence during assessment rejects.

B4 records one additive STATISTICAL_REVIEW_DOSSIER kind on the existing SQLite
HMAC chain. A dossier identity is the hash of exact canonical content, excluding
recording time. record() takes no caller payload/time; trusted source clocks and
STOP callback govern writes. A bounded 1–100 identity capacity permits replay
at capacity. Source bytes/authority are rechecked before and after append in
the transaction. A failure, observed STOP, expiry or changed projection before
commit rolls back the attempt. Concurrent source changes after the final check
are not an atomic cross-file transaction: any such record is historical only;
read() always recomputes current source content before exposing a dossier.
The recording receipt contains identity/state only and is not source attestation.

Read requires a verified operations journal, exact record schema/identity and
non-future recording time, two current producer checks, unchanged journal record
and a final expiry/clock fence. Journal integrity alone never authorizes facts.
Unavailable IDs and superseded/expired dossiers reject, without history writes.
No mutable latest-head authority is introduced. Normal operations backup includes
the record; source history, quarantine, original keys and externally held source
checkpoints are still needed for a current recovered read. Restoring the archive
alone cannot revive source validity. Existing privileged journal rollback limits
remain; this archive does not establish external custody.

Compatibility: legacy IntelligenceDossierStore, its bridge and E01–E08/B2/B3
formats are unchanged and reject this distinct candidate. Standalone explicit
calls are tested; scheduler, HTTP/UI, signed federation and accepted editorial
adoption require their own contract/MAR. Rollback removes these two
consumers and ignores the additive journal kind, preserving prior source/state.

Validate positive literal values/separation, mixed missing/observed data,
all-missing admission rejection, restart/replay,
backup recovery, no-current/expired input, same-ID forged content (including
numeric type changes), source substitution/rotation/release change, STOP,
partial append/commit rollback, clock regression, capacity and journal tamper.
