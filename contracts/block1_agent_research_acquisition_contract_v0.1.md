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
