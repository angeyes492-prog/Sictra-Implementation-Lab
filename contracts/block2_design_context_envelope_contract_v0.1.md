# Block 2 / Design Context Envelope Contract v0.1

> Estado: `CANDIDATE / LOCAL EXECUTED / NOT ACCEPTED / MAR REQUIRED`  
> Alcance: sobre inmutable entre el handoff de Intelligence y los candidatos
> E01–E04 de Block 2. No sustituye `UpstreamIntelligence` ni el Common Envelope
> operacional que pudiera ser aceptado en otra rama.

## Propósito, productor y consumidor

El contrato preserva los hechos y límites de un objeto de Intelligence mientras
añade el contexto mínimo que Design necesita para razonar sobre expresión,
canal y restricciones.

| Rol | Identidad candidata | Responsabilidad |
|---|---|---|
| Productor inicial | adaptador autorizado de `UpstreamIntelligence` | enlazar, no reinterpretar, el registro upstream actual. |
| Productores derivados | E01, E02, E03 o E04 | añadir sólo su payload y su delta de procedencia. |
| Consumidores | E01–E04 y futuros adapters autorizados | verificar requisitos, preservar campos y rechazar fuera de alcance. |
| Dueño de hechos/evidencia | Intelligence upstream | crear, corregir o retirar facts/claims/evidence. |
| Dueño de aceptación | autoridad externa a E01–E04 | decidir publicación, promoción o aceptación. |

## Forma lógica

```text
DesignContextEnvelope = {
  identity: {message_id, task_id, run_id, contract_version, producer, consumer,
             logical_time, fingerprint},
  upstream_binding: {object_id, source_identity, fact_ids[], evidence_refs[],
                     certainty, contradictions[], authority_reference,
                     temporal_state, provenance_refs[]},
  design_intent: {audience, decision, task, channel_set[], success_criterion},
  constraints: {accessibility_requirements[], brand_manifest_ref?,
                reference_rights_manifest_ref?, legal_constraints[],
                channel_constraints[]},
  epistemics: {state, uncertainty[], non_claims[]},
  payload: {kind, body},
  provenance_delta: {parent_fingerprint, transformation_id, timestamp,
                     added_by, added_fields[]}
}
```

`certainty` sólo puede tomar los valores protegidos: `VERIFIED`, `PROBABLE`,
`PLAUSIBLE`, `UNCONFIRMED`, `CONTRADICTED` o `INSUFFICIENT EVIDENCE`.
`temporal_state` sólo acepta `CURRENT` en la entrada inicial de E01. La
semántica de un campo no definido es `UNSPECIFIED`, no un valor favorable.

## Precondiciones

Para que el adaptador emita `CONTINUE` hacia E01, todos los siguientes campos
deben estar presentes, trazables y sin mutación: `object_id`, identidad de
fuente, al menos un fact ID, al menos una referencia de evidencia, certainty
gobernada, audiencia, decisión, tarea, autoridad, procedencia y estado
`CURRENT`.

Los consumers E03/E04 exigen además un `ReferenceRightsManifest` válido si
alguna referencia, fuente, logo, asset, captura o archivo tipográfico puede
afectar el artefacto. Un manifest ausente no autoriza inferir que no hay activos
o derechos relevantes.

## Salidas y disposición

| Disposición | Payload permitido | Semántica |
|---|---|---|
| `CONTINUE` | sobre congelado y fingerprint nuevo | la estructura es suficiente para el siguiente motor, no para aceptación. |
| `RETURN_UPSTREAM` | razones y referencias de campos ausentes; sin payload derivado | el propietario upstream debe reparar/versionar el objeto. |
| `RETURN_TO_PREVIOUS` | razón de invariante incumplido y fingerprint padre | el emisor anterior debe corregir su delta de diseño. |
| `QUARANTINE_REFERENCE` | IDs de referencia, riesgo y límite de reutilización | ningún activo de la referencia llega a output. |
| `CONTRADICTED` | restricciones incompatibles preservadas | exige revisión humana, no selección automática. |
| `UNSUPPORTED_CHANNEL` | canal y capacidades faltantes | el blueprint permanece incompleto y no se ejecuta. |

Una disposición no modifica el estado de acceptance, ejecución ni validación.

## Invariantes

1. `upstream_binding` es bit a bit inmutable para productores de Design.
2. Cada transformación añade un `provenance_delta` con padre exacto; nunca
   elimina una contradicción, non-claim o restricción material.
3. Dos `message_id` idénticos con fingerprint distinto producen
   `IdentityCollision`; un replay exacto es idempotente.
4. Un producer no se vuelve dueño de facts, authority o rights porque el sobre
   lo referencia.
5. Todo `claim_binding` derivado referencia al menos un `fact_id` o
   `evidence_ref`; una decoración no ligada se etiqueta `decorative`.
6. Una referencia en cuarentena nunca se convierte en token, componente,
   imagen, tipografía ni prompt de reproducción.

## Compatibilidad y migración

La versión `0.1.x` admite consumers que soporten exactamente el conjunto de
campos obligatorio. Campos desconocidos se preservan bajo `payload.body`, sin
que el consumer les atribuya semántica. Una versión `0.2+` requiere negociación
explícita; un consumer `0.1.x` emite `UNSUPPORTED_VERSION`, no downgrading
silencioso. Migrar exige conservar `parent_fingerprint`, mapear campos y dejar
un registro de pérdida `NONE` o lista explícita de campos no migrables.

## Fallo, recuperación y rollback

- Campos upstream faltantes, temporalidad stale, certainty inválida o
  procedencia rota → `RETURN_UPSTREAM`; el payload no alcanza E01.
- Mutación de facts, evidence, authority o contradiction →
  `RETURN_TO_PREVIOUS` y cuarentena del delta emisor.
- Colisión de identidad → `IdentityCollision`; no hay retry automático.
- Canal sin adapter/constraint → `UNSUPPORTED_CHANNEL`; no se aproxima una
  salida en otro canal.
- Se revoca una referencia después del handoff → `QUARANTINE_REFERENCE`,
  invalidación de los derivados que la usen y recomposición desde el padre.

El rollback elimina únicamente el delta de Design afectado; jamás reescribe el
registro upstream.

## Observabilidad y evidencia

Cada assessment debe registrar: `envelope_fingerprint`, fingerprint padre,
producer/consumer, disposición, reason codes, IDs de facts/evidence usados,
contradicciones preservadas, manifest de derechos, versión y timestamp lógico.
Las métricas candidatas son cobertura de claim bindings, porcentaje de returns,
quarantines por tipo de activo y transformaciones con pérdida prohibida.

## Vectores de validación requeridos

1. Handoff limpio y actual conserva cada campo upstream y alcanza E01.
2. Ausencia de audiencia, decisión, evidencia, autoridad o procedencia devuelve
   todas las razones en un solo `RETURN_UPSTREAM`.
3. Certainty fuera del vocabulario protegido se rechaza sin default.
4. Reuso de `message_id` con distinto payload genera colisión.
5. Delta de E02 que intenta elevar `PLAUSIBLE` a `VERIFIED` es rechazado.
6. Contradicción propagada por E01 llega intacta a E04.
7. Referencia revocada cuarentena los derivados y conserva lineage.
8. Consumer 0.1 ante `0.2` responde `UNSUPPORTED_VERSION`.

## No-claims

Conformidad con este contrato no demuestra razonamiento visual correcto,
calidad estética, accesibilidad real, derechos suficientes, ejecución de un
renderer, integración, publicación, validación humana ni aceptación global.
