# Statistical admission bridge — executed candidate evidence

Date: 2026-10-03 local / 2026-10-04 UTC. Windows / Python 3.12.
Reviewer: implementation agent, not independent. Scope: isolated candidate,
LABORATORY_INTERNAL_SUPERVISED. Certainty VERIFIED / confidence B for the
executed mechanism, not source truth, source approval or product acceptance.
Base 4d709e4550eb78f89e3de11096a2c75e89f13ff3 passed exact-SHA GitHub push
37164013169 and PR 37164015859, rechecked before this increment. The new
commit's CI must be checked separately after push; this file cannot contain
its own eventual commit SHA without changing that SHA.

## Observable closure delta

Contract block1_statistical_admission_bridge_contract_v0.1 and standalone
research_admission implement a concrete review and conditional admission port.
Existing SourceControlStore/SourceGateway signatures and independently
configured EvidenceVerifier are reused, not replaced by self-declared authority.
The exact new scope/host/claim/byte limit and retained terms/methodology review
lineage are checked before signing and again at the consumer. Expected values
and provenance are reconstructed from current retained bytes, not inferred
from signature validity. Collection and publisher-update times remain distinct.
Clock rollback, slow signing, expiry and signed authority rotation withhold
the result. No approval, keys, store migration, dossier, runtime request or
publication is emitted. Rollback removes this standalone port; legacy XLSX
content validation stays unchanged and rejects the new media type.

Fourteen focused unittest cases passed in 6.213 seconds. Positive fixtures use
explicit FIXTURE_ONLY source review, separate test keys and independent values
10.0 / 12.5. Attestation verification, restart and read-only replay are positive
cases. Negative cases cover absent/legacy authority, signed wrong terms/claim/
host/oversized grant, early review and tiny budget, binding/quarantine expiry,
trusted-issuer-signed forged values/extra fields, unsigned mutation, raw data/
terms/metadata/control tamper, mixed terms roots, empty coverage, legacy
consumer rejection, verification-time expiry/rotation and invalid clocks.
Tests do not claim a real reviewer approved any fixture or downloaded source.

## Actual retained-data execution

The read-only CLI prepared a review for actual data
c2650baf62a4c8f86b5a639f78e28c9954760cc6f879dfc074cc13a1ad1fd39d,
methodology 2ec276d6011d1276108777e833ad6fd7a14329342dd932c86151d8a2b380dd49
and terms c38122a03b5a6d38e7ffb6fc7aff8ba2e6845d7792d1bbeca7bf5e0a503175aa.
Review fingerprint:
3080fe3a8ba9cd59f07ad5a25cdf6c5fca7e574c7b07ffdfd980bf7fd7f95c98.
It preserves Belgium 2023 = 272698.25 and 2024 = 274369.05 thousand tonnes,
the raw API/metadata hashes and exact terms reference. Review-not-before is
1791069614; effective expiry is 1791155970, never refreshed by rereading.
State: PROPOSED / reviewer null / PENDING / NOT_ADMITTED / NOT_ACCEPTED,
runtime NONE, publication BLOCKED. No new downloads or fictional source
approval were necessary for this execution. Reacquire after expiry rather
than editing timestamps. Same Eurostat root is not independent corroboration.

Reproduce with PYTHONPATH=src and:
`python -m sictra_block1.research_admission --root .runtime/research-quarantine-2026-10-03 --data-candidate-id c2650baf62a4c8f86b5a639f78e28c9954760cc6f879dfc074cc13a1ad1fd39d --metadata-candidate-id 2ec276d6011d1276108777e833ad6fd7a14329342dd932c86151d8a2b380dd49`.

## Reconciliation, integration limits and next step

Notion plan 3c789f66-067b-8108-bb44-c13ac4b15ac0 remains historical reference
scope, last edited 2026-08-28; this turn's public Slack Telecare query returned
no results. Neither supplies this new source decision. GitHub provides the
base identity above and eventual exact-SHA CI separately. Wolfram enumerated
512 boolean signature/scope/terms/review/currentness/lineage configurations:
one satisfies the declared admission conjunction; legacy scope, stale inputs
and altered lineage cannot satisfy it; signature alone is insufficient.
This intentionally bounded model checks the declared authority condition, not
Python parsing, actual signatures, source truth, runtime effects or acceptance.

MAR decision 12 remains OPEN. The next safe increment is a distinct candidate
statistical retention/recovery consumer, preserving history while withdrawing
expired/superseded evidence. Real admission needs the exact reviewed signed
source grant; product corroboration still needs separately rooted comparable
inputs. The persistent owner goal is active; the earlier paused app heartbeat
and installed application are untouched. No gate was promoted.

Full local regression: 885/885 Python tests in 155.476 seconds, 17/17
JavaScript tests, compileall, launcher-path validation and diff checks passed.
The finite final-checkout 24-test preflight and exact final-SHA hosted CI are
separate execution evidence, retained with the PR/workflow identity rather
than inferred from this full-regression count.
