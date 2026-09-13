# Durable source control store — local preflight

## Result

`VERIFIED / B` for the local source-control boundary. A matching Eurostat
registration, exact `PROJECT_OWNER` approval and signed binding were persisted
to a temporary control store. After reconstruction, the store built a current
gateway and the supplied workbook bundle crossed it as one signed `OBSERVED`
record.

The emitted record's approval fingerprint equaled the binding's signed
approval fingerprint. Neither the binding key nor store-integrity key appeared
in persisted JSON. Temporary control and secrets were destroyed after the
exercise.

## Behavioral evidence

- Exact binding replay is idempotent.
- Rotation appends a strictly newer binding and preserves prior history.
- Expired bindings remain `NOT_CURRENT` history and cannot build a gateway.
- Approval substitution, wrong binding key, wrong integrity key, malformed
  artifacts and non-monotonic rotation fail closed.
- Injected failure before atomic replacement preserves the prior file exactly.
- Capacity exhaustion occurs after validating a current candidate and leaves
  state unchanged.

## Test

- Focused source-control/gateway/Eurostat suite: 16 tests, `OK`.
- Runtime group: 67 tests, `OK`.
- Remaining repository group: 178 tests, `OK`.
- Total: 245/245 on 2026-09-05.

## Boundary

The exercise proves local binding reconstruction, not production identity.
Keys were ephemeral byte strings, not KMS-managed secrets; the observed record
was not durably retained or independently reviewed. No gate, source portfolio
status, editorial claim or publication state changed.
