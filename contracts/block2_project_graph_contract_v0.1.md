# Block 2 — Project Graph Contract v0.1

> Estado: `CANDIDATE / BOUNDED IMPLEMENTED / LOCAL EXECUTED / MAR REQUIRED`

## Productores, consumidores y autoridad

El `Traceable Runtime Adapter` añade identidades, nodes y edges después de que
el runtime E01–E08 emite resultados tipados. Design Studio, Evidence Inspector,
Visual Ops y Export podrán leerlos. El grafo conserva lineage; no decide verdad,
rights, calidad, publicación, memoria o aceptación.

## Forma mínima

Un node contiene `project_id`, `node_id`, `node_type`, SHA-256 de contenido,
payload mínimo y fecha con zona horaria. Un edge contiene proyecto, origen,
relación tipada, destino, evidencia y fecha. Relaciones admitidas:
`DERIVED_FROM`, `SUPPORTS`, `CONTRADICTS`, `REPRESENTS`, `GENERATED_BY`,
`TRANSFORMED_FROM`, `USED_IN`, `VALIDATED_BY`, `SUPERSEDES` y `EXPORTED_AS`.

## Invariantes, errores y recuperación

- Identidad exacta repetida es idempotente; misma identidad con otro contenido
  es `IDENTITY_COLLISION` y no sobrescribe.
- Edges sólo enlazan nodes existentes en el mismo proyecto.
- `run_id` es distinto del fingerprint del brief y constituye la identidad de
  replay; dos runs del mismo brief pueden coexistir.
- El journal es append-only. Editar produce una nueva versión CDD enlazada; no
  muta historia.
- La persistencia local usa transacciones SQLite y WAL. Un fallo intermedio
  revierte todo el append del run.
- Un graph válido no prueba comportamiento de proveedor, accesibilidad real,
  publicación, aceptación ni gate global.

## Compatibilidad y migración

El backend v0.1 es SQLite local. Otro backend debe conservar identidad,
idempotencia, atomicidad, relaciones tipadas, orden observable y los mismos
contract tests. Cambiar relations, ownership o autoridad exige Master
Architecture Review.

## Evidencia y límites

La implementación acotada vive en `src/sictra_block2_design/project_graph.py`
y `traceable_runtime.py`. Las pruebas locales cubren replay, colisión, rollback,
missing nodes, relación no permitida y coexistencia de runs. No existe todavía
SHA GitHub, CI hospedada, revisión independiente o aceptación de arquitectura.

