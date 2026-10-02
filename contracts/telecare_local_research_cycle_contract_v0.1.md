# Telecare local research cycle v0.1

Status: CANDIDATE / LABORATORY_INTERNAL_SUPERVISED / MAR REQUIRED.
Producer/owner: Block 4 scheduling. Semantic producers: Block 1 comparison and
need assessment. Consumer: local operations view and next research cycle.

When a running cycle receives a current dossier, it derives its existing tasks
and examines distinct-root candidates already admitted in the local inventory.
Tasks with an unavailable original source cannot produce a new evaluation.
Each attempt re-exports both sides and binds IDs, evidence IDs, source hashes,
expiry, requirement fingerprint, comparison and per-need assessment. Recheck
before commit; changed or expired material produces no result from the attempt.

No candidate is a valid `WAITING_LOCAL_EVIDENCE` observation about the inventory
snapshot, not an exhaustive search of the world. A linked result is
`INSUFFICIENT`, `MEASUREMENT_DISAGREEMENT` or `REVIEW_REQUIRED`. All results keep
resolution `NOT_RESOLVED`, acceptance `NOT_ACCEPTED`, publication `BLOCKED`.
Scheduling never modifies the task state, manual link, reviewer decision,
dossier, output, source approval or delivery authority.

The attempt budget is an integer 1–32, default 8. A persistent round-robin
cursor covers tasks/candidates beyond one batch. Results have deterministic
IDs excluding wall-clock observation time; repeated input does not append a
duplicate. Append result and task head in one SQLite transaction, then advance
the batch cursor. Interruption before the cursor is recoverable by replay.
New source versions/requirements produce new identity.
The head is a lookup hint; reads recompute and compare the result with current
producer inputs. Unavailable/changed results show `STALE_OR_REVOKED` with no
retained verdict presented as current. Reads do not write history.

Pause/STOP preclude automatic writes. If STOP is observed before an attempt's
commit, its evaluation/head are not committed and the cursor does not advance.
Already committed observations remain historical. Corrupt journals stop
under the existing integrity policy. An unavailable candidate may be skipped
without starving another current pair. Budget and cursor are scheduling
mechanisms only, not a production retry/availability guarantee.

Compatibility: new journal kinds `RESEARCH_EVALUATION`, `RESEARCH_HEAD` and
cursor `research` are additive. Legacy tasks and manual links remain readable;
no migration of their authority. Backups include these records through the
existing operations SQLite snapshot. The local seal retains the existing
privileged rollback limitation.
The task head is the latest attempted successful observation, not an aggregate
verdict across all candidates. Earlier observations remain in the journal;
none of them permits task closure or acceptance.

Validation requires actual local source-to-dossier progression, empty search,
same-root rejection, stale/tampered/change-during-evaluation, restart/replay,
budget fairness, pause/STOP, forged result rejection, read-only snapshots and
backup/restore. No source gap closes from this cycle. External acquisition and
substantive task resolution require separately accepted source-specific ports.
