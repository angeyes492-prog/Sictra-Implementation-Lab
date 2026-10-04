# Statistical admission bridge v0.1

Status: CANDIDATE / LABORATORY_INTERNAL_SUPERVISED / MAR REQUIRED.
Producer: sictra_block1.research_admission. Consumers: source reviewer and
explicit candidate admission caller. Dependencies: current research quarantine,
statistical/methodology inspectors, existing SourceControlStore/SourceGateway
and independently configured EvidenceVerifier. No installed activation.

## Objective and authority

Prepare a concrete review packet for the retained Belgium 2023-2024 JSON-stat
scope and demonstrate a gated local attestation path. The bridge creates no
SourceApprovalRecord, binding, keys, persistent evidence, runtime request or
gate status. Its CLI only prepares a review. Existing XLSX approval is not a
grant for this new format-specific consumer.

Admission requires a trusted durable APPROVED/BOUND record for eurostat with
scope BLOCK1_EUROSTAT_STATISTICS_BE_2023_2024, exact ec.europa.eu host and
maritime_freight_weight_thousand_tonnes claim, MANUAL_SOURCE_BUNDLE access,
positive byte limit <=131072 and a terms_evidence_ref exactly identifying
both retained terms and methodology candidate IDs. SourceControlStore verifies
the stored approval fingerprint, signed binding, history and currentness.
The bridge checks reviewed_at is current and not earlier than either review
dependency's acquisition. Publisher rights and reviewer identity are review
inputs; fixture keys/identities do not prove a real review.

## Review and attestation

Review output retains exact data/metadata/terms candidate IDs and hashes,
scope, filters, original source URL, publisher time, all observations including
missing cells and raw flags, revision policy/practice text with anchors, and
the concrete required registration/approval fields. It remains PROPOSED,
NOT_ADMITTED, NOT_ACCEPTED, publication BLOCKED and runtime NONE.

The caller may supply separately configured source control and EvidenceIssuer
to attest a newly constructed canonical statistical selection. The content
identifies the raw JSON hash and all dependencies; it does not masquerade as
the XLSX mapper format. Collection time is observed_at, publisher update stays
separate. Require exact current approval/scope/terms lineage before signing.
No dossier/interpretation, resolution, corroboration, delivery or runtime effect
is produced. Empty observed coverage fails admission; missing values cannot
be evidence of zero or a positive freight observation.

## Consumer enforcement, failure and compatibility

A dedicated verification function must independently check the source
attestation and recompute expected content and public lineage fields from
current quarantine/source control. A valid generic source signature alone is
insufficient. Re-read all dependencies/control after slow verification; reject
alteration, expiry, superseded approval, scope/terms substitution, signature
mutation, forged self-consistent content, future/rollback time and changed reads.
Effective expiry is the earliest data/metadata/terms/binding boundary; this
candidate enforces the binding end exclusively, a stricter local boundary.

All functions are read-only. Restart repeats the same result while dependencies
remain current; no ledger migration or automatic replay promotion. The legacy
AttestedEvidenceStore/XLSX pipeline rejects this distinct content type. Runtime
adoption and a retained statistical pipeline require separate MAR/consumer
work; no scheduler imports this module. Rollback removes this standalone port.

Positive tests use explicit fixture approval and independently stated source
values; negative tests cover absent/legacy authority, terms/scope/byte/clock
violations, tamper, stale dependencies, empty coverage, independently verified
signature/lineage, issuer-side forged values, rotation and read-time expiry.
Actual real-candidate review may execute without approval; no fictional human
approval is created to force an actual attestation.
