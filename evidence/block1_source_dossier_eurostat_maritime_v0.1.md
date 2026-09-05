# Block 1 source dossier: Eurostat maritime data

| Field | Value |
| --- | --- |
| Dossier ID | `BLOCK1-SOURCE-EUROSTAT-MARITIME-001` |
| As of | 2026-09-04 |
| Source identity | Eurostat / European Commission |
| Source portfolio state | `PROPOSED` |
| Runtime admission state | `NOT BOUND`; `NOT EXECUTED`; `NOT VALIDATED` |
| Decision state | `INSUFFICIENT EVIDENCE` (admission); confidence `A` for the cited terms and dataset description |
| Intended scope | `BLOCK1_EUROPE_MARITIME_INTELLIGENCE` |

## Bounded candidate asset

The candidate is limited to Eurostat's *Maritime transport of freight by NUTS 2 regions* dataset, identifier `tran_r_mago_nm`, and its official maritime metadata.  Eurostat's maritime reference manual identifies that dataset and describes the maritime freight, regional and reference-period context.  The portfolio may therefore describe Eurostat as a proposed European `MARITIME` candidate; this dossier does **not** admit a source, create an evidence record, or authorize a network connector.

Candidate claim vocabulary, only if later approved and bound:

- `maritime_freight_weight_thousand_tonnes`
- `maritime_freight_load_unload_split`
- `maritime_freight_nuts2_coverage`

## Terms evidence and reuse boundary

Eurostat's copyright notice states that reuse of its statistical data, metadata, publications and dissemination tools is authorized for commercial and non-commercial purposes with attribution, subject to stated exceptions.  Its editorial content is CC BY 4.0.  The intended use is restricted to official statistical data and metadata from `ec.europa.eu`, with attribution to Eurostat, the access date, and an indication of transformations.

The following remain excluded unless a separate, asset-specific review authorizes them:

- third-party material, including any content whose rights are not held by the European Union;
- logos, trademarks and other brand assets;
- named exceptions in the copyright notice, including certain non-EU data and trade-data restrictions;
- materials served from any host not present in the signed allowlist.

Sources consulted:

- Eurostat, [Copyright notice](https://ec.europa.eu/eurostat/help/copyright-notice), accessed 2026-09-04.
- Eurostat, [Reference Manual on Maritime Transport Statistics](https://ec.europa.eu/eurostat/documents/d/transport/reference-manual-maritime-july-2026), accessed 2026-09-04.
- Eurostat, [Maritime transport metadata](https://ec.europa.eu/eurostat/cache/metadata/en/mar_esms.htm), accessed 2026-09-04.

## Admission controls

The proposed registration is intentionally manual-only and capped at 131,072 UTF-8 bytes per bundle.  It is blocked by the `SourceGateway` unless all of the following exist:

1. A human reviewer creates an `APPROVED` source record matching the host, claim keys, method and size limit exactly.
2. A trusted issuer creates a signed binding for a `BOUND` registration.
3. A manual bundle uses HTTPS on `ec.europa.eu`, a permitted claim key, an in-window observation time and content inside the limit.
4. The resulting evidence is independently reviewed for attribution, asset scope, numerical interpretation and relevance before editorial use.

The current test deliberately proves the inverse: a `PROPOSED` Eurostat draft cannot attest even a fixture bundle.  This is a contract regression, not evidence that Eurostat has been ingested or that Block 1 is operational.

## Human decision required

The reviewer must record a decision against `evidence/block1_eurostat_maritime_registration_draft_v0.1.md`, including reviewer identity, review date, exact terms evidence reference, confirmation that the selected asset is not an exception, and `APPROVED` or `REJECTED`.  Until then, the correct state is `INSUFFICIENT EVIDENCE` / `NOT BOUND`.
