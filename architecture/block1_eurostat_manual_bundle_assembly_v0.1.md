# Block 1 — Eurostat manual bundle assembly v0.1

`IMPLEMENTED CANDIDATE / LOCAL-TESTED / B`. This Layer 4 boundary turns one
explicitly selected geography level from the bounded `tran_r_mago_nm` mapper
into the exact seven-field payload expected by the governed manual source
gateway. It has no binding key, evidence issuer, persistence, network,
publication, insight or gate authority.

The caller must supply the original Eurostat HTTPS dataset URL, an observation
time and a correlation identifier. The URL must name `tran_r_mago_nm` on
`ec.europa.eu`; the selection must be exactly `COUNTRY`, `NUTS1` or `NUTS2`.
The assembler preserves the input file SHA-256, source-declared update time,
controlled filters, selection coverage and individual observations in a
canonical JSON content payload. It never selects a geography level, fills a
missing value, sums levels, or converts `:` to zero.

The resulting payload is `UNATTESTED_MANUAL_BUNDLE`, encoded inside
`content`; it remains non-evidentiary until a current matching source binding
and `SourceGateway.attest_manual_bundle` create a separately signed observed
record. Construction is deliberately not equivalent to admission, execution,
validation or acceptance.

If the URL, time, correlation identifier, selection or byte budget is invalid,
assembly fails closed. The current Eurostat registration admits at most
131,072 UTF-8 content bytes; oversized selections must be narrowed through a
new governed contract rather than truncated.
