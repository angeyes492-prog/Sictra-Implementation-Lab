# Official research acquisition — 2026-10-03

Scope: LABORATORY_INTERNAL_SUPERVISED, explicit owner research exception in
AGENTS.md. State: EXECUTED / QUARANTINED / NOT_ADMITTED. Implementation agent,
VERIFIED / confidence B for access, retained bytes and extraction; no
independent review, source admission or product completion.

## Selected need and exact retained identity

Eurostat: `Source metadata explaining revisions and coverage changes.`
Need type SOURCE_METHODOLOGY. Exact network GETs used pinned public-address TLS,
no credentials/proxy/cookies, no redirects or retries. Two successful downloads,
441148 received bytes total. Earlier discovery: three initial public queries,
two official page reads, two official-page find operations; subsequent API
discovery used two queries. These are tool operations, not an assertion about
the search service's internal crawl/request count. No denied endpoint was
bypassed. Installed app, runtime intake, approval/binding stores and journals
were not touched. Quarantine root (ignored local runtime data):
`C:/Users/angel/.codex/worktrees/telecare-autonomy-closure/Intelligence/.runtime/research-quarantine-2026-10-03`.

| Artifact | Retained identity | Content SHA-256 / bytes / acquired UTC |
| --- | --- | --- |
| [Eurostat reuse notice](https://ec.europa.eu/eurostat/help/copyright-notice) | c38122a03b5a6d38e7ffb6fc7aff8ba2e6845d7792d1bbeca7bf5e0a503175aa | 017ea1fc19de061de8cd42faf9a394eee5b605280d591b624344b91428ec6da5 / 177237 / 2026-10-03T23:19:30Z |
| [Maritime metadata](https://ec.europa.eu/eurostat/cache/metadata/EN/mar_esms.htm) | 2ec276d6011d1276108777e833ad6fd7a14329342dd932c86151d8a2b380dd49 | 03e9bd88d73ed405e0bd4d74a3eee802de5b555b0ec69d210d0ae934a06c125b / 263911 / 2026-10-03T23:20:14Z |

Each receipt has 24-hour research revalidation, distinct from publisher
cadence. The metadata receipt binds the notice receipt; readers also reject
expiry/tamper of that linked notice. Original bytes and descriptors can be
reopened by known candidate ID; no HTML is executed or published.

## What the actual extraction established

Eight exact named heading sections extracted: metadata update, description,
sector/time coverage, revision policy/practice, source data and frequency.
Publisher update text is 15 January 2025, not today's acquisition date. Report
fingerprint: `c2a895791da4256d1956193f56eb81b1cc91f0701b6a664ac4ade3ffa127fe1a`.
The report binds both input hashes/expiries and expires at 1791155970 (the
earlier terms boundary), not 1791156014 (metadata). A staggered-acquisition
red test first exposed the overlong report expiry; the repair retains the
earliest dependency expiry and rechecks both inputs after extraction.
It remains REVIEW_REQUIRED / NOT_RESOLVED / NOT_ACCEPTED / runtime_effect NONE.

The publisher describes national compilation, revisions/corrections after
validation and quarterly/annual collection. This supplies general methodology
for review, not the cause of any particular observed change. Maritime gross
weight and trade net weight/value remain different measures; another national
publication may share the input root. An independent comparable source has
not been established. No fabricated corroboration or resolution follows.

## Reproduction and repairs

With candidate src on PYTHONPATH, run
`python -m sictra_block1.research_methodology --root .runtime/research-quarantine-2026-10-03 --candidate-id 2ec276d6011d1276108777e833ad6fd7a14329342dd932c86151d8a2b380dd49`.
The command reads/revalidates, never writes. After expiry, retain history and
perform a new bounded acquisition rather than rewriting timestamps.

The first actual review hit Windows cp1252 UnicodeEncodeError. ASCII-safe JSON
output preserves Unicode through escapes; an ASCII stdout regression proves
the round trip. A separate EOF deadline attack initially passed too late; a
final monotonic check repaired it and the test now rejects. Acquisition has 17
tests and methodology 8, all passing. A first methodology discovery imported
the acquisition TestCase directly and ran its 16 tests again; module-qualified
fixture reuse removed that duplicate discovery. Counts report unique new tests,
not duplicate imports. Full regression and final SHA/CI remain separate checks
recorded through PR #18 and workflow history after publication.

Full regression first executed 851 tests and reproduced the prior Windows
10053 unauthorized POST failure. That observation triggered an independent
transport repair, not a source admission or relaxed test. Unit red tests
established the unread-body defect; bounded discard after flushing 403 retains
all authorization checks. Five unit tests plus a same-socket loopback vector
cover positive response/no mutation, framing/deadline/cancellation and subsequent
authorized control. Focused seven tests (including the unchanged prior HTTP
assertion) pass. The initial split-body fixture's automatic reconnect risk was
removed by using raw HTTPResponse on the original socket. A final complete
regression is required after this change, not inferred from the first run.
An intermediate 857-test regression passed in 140.470 seconds after the HTTP
repair. The later effective-expiry repair requires another complete run; that
intermediate result is not its oracle. The focused acquisition/methodology/
transport suite passed 30 unique tests after the expiry repair.
Final local regression after all repairs: 858/858 Python tests in 142.500s,
17/17 JavaScript tests, compileall, launcher paths and diff checks passed.
The finite 24-test preflight and exact final-SHA CI remain separately bound
through the final PR/workflow identity; these counts do not promote the product.

## Reconciliation and next work

Notion 3c789f66-067b-8108-bb44-c13ac4b15ac0 remains historical reference scope
(edited 2026-08-28); public Slack Telecare search returned no results. Neither
supplies admission or MAR acceptance. Base c528205 exact push 36958085729 and
PR 36958088947 succeeded. Wolfram checked 160 abstract status/security/terms
conjunctions with no modeled acquisition-to-admission transition; a deliberately
non-admitting model does not independently prove runtime enforcement.

Next safe technical route: bounded official statistical-data recipe and strict
format normalization, preserving original bytes and publisher time, before
admission through the existing approval/binding contract. Official API
[guidelines](https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-detailed-guidelines/api-statistics)
define JSON-stat 2.0 and bounded time filters; this research is not implementation
of that data route. Owner source approval and release-specific explanation
remain separate. No automated installed-runtime network acquisition, effects,
gate promotion or background restart occurred.
