# Block 2 — Model Gateway Contract v0.1

> Estado: `CANDIDATE / LOCAL STUB + INJECTED PROVIDER SANDBOX EXECUTED / MAR REQUIRED`

## Productor, consumidor y authority boundary

E06 es el único productor autorizado de `CreativeExecutionSpec`. El Gateway
elige un adapter compatible y devuelve asset candidates/receipts a E06. No
puede cambiar brief, claims, evidence, tokens, rights, human gates o aceptación.

## Precondiciones

Spec, E03/E04/E05 bindings, rights/policy, budget y capability requirements
deben ser actuales. Provider/adapter/model manifest debe estar pinned, vigente,
healthy y autorizado para medio/scope. Credenciales nunca aparecen en spec,
graph, CDD o receipt público.

## Resultado y fallos

El receipt incluye IDs/versiones, hashes, cost/latency/retries, timestamps,
policy/rights snapshot y outcome. Timeout, malformed media, hash mismatch,
scope expansion, provider substitution o unknown capability devuelven error
tipado; output queda en cuarentena y no modifica el CDD.

Retry usa idempotency key. Fallback requiere adapter allowlisted y equivalencia
de capabilities/rights; no ocurre silenciosamente. Cancel no afirma borrado en
provider sin evidencia contractual.

## Compatibilidad y no-claims

Provider versions son exactas o incompatibles. Stub determinista es evidencia
local, no prueba API real. Magnific/OpenAI/futuros adapters requieren contratos,
terms, sandbox, credentials, fixtures, rate/cost/error tests y review.

## Estado ejecutable acotado

`model_gateway.py` implementa un proveedor local sin red, manifiesto fijado por
ID y SHA-256 canónico, `CreativeExecutionSpec` exclusivo de E06, receipts,
idempotencia y cuarentena. `runtime.py` enruta E06 por esta frontera y Project
Graph registra `E06 → receipt → asset`. No existen credenciales, fallback o
adapter remoto; esto no acepta el contrato compartido ni demuestra una API.

## Sandbox gobernado local

`provider_sandbox.py` ejecuta adapters inyectados tras fijar manifest, policy,
rights, allowlist, budget, timeout e idempotency. Cancel previo evita invocación;
timeout solicita cancelación sin afirmar borrado remoto. Exceso de coste,
contenido/tipo/hash divergente, excepción, sustitución o rights stale producen
receipt tipado y cuarentena sin candidato. El receipt registra latency, cost,
budget, timeout, cancel state y hashes policy/rights.

La realización candidata v0.1 rechaza cualquier manifest con `remote_io=true`
antes de invocar el adapter, aun si una policy declara `allow_remote_io=true`.
Ese campo sólo reserva la forma de un contrato futuro: no es una capability ni
autoridad de ejecución. Las pruebas usan providers inyectados locales; no
demuestran credenciales, rate limits ni comportamiento contractual de una API
comercial real.
