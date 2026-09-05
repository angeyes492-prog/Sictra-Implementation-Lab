# Contract — Manual source preflight v0.1

Producer: `sictra_block1.manual_source_preflight`. Consumer: the future
operator-guided ingress. Scope: `BLOCK1_MANUAL_SOURCE_PREFLIGHT`. Authority:
format screening only.

The function accepts a bare `.csv` or `.xlsx` filename and a non-empty byte
payload no larger than 131,072 bytes. It rejects traversal-style filenames,
unsupported extensions, malformed payloads, invalid UTF-8 CSV, embedded NULs,
inconsistent CSV rows, malformed XLSX/XML, DTD-bearing worksheet XML, archives
with excessive expansion, and workbooks without at least a two-column header
and one tabular data row.

A structurally usable file returns `READY_FOR_SCHEMA_REVIEW` with a SHA-256 and
detected table-row count. That structural count is not a count of validated
business records; XLSX files can include metadata rows. An empty or malformed
file returns `REJECTED_NOT_EVIDENCE`.
Neither result creates a source, claim, binding, attestation, persistence,
license decision, network request or gate promotion. Schema mapping, source
approval, signed binding and independent data review remain separate controls.
