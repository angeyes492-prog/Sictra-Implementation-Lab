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

## Chained statistical-data increment

After exact-SHA bae06bd CI succeeded (push 37163119366, PR 37163123177), the
next specified item added fixed official API acquisition/JSON-stat inspection.
Same quarantined root, no runtime/approval imports or effects. Retained receipt:
`c2650baf62a4c8f86b5a639f78e28c9954760cc6f879dfc074cc13a1ad1fd39d`;
content SHA-256 `5525b2ac0f59d6439f62829ecda9a2bc7727d91486e6a3475fbda3965c8a6175`,
2647 bytes, acquired 2026-10-03T23:59:00Z (1791071940), data expiry 1791158340.
It binds the earlier terms receipt; effective report expiry is 1791155970.
This increment used one successful GET/no retries; cumulative direct downloads
this work cycle: three requests, 443795 bytes. Additional discovery opened the
official API guide and JSON-stat format specification; web preview of the
exact API URL was unavailable, not an endpoint access denial. The verified,
pinned direct official acquisition succeeded without any bypass.

Actual report fingerprint:
`46d6159d311674d818665dc9ac3bf40842cce06f36b2285945423ccfc30916e0`.
Exact selected scope: tran_r_mago_nm / A / FR_LD_NLD / THS_T / BE / 2023-2024.
The retained publisher reports 272698.25 thousand tonnes for 2023 and
274369.05 for 2024, no missing cells or flags in this subset. Publisher update
raw `2026-03-17T23:00:00+0100`, distinct from acquisition time. These are
quarantined publisher observations, not attested conclusions, source admission,
two versions of one observation or independent corroboration. No numeric
comparison is promoted to revision cause or strategic Intelligence.

The actual compact +0100 publisher offset initially rejected; its independent
regression case also failed. Valid compact and colon offsets now parse with
bounded hours/minutes; impossible/garbage offsets still reject. A red-team
query-removal mutation initially reached transport; it now rejects before
network by requiring the exact fixed statistical URL. Thirteen new tests cover
dense/sparse/reordered categories, missing versus zero, raw flags, malformed
scope/labels/indexes/JSON, errors/asynchronous warnings, media/query isolation,
exact retained bytes, restart/no writes, terms expiry, tamper and slow reads.
Focused combined acquisition/methodology/statistics/transport: 43/43 passed.
Wolfram checked 240 declared row-major positions across all 120 dimension
permutations for this singleton/two-year cube. It validates that bounded index
model only, not parsing, access, source truth, runtime or gate acceptance.
The earlier dated Notion/Slack context supplies no new admission authority.

Reproduction: `python -m sictra_block1.research_statistics --root .runtime/research-quarantine-2026-10-03 --candidate-id c2650baf62a4c8f86b5a639f78e28c9954760cc6f879dfc074cc13a1ad1fd39d`.
After expiry, reacquire bounded current candidates; never rewrite timestamps.
Remaining promotion boundary: exact reviewed source/API-format scope, approval
and binding lineage plus an accepted consumer before runtime ingestion.
Same-root retrieval cannot close the independent-input or causal-resolution
gap; those need genuinely comparable separately rooted evidence and contracted
semantics. Neither installed app nor paused heartbeat was activated.
Final statistical-increment local regression: 871/871 Python tests in 141.050s,
17/17 JavaScript tests, compileall, launcher paths and diff checks passed.
Forty-four new Python tests across both increments; final unchanged-tree
24-test preflight and exact-SHA GitHub CI are separately bound in PR #18.
VERIFIED / confidence B for this executed local boundary, not source truth,
product acceptance, independent review or complete autonomous operation.
