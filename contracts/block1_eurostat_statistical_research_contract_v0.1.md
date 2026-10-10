# Eurostat statistical research candidate v0.1

Status: CANDIDATE / LABORATORY_INTERNAL_SUPERVISED / NOT_ACCEPTED.
Producer: agent ResearchAcquirer and research_statistics; consumer: local
construction research only. Owner collection authority: AGENTS.md 2026-10-03;
source admission, binding, shared semantics and runtime adoption retain their
existing authority and MAR. This is not a generalized API client.

## Objective and selected scope

Extend the quarantined collection mechanism with one fixed official API recipe:
tran_r_mago_nm, annual A, freight loaded/unloaded FR_LD_NLD, thousand tonnes
THS_T, Belgium BE, 2023 and 2024. This is the existing workbook metric/scope,
not a national customs CIF measure or an independent source root. Observable
closure: acquire exact API bytes and normalize two declared year cells with
publisher update, missingness, flags, unit and retained identity, or explicitly
reject an invalid response. Never infer no change or zero from absent values.

The fixed HTTPS endpoint/query follows Eurostat's API Statistics guide:
https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-detailed-guidelines/api-statistics
JSON-stat 2.0 semantics: https://json-stat.org/format/ . The last dimension
varies fastest; category positions are authoritative, not label/key order.
Full generic JSON-stat support, additional geographies/periods/datasets,
cross-publisher corroboration, revision cause and runtime ingestion are excluded.

## Collection and compatibility

Reuse current terms lineage, pinned public-address TLS, no redirect/retry,
framing/byte/deadline limits and atomic content-addressed quarantine. Accept
application/json for this recipe only; HTML recipes still require text/html.
Only this exact fixed query is permitted; arbitrary query parameters are not.
Receipt version/schema remain 0.1.0; old recipe identities and readers are
unchanged. Existing methodology review must reject statistical candidates.
An HTTP error, access denial, asynchronous warning or incompatible response is
not a reason for unbounded polling or fallback to an unverified endpoint.

## Normalization and failure

Strict UTF-8 JSON <=1 MiB, no duplicate keys, NaN/Infinity or error/warning
envelopes. Require dataset/class/version, ESTAT source, nonempty bounded title,
ISO publisher update (Z, valid +/-HH:MM or publisher compact +/-HHMM offsets;
preserve unspecified timezone rather than assuming UTC) and exact five dimensions; size/category positions must
be bijective and exactly match the selected scope (two time categories).
If extension dataset identity is supplied, require TRAN_R_MAGO_NM.
Accept dense/sparse numeric values and dense/sparse/global status in the
documented JSON-stat shapes; reject bool, nonfinite/negative values, out-of-range
or noncanonical cell indexes, mismatched lengths/labels, scope and shapes.
Preserve both year cells; absent/null values remain missing. Flags are raw
bounded strings, not interpreted causes. No aggregation or unit conversion.

Read the known statistical and terms receipts before and after parsing; reject
substitution, stale/future/tampered dependencies. Bind both hashes/expiries and
use their earliest expiry, as the methodology review already requires. Reports
are reproducible and read-only: QUARANTINED_NOT_ADMITTED / NOT_RESOLVED /
NOT_ACCEPTED, runtime NONE, publication BLOCKED, root UNCONFIRMED.
Fingerprint is integrity, not attestation. No dossier/journal/task writes,
scheduler activation, source approval or signed adapter migration.

Positive oracle: independently stated values by period, including reversed
category order and sparse missingness; integration: retain/reopen/replay exact
bytes with terms linkage and stable state. Adversarial: malformed scope/index,
warnings, duplicated JSON, nonfinite values, flags/size, metadata recipe
substitution, tamper and parsing-time expiry. A real acquisition separately
demonstrates access, not source truth, independent corroboration or acceptance.
Rollback removes this recipe/review while retaining quarantine history.
