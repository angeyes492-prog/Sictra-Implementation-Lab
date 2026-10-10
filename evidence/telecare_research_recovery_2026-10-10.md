# Official candidate recovery — 2026-10-10

Scope: offline agent-operated laboratory candidate; no installed adoption.
Baseline: `3786cc46fc62fcce2f93c052f3fc0545384f2117`, clean synchronized branch
`codex/telecare-integrated-autonomy`; hosted run `37962371794` success.
Implementation/CI identity for this new increment is recorded by its containing
Git commit and the exact-SHA workflow, not inferred from baseline CI.

## Executed closure delta

New `sictra_block1.research_recovery` backs up explicitly selected Eurostat
candidate bytes/descriptors and their exact terms dependency, then restores to
a nonexistent quarantine. External manifest digest, bounded reads, exact file
inventory, unchanged admission/expiry and no-overwrite atomic publication apply.
Windows rename and Linux renameat2 NOREPLACE prevent concurrent empty-target
replacement. No source-selection inference, network, keys or admission effects.
`operations serve --research-regional-id` now reaches the existing regional
reader; initial invalid selection rejects before worker/server start.

RED: new recovery tests initially failed because the module was absent.
New positive/invalid-regional CLI tests failed on unrecognized regional option.
GREEN: 17 recovery cases completed (one host-privilege symlink skip) and three
real-review startup cases passed. Windows junction rejection executed successfully;
CI on Linux must execute the symlink case. Full regression results below are
separate, not implied by focused checks.

Fresh read-only code-review agent found no Critical/Important defect and two Minor
controlled-error issues. A cleanup-failure test reproduced raw OSError hiding the
primary write failure; cleanup now returns a controlled error naming its unpublished
residue, with the primary failure preserved as cause. A 20,001-byte nested JSON
manifest reproduced uncaught RecursionError; decoder/CLI now reject it without
traceback. Both rejection tests passed unchanged after repair. This is another
model's code review, not independent human/system acceptance.
Reviewer exclusions: publisher authenticity/admission, other stores and production
remain outside this candidate; accepted as separate authority/contracts. Power-loss
durability beyond atomic visibility is explicitly not claimed by this contract.

## Actual originals recovered offline

Original `.runtime/research-quarantine-2026-10-09-review`; archive
`.runtime/research-backup-2026-10-10`; recovered quarantine
`.runtime/research-restored-2026-10-10`. Originals were not removed or changed.
Retained payload+descriptor bytes: 678781; four candidates; zero network requests.
Archive manifest SHA-256:
`bbb81b5067e60f3d48dcf178411a81ec42a8824fe42f4c1dd456e89dc7d243c8`.

| Recipe | Exact candidate | Original body SHA-256 |
| --- | --- | --- |
| Reuse notice | bab9ce014088626f208f57bf3808c68461427051d8d628af4b35b590d90fd111 | c7aafdc2de47247ee62acc3eeee570f879e2b5e57539718c7e0b9f28078db63c |
| Generic methodology | 4d2fd5891333b9d5e3c74374af65db702214a58a584f600e96a1b9d9dd56fe84 | 03e9bd88d73ed405e0bd4d74a3eee802de5b555b0ec69d210d0ae934a06c125b |
| Belgium 2023–2024 data | 1942f11a6d8819134ccf231cf3091e7b6cc504941cd105e500bd0a6d7163ef3c | 5525b2ac0f59d6439f62829ecda9a2bc7727d91486e6a3475fbda3965c8a6175 |
| Regional methodology | cd6b44ba8d7830826478c0a708435f1c8f2703ae2f05f3a81ff71b15553d08e1 | 691449ac5aba1ea41e1ed6eab3e1c60c11f7df8d46b9b01ecb16ad23ce5d0db8 |

PowerShell Get-FileHash compared all eight original/restored files: identical.
Recovered data read at acquisition time returned 2647 bytes, expiry 1791646647,
`NOT_ADMITTED`, runtime `NONE`. Current read at 1791655543 rejected
`CANDIDATE_NOT_CURRENT`. Recovery preserved history without renewing authority.

## Complementary formal model

Wolfram enumerated all 64 Boolean combinations of external digest, exact
inventory, hashes, lineage, safe paths and missing target; only all-six accepts.
Zero unsafe accepted states in that abstract model. This describes required
conditions, not proof of filesystem behavior, publisher truth or acceptance.
Runtime rejection/recovery tests provide the separate executable evidence.
Wolfram also solved the continuous-domain expiry constraints (data acquisition
`a`, terms acquisition `t`, expiry `ed=a+86400`, `et=t+86400`, and restore/read
time `n`). Requiring `n>=Min[ed,et]` while both `a<=n<ed` and `t<=n<et`
returned `False`: no expired dependency can be simultaneously current if original
expiries are preserved. The real retained-byte read separately rejected expiry.

## Remaining product boundary

Actual source admission remains PENDING; these historical originals are expired.
Statbel quarantine and signed admitted stores have distinct recovery contracts.
Shared adoption remains MAR; interpretation/resolution semantics, accepted
reference/editorial cases, usability/account data and actual delivery outcomes
are not supplied by this increment. Currentness/waiting for a new source release
is a valid operating state, not unfinished code or permission to invent a delta.

Certainty VERIFIED / confidence B for the bounded executed recovery; product
completion INSUFFICIENT EVIDENCE. Final reviewed/regression results follow.

## Final local verification

Environment: Windows, Python 3.12; candidate `src` explicitly on PYTHONPATH.
`python -m unittest discover -s tests -v`: 1045 cases in 1598.360 seconds,
0 failures/errors, 1 host-privilege symlink skip (1044 passed). Twenty unique new
cases over the baseline. Windows junction rejection passed; Linux symlink execution
remains covered by hosted CI, not claimed from Windows. Retained full output:
`.runtime/regression-research-recovery-2026-10-10.log`, SHA-256
`083f7d944222b58eab094b489866b348c24c780093e399b8d690a69768ee8ee9`.

JavaScript console tests: 18 passed, 0 failures. Python compileall and preserved
launcher-path tests passed. Precommit twelve-arista preflight executed exactly
24 selected tests, all PASS, checkout unchanged; `product_completion` remains
`NOT_DEMONSTRATED`, all product closures `INSUFFICIENT EVIDENCE`. Clean committed
preflight and CI on this evidence's containing SHA are the final external checks.
Their immutable workflow results apply without manufacturing a new data release,
changing gates or requiring a further documentation-only commit.

## Product-closure assessment against each arista

This is a diagnostic against the current canonical contracts, not another backlog
or gate decision. The separate finite preflight below verifies selected mechanisms.

| Arista | Technical route / evidence | Remaining product input or decision |
| --- | --- | --- |
| 1 Sources | Signed local source controls; candidate admission/recovery modules | Actual format-specific statistical approval/binding and comparable source rights |
| 2 Acquisition | Authorized stable-file scheduling; bounded agent acquisition in quarantine | Accepted runtime adapter/activation; agent collection does not grant it |
| 3 Versions | Release watchlist and literal change/missingness/flag classifiers tested | Actual admitted release history for observed revision; unchanged source is valid waiting |
| 4 Correspondence | Same-scope pair validation; actual Eurostat/Statbel same-chain discrepancy retained | Independent comparable admitted root; coverage equivalence remains unconfirmed |
| 5 Needs | Typed bounded assessment and durable unresolved tasks | Accepted per-need resolution semantics/reference cases; not merely a new status label |
| 6 Intelligence | E01–E08 authority guards, separate facts/uncertainty, literal dossiers | Evidence-backed interpretation/hypotheses accepted on real cases |
| 7 Editorial | Traceable shortlist, selection/abstention, research-needed blocking | Accepted editorial relevance/quality cases; no publication inferred |
| 8 Design | Fact/provenance/limitation-preserving render and integrity guards | User comprehension/accessibility evaluation under accepted criteria |
| 9 Precision | Current generic profiles, geography and adaptation guards | Authorized actual account exposure/consent where applicable |
| 10 Orchestration | Bounded fair local search, atomic persistence, replay, STOP/pause | Accepted resolution-to-new-dossier/decision loop beyond triage |
| 11 Delivery/learning | Receipt/outcome contracts and no-receipt rejection tests | Channel permission, genuine receipt and observed outcome; external effects blocked |
| 12 Operation | Existing local integral recovery plus new original-byte recovery | MAR/installed activation, sustained real pilot, operator/key custody and independent review |

The narrower historical Block 1 supervised laboratory gate has different scope.
Its `AWAIT_NEWER_SOURCE` terminal state is not an unimplemented feature and does
not block its technical implementation closure. Conversely it cannot accept this
expanded twelve-arista architecture or resolve a specific editorial need.

Specific admission boundary: `research_admission._terms_reference` includes exact
terms and methodology candidate IDs; `_record` checks that reference and
requires `reviewed_at` not before their acquisition. The admission bridge contract
requires a trusted durable APPROVED/BOUND record for the new statistical format;
existing XLSX approval is not that record. A recapture can preserve content hashes
while changing acquisition-bound candidate IDs. Current code does not delegate
review/binding renewal to the construction agent. Source/architecture authority
must decide actual review/binding and any future renewal policy before autonomous
admission; collection permission and a backup digest cannot replace that decision.
