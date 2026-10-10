# Same-chain research diagnostic and HTTP output currency — 2026-10-08 UTC

Scope: `LABORATORY_INTERNAL_SUPERVISED`. This is a technical candidate, not
source admission, corroboration, accepted interpretation, production operation
or gate promotion. Exact final commit SHA and CI are recorded in the closure
ledger only after verification.

## B1: reproduce the retained publisher observations

`sictra_block1.research_same_chain` accepts exactly one Statbel and one
Eurostat 64-hex candidate ID with separate existing quarantine roots. It
reopens exact data and terms bytes, checks descriptor/content hashes and
lineage, requires current receipts and compares the two reads before returning.
The CLI rechecked the actual 2026-10-07 retained IDs and returned:

| Year | Statbel loaded | Statbel unloaded | Statbel sum | Eurostat `FR_LD_NLD` | Numeric gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2023 | 126,590 | 146,397 | 272,987 | 272,698.25 | +288.75 |
| 2024 | 128,118 | 146,776 | 274,894 | 274,369.05 | +524.95 |

Unit as labelled by each publisher: thousand tonnes. The four exact candidate
IDs, byte hashes, official URLs, times and rights evidence are in
`evidence/telecare_statbel_same_chain_research_2026-10-07.md`; the CLI report
returned an earliest research expiry of UTC epoch `1791497939`. The original
data/terms candidates were not rewritten. This arithmetic difference is not
evidence of equivalent port universe, release cutoff, revision cause or
independent corroboration. The report explicitly returns `NOT_ESTABLISHED`
independent root, `UNCONFIRMED` comparability/cause, `NOT_ADMITTED`,
`NOT_RESOLVED`, runtime `NONE` and publication `BLOCKED`.

Nine focused cases use independent expected numeric values and exercise
reopen, report/terms substitution, raw-byte tamper, expiry, missing Eurostat
value, a clock crossing expiry, CLI read-only root rejection, exact numeric
lexeme preservation, >28-digit subtraction and extreme-exponent rejection.
The module-import failure and both decimal precision failures were observed
before their repairs; all nine pass after implementation. The official
retained-byte CLI run passed while receipts were current; this is stronger
than fixture-only parsing but weaker than source admission or method review.
The hash-bound Eurostat JSON is reparsed with Decimal; accepted exact values
are capped at 64 significant digits and exponent magnitude 64, then the
gap is calculated in a bounded 256-digit local context. Out-of-bound numeric
values fail rather than silently round or exhaust arithmetic resources.

## B4: final HTTP response fence

Before repair, injected expiry after the first service read made both direct
output HTML and factsheet HTML return HTTP 200 with stale content; an
`/api/operations` snapshot rendered after expiry also returned 200. These
adversarial cases failed as expected. The handler now serializes the output,
factsheet or snapshot, then revalidates current service state before emitting
success headers. HTML/text/JSON output, HTML/JSON factsheet and dashboard
snapshot reject the injected expiry with HTTP 409 and no retained observation
in the error body. Existing positive HTTP cases and read-only store checks
still pass. The fence covers preparation-to-headers; it is not a promise that
external state can never change after bytes begin transmission.

The first 1008-test full discovery revealed a compatibility failure in a
cancelled-browser test: a direct JSON send bypassed the handler's `_json`
path. Repair restored that path with a post-serialization `before_send`
fence; the focused cancellation test passed. Read-only code review then
identified factsheet metadata (`DEFERRED_REVIEW`, recovery count, data class)
that could change without changing the underlying output. A new mutation
test returned 200 before repair; the final fence now rebuilds and compares
the full stable factsheet projection, and the test returns 409. The reviewer
also challenged float and default-Decimal precision; both counterexamples
were reproduced and repaired. The reviewer found no remaining Critical or
Important issue on its final targeted pass.

Focused check: `tests.test_research_same_chain`, `tests.test_factsheet`, and
the two new HTTP operation methods plus command-surface compatibility passed
20/20; the relevant normal HTTP path
also passed. JavaScript suites passed 18/18, `compileall` and preserved
launcher paths passed. The final changed-tree full Python discovery passed
1013/1013 in 258.051 seconds. The 24/24 twelve-arista preflight passed with
an unchanged clean checkout at code SHA
`d49e3a70ef7c18308860ffbb57b5aee72edebf7c`, source-tree SHA-256
`89f715907ba9b549e9ea6dae7c9d8e32a160d9503c72c97065fbd799f1a3ca5a`, and
reported `product_completion=NOT_DEMONSTRATED`. GitHub Actions workflow
`37715797525` completed success on that exact code SHA; PR #18 remains draft.
No gate was changed.
