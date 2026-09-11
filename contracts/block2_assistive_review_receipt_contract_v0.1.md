# Block 2 — Assistive Review Receipt Contract v0.1

> Estado: `CANDIDATE / LOCAL RECEIPT VALIDATOR / HUMAN REVIEW REQUIRED`.

## Propósito y alcance

Convierte una observación humana NVDA o VoiceOver en un recibo estructurado y
ligado a una consola local exacta. El productor es un revisor humano autorizado;
el consumidor es el registro de evidencia de Bloque 2. El validador local sólo
clasifica la forma, vínculo y límites del recibo: no ejecuta tecnología
asistiva, verifica identidad humana ni concede WCAG, MAR o aceptación.

## Binding e invariantes

`AssistiveReviewTarget` fija `git_sha`, fixture, URL loopback de consola, hash
del probe y tiempo de construcción. Cada recibo debe reproducir esos cuatro
valores, contener tecnología/versiones, SO, navegador, zoom, contraste, paso
del protocolo, observación esperada/real, severidad, evidencia y limitaciones.

- SHA, fixture, URL, probe o tiempo incompatibles → `RETURN_UPSTREAM`.
- Reviewer sin autoridad declarada, `PASS_LOCAL` con severidad no nula o issue
  sin severidad → `INVALID_REVIEW`.
- `RETURN_UPSTREAM` declarado por el reviewer conserva ese estado; no se
  convierte en un pass por la existencia del browser probe.
- Un recibo grabado siempre conserva `NOT_PROMOTED / NOT_ACCEPTED`.

## Recuperación y no-claims

Falta de tecnología, identidad, evidencia o entorno reproducible requiere un
nuevo target o `RETURN_UPSTREAM`. Un hallazgo debe recibir vector regresivo y
revisión humana posterior. Fixtures y tests de este contrato sólo prueban la
frontera local; no prueban lectura NVDA/VoiceOver, una persona real, WCAG AA,
ni aceptación global.
