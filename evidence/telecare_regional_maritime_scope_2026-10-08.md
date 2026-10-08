# Regional maritime scope research — 2026-10-08 UTC

Scope: agent-only `LABORATORY_INTERNAL_SUPERVISED` research. The retained
document is official Eurostat methodology, not an independent measurement,
source admission, runtime input or explanation of the two numeric gaps.

## Original bytes and rights lineage

The fixed pinned-TLS recipes made two successful official GET requests, no
redirects and no retry. The current [Eurostat reuse notice](https://ec.europa.eu/eurostat/help/copyright-notice)
was retained at 2026-10-08T19:16:21Z under candidate
`c9ca37be396a5c86d1ff4ede5febaf7ebe16b9360b677c85d7b24e56c98ab7a0`:
178,940 bytes, SHA-256
`aefa39b4c47665e8b7afed9a6e114cd2219d02385fe2f2f39d05e31ce633ace4`.
The exact [regional transport methodology](https://ec.europa.eu/eurostat/cache/metadata/en/tran_r_esms.htm)
was retained at 2026-10-08T19:16:30Z under candidate
`4671b996f6b9f1fcac0558d063959028d9eefa74d27aff02791dcc438243a33c`:
229,673 bytes, SHA-256
`691449ac5aba1ea41e1ed6eab3e1c60c11f7df8d46b9b01ecb16ad23ce5d0db8`.
The metadata descriptor binds the above reuse-notice candidate. Local originals
are in ignored `.runtime/research-quarantine-2026-10-08-regional/`; the IDs,
hashes and descriptors are recorded here. Across the two independent CLI
sessions: two GETs and 408,613 retained bytes, below the cycle budget of 100
requests, 100 MiB retained and 8 MiB per file. Both receipts expire no later
than UTC epoch `1791573381` (2026-10-09T19:16:21Z).

## Scope finding and limit

The read-only review reopened both original files, parsed the named `data_descr`
section and rechecked both files and clocks before handoff. Section SHA-256:
`ade168da5116dcc6d40ca6bc20adefeb9b03161951bef6c673a5e41bc6ce7d77`.
The section names `tran_r_mago_nm` as regional maritime freight and states that
regional maritime aggregation uses main ports only, with the detailed-data
threshold of more than one million tonnes of goods or more than 200,000
passenger movements annually. It also describes exclusion of double counting.
The report's narrow label is `EXPLICIT_MAIN_PORTS_ONLY` for the Eurostat regional
series. The [Statbel sea-transport table](https://statbel.fgov.be/en/themes/mobility/transport/sea-transport)
labels its figures as cargo loaded/unloaded at Belgian sea ports but does not
establish an identical port selection, aggregation and release cutoff.

Thus the earlier Statbel/Eurostat +288.75 and +524.95 thousand-tonne differences
remain arithmetic observations. Scope equivalence and the specific cause of
either gap remain `UNCONFIRMED`; different publication hosts do not create an
independent root. The exact-methodology review remains `NOT_ADMITTED`,
`NOT_RESOLVED`, runtime `NONE`, publication `BLOCKED`. Source authority still
owns approval; architecture authority still owns any runtime connection.
The existing four-receipt same-chain CLI was rerun while current at UTC epoch
`1791487678`; it reproduced those two gaps with `NOT_ADMITTED`, `NOT_RESOLVED`
and `NONE` runtime. Its earliest receipt expiry was `1791497939`.

## Executable evidence

The acquisition recipe is restricted to one exact official URL and a current
Eurostat terms receipt. The reviewer accepts only the regional recipe, the
named section and the full publisher sentence; wording changes or negation
yield `UNCONFIRMED`. Focused tests exercise reopen, rights/recipe substitution,
missing or duplicate section, expiry, altered bytes, changed second read,
clock crossing, forged report and negative wording. The first real read
returned `UNCONFIRMED` because the prototype selected `stat_conc_def`; the
retained original showed the passage under `data_descr`, and the corrected
reader returned `EXPLICIT_MAIN_PORTS_ONLY`. The negated-sentence test reproduced
and repaired a false positive from checking isolated phrases.

The new acquisition test failed first with `RECIPE_UNSUPPORTED`; the new
regional-review test failed first because the module was absent. The actual
source review exposed a wrong selected anchor (`stat_conc_def`), and a
negated-sentence test reproduced a false positive. A read-only code review
then found that a prefixed denial or struck-through sentence could still
receive the positive label; a new adversarial test failed twice and the
standalone-paragraph/retraction guard repaired both. Focused regional tests
passed 7/7 and acquisition tests 18/18. Final-tree full Python discovery
passed 1021/1021 in 917.531 seconds. JavaScript passed 18/18, `compileall`
succeeded and changed-tree preflight passed 24/24 with
`product_completion=NOT_DEMONSTRATED`. No gate is promoted by this research
result.

## Version and watchlist boundary: second official capture

The second capture is agent-only quarantined research, not an admitted
watchlist input or a second publisher release. At 2026-10-08T19:38–19:40Z,
the exact Eurostat response was retained as candidate
`5b04040309fec39c9c9e3a4f98a969623a4abe719fe1ab57c480147305a2b497`
(2,647 bytes, SHA-256
`5525b2ac0f59d6439f62829ecda9a2bc7727d91486e6a3475fbda3965c8a6175`),
with new current reuse-notice candidate
`35d446d4d849c83474cb01e002241e8664646ad3cf1e415dcab478780e72b2f8`.
The data hash exactly matches its 2026-10-07 capture. Its publisher-updated
field remains `2026-03-17T23:00:00+0100`; no measured byte or declared-release
change was observed for the fixed 2023/2024 slice.

The new Statbel page is candidate
`6145e74431bf592714ad8dd2b8ccb478af8b7071d5e1579d40fb5fb9adebcfbd`
(111,670 bytes, SHA-256
`c41fb8a1c41db4bf3784ea4a2f1ad144751b787278acb7277adc7c1cb92b3fea`),
with terms candidate
`7ab86d377d21d26bee37d926139df686da23dcbfe996adfa1fd55f41ccda7a34`.
The prior page hash was
`b8055a0d49022935200f21687cd90ab0026243331b49cf02439d0f9e3d6cc922`,
so raw HTML changed. The second read-only same-chain extraction nonetheless
returned the identical 2023/2024 loaded/unloaded rows and gaps (288.75 and
524.95 thousand tonnes), with `publisher_release_extracted=UNAVAILABLE`.
The page-byte difference cannot be classified as a statistical revision or
phenomenon change; it may include unrelated markup/content. The report
fingerprint was `06541ed2cf9fbabf397daa282fecdd1d8c1c79a03d3360b8f2c22443abc54f52`;
its earliest expiry was UTC epoch `1791574726`.

This recapture made five official GET attempts across the two source chains:
four successfully retained files, 385,629 retained bytes. One Statbel data
attempt fetched bytes but failed the local atomic rename with WinError 5; the
target was absent and no `.pending` file was selectable, and one bounded
retry succeeded. Including the failed fetch, at most 497,299 bytes were
received. The source pages' terms bytes also changed, but terms-page byte
changes do not establish data revision. Existing watchlist code already
distinguishes version states under its admitted-input contract; these research
receipts are not silently injected into it. The source pair remains
`NOT_ADMITTED`, comparability `UNCONFIRMED`, revision explanation
`INSUFFICIENT EVIDENCE`, runtime `NONE`.
