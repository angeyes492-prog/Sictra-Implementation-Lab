# Bloque 2 / Design — Dossiers E02 y E03 v0.2

> Estado común: candidatos de arquitectura local. Esta versión sustituye v0.1
> para el estado de E02; preserva el historial de v0.1 como diseño inicial.
> No acepta ningún motor ni modifica una arquitectura común.

## Decisión de actualización

El dossier v0.1 registraba correctamente que E02/E03 no tenían evidencia
localizada al 2026-08-24. Desde entonces se creó un contrato y un SUT limitado
para E02. La actualización es un cambio metodológico local, no una promoción:
el SUT valida propuestas sintéticas contra su contrato, no una dirección
creativa real ni un flujo completo E01→E03.

## E02 — Creative Direction

| Dimensión | Estado | Evidencia / límite |
|---|---|---|
| Diseño | `CANDIDATE / BOUND` | contrato `block2_e02_creative_direction_contract_v0.1.md`. |
| Implementado | `YES / LOCAL BOUNDED SUT` | `src/sictra_block2_design/e02_direction.py`; sólo clasificador. |
| Ejecutado | `YES / LOCAL` | 20 pruebas E02, 2026-08-28. |
| Validado | `LOCAL DIFFERENTIAL` | oráculo separado; no revisor externo ni CI. |
| Integrado | `NO` | no adapter E01→E02, caso real ni E03. |
| Aceptado | `NO` | requiere Master Architecture Review y evidencia adicional. |

### Propósito y límites vigentes

E02 conserva claims, certainty, contradicciones, non-claims y exposición de
incertidumbre mientras clasifica dos o tres direcciones propuestas. Exige dos
ejes materiales por par. No genera direcciones, selecciona ganador, usa assets
sin manifest, actualiza memoria, crea autoridad ni produce arte final.

### Dependencias y recuperación

Depende de envelope actual, tesis con binding, referencia permitida y canal
soportado. Insuficiencia/lineage roto retorna upstream; tesis o diversidad
inválida retorna al productor anterior; referencias dudosas se cuarentenan. El
rollback descarta el set local y conserva el padre.

### Red-team y riesgo residual

Se cubrieron cosmética, un eje, mutaciones de metadata, cuarentena, selección
ilegal, proxy sensible y matrices de mutación. Falta comprobar que diferencias
estructurales produzcan comprensión humana o valor creativo en un caso
autorizado.

## E03 — Design System

| Dimensión | Estado | Evidencia / límite |
|---|---|---|
| Diseño | `CANDIDATE` | contrato `block2_e03_design_system_contract_v0.1.md`. |
| Implementado / ejecutado / validado | `NO` | no SUT, tests ni CI. |
| Integrado / aceptado | `NO` | requiere selección E02 autorizada, manifest de marca y rights manifest. |

E03 mantiene su propósito de restricciones reutilizables: tokens semánticos,
fallbacks, tipografía, layout, excepciones, accesibilidad y compatibilidad por
canal. No decide argumento visual, certeza, dirección ni autoridad.

## Contradicciones y efectos downstream

1. El PR #3 de E01 sigue abierto y no contiene E02; E02 local no puede
   presentarse como continuación canónica de esa rama.
2. Slack y Notion no aportan evidencia específica de E02; el SUT se sustenta en
   contrato candidato y pruebas locales, no en autoridad histórica.
3. La nueva frontera mejora observabilidad y regresión local, pero aumenta la
   necesidad de un adapter versionado y de revisión de contrato común antes de
   E01→E02 o E02→E03.
4. No hay impacto en runtime de Block 1, gates globales ni Precision.

## Próximo gate local

Revisar el adapter de intake E01/E02 y un fixture autorizado; sólo entonces
proponer una integración local que conserve procedencia y no genere direcciones
desde información incompleta. Si el review no acepta la relación, el SUT E02
permanece aislado.

