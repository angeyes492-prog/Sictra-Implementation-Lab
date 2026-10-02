# Telecare content-design handoff v0.1

Status: `CANDIDATE / LOCAL IMPLEMENTATION / MAR REQUIRED`.
Date: 2026-09-14. Producer: Block 2 Design. Consumer: Block 3 Precision.

## Purpose and scope

The handoff carries a reviewable `CONTENT_DESIGN_CANDIDATE` derived from one
current Block 1 federated dossier package. It is a published language between
bounded contexts, not a shared database model or acceptance decision.

Block 2 owns information hierarchy, visual tokens, ordered content blocks,
accessible render constraints and the candidate's structural identity. Block 3
owns only selection and presentation of those blocks for a declared generic
audience. Block 4 transports/persists the result; it owns no design or audience
semantics.

## Required fields and invariants

The candidate contains: version, artifact type, `REVIEW_NEWSLETTER` format, case/dossier/source/evidence
identity, expiry, exact literal source claims, evidence-first design system,
ordered blocks, status, review/publication/delivery restrictions and a canonical
fingerprint. An `OBSERVED_CHANGE` block names every source claim it presents.
`UNCERTAINTY`, `LIMITATION` and `PROVENANCE` blocks are mandatory. The candidate
must stay `DESIGN_CANDIDATE_NOT_ACCEPTED`, `HUMAN_REVIEW_REQUIRED`, `BLOCKED`
and `NONE` respectively.

Precision must verify the canonical fingerprint before adapting. Its output
contains the originating artifact fingerprint and may remove geographical
observations for a declared filter or shorten a brief view. It cannot add,
rewrite, rank, infer, promote or delete uncertainty/provenance blocks. A renderer
verifies the adaptation-to-artifact binding before producing HTML or text.

## Rejection, expiry and compatibility

Block 2 rejects a dossier/source identity mismatch, contradiction, absent facts
or any dossier not publication-blocked. Block 3 rejects an altered, unsupported
or nonmatching artifact; a no-match geographic filter waits rather than creating
generic content. Block 4 rechecks source and profile freshness before serving.

Local rejection repair (2026-10-01): a nonempty `geo_codes` filter matches only
an explicit claim `geo_code`. A customs-point claim without that field is not
a match: neither its label nor an inferred source country supplies the field.
If no claim matches, Precision raises `NO_GEOGRAPHIC_MATCH` and B4 records a
wait while continuing other work. An empty filter preserves the source-bound
customs view. This repairs an uncaught `KeyError`, not a new geographic mapping
or schema: successful existing outputs remain byte-identical and replayable.
Country/customs-point mapping, if later needed, requires explicit producer
semantics and compatibility review rather than silently relabeling facts.

Local read-side integrity clarification (2026-09-28): Block 4 also re-exports
the current Block 1 package, reproduces the deterministic Block 2 design from
that dossier, reproduces the Block 3 adaptation for the current declared
profile, and compares the saved HTML, text, checksum, identity and blocked
authority fields before serving. A mismatch is unavailable, including through
the JSON/text/HTML endpoints. The overview may retain only a generic
`STALE_OR_REVOKED` placeholder; it must not display the unverified title or
profile. This is a stricter read check, not a new handoff schema or acceptance
decision. A future design algorithm change needs an explicit compatibility or
migration decision rather than treating old outputs as current by implication.

This is version 1. A consumer receiving another version must fail closed as
`UNSUPPORTED_CONTENT_DESIGN_VERSION` until the MAR records compatibility. The
legacy source-draft module is not part of this contract and is not called by the
operations runtime.

## Non-claims and validation boundary

The candidate is not research validation, a causal explanation, personalized
copy, an E01–E08 acceptance, a delivery instruction or authorization to publish.
Current tests cover exact numeric preservation, source/hash binding, mandatory
uncertainty/provenance, profile-only variants, tamper rejection, stale input and
escaped output. Independent review, real approved content sources, visual
usability evidence and global contract acceptance remain outside this candidate.
