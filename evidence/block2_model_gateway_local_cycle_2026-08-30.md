# Bloque 2 — Model Gateway local, ciclo ejecutable

> Fecha/contexto: `2026-08-30`, proveedor determinista local sin red.  
> Certeza/confianza: `VERIFIED / A` para runtime local.  
> Frontera: `STUB / NOT A REAL PROVIDER / NOT ACCEPTED`.

## Closure delta

- E06 produce una `CreativeExecutionSpec`; el runtime dejó de invocar el
  renderer fuera de la frontera Model Gateway.
- El gateway fija manifiesto por ID y hash canónico completo, valida lineage y
  devuelve receipt con input/output hash, outcome, quarantine, retries y coste.
- Replay exacto es idempotente. Provider remoto, manifiesto sustituido, hash
  mutado, lineage distinto o rights/health inválidos fallan antes de render.
- Project Graph registra la ruta `E06 → MODEL_GATEWAY_RECEIPT → ASSET`, mientras
  E07 conserva la validación del asset.

## Ejecuciones

| Comando | Resultado | Clase |
|---|---|---|
| `python -m unittest tests.test_block2_model_gateway -v` | 6/6 PASS | gateway focal/adversarial |
| `python -m unittest discover -s tests -p 'test_block2*.py' -q` | 105/105 PASS | regresión Bloque 2 |
| `python -m unittest discover -s tests -q` | 314/314 PASS | regresión workspace |
| `python -m compileall -q src tests` | exit 0 | sintaxis/import |
| `python -m sictra_block2_design` | E01–E08 exit 0 + receipt | runtime local |

Artefacto antes/después: SHA-256
`aaa78dec99764388100567416140fe9d288e06608de1dd5edf2555d898987370`.
Receipt de la ejecución de referencia:
`RECEIPT-e23fd60523297a12854a0897`, outcome `EXECUTED`, coste 0,
`LOCAL_VALIDATED`, `NOT_PUBLISHED / NOT_ACCEPTED`.

## Red-team y reparación

El diseño inicial fijaba sólo `manifest_id`. Un proveedor podía conservar ese
ID y mutar provider/adapter/state. Se añadió `provider_manifest_hash` al spec y
al input hash; el vector ahora detiene E06 con
`PROVIDER_MANIFEST_HASH_MISMATCH`. También se rechazan remote I/O y manifiesto
con ID sustituido.

## Límites y siguiente ataque

No hay proveedor real, credenciales, rate limits, coste externo, timeout,
cancelación, fallback ni sandbox contractual. Un adapter real permanece
`RETURN_UPSTREAM` hasta documentación oficial, terms, credenciales gobernadas y
review. El siguiente ataque local es edición CDD + diff semántico + invalidación
mínima antes de habilitar mutaciones desde Studio.

