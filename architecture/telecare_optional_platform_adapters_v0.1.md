# Telecare optional platform adapters v0.1

Status: `CANDIDATE / LOCAL CONTRACT IMPLEMENTATION / MAR REQUIRED`
Date: 2026-09-14
Authority: owner request to prepare optional Figma, Framer and HubSpot integration contracts.

## Purpose

This architecture adds a provider-neutral adapter boundary. It lets Telecare OS plan or bind a future integration without allowing a block to depend directly on an external SDK, secret, API, or vendor-specific object.

It does not activate Figma, Framer, HubSpot, an LLM, network acquisition, publishing, delivery, CRM mutation, or production operation.

## Ownership and route

```text
B1 evidence/dossier ──────┐
                          ├─ B2 Design ─ DesignPlatformPort ─ Figma / Framer adapter
B3 declared audience ─────┘
                           B3 Precision ─ AudienceContextPort ─ HubSpot adapter
                                      │
                             B4 Orchestrator ─ audit / pause / stop / human gate
```

- B2 owns the design candidate. A design adapter may read a design reference or bind a review draft, but cannot make the candidate accepted or published.
- B3 owns adaptation for admitted context. A HubSpot adapter may supply an approved, minimized context record; it cannot write to CRM, send a message, or make a commercial decision.
- B4 owns only the operation record and explicit control boundary. It cannot supply platform authority or substitute a human export/activation decision.
- Vendor adapters own credential exchange and API mechanics only. They never own facts, evidence, editorial decisions, customer consent, or gate promotion.

## Shared adapter states

`DISABLED → CONFIGURED → ACTIVE → FAILED`

- `DISABLED`: a contract can be planned. It has no credential reference and cannot emit traffic.
- `CONFIGURED`: a secret reference may exist outside the repository, but no request is admitted for execution.
- `ACTIVE`: requires a credential reference and activation receipt. Binding is still `BOUND_NOT_EXECUTED`; a separate worker is required to cause an external effect.
- `FAILED`: fail closed, record only non-sensitive reason and require explicit recovery.

Every operation uses an immutable case/run/artifact identity and source hash. It is separately classed as `PLANNED`, `BOUND_NOT_EXECUTED`, or `EXECUTED`; a binding is never evidence that the platform was called.

## Platform boundary matrix

| Platform | Initial allowed operation | Data allowed in v0.1 | Explicitly prohibited |
| --- | --- | --- | --- |
| Figma | Read a named design reference; observe an approved design-change event | File/reference IDs, hashes, non-sensitive component metadata | Arbitrary canvas mutation, publication, data-source acquisition, unbounded file ingestion |
| Framer | Bind a review draft export for a named approved project/branch | Candidate artifact ID/hash and approved destination reference | Direct production publish, domain change, arbitrary project mutation, analytics/visitor data ingestion |
| HubSpot | Read audience context | Allowlisted segment, industry, size band, language, region, lifecycle and content-interest fields | Contact creation/update/deletion, email/phone/name/address access, enrollment, marketing send, CRM write |

An actual Figma canvas-writing feature may need a dedicated plugin/bridge and separate capability validation; this candidate does not assume that the REST API can perform it.

## Preconditions for real activation

1. Master Architecture Review decides ownership, tenancy, retention, identity, audit and kill-switch semantics.
2. The owner chooses a specific test account/project/portal and the exact allowed operation.
3. OAuth/client or project credential is created with least privilege and stored outside Git.
4. A source/destination allowlist, expiration, rate limit, timeout, retry and rollback policy is accepted.
5. Webhook handlers, if any, use HTTPS, signature/passcode validation, replay protection and payload bounds.
6. Tests prove rejection of invalid identity, missing authorization, revoked credential, replay, schema drift, scope escalation, PII leakage and an attempted publication/write.
7. A human activation/export receipt is recorded before each effect class is enabled.

## Observability, recovery and non-claims

Every adapter attempt must emit a correlation ID, adapter ID, platform, operation, mode, contract version, request fingerprint, result class and non-sensitive reason code. It must never log tokens, client secrets, raw PII, raw external payloads or unpublished design content.

A timeout, scope failure, signature failure, rate-limit event, webhook replay or schema mismatch transitions the adapter to a safe failed/deferred result; B4 returns the case for review or upstream rather than retrying an unknown external effect.

The contract and its local tests prove only local admission behavior. They do not prove vendor availability, OAuth installation, platform interoperability, runtime execution, customer consent, legal compliance, external delivery or production readiness.
