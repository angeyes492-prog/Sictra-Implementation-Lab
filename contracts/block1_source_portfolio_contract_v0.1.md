# Contract — Source Portfolio v0.1

Producer: E02 planning catalogue. Consumer: local Intelligence Workspace.
Authority: planning only; no acquisition or gate authority.

The endpoint admits exactly one supported region and one supported domain.
It returns a fixed candidate identity, publisher, candidate hosts, coverage,
cadence and `status=PROPOSED`. It always reports zero admissible sources and
the blockers: terms, access, host allowlist and claim authorization.

This contract intentionally does not provide source binding, HTTP, uploads,
credentials, truth, availability, licensing, production, or gate acceptance.
