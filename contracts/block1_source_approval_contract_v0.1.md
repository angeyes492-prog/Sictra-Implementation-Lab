# Contrato ejecutable — Block 1 Source Approval Record v0.1

**Versión:** `0.1.0`
**Productor:** revisión humana registrada para E02.
**Consumidores:** revisión de configuración del Source Gateway.
**Scope:** `intelligence`.
**Autoridad:** trazabilidad de revisión; ninguna autoridad de adquisición o gate.

## Registro

`SourceApprovalRecord` contiene `source_id`, `reviewer_id`, `reviewed_at`,
`terms_evidence_ref`, `approved_hosts`, `approved_claim_keys`,
`max_content_bytes`, `access_method` y `decision`.

- Todos los textos son no vacíos.
- `reviewed_at` es entero no booleano, no negativo y no futuro durante la
  evaluación.
- Hosts son DNS normalizado sin IP, localhost, ruta, puerto ni credenciales.
- Claims no son vacíos; límite es entero positivo.
- El único método v0.1 es `MANUAL_SOURCE_BUNDLE`.
- La decisión es `APPROVED` o `REJECTED`.

## Evaluación

`readiness_for(candidate, now)` rechaza fuente distinta, fecha futura, host
fuera del perfil candidato y candidato no `PROPOSED`. Con `REJECTED` devuelve
`NOT_APPROVED`; con `APPROVED` devuelve
`READY_FOR_GATEWAY_CONFIGURATION_REVIEW` y conserva la decisión, referencia,
hosts, claims y límite.

Ningún método crea `SourceRegistration`, atestación, solicitud HTTP o cambio de
estado. El resultado `READY` necesita después una configuración explícita y
revisión independiente.
