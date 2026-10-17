# Statistical watchlist and fact projection v0.1

Status CANDIDATE / MAR REQUIRED / LABORATORY_INTERNAL_SUPERVISED.
Producer/consumer: sictra_block1.statistical_watchlist.StatisticalWatchlist.
Dependency: trusted configured StatisticalEvidenceStore, its current selection
and checkpoint-bound verified history. No new key, journal or approval plane.

## Observable objective and boundary

Read retained statistical releases and produce a deterministic watchlist/fact
projection. It must distinguish NO_CHANGE, CHANGE_DETECTED, INSUFFICIENT_EVIDENCE
and REVIEW_REQUIRED without deriving cause or resolving an Intelligence need.
This candidate integrates the distinct JSON-stat admission/retention path;
it does not pretend its content is an XLSX manual bundle or an accepted
IntelligenceDossierStore input. E01-E08/B4/UI adoption remains a separate review.

read() obtains a verified current-head/history snapshot, compiles the projection,
then re-reads and compares the entire snapshot and public custody checkpoints.
Changed/expired/rotated input yields no projection. Return expiry is the earliest
current dependency/binding boundary or configured evidence freshness boundary.
No caller may override time or provide unverified source dictionaries.

## Comparison and literal facts

The current release must be the uniquely current head selected by the existing
statistical store. No current source means no measurement facts: insufficient
fresh/admissible data yields INSUFFICIENT_EVIDENCE; ambiguous/unordered publisher
identity yields REVIEW_REQUIRED. Reasons remain explicit, not a successful empty
read or an implicit fallback to historical content.

Baseline selection is the greatest strictly earlier timezone-aware publisher
instant. Same-instant different raw hashes at that baseline require review,
not arbitrary selection. Equivalent copies use newest collection/admission/ID
as the existing retention selector does. A single release is insufficient for
change comparison; repeated collection of its exact raw hash is NO_CHANGE /
SAME_RELEASE_RECOLLECTED, not two independent publications or corroboration.

Compare only exact scope/dataset/metric/unit/frequency/geography/period grain.
Never subtract 2023 from 2024 or tonnes from money. Rows keep their explicit
missing bit and raw flag. Classify observed->observed unequal value as
VALUE_CHANGED, equal value/different flag as FLAG_CHANGED, missing->observed
as OBSERVATION_AVAILABLE, observed->missing as OBSERVATION_UNAVAILABLE, and
two missing cells with changed flags as MISSING_FLAG_CHANGED. Arithmetic exists
only when both values are observed; missing/coverage changes have delta null.
Before/after flags are retained even when value and flag change together.

Old baseline data is HISTORICAL_CONTEXT_ONLY, verified at its original signed
admission time; expiry or supersession does not become current authority again.
It cannot contribute a current source, independent root, engine effect or
editorial readiness. This historical comparison policy requires MAR before
runtime adoption. Current source authority/dependencies must remain valid.

Projection facts enumerate only observed current publisher measurements with
exact evidence/period/unit/source lineage. Comparison changes are separate
derived literal observations, not causal facts. Missing cells are uncertainty,
never zero. Certainty UNCONFIRMED / confidence C for publisher claims; no truth
or independent validation is inferred from signatures or arithmetic.

## Dossier separation, verification and recovery

Keep facts, evidence references, comparison, interpretations, hypotheses,
uncertainty, contradictions, limitations, affected scope, executive questions
and next-data needs separate. Interpretations/hypotheses remain empty, source
corroboration INSUFFICIENT EVIDENCE, resolution NOT_RESOLVED, editorial state
RESEARCH_NEEDED, runtime NONE, publication BLOCKED, acceptance NOT_ACCEPTED.
Generic revision-policy metadata never explains a particular value change.

Projection/fact identity derives from exact verified inputs, not wall-clock
activity. Source history is already durable; this view adds no second journal.
Restart and data-only recovery under original keys/external checkpoints reproduce
the same projection while current. The projection itself is NOT_PERSISTED and
is not an accepted/federated dossier or an attested source.

verify_projection(report) recomputes from current retained inputs and requires
exact canonical JSON equality, not Python numeric/custom equality, a
self-supplied hash or producer conclusion. A rehashed
forgery, altered value/lineage/limits, false resolution or stale projection fails.
Recomputation proves local equivalence, not independent source truth/semantics;
tests also use independently stated values and classification reference cases.
Rollback removes this read-only consumer, preserving source history unchanged.
