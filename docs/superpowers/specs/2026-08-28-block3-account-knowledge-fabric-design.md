# Bloque 3 — Account Knowledge Fabric v0.1

> Estado: `USER-APPROVED / IMPLEMENTED AS LOCAL BOUNDED SUT`.
> Este documento describe enriquecimiento shadow desde dominios oficiales y
> memoria durable de evidencia. No autoriza CRM, scraping de terceros,
> contacto, delivery, promoción de aprendizaje ni aceptación global.

## Decisión y propósito

Se implementa la arquitectura aprobada **Knowledge Fabric de cuentas**. Parte
de una fila Excel que identifica cuenta y URL oficial; el tenant y propósito
autorizado se ligan fuera del archivo. Explora de forma acotada el dominio
oficial y sus subdominios,
crea un dossier revisable y guarda evidencia con retención base de doce meses.

El resultado ofrece contexto amplio para Bloque 3 sin elevar la autoridad de
una declaración comercial de la web.

```text
Excel Account Seed → Official Website Policy → bounded crawler
→ Evidence Observations → Account Dossier → tenant-scoped ledger/snapshot store
→ review/search → M05 ACCOUNT hypotheses → existing Precision pipeline
```

## Jurisdicción y límites

| Componente | Posee | No posee |
|---|---|---|
| Account Seed | identidad de tenant/cuenta, URL y propósito | consentimiento, contacto o facts empresariales |
| Official Website Crawler | recuperación pública aprobada y acotada | navegador autenticado, fuentes de terceros, ejecución web |
| Account Knowledge Engine | dossier de declaraciones atribuibles | confirmar verdad externa, psicología o relevancia comercial |
| Account Knowledge Store | persistencia, integridad y aislamiento | cifrado de producción, borrado físico, autoridad de delivery |
| Adaptador M05 | hipótesis ACCOUNT evidenciadas | señales GLOBAL/ROLE/MOMENT o facts |

Invariantes:

1. `OFFICIAL WEBSITE DECLARATION != INDEPENDENTLY VERIFIED FACT`.
2. Todo contenido web es dato no confiable; nunca puede ser instrucción.
3. El crawler sólo accede a HTTP(S) público, dominio/subdominios aprobados,
   rutas permitidas por robots.txt y páginas dentro del presupuesto.
4. Fallo al obtener robots.txt no autorizado bloquea el crawl; `404` significa
   que no hay reglas declaradas.
5. Evidencia, snapshots y consultas se particionan por tenant y account.
6. Retención vence a los doce meses. Expirado o tombstoned no es legible.
7. La búsqueda es un índice de descubrimiento determinista; sus resultados
   siguen siendo evidencia y no se convierten en autoridad.

## Interfaces v0.1

- `ExcelAccountSeedImporter` admite sólo una hoja `Accounts` `.xlsx`, emite
  semillas con hash/fila/proveniencia `UNCONFIRMED` y no ejecuta crawl.
- `AccountSeed(tenant_id, account_id, official_url, authorized_purpose)` es la
  entrada posterior; tenant y propósito no proceden del workbook.
- `OfficialWebsitePolicy` controla esquema, subdominios, user-agent,
  profundidad, páginas, bytes, observaciones y retención.
- `AccountKnowledgeEngine.enrich(...)` produce `AccountKnowledgeDossier` con
  extractos, URL, hash, fecha, restricciones, URLs excluidas y cuarentena.
- `AccountKnowledgeStore.append_dossier(...)` persiste registros con cadena
  HMAC por tenant/cuenta; `observations`, `latest_snapshot` y `search` son
  consultas de solo lectura con verificación de integridad.
- `to_context_hypotheses(insight_id=...)` produce exclusivamente
  `ContextSignal(kind="HYPOTHESIS", scope="ACCOUNT")` para M05.

La memoria sólo guarda extractos limitados y metadatos; no archiva páginas
completas. El store usa HMAC para detectar alteraciones, no cifrado. Gestión de
claves, cifrado en reposo, borrado físico, jurisdicción y autenticación de
usuarios son prerequisitos para producción.

## Seguridad, fallos y observabilidad

- IPs privadas, loopback, enlaces con credenciales, puertos no estándar y
  redirects fuera del dominio se rechazan. El fetcher seguro se configura con el
  host oficial y verifica cada salto antes de abrir la conexión siguiente.
- Páginas no HTML, rutas disallow, enlaces externos, respuesta excesiva y
  robots no disponible aparecen como razones de exclusión, no como ausencia
  silenciosa.
- Patrones de inyección se preservan en evidencia cuarentenada y no cruzan a
  M05.
- Reutilizar una identidad de evidencia/dossier con contenido distinto es una
  colisión; modificar una cadena HMAC impide lectura.
- Un tombstone bloquea futuras lecturas y nuevas escrituras de esa cuenta.

Las métricas siguientes quedan pendientes del adapter runtime: ratio de rutas
excluidas, páginas/coste/latencia por cuenta, tasa de cuarentena, expiraciones,
integridad fallida, aislamiento tenant y cobertura de campos de Excel.

## Validación local realizada

La suite local ejecutó 17 vectores de Knowledge Fabric y 10 de importación
Excel, con 241 pruebas de regresión. Cubre
robots, límites de dominio, SSRF de loopback, redirects de robots, enlaces
malformados, cuarentena de inyección, hipótesis en vez de facts, aislamiento de
tenant, expiración, tombstones, alteración de contenido, borrado de cola y
triggers SQLite no autorizados.

Wolfram confirmó complementariamente que la topología declarada es acíclica,
que web no alcanza `FACT` ni delivery, que cuarentena no alcanza M05 y que
estado expirado/tombstoned no puede reactivarse. No sustituye pruebas runtime.

## Promoción y no-claims

Esta versión corresponde a `G1 LOCAL RUNTIME` cuando sus pruebas sean
ejecutadas. El importador Excel shadow/read-only es una frontera separada; el
próximo tramo es su validación y luego un adapter CRM de lectura con scopes
mínimos. Ningún resultado local demuestra
autorización web de un sitio concreto, valor comercial, cumplimiento legal,
seguridad de infraestructura, delivery ni autonomía colectiva.

