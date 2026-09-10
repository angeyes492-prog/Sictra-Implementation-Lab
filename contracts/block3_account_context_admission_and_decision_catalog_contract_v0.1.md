# Contrato candidato — Admisión de contexto de cuenta y catálogo M02 v0.1

**Estado:** `CANDIDATE / LOCAL BOUNDED SUT`.

## Propósito

Conectar una investigación de cuenta ya aprobada y durable con M05 y, sólo por
reglas explícitas y versionadas, con candidatos de señal M02. Esta frontera
resuelve el salto de procedencia; no otorga relevancia, identidad personal,
consentimiento, ejecución ni contacto.

## Precondiciones de admisión M05

`AccountContextIngress.admit` recibe un `AccountResearchReceipt`, un
`AccountKnowledgeDossier`, un `insight_id` ya existente y tiempo lógico. Antes
de producir una señal exige simultáneamente:

1. igualdad de tenant, cuenta, dossier ID, fingerprint y tiempo de captura;
2. recibo no futuro ni vencido, presente byte-a-byte en un ledger HMAC íntegro;
3. snapshot del dossier aún presente e íntegro en `AccountKnowledgeStore`;
4. dossier y observaciones dentro de su vigencia.

Un fallo rechaza antes de emitir `ContextSignal`. Las observaciones en
cuarentena se omiten; si no queda ninguna, devuelve `RETURN_UPSTREAM`.

## Salida M05

La admisión sólo expone `ContextSignal(scope=ACCOUNT, kind=HYPOTHESIS)` desde
declaraciones no cuarentenadas del sitio oficial. Conserva `EvidenceRef`,
vigencia y raíz de procedencia. Prohíbe fact promotion, inferencia de atributos
personales, decisión de relevancia y delivery authority. Para un mapa M05
completo siguen siendo necesarias fuentes separadas `GLOBAL`, `INDUSTRY`,
`ROLE` y `MOMENT`.

## Catálogo de señales M02

`AccountContextIngress` atesta el material exacto de cada admisión con una
clave local configurada por issuer; el catálogo sólo acepta la atestación de
un issuer configurado y una policy de admisión declarada. Un objeto `AccountContextAdmission`
construido, modificado o sustituido por un llamador no es una admisión.

`DecisionSignalCatalogPolicy` contiene reglas identificadas, acotadas y con
autoridad declarada. Cada `DecisionSignalRule` vincula un conjunto de tags de
cuenta a una dimensión/valor M02 ya gobernados. Sólo una coincidencia explícita
produce `DecisionSignal(source_engine=GOVERNED_RULE, basis_kind=HYPOTHESIS)`;
usa la misma evidencia de la declaración de cuenta y no puede elevar certeza.

Sin coincidencia se devuelve `RETURN_UPSTREAM`, no un driver inventado. La
salida es una hipótesis falsable sobre la pertinencia de un ángulo, nunca una
preferencia o intención de la persona, y carece de autoridad de contacto.

## Rechazos y no-claims

- recibo ausente, alterado, vencido o sustituido;
- sustitución tenant/cuenta/dossier/fingerprint; snapshot ausente o distinto;
- admisión sin atestación válida, issuer desconocido o policy sustituida;
- señal fuera de `ACCOUNT/HYPOTHESIS`; reglas duplicadas, vacías o no
  gobernadas; exceder capacidad;
- ningún CRM, búsqueda nueva, email, contacto, consentimiento, ejecución,
  autenticación de revisor, cifrado de producción ni aceptación global.

## Compatibilidad y observabilidad

Versión `v0.1`; no hay migración automática. `EngineAssessment` expone
disposition, razones, IDs de evidencia y fingerprint. `AccountContextAdmission`
guarda IDs de recibo/dossier, vigencia, policy y restricciones. Los cambios de
reglas requieren nueva `policy_id` y revisión de gobernanza.
