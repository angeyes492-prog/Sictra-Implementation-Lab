# RETIRED historical registration draft — UNCTAD Data Hub maritime v0.1

- `DRAFT_ID`: `BLOCK1-UNCTAD-DATAHUB-MARITIME-REG-001`
- `STATE`: `RETIRED_BY_OWNER_DECISION / NOT BOUND / NOT APPROVED`
- `RELATED_DOSSIER`: `BLOCK1-SOURCE-UNCTAD-001`
- `PRODUCER`: Block 1 E02 Source Governance
- `CONSUMER`: Source Gateway v0.1, manual bundles only

## Historical proposed registration

```json
{
  "source_id": "unctad",
  "publisher": "UN Trade and Development — Data Hub",
  "scope": "BLOCK1_GLOBAL_MARITIME_INTELLIGENCE",
  "allowed_hosts": ["unctadstat.unctad.org"],
  "claim_keys": [
    "liner_shipping_connectivity",
    "port_call_performance",
    "container_port_throughput"
  ],
  "access_method": "MANUAL_SOURCE_BUNDLE",
  "max_content_bytes": 131072,
  "status": "PROPOSED"
}
```

## Why these bounds

- The exact Data Hub host is intentionally distinct from `unctad.org`; the
  host mismatch recorded in the source dossier must be resolved explicitly.
- Claim keys are vocabulary for controlled observations, **not claims already
  established by the system**.
- The 128 KiB cap permits a small, attributable manual excerpt/metadata bundle
  while making bulk acquisition impossible in this v0.1 slice.
- No URL pattern, account, credential, API token, scraper, scheduler or network
  permission is proposed.

## Approval record template

All placeholders below must be supplied by a human source-governance decision.
An empty field means the record is invalid and cannot issue a binding.

```json
{
  "source_id": "unctad",
  "reviewer_id": "<required-human-or-governed-reviewer-id>",
  "reviewed_at": "<required-unix-timestamp>",
  "terms_evidence_ref": "evidence/block1_source_dossier_unctad_v0.1.md#primary-source-observations",
  "allowed_hosts": ["unctadstat.unctad.org"],
  "claim_keys": [
    "liner_shipping_connectivity",
    "port_call_performance",
    "container_port_throughput"
  ],
  "access_method": "MANUAL_SOURCE_BUNDLE",
  "max_content_bytes": 131072,
  "decision": "<APPROVED-or-REJECTED>"
}
```

## Retired checklist

- [ ] Confirm that the Data Hub FAQ's CC BY 3 IGO statement governs the **exact**
      dataset, metadata and intended internal use.
- [ ] Confirm whether citation text, attribution placement and derivative-use
      conditions need additional controls.
- [ ] Approve or reject the exact hostname and reject all other subdomains.
- [ ] Approve or reject each claim key; add none implicitly.
- [ ] Confirm manual bundle provenance, observation time and correlation ID.
- [ ] Populate an approval record with a real reviewer identity and timestamp.
- [ ] Only after all checks pass, change registration to `BOUND` and issue a
      short-lived signed binding outside source code.

## Explicit non-claims

This retired draft has no legal effect and cannot be used as a source approval.
It creates no binding, admits no real evidence, changes no gate, and does not
authorize the system to contact UNCTAD or access the internet. A fresh owner
decision and a new dossier would be required before any reconsideration.
