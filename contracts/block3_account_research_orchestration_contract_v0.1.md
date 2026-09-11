# Contrato candidato — Block 3 Account Research Orchestration v0.1

**Estado:** `CANDIDATE / LOCAL BOUNDED SUT`.

## Propósito

Conectar, en modo shadow, una semilla emitida por el adaptador Excel con el
enriquecimiento de sitio oficial y el Account Knowledge Store. La orquestación
no convierte una importación en permiso de red: requiere una aprobación humana
explícita, limitada en tiempo y ligada por fingerprint al lote, fila, tenant,
cuenta y URL que puede investigar.

## Entrada autorizada

`ResearchApproval` declara `approval_id`, `tenant_id`, `import_id`, hash del
workbook, número de fila, cuenta, fingerprint de semilla, referencia de
aprobación, revisor declarado y ventana temporal. Sólo se admite
`decision=APPROVED`; una aprobación vencida, futura, cruzada de tenant, fila,
lote, URL o fingerprint devuelve rechazo antes de abrir una URL.

La identidad del revisor es una declaración trazable en esta versión: no es
autenticación criptográfica ni autorización de producción.

## Transición permitida

```text
ExcelAccountImportBatch (UNCONFIRMED declaration)
  → ResearchApproval (human review binding)
  → AccountKnowledgeEngine (official-site shadow enrichment)
  → AccountKnowledgeStore (dossier/evidencia durable)
  → ResearchReceiptLedger (recibo durable y verificable)
```

La única salida es `AccountResearchReceipt(status=SHADOW_COMPLETED)`. Conserva
las identidades de aprobación, dossier y política. No puede producir
`ContextSignal`, copy, `DeliveryProposal`, CRM write, correo ni aprendizaje.

## Durabilidad e idempotencia

Los recibos se guardan en un ledger SQLite append-only, particionado por tenant
y cuenta, con cadena HMAC y head autenticado. Repetir el mismo `receipt_id`
con contenido igual es idempotente; contenido distinto es colisión. Alterar o
borrar una fila o head impide consultas posteriores.

## No-claims

No hay autenticación real de revisor, autorización legal del sitio, crawling de
producción, scheduler autónomo, vault de claves, cifrado, borrado físico, CRM,
delivery, consentimiento ni promoción de gate global. Una ejecución local no
es una prueba shadow real hasta que use una plantilla y dominio explícitamente
autorizados.
