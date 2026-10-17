# Collection rejection portability — 2026-10-11

Scope: LABORATORY_INTERNAL_SUPERVISED, task C0 of the closure checklist.
Base SHA: 210843b6ec43204461530512bdc3640930dca638.
Status: CLOSED_TECHNICAL C0; no product/arista acceptance inferred.
Certainty VERIFIED / confidence B for the observations below; no gate promotion.

## Reproduced failure and diagnosis

Exact hosted CI 38088995012, job 114321361316, CPython3.11.17 failed the
malformed HTML test: it expected AssertionError and recorded
ResearchAcquisitionError. Local CPython3.12.10 reproduced the AssertionError
from HTMLParser.parse_marked_section for the same b'<![bad]>' input.

Official CPython sources explain the paths:

- https://raw.githubusercontent.com/python/cpython/v3.11.17/Lib/html/parser.py
  parse_html_declaration consumes <![...]> as an unknown declaration;
  the application then rejects missing methodology sections.
- https://raw.githubusercontent.com/python/cpython/v3.12.10/Lib/html/parser.py
  calls parse_marked_section; the unknown status keyword raises AssertionError.

The collection contract requires failure accounting, retained originals and
unusable selection on failure, not an identical private parser exception
across versions. No local3.11 interpreter was installed. The exact new-SHA
hosted suite must establish native3.11 behavior after repair.

## Changed verification

Real malformed publisher HTML remains exercised through real collectors,
readers and persistence. The test now requires FAILED, seven attempts, exact
received-byte budget, all selected identities and original bytes/SHA-256,
and no selections directory. It does not accept arbitrary exceptions.

A separate parser-fault injection at MethodologyParser.feed requires the
AssertionError to become COLLECTION_FAILED and a durable failure outcome,
preserving budget/retained identities and preventing publication. This keeps
the exception-capture regression independent of upstream parser behavior.
Product code, failure handler, source controls and authority are unchanged.

Focused execution: 33 tests passed in 93.772s.
Log: .runtime/collection-portability-focused.log.
Focused log SHA-256: 5241900be2df87966b2f3ba41def8196bc57439fa3560136e41ce8e25e685ee9.
Full regression: 1078 unique cases in 1030.967s, zero failures/errors; 1077
passed, one Windows symlink-creation permission skip. Log:
.runtime/closure-c0-full-regression.log; SHA-256:
17891159a6869971fade64152757d4944aed357d26cc196060761540950b3f7d.
JavaScript18/18, compileall, launcher path checks and diff checks passed.
Stable changed-tree preflight24/24 passed at 2026-10-11T17:06:28Z, reporting
product_completion NOT_DEMONSTRATED; clean committed preflight follows commit.
Final full regression, preflight and exact new-SHA hosted evidence are recorded
in the canonical closure ledger after execution, never inferred here.

Exact code/test SHA4dcaa83c61463cdd01e552ee96825289415dbdcd passed GitHub
push38158647420/job114526748651, including nativeCPython3.11.17 full suite,
preflight, launcher, JavaScript and both reference engine steps.
Clean local preflight24/24 at2026-10-11T17:12:46Z reported dirty=false,
unchanged checkout and product_completion NOT_DEMONSTRATED.

## Fresh read-only agent review

No Critical/Important; one Minor deferred: the injected-fault case checks
retained identities rather than repeating the original-byte/hash loop already
executed by the real malformed-input vector. Cost: deletion specific to the
injected exception could be less directly detected on a future parser version.

Ruling: global regression/CI were not reviewer-executed; local suite and exact
hosted workflow provide separate evidence. Cost if wrong: missed regressions.
Ruling: native3.11 was not reviewer-executed; use its exact hosted CI before
crediting closure. Cost if wrong: another platform-specific failure.
Ruling: source admission/activation/global closure were outside this increment;
they remain open. Cost if wrong: unsupported autonomy or effects.

## Next executable criterion

After C0 CI, re-enter the skill/checklist. Candidate P12 operator-path improvement:
select an existing committed research collection by root and exact selection ID
for the read-only console, revalidating the entire collection on read and final
HTTP response. Preserve absence/default configuration, manual-ID compatibility,
expiry/tamper/restart behavior and source/MAR boundaries. This is not network
activation, source approval, interpretation, installation or final autonomy.
