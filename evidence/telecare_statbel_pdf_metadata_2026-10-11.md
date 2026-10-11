# P04 Statbel metadata original-PDF reader — 2026-10-11

Scope: LABORATORY_INTERNAL_SUPERVISED, candidate standalone B1 agent tool.
Baseline: 3324c6ba1512c32fdf58b0c06bfee57ffb7fbe20; its hosted PR38161156197
and push38161151854 succeeded. Not acceptance or installed activation.

## Delta and independent observations

`research_statbel_metadata` reads the known manual PDF descriptor/original and
exact current Statbel terms. It derives eleven literal page-labelled fields,
separates unspecified unit/population, checks bytes/rights/expiry after parsing
and rejects caller-resealed reports by recomputation. Standalone CLI serializes
then verifies before printing. No engine, seven-recipe collection, scheduler,
source issuer, installed application or paused automation is altered.

Parser runs in an isolated child using optional pypdf6.10.0. Original limit
256KiB, four pages, depth32,4096 traversed objects,512KiB per page content,
8MiB total decoded resources,128KiB extracted text and15-second timeout.
Encryption, reachable active/embedded actions and unsupported stream filters
reject. This is not an OS sandbox or a hard memory quota. Default package
installation does not require this addon; CI explicitly installs it.
Primary parser guidance: https://pypdf.readthedocs.io/en/6.10.0/user/extract-text.html.

Old actual receipt3acaa708c79ad03241f8ba1a49830aa4d185bffb825ed7249db85c828a8f2c59
expired1791753418 and was correctly rejected, not edited to look current.
New bounded agent research: two official requests,122567 received bytes
(92370 terms +30197 PDF), no redirects/retries. New receipt
4cc73900cd59cb0b4e2bb6ffed38d635819fe3d5125ce097964f765ceb6ed798,
PDFSHA256c50665e258b3215505399034d678a5922441e6fa4460ce55146014bf23a8d208,
terms2717b0f80c174031ea16cdfe84c561c13fc87aba5b2e15ff026b7de558f56400,
termsSHA256721083ed49c8fecb2aa7596d831fc3f41e721290acee21746c8320f36f7e8529,
expiry1791840518. Root `.runtime/agent-scope-current-2026-10-11`.
Original publisher URL:
https://statbel.fgov.be/sites/default/files/files/metadata/T38.STAT_DTST_743.CTAC_ORG_1.DIFF_LVL_1.EN.pdf.

Actual reader run extracted document date12/02/2025, Belgian seaports,
quarter/quarterly, all-Belgian-seaport administrative origin, reuse of
administrative data, and policy/practice `Not applicable.`. Neither unit nor
population was specified. Inland-water database reference is a scope conflict.
Date is literal, not a release identity for the current statistical series.
Prior four-page inspection and visual checks of pages1/3 apply to identical
original bytes, not a different PDF. Acquisition freshness is not publisher
publication validity or PDF-specific rights acceptance.

No evidence of actual Eurostat/Statbel port-universe equivalence/difference,
independent upstream observation, statistical revision, numeric-gap cause or
resolved need follows. NOT_ADMITTED / NOT_RESOLVED / NOT_ACCEPTED / NONE.

## TDD and review

Initial15 cases failed because the reader was absent, then passed8.595s.
Additional real vectors cover filled unit/population preservation, parse-time
tamper/expiry, serialization-time withdrawal and absent root/no creation.
Actual-original diagnosis exposed embedded-font size and Windows Unicode pipe
failures. Two independent fixture cases failed before fixes and passed after;
content/text limits remain enforced. Dependency-focused30/30 passed51.976s
before the final review fixes. Fresh Astra reviewer ran21/21 in45.367s.

Reviewer identified two Important defects: self-resealed checked_at=-1 or
pre-acquisition time accepted; duplicate end delimiters silently truncated
revision text. Executor reproduced both as two RED cases/three failures,
then repaired minimum acquisition chronology and unique ordered delimiters.
One fix pass, not another reviewer; full regression/final-SHA CI pending below.

Complementary Wolfram model executed2026-10-11T21:51Z:1,350 finite integer
combinations, a/t∈0..2,c∈-1..4,n∈0..4,e∈1..5. Old guard c≤n<e accepted305
pre-acquisition chronologies, including(a,t,c,n,e)=(0,0,-1,0,1). Repaired guard
max(a,t)≤c≤n<e accepted zero such cases. The old expiry guard already rejected
n≥e; chronology was the missing condition, not an expiry-policy relaxation.
Certainty VERIFIED/confidence B for executed finite model only. No parser,
byte-hash, authentication, concurrent-file or runtime/governance proof follows.
Reproduce in Wolfram Language:

```wl
rows=Tuples[{Range[0,2],Range[0,2],Range[-1,4],Range[0,4],Range[1,5]}];
old=Select[rows,Function[x,x[[3]]<=x[[4]]<x[[5]]]];
repaired=Select[rows,Function[x,Max[x[[1]],x[[2]]]<=x[[3]]<=x[[4]]<x[[5]]]];
{Length[rows],Length[Select[old,Function[x,x[[3]]<Max[x[[1]],x[[2]]]]]],
 Length[Select[repaired,Function[x,x[[3]]<Max[x[[1]],x[[2]]]]]]}
```

Final: minor (deferred): invalid CLI ID/root constructs outside the exception
handler, yielding traceback rather than short diagnostic. It rejects without
stdout or effects; consistency polish is deferred, not hidden as completion.

Final review rulings, every declined topic and cost if wrong:

1. Hard memory/sandbox isolation: not claimed for this standalone candidate;
   residual hostile-decoder memory/exploit risk retained. Cost: agent-machine
   resource failure; never installed background operation.
2. Fully replaced receipt/historical check authenticity: hash IDs are not
   signatures; exact known identity and acquisition lower bounds enforced.
   Cost: unauthenticated plausible historical check instant; never authority.
3. Embedded hyperlinks: retain literal text only, no browser/network following.
   Cost if interpretation changed: unintended network effect, prohibited.
4. Truth/reuse/annual equivalence/root independence/causality: remain unconfirmed
   or not established, not parser verdicts. Cost: false Intelligence/promotion
   if a later consumer discards these mandatory boundaries.
5. Exhaustive actions/concurrent filesystem/inherited quarantine races: review
   did not establish atomic-snapshot or exhaustive hostile-PDF guarantees.
   Final byte fences/known paths and explicit residual risk stand. Cost:
   concurrent post-fence replacement or hostile parser failure; no installed use.
6. Cross-platform/dependency vulnerability/real-original/full regression/CI:
   review alone establishes none. Execute original demonstration, full suite
   and exact hosted3.11 CI separately; pin is not security certification.
   Cost if skipped: false portable/verified claim; no closure until evidence.

## Verification boundary

Final full regression1117 unique cases in1991.046s:1116 passed, one Windows
symlink-permission skip, zero failures/errors. Includes all23 new PDF cases
and both review repairs. Log `.runtime/statbel-pdf-full-regression.log`, SHA256
aa9b8bb5d62ba75e2af1a6bacd389b1ef5944a1d1bae1c74ca0edda03f23daba.
Source/test code stayed frozen during this final execution. JavaScript18/18,
compileall, launcher and git diff checks passed. Stable changed-tree preflight
24/24 passed at2026-10-11T21:38:24Z (dirty candidate), not committed-SHA evidence.
Actual post-fix reopen/verification:11 fields, five original/receipt files
unchanged, no source requests, acquired1791754122/terms1791754118,
checked1791754731/expiry1791840518, runtime NONE. Final CLI log
`.runtime/statbel-pdf-original-review-final.json`, SHA256
2b3abf60819b6901a495c6986aafcd3f4a1d973357e3e969dda163f48a8236d9.
New committed-SHA/preflight/CI receipts remain separate until executed.
No product arista or governance gate is promoted by these tests.
P04 parent remains INSUFFICIENT EVIDENCE for actual approved comparable sources.
Next: retained collection recovery/admission consumers only where specified;
source approval, need policy and installed activation remain separate decisions.

Context: Notion plan fetched2026-10-11, latest contextual projection from
17:49:37Z; it does not approve this source. Slack public search returned no
Telecare decisions earlier this cycle. Earlier Wolfram call failed internally;
new guard-model input/context and evaluator succeeded later as recorded above,
not as runtime evidence. GitHub exact CI remains executable immutable evidence.
