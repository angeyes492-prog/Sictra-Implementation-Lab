# Block 2 / E02 — DirectionSet local SUT cycle

> Fecha: `2026-08-28`  
> Estado: `IMPLEMENTED / EXECUTED / LOCAL BOUNDED DIFFERENTIAL CHECK`; no
> integración, evidencia humana, CI externa ni aceptación.

## Closure delta

Se implementó un SUT local que **clasifica propuestas sintéticas** de
direcciones E02 sin generarlas ni seleccionarlas:

- `src/sictra_block2_design/e02_direction.py`;
- oráculo declarativo separado: `src/sictra_block2_design/e02_direction_oracle.py`;
- pruebas directas y diferenciales:
  `tests/test_block2_e02_direction.py` y
  `tests/test_block2_e02_direction_oracle.py`.

El SUT preserva claim bindings, certainty, contradicciones, non-claims y
exposición de incertidumbre. Requiere dos ejes estructurales materiales por
par y rechaza selección de ganador, referencias en cuarentena, adaptación
prohibida, lineage roto, stale input y canal fuera de contrato.

## Ejecución

| Ejecución | Resultado | Alcance |
|---|---|---|
| `python -m unittest tests/test_block2_e02_direction.py tests/test_block2_e02_direction_oracle.py -v` | `20/20 PASS` | SUT E02, fallos, adversarial y oráculo diferencial. |
| `python -m unittest discover -s tests` | `193/193 PASS` | regresión local del workspace. |
| `python -m compileall -q src tests` | éxito | sintaxis Python local. |

El primer intento de la suite del oráculo falló porque importaba helpers del
otro módulo de pruebas (`ModuleNotFoundError`). Se corrigió duplicando fixtures
sintéticos locales, sin reutilizar lógica de evaluación; el resultado final
arriba es posterior a la reparación.

## Red-team ejecutado

- variación sólo cosmética y sólo un eje material;
- mutación de claim, certainty, contradicción y non-claim;
- selección ilegal dentro de E02;
- referencia en cuarentena y referencia no autorizada;
- adaptación basada en proxy sensible;
- envelope stale/no `CONTINUE`, lineage roto y canal no soportado;
- 32 combinaciones de diversidad, preservación y cuarentena comparadas con el
  oráculo;
- set de tres direcciones donde un par sólo difiere cosméticamente.

## Reconciliación de cuatro fuentes

| Fuente | Observación | Certeza / límite |
|---|---|---|
| GitHub PR #3, consultado 2026-08-28 | E01 sigue en rama abierta con mecanismos CI acotados; no hay E02 en el PR. | `VERIFIED / A` para el PR; no autoridad E02. |
| Slack | búsqueda `E02` + `Creative Direction` sin resultados. | `INSUFFICIENT EVIDENCE`; ausencia no prueba inexistencia. |
| Notion | búsqueda E02 recupera sólo reassessments de E01. | `INSUFFICIENT EVIDENCE` para E02. |
| Rovo SI-1 | alcance: activos desde handoffs tipados sin semántica de Intelligence. | `VERIFIED / A` como alcance operativo, no promoción. |
| Wolfram | modelo: falta de tesis, divergencia cosmética o mutación de claim bloquean; requisitos completos permiten set candidato. | `VERIFIED / A` para modelo, no runtime. |

## Estado por dimensión

| Dimensión E02 | Estado |
|---|---|
| Diseño | `VERIFIED / CANDIDATE` según contrato v0.1 |
| Bound | `LOCAL / CANDIDATE` |
| Implementado | `YES / LOCAL BOUNDED SUT` |
| Ejecutado | `YES / 20 pruebas E02` |
| Validado | `LOCAL DIFFERENTIAL ORACLE`, no independiente humana/externa |
| Integrado | `NO` |
| Aceptado | `NO` |

## No-claims y siguiente ataque

No se generó una dirección creativa real, no se usó un objeto upstream real, no
se evaluó comprensión/preferencia humana, no se conectó software de diseño y
no se probó licencia real. El siguiente ataque de mayor valor es enlazar E01
normalizado con el envelope E02 mediante un adapter explícito y un fixture
autorizado; si falta el objeto, el resultado debe ser `RETURN_UPSTREAM`.

