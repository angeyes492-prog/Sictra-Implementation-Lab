# Supervised local intake worker — candidate

Scope: technical laboratory implementation, not production acceptance.
This worker invokes the real Block 1 Eurostat pipeline for explicitly queued
local workbooks. It does not execute Block 2/3, manufacture an editorial
interpretation, approve sources, download files or publish anything.

## Inputs and authority

Use an existing initialized and verified operator pipeline. Its retained source
approval, binding, freshness and schema checks remain authoritative. Supply a
separate inbox containing only explicitly selected XLSX files, a queue SQLite
path outside the inbox, and a separately provisioned 32-byte-or-longer queue key.
No startup command creates source approval or silently registers every inbox file.
Never place keys in the inbox or check them into Git.

All commands have this prefix (replace the example paths with configured local
paths; these are examples, not installed services):

```powershell
python -m sictra_block4_orchestrator.local_worker --queue C:/Telecare/state/jobs.sqlite --inbox C:/Telecare/inbox --pipeline C:/Telecare/pipeline --key-file C:/Telecare/secrets/worker.key status
```

Replace the final `status` with:

- `enqueue eurostat.xlsx --sha256 <exact SHA256>`: register those exact bytes
  and the requested geography selection, default COUNTRY.
- `run --max-jobs 4`: execute at most four queued jobs, stopping on review.
- `watch --cycles 12 --interval-seconds 5 --max-jobs 4`: bounded repeated
  processing of registered jobs, including jobs explicitly enqueued meanwhile.
- `pause` / `resume`: persist the dispatch control. Pause prevents the next
  claim; it does not interrupt an already executing pipeline.

At most 128 unique jobs and 2048 audit events fit in this candidate queue.
Single dispatch is enforced through a committed RUNNING claim. Another worker
cannot dispatch while a claim exists. Duplicate content and geography return
the same job ID; completed work is not blindly repeated after restart.

## Execution and recovery semantics

Hash and file boundaries are rechecked at dispatch. The verified bytes are staged
in a private temporary directory before invoking the actual pipeline, avoiding
an inbox read/execute race. A baseline is not a dossier; a changed release can
produce literal facts but the worker then stops at REVIEW_REQUIRED.

An exception may occur after upstream state changed. Such jobs become
REVIEW_REQUIRED, never an assertion that no side effects occurred. A process
crash leaves RUNNING; the next worker reports RECOVERY_REQUIRED instead of
replaying it. Both conditions stop later dispatch. Resume clears only pause,
not a failed job or a review requirement.

Recovery is deliberately manual in this slice: inspect the upstream attested
ledgers and the queue against the input hash. Do not edit the SQLite row, delete
the queue, or mark a job completed to clear the stop. An authenticated recovery
receipt/migration interface remains unfinished. The HMAC detects content
tampering, wrong keys and changed inbox/pipeline identity; it does not detect
replacement of the entire database by an older correctly signed backup.
External rollback anchors, complete job/database recovery and durable reviewer
identity remain required before sustained production operation.

## Command Center

The server accepts all four optional arguments together:
`--worker-queue`, `--worker-inbox`, `--worker-pipeline`, `--worker-key-file`.
Without them, it truthfully displays NOT_CONFIGURED.
The read-only /api/worker endpoint returns job IDs, hashes and states, never
paths, file contents or keys. AVAILABLE means the queue is readable, not that a
background runner is alive. A RUNNING claim may be active or interrupted; the
console explicitly preserves that uncertainty.

## Validation and remaining integration

Eight focused tests execute real pipeline fixtures and cover baseline/delta,
review stopping, pause/restart, duplicate identity, hash tamper, queue tamper,
missing signed state, interrupted execution, polling limits, HTTP sanitization
and denied HTTP mutation. Test workbooks are synthetic and are not claimed as
approved real-world source evidence.

Still missing: real dossier export/producer execution adapters, end-to-end
B2/B3 execution from admissible real inputs, authenticated recovery decisions,
rollback anchors, durable deployment and final acceptance. These remain in the
single closure ledger. No shared contract or gate is promoted by this candidate.
