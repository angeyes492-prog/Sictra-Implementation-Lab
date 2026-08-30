# Contrato candidato — Block 3 Account Knowledge Fabric v0.1

**Estado:** `CANDIDATE / LOCAL BOUNDED SUT`.

## Entrada y salida

`AccountSeed` requiere `tenant_id`, `account_id`, `official_url` y propósito
autorizado. Puede provenir de un lote Excel read-only, pero tenant y propósito
deben estar ligados fuera del workbook. `official_url` no puede contener
credenciales y se normaliza sin query ni fragment. La política limita HTTP(S),
páginas, profundidad, bytes y retención.

`AccountKnowledgeDossier` contiene sólo observaciones atribuibles: URL,
extracto limitado, tipo de página, hash del contenido, timestamp, expiración,
EvidenceRef, tags, cuarentena y restricciones. El dossier no contiene copy,
destinatario, consentimiento ni acción de contacto.

## Reglas de aceptación

- El host debe ser el dominio oficial o un subdominio permitido.
- El fetcher debe configurarse con el host oficial aprobado, rechazar destinos no
  públicos y detener la cadena de redirect antes de solicitar un host no aprobado.
- `robots.txt` vigente se cumple; excepción `404` equivale a ausencia de regla.
- Una observación website es una declaración de fuente y sólo puede convertirse
  en hipótesis M05 ACCOUNT; no en `FACT`.
- Texto con patrón de instrucción queda cuarentenado y no llega a M05.
- Tenant y account coinciden entre dossier y cada observación.
- El ledger rechaza colisiones y verificará la cadena HMAC antes de leer.
- La consulta no expone registros expirados ni tombstoned.

## No-claims

No hay escritura Excel, CRM, autenticación de usuario, cifrado, borrado físico,
renderizado JavaScript, OCR, crawling de terceros, entrega, consentimiento ni
aceptación de gate global. El adapter Excel read-only es una frontera separada;
la detección de inyección es una defensa adicional, no una prueba completa de
contenido inocuo.

