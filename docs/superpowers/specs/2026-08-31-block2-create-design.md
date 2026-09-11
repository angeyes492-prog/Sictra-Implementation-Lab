# Block 2 Create — Design Context Compiler

## Decisión

Create será un compilador híbrido de un Design Context Envelope, no un prompt
libre ni un generador directo. La pantalla agrupa intención, evidencia upstream
y límites/derechos. Al compilar, un Handoff Seal presenta `CONTINUE` con
fingerprint o todos los motivos `RETURN_UPSTREAM` en una sola respuesta.

Se descartó un wizard porque oculta contradicciones entre pasos y un formulario
único sin estructura porque aumenta la carga de revisión. La autorización humana
vigente permite avanzar sin una pausa adicional; la arquitectura continúa
`CANDIDATE / MAR REQUIRED`.

## Flujo y autoridad

```text
Human inputs → allowlisted POST → CreateDesignRequest
             → compile_design_context
             ├─ RETURN_UPSTREAM → assessment only
             └─ CONTINUE → assessment + immutable envelope + fingerprint
```

Create nunca completa facts, evidencia, autoridad, certainty, procedencia o
rights. Un sobre `CONTINUE` sólo está listo para E01; no ejecuta E01, produce
artefactos, publica ni acepta.

## Interfaz

- Escritorio: formulario principal + readiness rail; móvil: secuencia apilada.
- Secciones reales numeradas: 01 intención, 02 binding upstream, 03 límites.
- Handoff Seal como única firma visual: franja azul para `CONTINUE`, ámbar/rojo
  para retorno, fingerprint monoespaciado y lista de reparaciones.
- Labels persistentes, ayudas breves, controles ≥44 px, foco visible, estado
  `aria-live` y errores accionables.

## Seguridad y pruebas

POST local con token anti-CSRF, JSON exacto, límite 32 KiB, schema allowlisted,
version `0.1.x`, timestamp timezone-aware y colecciones limitadas. Pruebas:
happy path, faltantes agregados, stale/certainty/version, canal, rights,
determinismo, replay/collision, HTTP adversarial, browser móvil y regresión.

## Self-review

Sin placeholders. Create y runtime permanecen separados; `CONTINUE` no equivale
a ejecución ni aceptación. La ausencia de Git HEAD impide el commit requerido y
queda registrada como bloqueo de promoción, no como bloqueo de implementación.
