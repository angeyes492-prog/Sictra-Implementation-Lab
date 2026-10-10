# Retained Statbel / Eurostat same-chain research — 2026-10-07

Scope: `LABORATORY_INTERNAL_SUPERVISED`; agent-only research. State:
`QUARANTINED / NOT_ADMITTED / NOT_RESOLVED / NO_RUNTIME_EFFECT`. These
observations do not promote a source, attest a fact, or corroborate a second
independent root. The repository ledger remains the single backlog.

## Actual official acquisition

The fixed, pinned-TLS Statbel recipe retained exact bytes under ignored local
`.runtime/research-quarantine-2026-10-07-statbel/`. The [Statbel terms page](https://statbel.fgov.be/en/cc-40)
was acquired at 2026-10-07T22:18:59Z: candidate
`f9d10cad2c44264fbdb413bd8097fff2b98a6b5c38ecb8d14cce9d147f67385d`,
92,370 bytes, content SHA-256
`60c0f0d97afc75d8e547207fa583d80772c2ee6bb7f74121fd8a5e6f5c7686af`.
The [official sea-transport HTML](https://statbel.fgov.be/en/themes/mobility/transport/sea-transport)
was acquired at 2026-10-07T22:19:10Z: candidate
`04599383d7daa4bc3b46aa50e093d9fe82a756aa017673d21b398bd0ac981494`,
111,670 bytes, content SHA-256
`b8055a0d49022935200f21687cd90ab0026243331b49cf02439d0f9e3d6cc922`.
The latter receipt is bound to the former rights candidate. Both have a
24-hour research expiry. The source HTML was read back and hash-verified by
the quarantine reader. An initial TLS handshake failed because this Python
installation lacked the necessary default trust path; one retry with the
installed `certifi` CA bundle validated TLS normally. Verification was not
disabled, no challenge was bypassed, and redirects are rejected.

The existing fixed Eurostat recipe reacquired the [reuse notice](https://ec.europa.eu/eurostat/help/copyright-notice)
at 2026-10-07T22:20:34Z: candidate
`0341264fbad57b9f424cc87e248faa5df94ea70a5d946736a34d9cb39849e8ea`,
178,941 bytes, SHA-256
`e49b5c4849d69398dc3bf8bf6a0497a165e5802b51d7c561a454f3fd2268d1a0`.
The [fixed maritime API response](https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/tran_r_mago_nm?lang=EN&freq=A&tra_meas=FR_LD_NLD&unit=THS_T&geo=BE&sinceTimePeriod=2023&untilTimePeriod=2024)
was acquired at 2026-10-07T22:20:45Z: candidate
`9073c5120b201187f7302aa508e63074c92b68363ad539d4e3933fafafaaef12`,
2,647 bytes, SHA-256
`5525b2ac0f59d6439f62829ecda9a2bc7727d91486e6a3475fbda3965c8a6175`.
This data hash is identical to the earlier retained Eurostat response, so
the fixed query's original bytes did not change between those two acquisitions;
the new rights receipt makes this a current *research* candidate only.

Budget: four successful GETs, one failed pre-response TLS handshake, 385,628
bytes retained across four files, no redirect followed, no access-denial retry.
Each successful request used a separate CLI process with a one-attempt session
counter. Per-file size is below 8 MiB and aggregate retention below 100 MiB.
No source was admitted or sent to the installed Telecare runtime.

## Literal extraction and comparability boundary

The fixed HTML table reader selected exactly one sea-transport table and the
2023/2024 columns by header identity, independent of column order. It read:

| Year | Statbel loaded | Statbel unloaded | Arithmetic sum | Eurostat fixed `FR_LD_NLD` | Sum minus Eurostat |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2023 | 126,590 | 146,397 | 272,987 | 272,698.25 | +288.75 |
| 2024 | 128,118 | 146,776 | 274,894 | 274,369.05 | +524.95 |

All quantities are in thousand tonnes as labelled by each publication. The
Statbel page currently also displays a 2025 column; that is **not** a
release timestamp or proof of the revision history for 2023/2024. The
Eurostat response declares publisher update `2026-03-17T23:00:00+0100`;
Statbel HTML offered no unambiguous row-level release ID or revision receipt.
The fixed reader therefore records Statbel publisher release as `UNAVAILABLE`
and revision policy as `UNCONFIRMED`. The totals are arithmetic observations,
not proof that the two publishers' definitions, port universe, adjustments
or release cutoffs match. The difference's cause is `UNCONFIRMED`.

The [Belgian maritime ESMS](https://ec.europa.eu/eurostat/cache/metadata/EN/mar_esms_be.htm)
identifies Statistics Belgium as the compiler transmitting Belgian port
administrative observations to Eurostat. Accordingly, the two publications
are a same-upstream-chain version/scope question, not independent
corroboration. Original bytes and rights receipts do not substitute for source
approval/binding, an independent root, or a contracted `RESOLVED` need.

## Executable boundary and remaining decision

The new Statbel adapter accepts only two exact official HTTPS recipes, pinned
public-address TLS, fixed media/size/time/rights lineage and immutable hashed
quarantine. Tests cover replay/tamper/expiry, redirect, hostile DNS, wrong
media/size, wrong visible identity, duplicate table fields, malformed numbers
and units. Its table extraction is read-only and not imported by the installed
operations scheduler. These tests prove the bounded mechanism, not source
truth or compatibility of the two statistical definitions.

Next: establish the exact port universe/calculation and release-specific
metadata before classifying the numerical gap; find a truly independent
same-scope observation or retain `INSUFFICIENT EVIDENCE`. Source authority owns
admission, architecture authority owns shared runtime activation, and the
agent owns further bounded research. No gate changes here.
