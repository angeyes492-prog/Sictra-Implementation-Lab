# Bloque 1 Intelligence — Preflight de cierre operacional v0.1

## Baseline auditado

- **Código:** `5f4075711eb4cafddc9f46f5fd36ba37cf0cc47f`.
- **CI externa:** workflow `32924202885`, job `98043644393`, `success`.
- **Reejecución limpia:** `python -m unittest tests.test_block1_runtime -q`,
  67/67, 0 fallos, 0 errores, 25.449 s, worktree detenido en el SHA auditado.
- **Límite:** perfil `BOUNDED OPERATIONAL` en un host y SQLite local; no es
  producción ni aceptación G01–G12.

## Auditoría contra los criterios v0.3

| Criterio | Evidencia directa | Estado |
|---|---|---|
| 1. Cero CRITICAL/HIGH abiertos en revisión independiente | Revisión estática adversarial propia sin hallazgo CRITICAL/HIGH; PR #1 contiene solo una revisión automatizada. Ninguna es independiente. | `INSUFFICIENT EVIDENCE / B` |
| 2. Autoridad falsa, stale, futura o fuera de scope no escribe | `test_missing_or_uncommitted_authority_never_writes`, `test_forged_signature_untrusted_issuer_and_binding_fail_closed`, `test_validly_signed_future_authority_is_not_current`, `test_authority_expiring_during_pipeline_cannot_commit`. | `VERIFIED / B` para el perfil ejecutado |
| 3. Evidencia inadmisible no escribe | `test_unattested_tampered_stale_future_foreign_and_synthetic_sources_do_not_write`, `test_evidence_substitution_after_e03_invalidates_execution_attestation`. | `VERIFIED / B` para el perfil ejecutado |
| 4. Replay/concurrencia no duplican ni pierden estado | Pruebas de replay, colisión, concurrencia y capacidad: `test_exact_replay_returns_terminal_without_second_effect`, `test_concurrent_exact_replays_have_one_effect`, `test_concurrent_distinct_runs_get_unique_versions`, `test_concurrent_last_capacity_is_a_terminal_no_effect_not_failure`. | `VERIFIED / B` para el perfil ejecutado |
| 5. Restart recupera terminal y memoria | `test_restart_recovers_terminal_and_memory`, `test_failed_transaction_recovers_after_restart_and_clock_advance`, `test_exact_no_effect_replay_is_historical_and_restart_safe`. | `VERIFIED / B` para el perfil ejecutado |
| 6. Fallo entre efecto y terminal revierte ambos | `test_atomic_rollback_and_retry_after_injected_commit_failure`, `test_effect_transaction_requires_authenticated_started_journal`, `test_committed_terminal_requires_matching_durable_effect`. | `VERIFIED / B` para el perfil ejecutado |
| 7. CI externa sobre SHA exacto | Workflow `32924202885` sobre `5f407571…`; pasos de pruebas, manifiesto y ejecución E01–E08 exitosos. | `VERIFIED / A` |
| 8. Cierre no reclama y conserva decisión humana de merge | Ledger v0.3, PR #1 abierto y sin merge. | `VERIFIED / A` |

## Red team complementario

`evidence/block1_promotion_spine_wolfram_2026-08-25.json` valida el modelo
formal de promoción: la ruta de referencia es acíclica y los ataques
`LOCAL → PROMOTED` y `PROMOTED → LOCAL` se detectan. Clasificación:
`FORMAL_MODEL_EVIDENCE / VERIFIED / B`; no sustituye el runtime ni la revisión.

## Resultado del preflight

- **Runtime acotado:** `PROBABLE / B`.
- **CI de baseline:** `VERIFIED / A`.
- **Gate BOUNDED OPERATIONAL:** `RED / B` exclusivamente porque el criterio 1
  permanece sin evidencia independiente vigente.
- **Gates globales G01–G12:** `NOT ASSESSED / INSUFFICIENT EVIDENCE`; Slack
  describe sus requisitos, pero no existe aquí una matriz canónica
  machine-readable que permita marcar su cierre.

## Condición mínima restante

Una revisión independiente, ligada a `5f407571…` o a un descendiente que no
altere el runtime, debe confirmar ausencia de hallazgos CRITICAL/HIGH dentro
del perfil acotado. Después se reevalúa únicamente el criterio 1 y el gate;
la decisión de merge continúa siendo humana.

## No-claims

No prueba producción, KMS/PKI, disponibilidad distribuida, datos logísticos
reales, adaptadores externos, efectos observados fuera del host, ni aceptación
global de la arquitectura.

