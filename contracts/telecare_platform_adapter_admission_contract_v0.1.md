# Telecare platform adapter admission contract v0.1

Status: `CANDIDATE / LOCAL BOUNDED SUT / NOT ACCEPTED`
Implementation: `sictra_block4_orchestrator.platform_adapters`
Architecture: `architecture/telecare_optional_platform_adapters_v0.1.md`

## Producer and consumer

Producer: an approved B2 or B3 candidate bound to a current Block 4 case.
Consumer: a platform adapter worker that is not implemented or activated by this contract.
Coordinator: Block 4 records the intent and approval boundary only.

## Version and schema

Contract version: `0.1.0`.

```text
AdapterConfiguration {
  adapter_id, platform, mode,
  allowed_operations[],
  credential_reference?, activation_receipt?
}

AdapterOperation {
  case_id, run_id, artifact_id, source_hash,
  platform, operation, input_fields[],
  human_authorization?
}
```

`platform` is exactly one of `FIGMA`, `FRAMER`, or `HUBSPOT`.
`mode` is exactly `DISABLED`, `CONFIGURED`, `ACTIVE`, or `FAILED`.

## Operation allowlist

| Platform | Allowed operations | Input rule |
| --- | --- | --- |
| Figma | `READ_DESIGN_REFERENCE`, `OBSERVE_DESIGN_CHANGE` | No audience fields |
| Framer | `EXPORT_REVIEW_DRAFT` | No audience fields |
| HubSpot | `READ_AUDIENCE_CONTEXT` | Non-empty subset of the context allowlist |

The HubSpot context allowlist is: `company_size_band`, `content_interests`, `industry`, `lifecycle_stage`, `preferred_language`, `region`, `segment`, and `subscription_status`.

Email, name, phone, mobile phone and address are rejected. No write, delete, contact, enrollment, send or publish operation appears in this version.

## Preconditions and outcomes

- Every identifier and source hash must be non-empty.
- The operation platform must equal the configured platform and appear in that configuration's allowlist.
- A `DISABLED` configuration has neither credential reference nor activation receipt. It may produce `PLANNED`, never traffic.
- `CONFIGURED` and `ACTIVE` require a non-secret credential reference such as a vault URI. The reference is not a token and must not contain a secret.
- `ACTIVE` requires an activation receipt. A request additionally requires a human authorization receipt before it can become `BOUND_NOT_EXECUTED`.
- Binding does not call the platform. It only allows a separately implemented worker to consider the work; that worker must record `EXECUTED` or a fail-closed outcome.

## Rejections and recovery

Reject with no external effect on: unknown platform/mode/operation, missing identity, configuration-platform mismatch, missing credential reference/receipts, secret bound in disabled mode, direct identifier field, non-allowlisted HubSpot field, audience fields sent to a design adapter, or a request against a non-active adapter.

A worker that later exists must reject expired case evidence, revoked credentials, invalid OAuth state, webhook signature/passcode mismatch, replayed event, destination substitution, schema drift, scope expansion, rate limit or ambiguous timeout. It may not retry an unknown external effect without a provider-specific idempotency key and audit record.

## Compatibility, authority and non-claims

New platforms, operations, fields or state values require a new contract version and Master Architecture Review. A v0.1 consumer rejects them.

This contract authorizes no network, OAuth exchange, secret storage, vendor SDK use, CRM mutation, publication, delivery, contact, gate promotion or human-approval substitution. Local contract conformance and tests are not proof of a live Figma, Framer or HubSpot connection.
