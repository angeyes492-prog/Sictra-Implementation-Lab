# Block 1 — Source Approval Record v0.1

**Clasificación:** cambio metodológico incremental, local a E02.
**Estado:** `IMPLEMENTED CANDIDATE / LOCAL-TESTED` tras ejecutar su suite.
**Propietario semántico:** E02 Knowledge Acquisition.

## Propósito y alcance

El expediente de aprobación registra las condiciones que una persona debe
revisar antes de que una fuente propuesta pueda presentarse a una revisión de
configuración del Source Gateway. Es el puente auditable entre descubrimiento y
configuración; no crea un registro `BOUND` ni modifica el gateway.

La v0.1 permite solamente `MANUAL_SOURCE_BUNDLE`. No almacena secretos,
credenciales, cookies ni licencia completa, y no hace llamadas de red.

## Invariantes y autoridad

- Un registro declara fuente, revisor identificable, fecha, evidencia de
  términos, hosts revisados, claims, límite de contenido, método y decisión.
- Sólo una decisión `APPROVED` puede resultar `READY_FOR_GATEWAY_CONFIGURATION_REVIEW`.
- Los hosts aprobados deben ser subconjunto de los hosts candidatos del
  Portfolio; ningún registro puede ampliar la superficie de adquisición.
- La fuente conserva estado `PROPOSED`; `READY` significa que falta configurar
  explícitamente `SourceRegistration` y no que la fuente está habilitada.
- El valor de revisor y referencia de evidencia son campos de trazabilidad,
  no una prueba criptográfica de identidad ni de autoridad.

## Fallos, recuperación y observabilidad

Valores vacíos, host inseguro, fecha futura, decisión o método desconocido,
claims vacíos, fuente distinta y ampliación de host fallan cerrados. El registro
es inmutable. La salida de evaluación incluye todos los campos de procedencia,
la decisión y un bloqueo explícito cuando no es apto.

Recuperar una revisión implica emitir un expediente nuevo; no hay mutación ni
reintento. Un futuro sistema de identidad, firmas y retención requerirá otra
versión y revisión de arquitectura.

## Validación y no-claims

Las pruebas cubren aprobación, rechazo, host adversarial, fecha futura,
identidad cruzada, ampliación de allowlist y conservación de `PROPOSED`.
La evidencia local no prueba que la revisión humana, términos, autoridad o
fuente sean auténticos, ni habilita acceso a internet, producción o un gate.
