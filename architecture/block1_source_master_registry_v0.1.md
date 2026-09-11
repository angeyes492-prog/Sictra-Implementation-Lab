# Block 1 — Source Master Registry v0.1

`IMPLEMENTED CANDIDATE / LOCAL-TESTED / B`.

## Purpose and scope

The Source Master Registry is a bounded, read-only discovery catalogue owned
by E02. It records what was observed on an official publisher page about a
potential source: its proposed role, region/domain coverage, expected cadence,
revision behavior, access posture and legal-review state.

It is not a source allowlist, downloader, scheduler, credential store, claim
authorization, or evidence store. A registry entry remains `PROPOSED` even
when its official publisher page has been checked.

## Flow and invariants

`official discovery → PROPOSED registry entry → human terms review → source
approval → BOUND registration → manual bundle → E01–E08`

- Discovery never changes `admissible_source_count`, which remains zero.
- `PUBLIC_ACCESS_IS_NOT_REUSE_PERMISSION`; public pages must not be treated as
  an open-data license.
- The only allowed registry actions are `DISCOVER` and `REVIEW`.
- An E1/E2 role is a research hypothesis, not evidence authority.
- `SIGNAL_ONLY` and `PRESENTATION_ONLY` may never acquire evidence authority
  through the registry.
- A candidate reference must be HTTPS and use one of its declared candidate
  hosts. This checks identity consistency; it does not verify content or law.
- `REGULATION` is a domain for discovery and watchlist planning. It does not
  assert that a notice affects a particular company or corridor.

## Authority and downstream impact

The registry does not change the Source Gateway contract. Only a separate
`SourceApprovalRecord`, a matching `BOUND` `SourceRegistration`, a current
HMAC binding and a controlled `MANUAL_SOURCE_BUNDLE` can reach the gateway.
Dashboards and editorial systems remain downstream consumers and cannot write
to this registry or to evidence.

## Failure and recovery

Malformed metadata, an unrecognized role/license/access/revision state, or an
official reference outside the declared candidate hosts fails closed at local
construction time. Recovery is correction of the proposed metadata plus a new
test; it is never a silent fallback to a generic source.

## Validation

The local suite proves that the registry exposes governance metadata, retains
zero admissible sources, rejects a fabricated role/reference host, and exposes
a regulatory candidate without enabling ingress. It does not prove source
truth, terms, availability, a production integration, or independent review.
