# Source binding approval-lineage repair v0.1

## Finding

`HIGH / B` pre-repair risk: a binding signature covered source identity,
scope, hosts, claims, method, size and validity window, but its signed material
did not identify the exact `SourceApprovalRecord` that authorized issuance.
A durable token could therefore remain technically valid while its reviewer,
review time or terms evidence became ambiguous outside the issuing process.

## Repair

`VERIFIED / B` locally. `SourceBindingIssuer` now fingerprints the complete
normalized approval and signs that SHA-256 as part of the binding. The gateway
requires a lowercase hexadecimal SHA-256 and propagates both the approval
fingerprint and signed-binding fingerprint into the evidence issuer's signed
observed record.

Changing reviewer identity produces a different approval fingerprint. Missing,
altered, malformed or re-signed non-hex lineage fails closed. A non-approval
object cannot request an approval fingerprint.

## Validation

- Focused source gateway and Eurostat binding suite: 11 tests, `OK`.
- Runtime group: 67 tests, `OK`.
- Remaining repository group: 173 tests, `OK`.
- Total: 240/240 on 2026-09-05.

## Compatibility and boundary

This is a deliberate binding-schema incompatibility: previously issued local
tokens must be reissued from an exact approval record. No source was newly
bound, no durable secret or binding was created, and the fingerprint does not
prove reviewer identity, legal correctness, source truth or independent
validation.
