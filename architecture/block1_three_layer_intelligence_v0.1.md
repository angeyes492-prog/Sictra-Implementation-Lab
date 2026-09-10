# Bloque 1 — Arquitectura de Inteligencia en Tres Capas v0.1

## State and purpose

`IMPLEMENTED CANDIDATE / LOCAL-TESTED / B`. This durable architecture artifact
incorporates the thematic brief into a controlled, testable research frame. It
does not change the global gate, source authority, or production claim.

## Model

```text
Global event / evidence
  └─ GLOBAL frame: common logistics interpretation
       └─ SEGMENT frame: industry-specific implication
            └─ ACCOUNT frame: pseudonymous account-specific hypothesis
```

The last arrow is a dependency, not an inference of truth. An Account frame
must preserve its Global and Segment context and can remain `UNCONFIRMED` or
`INSUFFICIENT EVIDENCE`.

## Thematic universe

The controlled taxonomy covers all topics provided by the owner in twelve
domains: geopolítica y comercio internacional; transporte marítimo; transporte
aéreo; aduanas y comercio exterior; supply chain; tecnología logística; costos
y economía; sostenibilidad; puertos e infraestructura; riesgo; comercio
electrónico; and industrial sectors. `TOPIC_CATALOG` is the executable source
of allowed topic keys, including such overlaps as `de_minimis` and reverse
logistics.

## Invariants and ownership

- E02 owns research framing and topic vocabulary; E05 continues to challenge
  claims; E08 continues to authorize source and promotion transitions.
- Global/Segment/Account is not equivalent to global/regional/local geography.
- No Account interpretation may exist without declared Global and Segment
  parents in the same validated bundle.
- Evidence references do not become facts through personalization.
- Account identifiers are pseudonymous; this contract contains no PII, CRM or
  commercial-action authority.

## Failure, recovery and validation

Unknown topics, incompatible layer fields, unresolved/wrong-layer parents,
duplicates and self-references fail closed. Frames are immutable normalized
copies; recovery is reconstruction from the submitted bundle. Unit and
adversarial tests cover valid lineage and each rejection class.

## Downstream impact and open decisions

The Workspace must later add a separate layer selector and research-frame
views; its current Scope Lens stays geographic. Real Account Intelligence
needs a separately approved privacy, identity, tenancy and retention contract.
Source Gateway remains the only candidate route for real source evidence.
