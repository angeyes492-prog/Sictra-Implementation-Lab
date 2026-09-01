# Block 2 — Document Evolution Contract v0.1

> Estado: `CANDIDATE / LOCAL EXECUTED / MAR REQUIRED`

## Productor, consumidores y autoridad

Design Studio produce una `DocumentEditProposal` sobre una versión CDD actual.
El servicio común de evolución valida y produce una nueva versión, un diff
semántico y un plan de invalidación. E03–E08, Inspector, Orchestrator y Export
consumen esos resultados. El servicio no decide calidad, rights, publicación,
aceptación ni validez factual del copy.

## Precondiciones

- Proyecto, documento, base version/hash y actor son explícitos.
- La base existe, es current y coincide exactamente con el hash declarado.
- Cada operación apunta a un `element_id` editable existente.
- Sólo se pueden proponer cambios a contenido, geometría, tokens, asset refs,
  accessibility label o rights state; claims, evidence, limitations y lineage
  no son mutables desde Studio.
- Assets son SHA-256 allowlisted; texto conserva las restricciones CDD.

## Resultado

La aplicación válida crea un hijo inmutable con nuevo `version_id`,
`parent_version_id`, actor/time, estado `EDITED_CANDIDATE_NOT_VALIDATED` y
validations vacías. `DocumentDiff` reporta cada dominio material modificado:
`CONTENT`, `GEOMETRY`, `STYLE`, `ASSET`, `ACCESSIBILITY` o `RIGHTS`.

El plan de invalidación contiene el conjunto mínimo conservador de motores:

| Dominio | Invalidar desde |
|---|---|
| STYLE | E03 |
| CONTENT, GEOMETRY, ACCESSIBILITY | E04 |
| ASSET, RIGHTS | E05 |

Todo cambio invalida E06, E07 y E08. Los motores anteriores al primer root se
conservan sólo si manifiestos, policies, rights y hashes siguen current.

## Errores, replay y recuperación

- Base stale, hash distinto, campo prohibido, elemento inexistente/no editable,
  operación duplicada o no-op devuelven error tipado y no escriben.
- Mismo `edit_id` con mismo input es idempotente; mismo ID con otro input es
  identity collision.
- Persistencia de child CDD, graph nodes/edges, diff e invalidation es atómica.
- Rollback preserva la versión padre y cualquier historia previa.

## Compatibilidad, evidencia y no-claims

Versión soportada `0.1.x`. Cambiar dominios, roots u ownership exige MAR y
regresión. Un diff correcto no prueba corrección visual, accesibilidad real,
rights, publicación, aceptación, render ni que el cambio sea profesionalmente
conveniente.
