# Bloque 2 — CDD + Project Graph, ciclo local trazable

> Fecha/contexto: `2026-08-30`, Python 3.11+, Windows, SQLite local.  
> Certeza/confianza: `VERIFIED / A` para las ejecuciones locales descritas.  
> Frontera: `BOUNDED IMPLEMENTATION / NOT INTEGRATED / NOT ACCEPTED`.

## Closure delta

- Implementado CDD inmutable con SHA-256 canónico, pages/elements, lineage,
  assets por contenido y versiones padre-hijo.
- Implementado Project Graph SQLite WAL append-only con nodes, edges tipados,
  idempotencia, colisión fail-closed y transacción por run.
- Implementado adapter explícito E01–E08 → Graph/CDD sin cambiar el runtime
  anterior ni permitir que el grafo adquiera autoridad semántica.
- Expuesta ejecución trazable en CLI mediante `--trace-db`, `--run-id` y
  `--run-at`.
- Separada identidad de run del fingerprint upstream para permitir reintentos,
  forks y reevaluaciones del mismo brief sin colisiones falsas.

## Ejecuciones

| Comando | Resultado | Evidencia |
|---|---|---|
| `python -m unittest tests.test_block2_traceable_state -q` | 9/9 PASS | contract, adversarial, rollback |
| `python -m unittest discover -s tests -p 'test_block2*.py' -q` | 93/93 PASS | regresión Bloque 2 |
| `python -m unittest discover -s tests -q` | 302/302 PASS | regresión workspace |
| `python -m compileall -q src tests` | exit 0 | sintaxis/import local |

La prueba CLI además ejecuta dos veces el mismo `run_id`/timestamp: primera
acción `APPENDED`, replay `IDEMPOTENT`; estado CDD
`CANDIDATE_NOT_ACCEPTED` y estado runtime `NOT_ACCEPTED`.

## Red-team y reparación

| Vector | Resultado |
|---|---|
| URL o script dentro de CDD | rechazado |
| asset sin SHA-256 | rechazado |
| version ID con contenido distinto | collision, historia preservada |
| parent inexistente/otro documento | rechazado |
| relación fuera del allowlist | rechazada |
| edge hacia node inexistente | rechazado |
| fallo inyectado a mitad del run | rollback completo |
| mismo brief con dos `run_id` | ambos coexisten |
| mismo `run_id` exacto | idempotente |

El primer diseño identificaba run mediante fingerprint upstream. Red-team
demostró que dos ejecuciones legítimas del mismo brief colisionarían; se reparó
introduciendo `run_id` independiente y se añadió regresión.

## Reconciliación y promoción

No se repitieron consultas remotas: el cache de evidencia del ciclo E01–E08 del
mismo día seguía vigente y ninguna incertidumbre activa requería Slack, Notion,
GitHub, Rovo o Wolfram. GitHub continúa sin poder acreditar esta capacidad
porque el checkout local no tiene `HEAD`/SHA. Los resultados son evidencia de
runtime sintético local, no arquitectura aceptada, UI, proveedor real ni gate.

## Riesgos y siguiente ataque

Faltan serialización de lectura CDD, diff semántico, invalidación mínima,
checkpoints/reanudación, UI Evidence Inspector, aislamiento multiusuario,
review independiente y CI ligada a SHA. El siguiente slice de mayor valor es
un read model seguro para Design Console y Lineage Ribbon sobre este grafo.

