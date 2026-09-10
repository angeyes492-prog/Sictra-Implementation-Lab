# Bloque 3 — Ingress de Contexto de Cuenta y Catálogo M02 v0.1

**Estado:** `IMPLEMENTED / EXECUTED / LOCAL INTEGRATION`; aceptación común:
`NO`.

## Jurisdicción

| Componente | Posee | No posee |
|---|---|---|
| `M05_ACCOUNT_INGRESS` | validar lineage durable y admitir hipótesis `ACCOUNT` | hechos, atributos personales, relevancia, red o delivery |
| `M02_DECISION_SIGNAL_CATALOG` | aplicar reglas explícitas a tags admitidos | preferencia personal, intención, consentimiento, contacto o envío |

## Dependencias y transición

```text
Excel seed → aprobación humana declarada → sitio oficial acotado
→ AccountKnowledgeStore + ResearchReceiptLedger
→ M05_ACCOUNT_INGRESS → ContextSignal(ACCOUNT, HYPOTHESIS)
→ M02_DECISION_SIGNAL_CATALOG → DecisionSignal(HYPOTHESIS)
→ M05 + M02 existentes
```

M05 no se completa solamente con esta ruta: los contextos Global, Industry,
Role y Moment permanecen bajo sus autoridades propias. Las reglas no se
autopromueven desde outcomes.

## Invariantes y recuperación

- el recibo exacto y el dossier exacto deben subsistir en dos almacenes íntegros;
- M02 sólo acepta una admisión sellada por el issuer local configurado y una
  policy de admisión declarada; un objeto construido por el llamador no cruza
  esta frontera;
- expiración, cuarentena, sustitución o divergencia detienen la admisión;
- una regla sin coincidencia retorna upstream; no rellena una hipótesis;
- toda salida conserva `HYPOTHESIS`, `EvidenceRef` y límites de reutilización;
- rollback: retirar la policy del consumidor, conservar ledger/snapshots y
  evidencia histórica; no se borra ni reescribe memoria.

## Evidencia local

`tests/test_block3_account_context_ingress.py` cubre admisión válida, recibo o
snapshot ausente, sustitución, vencimiento, cuarentena, regla coincidente y no
coincidente, y el paso integrado hacia M05→M02. Esa evidencia es local y no
demuestra una ejecución con un dominio/plantilla real autorizados.

## Gaps antes de promoción

1. fuente y contrato autorizado para Global/Industry/Role/Moment de Bloque 1;
2. identidad autenticada de revisor y key management/cifrado de producción;
3. catálogo de reglas revisado por dominio, versionado y aprobado;
4. CRM/event adapter con consentimiento, retención y enforcement externo;
5. shadow run autorizado con cuentas/dominios reales, CI del SHA final y
   revisión independiente.
