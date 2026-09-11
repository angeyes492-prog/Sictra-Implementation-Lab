# Contract — Source Master Registry v0.1

## Producer and consumer

Producer: `sictra_block1.source_portfolio.SourceCandidate`.
Consumer: local `GET /api/source-readiness` and the read-only Sources tab.
Scope: `BLOCK1_SOURCE_PORTFOLIO_READINESS`.

## Candidate schema

Every snapshot has exactly these source-governance fields in addition to its
stable identity and coverage: `source_role`, `license_status`,
`access_posture`, `revision_policy`, `research_state`, `official_reference`,
`status`, and `allowed_actions`.

Allowed values are closed:

- roles: `E1_CANDIDATE`, `E2_CANDIDATE`, `SIGNAL_ONLY`, `PRESENTATION_ONLY`;
- license states: `UNREVIEWED`, `PUBLIC_TERMS_UNCLEAR`, `REGISTERED_ACCESS`,
  `RESTRICTED`;
- access postures: `MANUAL_REVIEW_REQUIRED`,
  `REGISTERED_MANUAL_REVIEW_REQUIRED`;
- revision policies: `UNKNOWN`, `POSSIBLE_REVISIONS`,
  `PUBLISHED_REVISIONS`;
- research states: `OFFICIAL_PAGE_VERIFIED`, `DISCOVERY_PENDING`;
- candidate status: only `PROPOSED`;
- actions: exactly `DISCOVER`, `REVIEW`.

`official_reference` must be an HTTPS URL without credentials or port, and its
host must occur in `candidate_hosts`. It is a provenance pointer only.

## Preconditions, postconditions and non-claims

The query accepts one region and one domain from their closed sets. It returns
only matching `PROPOSED` candidates, `admissible_source_count=0`, mandatory
promotion blockers and these non-claims:

- `CANDIDATE_DISCOVERY_IS_NOT_SOURCE_APPROVAL`
- `PUBLIC_ACCESS_IS_NOT_REUSE_PERMISSION`
- `NO_NETWORK_ACQUISITION_OR_AUTOMATIC_IMPORT`

Unknown region/domain, malformed metadata, invented governance state, or a
reference-host mismatch raises `ContractViolation`. The response has no URL
submission, content ingestion, credential, mutation, bind or approval path.

## Compatibility

New fields are additive to the prior candidate snapshot. Consumers must never
infer a missing future field as approval. Changes to the closed enumerations or
to the zero-admissibility invariant require a new contract version and a Master
Architecture Review.
