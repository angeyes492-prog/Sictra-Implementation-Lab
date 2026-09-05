# Source-admissibility dossier — UN Trade and Development (UNCTAD) v0.1

- `DOSSIER_ID`: `BLOCK1-SOURCE-UNCTAD-001`
- `DATE`: `2026-09-05`
- `STATE`: `RETIRED_BY_OWNER_DECISION / CONTRADICTED`
- `CONFIDENCE`: `A` for the recorded primary-source observations; `E` for runtime admissibility
- `CANDIDATE`: `unctad` / UN Trade and Development
- `INTENDED_SCOPE`: global maritime and trade intelligence
- `PROPOSED_ACCESS_METHOD`: `MANUAL_SOURCE_BUNDLE`
- `RUNTIME_STATUS`: retired; no registration, binding, approval record, manual bundle or observed source exists

## Decision

**Do not admit, ingest or reconsider this source without a new owner decision.**
The owner retired UNCTAD on 2026-09-04 after preserving the unresolved conflict
between general site terms and the Data Hub FAQ. This dossier is historical
evidence, not a candidate, licence approval or authorization to acquire data.

## Primary-source observations

| Observation | Evidence | Classification |
| --- | --- | --- |
| UNCTAD's 2025 Review of Maritime Transport is an official recurring maritime publication and describes maritime trade, capacity, freight-rate and chokepoint context. | [UNCTAD, *Review of Maritime Transport 2025*](https://unctad.org/publication/review-maritime-transport-2025) | `VERIFIED / A` |
| The UNCTAD Data Hub FAQ states that its data and metadata are under Creative Commons Attribution 3.0 IGO, may be copied/distributed with source citation, and are free without registration. | [UNCTAD Data Hub FAQ](https://unctadstat.unctad.org/EN/FAQ.html) | `VERIFIED / A`, **limited to the named Data Hub scope** |
| General UN site terms permit personal, non-commercial download/copy subject to terms and note that specific material may carry additional restrictions. | [UNCTAD terms](https://unctad.org/terms) | `VERIFIED / A`, not sufficient to authorize commercial or derivative reuse |
| A separate UNCTAD Data Hub copyright page says materials may not be used or reproduced except under applicable terms or written permission, while making a distinct allowance for news material. | [UNCTAD Data Hub copyright](https://unctadstat.unctad.org/EN/Copyright.html) | `VERIFIED / A`; potential scope conflict requiring explicit resolution |

## Contract-fit assessment

| Required control | Result | Why |
| --- | --- | --- |
| Canonical source identity | `RETIRED / A` | The owner removed `unctad` from the bounded portfolio. |
| Host allowlist | `CONTRADICTED / A` | The candidate currently lists `unctad.org`; the Data Hub pages are hosted at `unctadstat.unctad.org`. A host cannot be silently widened. |
| Terms/licence reference | `INSUFFICIENT EVIDENCE / A` | The FAQ and copyright page have overlapping but not identical reuse wording. The intended material and use must be tied to one authoritative licence interpretation. |
| Claim authorization | `INSUFFICIENT EVIDENCE / A` | No approved claim keys, temporal limits or allowed dataset/report slice exist. |
| Access method | `INSUFFICIENT EVIDENCE / A` | The runtime permits only manually supplied bounded bundles; no such bundle was evaluated. |
| Reviewer identity and approval record | `INSUFFICIENT EVIDENCE / A` | Required by the contract; absent by design. |
| Provenance root and observed evidence | `INSUFFICIENT EVIDENCE / A` | These can only be issued after a valid binding and bundle validation. |

## Reconciliation

The apparent licence tension is not resolved by choosing the more permissive
statement. The FAQ may govern **Data Hub data and metadata**, while the broader
copyright page and general terms may govern other material. The intended
artifact must therefore be specified before any admissibility decision:

1. **Data Hub route:** register the exact Data Hub hostname(s), identify a
   named dataset and require citation under the FAQ's stated CC BY 3 IGO terms.
2. **Publication route:** use a specific report from `unctad.org`, then obtain
   an explicit reuse determination for the intended excerpt/derived use.
3. Reject any route that cannot produce a reviewer-approved terms reference,
   exact host allowlist, claim scope and byte limit.

## Forbidden transitions

This dossier does **not** authorize:

- modifying the host allowlist;
- treating a web page, report or search result as an observed source;
- network fetching, scraping, credentials or scheduling;
- using an UNCTAD statement in a newsletter, dashboard or customer output;
- changing the Block 1 gate.

## No next action

UNCTAD is retired from the source portfolio. Any future reconsideration requires
a fresh owner decision and a new evidence dossier; this historical dossier may
not be promoted or reused as an approval draft.
