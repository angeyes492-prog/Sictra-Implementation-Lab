# Agent-assisted public research acquisition v0.1

Status: CANDIDATE / LOCAL IMPLEMENTATION / MAR REQUIRED for runtime adoption.
Owner scope decision: root AGENTS.md, 2026-10-03. Producer:
`sictra_block1.research_acquisition`; consumer: construction agent's research
quarantine only. No connection to the operations scheduler, source approval,
binding issuer, evidence attestation, dossier resolution or installed app.

## Observable objective and authority

Previously UNSPECIFIED / NOT IMPLEMENTED: securely acquire and recover exact
official metadata bytes without asking the owner to supply files. Terminate
with a hash-bound NOT_ADMITTED candidate, or a specific rejection without a
partial candidate. Select the known Eurostat maritime SOURCE_METHODOLOGY need;
metadata does not explain the cause of a particular numeric change.

The initial version 0.1 has two reviewed, fixed HTTPS recipes on `ec.europa.eu`: the reuse
notice and maritime metadata. They are not arbitrary URLs or source admission
approvals. Eurostat's public notice permits attributed reuse of its content,
subject to exceptions. Metadata acquisition requires a current retained reuse
notice receipt; this binds a terms reference, not a legal/independent review.
No credentials, cookies, private payload, environment proxy or authentication.
The separately specified candidate extension
`block1_eurostat_statistical_research_contract_v0.1.md` adds one exact fixed
JSON API recipe. It preserves this receipt schema, old recipe identities and
all quarantine/non-admission boundaries; it does not permit arbitrary queries.
The candidate national-methodology contract adds one exact Belgian ESMS URL
linked by the generic metadata. It uses the same terms/quarantine boundary;
hosting identity is not statistical origin or an independent root. The new
recipe cannot replace the generic metadata required by statistical admission.

## Network and capacity invariants

- Validate exact recipe URL, HTTPS, canonical hostname, no userinfo, explicit
  port, fragment or control characters. Resolve and reject ANY non-global,
  mapped-private, multicast or reserved DNS answer. Connect to a validated
  numeric address, with certificate verification and original hostname SNI:
  no second hostname lookup after validation. No redirects, even to an allowed
  host; record rejection and review the recipe rather than bypass an error.
- Request identity encoding. Reject compressed responses, duplicate framing
  headers, ambiguous framing (only plain or lone chunked is supported), non-200 status, incompatible media, empty or
  oversized/truncated body. Do not execute or render downloaded HTML.
- Session maximum 100 network attempts and 100 MiB received; 8 MiB per file,
  30-second socket timeout plus 30-second response-read deadline. One attempt
  per acquisition in v0.1, no automatic retries (hence no Retry-After bypass).
  Failed/partial attempts consume budget; never reset it to conceal failure.

## Persistence, identity, failure and recovery

Candidate descriptor has exact schema, original/final URL (identical), recipe,
publisher, declared source identity, requirement/need type, UTC timestamp,
24-hour research freshness (not a statement of publisher release cadence),
media, byte length, content SHA-256, linked terms receipt, collection-authority
reference, and fixed QUARANTINED / NOT_ADMITTED / NONE / BLOCKED boundaries.
Root provenance is UNCONFIRMED, never independently corroborating evidence.

Candidate ID hashes canonical descriptor bytes; data and descriptor are written
and fsynced in a temporary directory before an atomic directory rename. Exact
replay reuses the receipt; a mismatch, symlink, out-of-root path, wrong schema,
changed hash, stale/future time or changed boundary fails closed. A crash may
leave an unselected `.pending-*` directory; readers accept only an explicitly
identified complete candidate. No historical rewrite or automatic recovery
promotion. Multi-process coordination and signed approval remain out of scope.
Stored hashes provide integrity against a known receipt, not authenticated
approval: a fully replaced/quarantined record cannot issue runtime authority.

## Candidate manual Statbel PDF inspection extension — 2026-10-11

Version `STATBEL_PDF_METADATA_REVIEW_V1`, producer B1
`research_statbel_metadata`, consumer construction-agent CLI only. This is a
read-only inspection of a separately retained `AGENT_RESEARCH_PDF_CANDIDATE_V1`
receipt, NOT an eighth collection recipe, signed input, accepted source or
installed-runtime parser. Default application and legacy readers are unchanged.
Shared adoption requires its own MAR; this candidate does not issue authority.

Inputs: existing PDF root, exact canonical descriptor ID, existing Statbel
terms root and caller clock. Fixed publisher PDF URL ends in
`/metadata/T38.STAT_DTST_743.CTAC_ORG_1.DIFF_LVL_1.EN.pdf`; no URL fetching or
following embedded links. Receipt fields/hash, original bytes/hash, source,
publisher, research budget, UTC/currentness, non-admission boundary and exact
referenced terms ID/hash must match. Terms must be current under their existing
contract. Effective expiry is the earlier receipt/terms expiry. Symlink,
traversal, duplicate JSON keys, missing root/bytes, tamper, future/expired times
and rollback during reading fail closed. Hash identity is not authentication.
Optional diagnostic images in the folder are not inputs or evidence authority.

The fixed English four-page layout is parsed from original bytes, not copied
descriptor conclusions: product/date, geographic and temporal coverage,
periodicity, timeliness, revision policy/practice, administrative origin,
collection method and online-database reference. Each literal retains page
number. Unsupported, missing, duplicate or ambiguous sections fail closed;
blank statistical-unit/population fields stay unspecified. A literal
`Not applicable.` revision statement never means revisions cannot occur.
Quarterly coverage never proves annual-series equivalence. Inland-water
database references remain explicit scope conflicts, never substitute endpoints.
Independence, actual port-universe equivalence, reuse applicability to this PDF,
release-specific applicability and cause of a numeric gap remain unconfirmed.

Optional `research_pdf` dependency pins pypdf 6.10.0. Parsing executes in a
separate interpreter with isolated import flags and no remote instructions or
network calls. Limits: 256 KiB PDF, exactly four pages, 512 KiB decoded stream,
128 KiB extracted UTF-8 text, 4096 traversed objects, depth 32, 15-second child
timeout; decoded fonts/resources are separately capped at 8 MiB total, while
each textual page-content stream remains capped at 512 KiB. The original
publisher embeds fonts larger than the initial content-only limit; no text
limit or authority is relaxed. Reject encryption and active/embedded actions. Timeout terminates and
reaps the child. This is bounded inspection, NOT an OS sandbox or a hard
cross-platform memory quota; decoder resource exhaustion remains a residual
risk. No arbitrary PDFs or installed background operation are authorized.

Output separates literal observations and limits from verdict/authority:
`NOT_ADMITTED`, `NOT_RESOLVED`, `NOT_ACCEPTED`, `NONE`, `BLOCKED` and
`NOT_ESTABLISHED`. It binds PDF/terms IDs, hashes, check time and earliest expiry.
Verification rereads original bytes/terms and recomputes observations; a
self-resealed saved projection cannot substitute new facts or authority. CLI
check time cannot predate either original acquisition; an unsigned projection
does not authenticate the exact historical instant of a claimed check. CLI
serializes first then verifies before printing, so serialization-time changes
withdraw the report. No cache, journal, source-control or remote write occurs.
On failure no partial report is printed. Recovery is reopening the same known
receipt, not renewing expiry or admitting a source. Rollback removes this
optional inspection tool while preserving all originals and legacy behavior.

Tests: literal independent fixture oracles; positive/reopen/no-write/no-network;
tamper/expiry/rollback, rights substitution, forged report, malformed/encrypted/
active PDF, limits/ambiguity and parser timeout. A real-original run proves only
bounded extraction/provenance, not publisher truth, rights acceptance, resolved
Intelligence or accepted architecture.

Rollback removes this standalone agent tool, leaving existing local pipelines
and quarantined history intact. Generalized recipes, scheduled acquisition or
new consumer effects require their own contract/review and compatibility plan.

## Positive and refutation evidence

Tests must exercise real persistence/reopen, replay, exact bytes, terms lineage,
no runtime effects, fixed URL/DNS rejection, pinned TLS transport, redirection,
headers/media/size/truncation, failed-byte budget, deadline, write interruption,
tamper, future/expiry and symlink rejection. Fake network fixtures test the
mechanism; an explicit real acquisition separately demonstrates access and
retention, not source truth, comparability, resolved need or global acceptance.
