# Bloque 3 M06–M08 — Red-team local 2026-08-27

## Ataques ejecutados

- Gate completo sin interés observado: no confunde ausencia con desinterés.
- 16 combinaciones de scopes comparadas con oráculo independiente.
- 64 combinaciones de hard constraints comparadas con oráculo independiente.
- beneficio igual/inferior al sacrificio y baseline regression: L0.
- policy más estricta: ceiling no aumenta.
- functional mailbox: ruta reenviable y CTA de baja fricción.
- asset extranjero, ausente o stale: sin estrategia.
- channel history stale, channel no autorizado y frecuencia agotada: return/wait.
- medium relevance: presión máxima 1.
- unsubscribe: `DO_NOT_SEND`, sin confundir permiso contextual con consent.
- receipt ausente/rechazado y outcome ausente: no learning.
- execution contra proposal `WAIT`: rechazo contractual.
- outcome previo/mismatched y evidencia self-authored M08: rechazo.
- no-response: no se interpreta como rechazo.
- raíces correlacionadas: visibles, sin presentarse como independencia.

## Reparaciones

Las cinco debilidades materiales encontradas están descritas en el dossier y
poseen vectores de regresión. No se debilitó ningún test existente.

## Resultado

`40/40` nuevos vectores y `173/173` regresión total PASS. Esto valida el bounded
SUT local; no prueba comportamiento productivo, outcome ni aceptación global.

