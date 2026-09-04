# Block 2 / E01 — recibo de observación externa acotada (2026-09-01)

## Estado y límite

- Implementación: `CANDIDATE / EXECUTED LOCAL`.
- Validación perceptual, revisión independiente y aceptación: `NOT EXECUTED / NOT ACCEPTED`.
- Certeza: `VERIFIED`; confianza `A` para lógica local y sus vectores.

El artefacto no hace pasar un fixture a una observación ni convierte una
observación en regla. Sólo valida que un futuro recibo humano esté ligado al
fixture y al upstream correctos y conserva explícitamente
`NOT_PROMOTED / NOT_ACCEPTED`.

## Invariante formal desafiado

Wolfram evaluó la condición local de elegibilidad. El resultado confirma que
un recibo requiere simultáneamente `preflightReady`, upstream actual con
autoridad, reviewer independiente y distinto del autor, ausencia de fuga y
confounder material, observación anterior a exposición de tesis y observación
externa. Al fijar `materialLeakage` o `materialConfounder` en verdadero, la
expresión resulta `False`. Este análisis es una comprobación formal auxiliar;
no es evidencia runtime ni evidencia humana.

## Ejecución local

| Vector | Resultado |
|---|---|
| recibo íntegro sobre fixture preflighted | `OBSERVATION_RECORDED`, pero `NOT_PROMOTED / NOT_ACCEPTED` |
| autorrevisión + exposición de tesis + confounder | `INVALID_TRIAL` con tres razones preservadas |
| sustitución de hash de fixture | `INVALID_TRIAL / FIXTURE_HASH_MISMATCH` |
| upstream stale | `RETURN_UPSTREAM / UPSTREAM_NOT_CURRENT` |
| preflight upstream incompleto | `RETURN_UPSTREAM` precede cualquier recibo bien formado |

Comando focal: `python -m unittest tests.test_block2_e01_external_observation -v`:
4/4 PASS. `python -m compileall -q src tests`: PASS.

GitHub Actions ejecutó el workflow `SICTrA bounded runtime validation` con
resultado `success` en el run `33576265333`, ligado al SHA
`fc3d74e7f67214ca8dffc074328e9128734e46a9`. Esta es evidencia de CI para ese
validador local; no acredita la identidad o independencia de un reviewer real.

## Riesgos y siguiente ataque

La identidad real del revisor, firma/atestación externa, almacenamiento remoto,
el objeto upstream de producción y la observación humana no están disponibles
en este ciclo. Para un caso real, el owner upstream debe aportar primero el
objeto actual y autorizado; después un revisor independiente debe emitir el
recibo con evidencia atribuible. Si falta cualquiera de ellos, `RETURN_UPSTREAM`.

## Reassessment de fuentes — 2026-09-02

| Fuente | Consulta / identidad | Resultado | Clasificación |
|---|---|---|---|
| Slack | `"Wave 37" after:2026-09-01` y `"E01" "fixture" after:2026-09-01` | sin resultados | `INSUFFICIENT EVIDENCE` |
| Notion | `Wave 37 E01 authorized upstream fixture` | sólo páginas históricas Wave 34/35 del 2026-08-25, marcadas `unverified` | `INSUFFICIENT EVIDENCE` |
| GitHub | PR #11, head `09fe341e83df393290032e874ed7b193876983d1`, reviews | CI 33711675428 verde para código; cero reviews | `VERIFIED` para CI local; `INSUFFICIENT EVIDENCE` para MAR/observador |
| Wolfram | `upstream && independentReviewer && !materialLeakage && !materialConfounder` | la forma normal conserva las cuatro condiciones conjunctivas | `VERIFIED` formal auxiliar, no evidencia runtime/humana |

Conclusión: no existe un objeto upstream autorizado, observador independiente ni
decisión MAR que pueda alimentar el recibo. El caso E01 real queda
`RETURN_UPSTREAM`; el fixture y el validador locales no se promueven por la
ausencia de resultados ni por CI verde.

## Red-team de identidad del autor — 2026-09-03

Se detectó y reparó una debilidad local: `fixture_author_id` vivía sólo en el
recibo, lo que permitía declarar un autor distinto para ocultar una
autorrevisión. La identidad ahora pertenece al `Fixture`, forma parte de su
fingerprint y el recibo debe repetirla exactamente. Autor ausente retorna
`RETURN_UPSTREAM / FIXTURE_AUTHOR_ID_MISSING`; discrepancia de autor invalida
el ensayo con `FIXTURE_AUTHOR_MISMATCH`; el reviewer se compara contra la
identidad del fixture, no contra una declaración autocontenida del recibo.

Los vectores de preflight, entrypoint, oracle independiente y recibo (26/26)
pasaron localmente, junto con 472/472 pruebas del workspace. Esto cierra la
sustitución estructural, no acredita la identidad de una persona, una firma
externa ni una observación real.
