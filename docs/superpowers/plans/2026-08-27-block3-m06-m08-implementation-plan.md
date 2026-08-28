# Bloque 3 — Plan de implementación acotada M06–M08 v0.1

> **Base de diseño:** A∴ v0.1, commit
> `6d87170d2fc01502d3c0338f905f9d6993219046`.
> **Scope:** bounded deterministic SUT; sin adapters reales, delivery,
> consentimiento operativo, memoria durable o promoción global.

## Objetivo

Extender `sictra_block3_precision` sin modificar la semántica aceptada de
M01–M05. El nuevo pipeline deberá producir decisiones de relevancia,
estrategia, propuesta de entrega y aprendizaje candidato con identidad,
provenance, vigencia, restricciones y fingerprints deterministas.

## Tramos

### 1. Contratos y capas transversales

- ampliar tipos comunes sin cambiar contratos M01–M05;
- crear Context Pack inmutable;
- implementar Persona State Projection y Personalization Ceiling;
- implementar Relevance Gate mediante lattice explícita;
- añadir tests de identidad, versión, stale, contradicción y monotonicidad.

### 2. Adaptive Frontier y M06

- decidir L0–L3 con restricciones duras antes de beneficio marginal;
- degradar conservadoramente ante evidencia insuficiente;
- construir `MESSAGE_STRATEGY` sólo para Gate HIGH/MEDIUM cualificado;
- garantizar `applied_level <= effective_ceiling`;
- impedir creación de facts, assets extranjeros y delivery authority.

### 3. M07 y M08

- producir `SEND_CANDIDATE`, `WAIT`, `DO_NOT_SEND` o `RETURN_UPSTREAM`;
- conservar expiración, timezone, presión, cadence y checks del executor;
- modelar receipt/outcome como evidencia externa explícita;
- producir `NEXT_BEST_TEST` candidate-only;
- bloquear aprendizaje sin cadena completa o con autorreferencia circular.

### 4. Orquestación completa

- conservar `PrecisionFoundationPipeline` sin cambios de comportamiento;
- añadir un pipeline A∴ separado que consume el resultado fundacional;
- detenerse por precedencia de failure antes de producir artefactos downstream;
- no incluir efectos externos ni storage durable.

### 5. Validación

- unit, contract, boundary, state transition y adversarial tests;
- propiedad de monotonicidad: más restricciones nunca aumentan ceiling,
  presión o adaptive level;
- replay/fingerprint e identity collision;
- oráculos independientes para Gate y Controller;
- regresión completa del repositorio;
- Wolfram para DAG y caminos prohibidos.

## Archivos previstos

- `src/sictra_block3_precision/precision_context.py`
- `src/sictra_block3_precision/relevance.py`
- `src/sictra_block3_precision/adaptive.py`
- `src/sictra_block3_precision/message.py`
- `src/sictra_block3_precision/delivery.py`
- `src/sictra_block3_precision/learning.py`
- `src/sictra_block3_precision/adaptive_pipeline.py`
- `src/sictra_block3_precision/__init__.py`
- `tests/test_block3_precision_adaptive_frontier.py`
- contratos, dossier, evidencia y closure específicos del corte.

## Criterios de salida

1. M01–M05 mantienen su suite sin modificaciones ni regresiones.
2. M06–M08 poseen outputs tipados, deterministas y sin efectos externos.
3. Gate y Controller tienen oráculos independientes con mutaciones.
4. Todos los failure paths materiales son observables y conservadores.
5. CI queda ligada a un SHA exacto; no se declara integración productiva.


