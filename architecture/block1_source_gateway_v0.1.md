# Block 1 — Source Gateway gobernado v0.1

**Clasificación:** cambio metodológico incremental y local a E02.  
**Estado:** `IMPLEMENTED / LOCAL-TESTED` sólo cuando su suite se ejecute; no es aceptación de gate.  
**Propietario semántico:** E02 Knowledge Acquisition.

## Propósito y alcance

El Source Gateway convierte un **paquete manual** de una fuente previamente registrada en una observación atestada compatible con el runtime de Block 1. Establece el límite entre catálogo de fuentes y evidencia admisible.

La v0.1 no hace solicitudes HTTP, scraping, RSS, autenticación externa, persistencia de credenciales ni programación. Es un paso previo verificable para evaluar conectores reales sin abrir una vía de adquisición no gobernada.

## Entradas y salida

- Entrada de configuración: hasta 50 registros de fuente. Cada registro
  `BOUND` requiere además autorización de binding HMAC vigente y exacta, junto
  con identidad, editor, scope, hosts HTTPS, claims y límite de contenido.
- Entrada de ejecución: `source_id`, URL canónica del artefacto, contenido, `observed_at`, claim, polaridad y correlación.
- Salida: registro `OBSERVED` atestado por el issuer configurado, con URL, hash, método de ingreso y procedencia firmados.

La salida pasa después por el `EvidenceVerifier` existente; emitirla no prueba que sea verdadera, actual, independiente, útil ni aceptada.

## Invariantes y autoridad

1. Sólo una fuente `BOUND` con autorización firmada, vigente y exacta puede
   emitir a través del gateway; el estado por sí solo no es autoridad.
2. La URL debe ser HTTPS, sin credenciales, fragmento, puerto o host local/IP, y pertenecer a la allowlist de esa fuente.
3. El Gateway calcula el hash del contenido; el cliente no lo declara.
4. La procedencia raíz se fija en la identidad registrada de la fuente, de modo que varios artefactos de una misma fuente no se presenten como raíces independientes.
5. `observed_at` no puede ser futuro respecto del reloj inyectado; la vigencia posterior la hace cumplir `EvidenceVerifier`.
6. El Gateway no eleva estados epistémicos: sólo emite `OBSERVED`, y E05/E08 conservan sus límites de evaluación/autorización.

La allowlist, el issuer y el autorizador de binding son autoridad de
configuración del host. El paquete manual, la URL, el contenido o un expediente
no firmado no crean autorización por sí mismos.

## Fallo, recuperación y observabilidad

- Cualquier registro, URL, campo, estado, claim, polaridad o tiempo inválido falla cerrado sin emitir evidencia.
- El gateway es puro y no persistente: un error no deja efectos parciales; reintentar el mismo paquete entrega el mismo material firmado mientras se conserve la misma configuración e issuer.
- La salida conserva `source_id`, editor, URL, hash SHA-256, timestamp, método `MANUAL_SOURCE_BUNDLE`, correlación y raíz de procedencia.
- La red queda fuera del binario. Una futura adquisición de red requiere contrato de adaptador, términos de uso, rate limits, aislamiento de secretos, observabilidad y revisión de arquitectura.

## Dependencias, impactos y no-claims

Depende de `EvidenceIssuer` / `EvidenceVerifier` y del contrato operacional v0.3. No modifica E03–E08, SQLite, gates ni contratos compartidos de los Bloques 2–4.

Efecto directo: E02 recibe evidencia con identidad de fuente registrada. Efectos de segundo orden: reduce la superficie de procedencia fabricada y prepara la revisión de licencias por fuente. Efectos de tercer orden: futuros conectores deberán respetar el mismo contrato; no se les concede autoridad por esta implementación.

No reclama ingestión real, acceso a internet, legalidad de una fuente, licencia validada, datos actuales, verdad del contenido, independencia entre editores distintos, producción ni aceptación global.

## Validación prevista

Pruebas de contrato y adversariales: capacidad 50/51, IDs duplicados, fuente no registrada o no BOUND, URL no HTTPS/host no autorizado/local/IP/con credenciales/fragmento, contenido excedido, claim/polaridad/tiempo inválidos, mutación tras atestación e integración con `EvidenceVerifier` y el runtime.
