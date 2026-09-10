# Contract — Dossier workspace reader v0.1

Version `0.1`; producer `sictra_block1.lab_web`, consumer local browser. Scope
`BLOCK1_LOCAL_DOSSIER_READER`. Authority: integrity-verified read only.

## Inputs and outputs

- `create_server(dossier_store=...)` accepts only an
  `IntelligenceDossierStore`; omission is the explicit unconfigured state.
- `GET /api/dossiers` returns `NOT_CONFIGURED` with zero dossiers, or
  `AVAILABLE` with bounded summaries recomputed from a verified ledger.
- `GET /api/dossiers/{dossier_id}` returns exactly one verified dossier plus
  its `DossierEditorialBridge` result.
- `/health` reports `NOT_CONFIGURED`, `AVAILABLE` or `INTEGRITY_ERROR` for the
  reader. It does not promote overall health or a gate.

List/detail responses expose fact, interpretation and hypothesis counts,
review/publication state, the recomputed dossier and the blocked editorial
candidate. They never expose integrity keys, bridge attestations, filesystem
paths or write controls. `publication_authority` is always `NONE`.

## Failure and compatibility

Unknown identities and malformed paths return `404`; unexpected query
parameters return `400`. Ledger mutation, wrong key/configuration or a bridge
result that escapes the required editorial block returns `500` and no dossier.
The UI may continue showing unrelated synthetic laboratory functions, but it
must display the reader integrity error and may not substitute synthetic
content in the dossier panel.

Version `0.1` does not configure secrets, ingest data, select editorial
content, create a Block 2 handoff, publish, authenticate users or grant gate
authority.

