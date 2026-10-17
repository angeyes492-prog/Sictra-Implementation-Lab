# Comparable official source search — Belgian maritime freight

Date: 2026-10-07, America/Tegucigalpa. Scope: `LABORATORY_INTERNAL_SUPERVISED`.
Backlog item: `COMPARABLE-APPROVED-INPUT`. Research disposition only;
`NOT_ADMITTED`, `NOT_RESOLVED`, no runtime effect or gate change. This review
used official publisher pages as discovery/inspection, not downloaded originals.
No new candidate receipt, content hash, approval, binding or independent
attestation was created. The previously retained Eurostat statistical response
is historical research evidence; its 24-hour receipt is expired.

## Exact need and reference

The current Block 1 reference is Eurostat `tran_r_mago_nm`, annual `A`,
`FR_LD_NLD` (freight loaded and unloaded), `THS_T`, `BE`, years 2023 and 2024.
The [earlier official API acquisition](telecare_official_research_acquisition_2026-10-03.md)
retained 272698.25 and 274369.05 thousand tonnes, with publisher update
`2026-03-17T23:00:00+0100`; raw SHA-256
`5525b2ac0f59d6439f62829ecda9a2bc7727d91486e6a3475fbda3965c8a6175`.
That observation and its rights receipt are expired for current use. The
question here is whether a second *upstream-independent* official observation
measures the same Belgian annual gross freight, not whether another URL
repeats similar figures. Certainty for the historical bytes: `VERIFIED`, B;
currency and admissibility on 2026-10-07: `INSUFFICIENT EVIDENCE`.

## New official findings

1. The direct [Statbel sea-transport page](https://statbel.fgov.be/en/themes/mobility/transport/sea-transport)
   was readable through public search/inspection on 2026-10-07. This is a
   changed access observation from the challenged French page reported on
   2026-10-03; no challenge was bypassed or reattempted. Its annual table
   reports loaded/unloaded (thousand tonnes) of 126590/146397 for 2023 and
   128118/146776 for 2024. Arithmetic totals are 272987 and 274894 thousand
   tonnes, respectively. Against the *expired historical* Eurostat response,
   the differences are +288.75 and +524.95 thousand tonnes. The difference
   is a question about release version, population, aggregation or method,
   not evidence of a particular revision cause and not a current same-release
   contradiction. Statbel lists quarterly and annual tables, downloadable
   source files, and a quarterly publication cadence. The page's new headline
   is dated 2026-09-04; it is not a release timestamp for either 2023 or 2024
   row. Certainty: `VERIFIED`, B for the rendered table and arithmetic;
   `UNCONFIRMED`, D for causal explanation.
2. The [Belgian Eurostat ESMS](https://ec.europa.eu/eurostat/cache/metadata/EN/mar_esms_be.htm)
   names Statistics Belgium as compiler, sea ports as the source, quarterly
   exhaustive port submissions and validation before transmission to
   Eurostat. The newer [Statbel product metadata PDF](https://statbel.fgov.be/sites/default/files/files/metadata/T7.STAT_DTST_743.CTAC_ORG_1.DIFF_LVL_1.FR.pdf),
   updated 2025-02-12, says its source is administrative data from all Belgian
   seaports and data collection reuses those administrative records. Therefore
   the Statbel web table is a *same-chain* publication candidate, not a second
   independent observation. It may help diagnose version/scope differences.
   The Statbel PDF marks revision policy/practice `Pas d'application`, while
   the older Eurostat Belgian ESMS, updated 2021-02-19, says corrections may
   be validated, transmitted and published when needed. These dated metadata
   statements need source-level reconciliation before any release-specific
   conclusion; they do not prove a 2023/2024 correction.
3. [Statbel reuse terms](https://statbel.fgov.be/en/cc-40) state CC BY 4.0 for
   Statbel-owned website information/data, subject to third-party exceptions;
   attribution, licence link and transformation notice are required. This is
   rights evidence for inspection/possible bounded retention, not source
   admission or proof that every linked file has identical rights.

## Candidate matrix against the fixed measurement

| Official candidate | Phenomenon / metric / unit | Geography / period / coverage | Method and upstream root | Decision |
| --- | --- | --- | --- | --- |
| [Statbel sea transport](https://statbel.fgov.be/en/themes/mobility/transport/sea-transport) | Maritime cargo loaded + unloaded, thousand tonnes; near the reference metric but exact transformation unproved | Belgian sea ports; annual 2023/2024 rows; all-port administrative coverage claimed in [metadata](https://statbel.fgov.be/sites/default/files/files/metadata/T7.STAT_DTST_743.CTAC_ORG_1.DIFF_LVL_1.FR.pdf) | Statistics Belgium compiles port administrative data and sends national records to Eurostat, per [Belgian ESMS](https://ec.europa.eu/eurostat/cache/metadata/EN/mar_esms_be.htm) | Reject as independent corroboration; inspect as same-chain release/scope comparison after retained bytes and versions are bound. |
| [Port of Antwerp-Bruges 2024](https://newsroom.portofantwerpbruges.com/en/press-releases/annual-figures-for-port-of-antwerp-bruges-show-growth-despite-challenging-times) | Total port throughput, about 278 million tonnes, not an established Eurostat gross-weight transformation | One combined port, calendar 2024; not all Belgian sea ports | Port authority is an upstream reporting party for the national port collection; overlap is plausible and exact contribution unresolved | Reject: geography/coverage mismatch and likely origin overlap. No sum with other port sites without an explicit port universe and matching definitions. |
| [ESPO Rapid Exchange](https://www.espo.be/fact-and-figures) | Port throughput statistics; a compatible exact measure was not established | Official search excerpt describes voluntary quarterly submissions from European port authorities; Belgian 2023/2024 all-port series not established | The claimed port-authority source would overlap Belgian national inputs; [Eurostat ESMS](https://ec.europa.eu/eurostat/cache/metadata/EN/mar_esms.htm) warns ESPO/port figures can differ in scope, definitions and method | Reject as proven independent/same-scope source; direct ESPO page retrieval failed, so its own method/rights remain `UNCONFIRMED`. |
| [UNCTAD container throughput](https://unctadstat.unctad.org/datacentre/reportInfo/US.ContPortThroughput) | Official search excerpt describes containers in TEU, not total cargo mass in thousand tonnes | Country annual series; smaller-port coverage requires direct confirmation | Excerpt names intermediaries and ultimate port-authority/industry sources; possible root overlap | Reject: metric/unit mismatch. Direct report-info page retrieval failed; method details remain `UNCONFIRMED`. |
| [UNCTAD AIS port calls](https://unctadstat.unctad.org/datacentre/reportInfo/US.PortCallsArrivals_S) | Official search excerpt describes vessel arrival calls, not freight mass | Country annual/half-year; AIS ship threshold and suppression require direct confirmation | Excerpt identifies MarineTraffic AIS and port mapping, a distinct measurement channel for *calls* | Reject for the current freight need. Direct report-info page retrieval failed; could be a separately versioned vessel-call candidate after direct method review, not an implicit substitution. |

## Next bounded experiment and promotion boundary

Reacquire the *fixed* Eurostat API recipe and current reuse notice under the
existing research budget, and retain exact official Statbel table/source-file
bytes in a separate candidate quarantine only after an explicit fixed
`statbel.fgov.be` recipe with pinned-public TLS, redirect/size/media/rights
checks and positive/adversarial tests. Bind each acquisition UTC, publisher
version if available, URL, SHA-256 and terms expiry. Then compare 2023/2024
loaded, unloaded and total values at the same release cutoff and examine the
port universe and calculation notes. Observable result: a source-specific
`SAME_ROOT_VERSION_OR_SCOPE_REVIEW_REQUIRED` explanation or an explicit
unexplained difference, never `CORROBORATED`. No attempt to replay expired
receipts or generalize arbitrary URLs. A *separate* admissible root still
requires an independently collected, same-scope mass observation with rights,
revision policy, original bytes and an approved source/binding lineage. If
none exists publicly, the corroboration need remains insufficient and any
alternative phenomenon requires a versioned contract/MAR decision.

Budget for this review: 14 search queries, 6 attempted official-page opens
(4 returned content) and 5 page finds through the web reader; internal crawler
requests are not observable. ESPO and UNCTAD report-info claims above rely
only on official-page search excerpts because direct opens returned an error.
Direct file downloads: 0; retained bytes: 0; network retries: 0; access-denial
retries: 0. Search snippets were used to locate official pages; claims above
are attributed to the linked official publishers. No external contact,
installed-runtime acquisition or publication occurred.
