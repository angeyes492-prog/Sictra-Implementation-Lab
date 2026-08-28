# Bloque 3 — Contrato ejecutable A∴ / M06–M08 v0.1

> Estado: `CANDIDATE / LOCAL BOUNDED SUT`. Extiende el contrato M01–M05 sin
> autorizar delivery, consentimiento, adapters reales, memoria durable,
> integración interbloques ni aceptación global.

## Topología

```text
M01/M03/M04/M05 → M02 → PRECISION_CONTEXT_PACK
→ RELEVANCE_DECISION → ADAPTIVE_LEVEL_DECISION
→ M06 MESSAGE_STRATEGY → M07 DELIVERY_PROPOSAL
→ external DELIVERY_RECEIPT + OUTCOME → M08 NEXT_BEST_TEST
```

## Contratos transversales

- El Context Pack es inmutable, temporal, versionado y ligado por fingerprints
  a M01–M05.
- Persona State es una proyección reversible; no psicología ni identidad
  permanente.
- Personalization Ceiling es el mínimo de límites explícitos y nunca un
  objetivo.
- Relevance Gate usa estados visibles por dimensión, no score opaco.
- Adaptive Frontier aplica restricciones duras antes de beneficio marginal;
  duda, empate o regresión conservan L0.

## M06

Consume Gate `HIGH/MEDIUM`, Adaptive Decision y assets actuales del
`BLOCK2_ASSET_REGISTRY`. Produce estrategia, no copy final. El nivel aplicado
no excede ceiling, gate, policy ni asset. No crea facts ni delivery authority.

## M07

Consume Message Strategy, historial de canal con evidencia vigente y política
versionada. Produce `SEND_CANDIDATE`, `WAIT`, `DO_NOT_SEND` o
`RETURN_UPSTREAM`. Toda propuesta exige revalidación externa de consentimiento,
opt-out, frecuencia, credencial y vigencia.

## M08

Aprende sólo de una cadena completa y coherente. `REJECTED` por el executor no
es comportamiento; un receipt `EXECUTED` exige propuesta `SEND_CANDIDATE`.
Evidencia autoescrita por M08 se rechaza. El output es candidate-only y sólo
puede afectar una versión futura tras Governance Review.

## Failure y replay

- Identidad, versión, provenance o freshness inválidos: `RETURN_UPSTREAM`.
- Contradicción esencial: preservar, no desempatar.
- Asset o historial no autorizado/stale: no estrategia/propuesta.
- Relevance LOW o unsubscribe observado: no send candidate.
- Ausencia de receipt/outcome: no learning.
- IDs repetidos con payload diferente: collision.
- Outputs inmutables y deterministas: replay sin efectos externos.

## Non-claims

No demuestra valor comercial, causalidad, producción, seguridad de storage,
ejecución real, consentimiento, integración con Bloques 1/2, oráculo humano ni
gate global.


