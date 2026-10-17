# Candidate contract — twelve-arista mechanism preflight v0.1

Producer `sictra.closure_preflight`; consumer local developer/operator or CI.
Scope `TWELVE_ARISTA_LOCAL_MECHANISM_PREFLIGHT`, version `0.1.0`.
Authority: execute a finite diagnostic, not accept architecture or promote gates.

Input is the repository checkout and the fixed 12-objective/24-test inventory.
Each objective has a unique ordinal, observable goal, owner, positive test,
rejection test and remaining product evidence. The inventory is defined in code,
not supplied by an untrusted report. Tests execute once in isolated fixtures.

Before/after identity includes HEAD, dirty state and a canonical SHA-256 over
tracked/untracked checkout file bytes, including test fixtures (not ignored
runtime files). The digest exposes hashes, never file contents.
Source disappearance, invalid paths and changing checkout reject the diagnostic.
Exact test identity and actual successful execution are required: missing,
duplicate, skipped, expected-failing, unexpectedly successful, failing subtest,
setup/teardown error or incomplete inventory cannot count as PASS. No cached
test report is consumed as execution evidence.

JSON output separates `mechanism_check` from `product_closure`, preserves every
objective and outstanding evidence, and always retains `NOT_DEMONSTRATED`
product completion, `NOT_ACCEPTED`, `BLOCKED` and the separate exact-SHA CI
requirement. Exit 0 means all selected local mechanism checks passed, never
product acceptance. Exit 1 denotes failed/incomplete/unstable execution; a Git
or input error also exits nonzero. Full regression and independent acceptance
are separate requirements.

No runtime journal, installed application, approval, key, gate or external
service is mutated. Test fixtures create/clean isolated temporary data only.
There is no retry loop or continuing execution after this single finite run.
Rollback removes the diagnostic without migrating runtime state. This selected
inventory is a regression sentinel, not exhaustive proof of the 12 objectives.
