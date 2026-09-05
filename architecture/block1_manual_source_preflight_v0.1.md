# Block 1 — Manual source preflight v0.1

`IMPLEMENTED CANDIDATE / LOCAL-TESTED / B`. This is the first bounded part of
the operational-ingress layer. It sits before Source Gateway and accepts bytes
only from an explicit future operator action; it has no HTTP client, browser
upload route, persistence, credential access or automatic execution.

Purpose: distinguish a minimally tabular operator-supplied CSV/XLSX from an
empty, malformed or unsafe file before any schema mapping. Input: filename and
bytes. Output: format decision, SHA-256, detected table-row count and a
non-evidentiary state. XLSX row counts may include metadata until schema
mapping identifies data rows.
It cannot establish truth, licence scope, source identity, freshness or a
claim. Rejection is recoverable by exporting a proper table and resubmitting it
to the later guided-ingress surface.

The design limits payload and decompressed archive size, rejects XML DTDs and
does not retain a file. Its next dependency is a reviewed schema mapper that
will verify Eurostat dimensions and units before the existing signed Source
Gateway may attest a bundle.
