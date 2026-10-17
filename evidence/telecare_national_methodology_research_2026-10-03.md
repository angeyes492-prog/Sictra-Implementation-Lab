# Belgian maritime origin/methodology research — candidate execution

Date 2026-10-03 local / 2026-10-04 UTC. Windows / Python 3.12.
Base 4c9cf7a6c6963b988b92331cae5ddb711142b78f, exact GitHub push
37169904811 / PR 37169907204 successful and rechecked this cycle.
Scope LABORATORY_INTERNAL_SUPERVISED; MAR item 11 OPEN. Validator implementation
agent, not independent. VERIFIED / confidence B for executed mechanisms and
retained bytes, not real-world source truth, independence or acceptance.

## Need selection and actual source findings

Highest-risk unfinished item COMPARABLE-APPROVED-INPUT: obtain evidence matching
the actual measurement scope and establish origin before claiming corroboration.
The [Eurostat national maritime metadata](https://ec.europa.eu/eurostat/cache/metadata/EN/mar_esms_be.htm)
is publicly linked from the generic maritime metadata. It names Statistics
Belgium as compiler, describes port-supplied records and validation before
transmission to Eurostat. Inference: a national republication/port publication
may overlap the existing Eurostat measurement's upstream origins. No claim of
independent measurement or authenticated lineage follows from the prose.
The original national metadata update is 19 February 2021; it is not a
release-specific explanation of a 2023/2024 observation or a 2026 revision.
Data compilation is explicitly unavailable. These gaps remain unresolved.

The [Statbel maritime page](https://statbel.fgov.be/fr/themes/mobilite/transport/navigation-maritime)
presented a human-verification challenge through the search/browser reader.
No attempt was made to bypass it, contact anyone, authenticate or access
alternate paths on that challenged service. The separately published Eurostat
page is a public source already linked by its own metadata, not an access bypass.
Port of Antwerp-Bruges' official yearly results were discovered, but a two-port
throughput statement is not an established same-coverage national observation;
it was not downloaded/admitted or treated as independent corroboration.

## Actual acquisition, lineage and limits

Fixed recipe EUROSTAT_BE_MAR_METADATA. One real GET, 192526 received/retained
bytes, no retries, using existing pinned public-address TLS, identity media,
strict status/framing/redirect limits and content-addressed quarantine.
Candidate ID 5ec1076dd4954ba208f5cab0bb1afe96061ba49236526d2df92f1f2b85798292.
Raw SHA-256 5e185857b41051fb6b0bcb627ed0092495797725276269bf5c8c4e92862a4c95.
Acquired 1791082310 / 2026-10-04T02:51:50Z; metadata expiry 1791168710.
Linked current terms ID
c38122a03b5a6d38e7ffb6fc7aff8ba2e6845d7792d1bbeca7bf5e0a503175aa,
terms hash 017ea1fc19de061de8cd42faf9a394eee5b605280d591b624344b91428ec6da5.
Effective review expiry 1791155970, the earlier terms boundary.
Raw bytes remain in the ignored existing .runtime research quarantine, not Git.
Actual sixteen-section review fingerprint
0e02d4b9ec4091db83f1594e2c00787b0e2e4a61e700cb24c7fbab04014486f6.

Hosting publisher/source identity remains Eurostat; the raw national compiler
claim is separate. No root ID, approval, binding, attestation, task resolution,
registry acceptance, dossier, installed state or gate was minted or changed.
The prior statistical source review remains PENDING / NOT_ADMITTED.

## Concrete implementation, failure, repair and independent oracles

The new national_methodology reader binds exact terms/data hashes and extracts
sixteen fixed ESMS sections for agency/update, concepts, unit, population,
geography, period, source collection, validation, compilation and revisions.
It preserves unavailable text literally and separates acquisition from the
publisher's raw date. Source/dependency re-read, clock monotonicity and final
expiry fence reject slow/changed reads. REVIEW_REQUIRED / NOT_RESOLVED /
NOT_ACCEPTED / INSUFFICIENT EVIDENCE / UNCONFIRMED / NONE / BLOCKED are preserved.

1. Inspecting actual retained HTML contradicted the first candidate header
   assumption: unit and period use button/h2 headers, period uses list items,
   and the validation anchor is data_validation, not data_val. Candidate
   contract/parser were reconciled before adoption, without guessing labels.
   The shared parser adds explicitly opted-in top-section/list handling;
   generic eight-section behavior and original admission remain unchanged.
2. The first actual CLI rejected its default float wall clock under an integer
   clock validator. A dedicated integer system clock and strict callback
   validation repaired it; actual retained-byte review then succeeded. The
   ASCII CLI test exercises this default path and raw Unicode agency text.
3. Initial 37-case focused run failed one injected-change fixture: recursive
   terms validation triggered the mutation before its initial explicit read,
   making both observations equally mutated. Injection is now armed after
   extraction, representing the specified between-read change. The same
   rejection assertion remains; final focused 37/37 passed in 4.100s.

Twelve new cases cover exact expected sixteen fields and raw 2021 date; nested
list/inline-link text without executing content; missing/duplicate/script-forged
anchors; wrong/ambiguous/nested top headers, unclosed blocks, empty/oversized or
invalid encoding; exact country URL/media/current-terms requirements; original
generic/statistical-admission substitution rejection; tampered/stale terms;
post-parse changed metadata/terms; mid-parse/final expiry and regressed/invalid
clock; actual fixture-data restoration and tampered restored bytes; default
clock and ASCII CLI. Oracles are fixed fixture text/headers and injected states,
not the report's own verdict or source truth. No new authority plane was added.

## Four-source reconciliation and next boundary

Notion 3c789f66-067b-8108-bb44-c13ac4b15ac0 was retrieved this cycle; its
unverified 2026-08-28 reference-runtime plan does not approve this recipe or
accept MAR. Public Slack Telecare query returned no results. GitHub binds the
base CI above and later exact-SHA CI separately. Wolfram enumerated 128
declared-origin/complete-lineage/publisher-label cases: zero model violations,
110 insufficient-lineage, 14 shared-origin and four disjoint-declared-origin
cases. Of the 64 different-publisher cases, 62 still lacked modeled independence.
The model uses origin sets empty/{PORT_A}/{PORT_B}/{PORT_A,PORT_B} and boolean
lineage completeness for each side; it does not authenticate actual origins,
execute Python or promote gates. No independence classifier was activated.

Next research: publication-specific explanation and admissible same-scope
evidence with reviewed upstream independence. This source reduces uncertainty
about origin/definitions; it does not fill that remaining measurement gap.
No repeated challenge attempt, installed acquisition, publication/contact/CRM,
installation, gate promotion or paused-heartbeat activation occurred.
The full owner goal remains active; no product arista is claimed complete.
Final full regression/preflight/new exact-SHA CI must be recorded after execution.
Resumed handoff 2026-10-04 local; the preceding collection began 2026-10-03
local. Revalidated the same quarantined candidate without a new network request:
the exact review fingerprint, original 2021 update and unresolved boundary match.
Full final Python regression passed 940/940 in 1890.746s. Separate discovery
counted 940 unique identities, twelve new cases over the base. JavaScript
17/17, compileall, launcher paths and diff checks passed. Final unchanged-checkout
preflight and hosted CI remain separately bound to the implementation SHA in
PR #18/workflow history; no product-completion claim follows from these counts.
