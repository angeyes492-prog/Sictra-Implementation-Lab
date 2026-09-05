# Proposed registration: Eurostat maritime data

This record has an owner approval for the bounded asset below. It is not a
binding, data ingest or validated runtime source.

```json
{
  "source_id": "eurostat",
  "publisher": "Eurostat / European Commission",
  "scope": "BLOCK1_EUROPE_MARITIME_INTELLIGENCE",
  "allowed_hosts": ["ec.europa.eu"],
  "claim_keys": [
    "maritime_freight_weight_thousand_tonnes",
    "maritime_freight_load_unload_split",
    "maritime_freight_nuts2_coverage"
  ],
  "access_method": "MANUAL_SOURCE_BUNDLE",
  "max_content_bytes": 131072,
  "status": "PROPOSED"
}
```

## Owner approval record

| Required field | Reviewer entry |
| --- | --- |
| Reviewer identity | `PROJECT_OWNER` (decision recorded in this Codex task) |
| Review date | `2026-09-04` |
| Terms evidence reference | `evidence/block1_source_dossier_eurostat_maritime_v0.1.md` |
| Selected asset checked against exceptions | `APPROVED ONLY for Eurostat-owned statistical data and metadata in tran_r_mago_nm; exclusions remain blocked` |
| Attribution and change-notice method | `Eurostat dataset DOI/datacode + access date; disclose any transformation` |
| Decision | `APPROVED` |

An approval is valid only when its source ID, hosts, claim keys, access method and content limit exactly match this draft.  Any changed asset, exception, host, or term requires a new review.  Approval alone is not a signed binding, source execution, validation or gate acceptance.
