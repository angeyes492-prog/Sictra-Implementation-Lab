# Contract — Local Eurostat operator pipeline v0.1

Version `0.1`; producer/consumer:
`sictra_block1.operator_pipeline`. Scope:
`BLOCK1_LOCAL_EUROSTAT_OPERATOR_PIPELINE`. Authority: controlled local
orchestration for the already approved Eurostat `tran_r_mago_nm` path only.
It has no network, approval, publication, interpretation or gate-promotion
authority.

`init(root)` accepts only an empty regular local directory or its exact prior
manifest. It creates 32-byte local keys and a first signed source binding from
the retained approval. A non-empty uninitialized directory, symlink, malformed
manifest, unsafe key, historical ledger tamper or expired binding fails closed.
The manifest carries no secret.

`ingest(root, workbook, geo_level)` accepts one regular local XLSX file and
one of `COUNTRY`, `NUTS1`, `NUTS2`. It preflights the supplied bytes, enforces
the exact Eurostat dataset URL/scope, then performs the documented chain. The
response returns only status receipts. A baseline has no dossier. A changed
release can create a dossier containing literal facts and explicit limits;
publication authority is always `NONE`.

E01–E08 receives only evidence whose attestation is current at the shared
trusted clock. Expired retained receipts are lineage, not runtime input. The
watchlist requires exactly one current attested source record. Stale, duplicate,
altered, malformed, out-of-scope or unsafe inputs reject before the relevant
downstream state can advance.

`backup(root, destination)` writes a new external directory containing hashes
of source-control, evidence, watchlist and dossier ledgers after a stable
read/revalidation. Keys and runtime SQLite journal are excluded. `restore`
requires an external exact backup and an entirely absent local ledger set; it
never overwrites data and revalidates under the original local keys. This is a
local recovery mechanism, not cross-device portability, key recovery or a
production backup system.
