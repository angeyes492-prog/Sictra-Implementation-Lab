# SICTrA Bloque 2 / Design — Runtime acotado E01–E08 v0.4

> Fecha: `2026-08-30`  
> Estado: `DESIGNED / IMPLEMENTED CANDIDATE / LOCAL-EXECUTED / YELLOW`  
> Sustituye el orden candidato v0.3 para la implementación local. No promueve
> arquitectura común, producción ni aceptación.

## Propósito y alcance

El runtime transforma un objeto upstream gobernado en un candidato visual
reproducible mediante ocho fronteras: preflight, dirección, sistema, diseño de
información, investigación, producción, evaluación y memoria. Admite
newsletter HTML+texto y gráfico SVG+descripción. No publica, concede derechos,
decide selección creativa, inventa hechos, ejecuta estudios humanos ni acepta.

## Motores y propiedad semántica

| Motor | Propiedad | Entrada → salida | Fallo seguro |
|---|---|---|---|
| E01 | preflight y fidelidad upstream | fixture → readiness | `RETURN_UPSTREAM` / `INVALID_TRIAL` |
| E02 | divergencia creativa trazable | tesis → 2–3 direcciones | `RETURN_TO_PREVIOUS` / cuarentena |
| E03 | sistema de diseño semántico | selección externa → profile | canal/rights/estado bloquean |
| E04 | información y encoding | payload+profile → blueprint | claim/attribution/accessibility bloquean |
| E05 | referencias y rights | blueprint+manifests → principios | identidad/rights se ponen en cuarentena |
| E06 | materialización determinista | blueprint+research → HTML/SVG | I/O remoto/publicación se rechaza |
| E07 | red-team independiente | candidato+observaciones → recomendación | self-review/criterio faltante bloquean |
| E08 | memoria versionada | review+validación externa → registro | same-generation/poisoning se aíslan |

## Flujo, autoridad e invariantes

```text
E01 → E02 → [selección externa] → E03 → E04 → E05 → E06 → E07
    → [validación externa] → E08 (sólo generación futura)
```

Wolfram confirmó que el grafo es acíclico, con E01 como única fuente, E08 como
único sink y una sola ruta simple completa. El orquestador detiene el run en el
primer motor no listo. E07 recomienda pero no acepta; E08 almacena candidatos
pero no reentrena ni modifica la misma generación. Los outputs son
`NOT_PUBLISHED / NOT_ACCEPTED`.

## Dependencias y efectos downstream

- Directos: E06 depende de E04 y E05 listos; E08 depende de E07 y validación
  externa actual.
- Segundo orden: nuevos adapters amplían superficie de sanitización,
  accesibilidad y render cross-client.
- Tercer orden: una mala promoción de E08 contaminaría generaciones futuras;
  por ello exige dos raíces de evidencia y elegibilidad posterior.
- Rollback: descartar el candidato E06 y deprecar, sin borrar, el registro E08.

## Observabilidad y validación

Cada stage registra motor, disposición y reasons. E06 registra media types y
hashes SHA-256. E07 conserva criterio, score, severidad, método y evidencia.
E08 conserva lineage, hash, estado y deprecación.

Validación actual: 178 pruebas Block 2, 466 pruebas workspace, compileall y CLI
E01–E08. El workspace reconciliado con `main` está ligado a GitHub por PR #11;
el SHA `0b61e8481f02ba93219be23fea9790e45897ef62` concluyó CI hospedado con
`success` (run `33700724827`). Los runs históricos permanecen como evidencia de
sus SHA, no sustitutos del head actual. Cobertura adversarial: rights, imitación, lineage, copy no aprobado,
markup, publicación/red, criterios faltantes, self-review, thresholds,
same-generation, colisión, idempotencia y detención temprana.

## Contradicciones y estado de promoción

Slack y Notion contienen registros previos que usan E01–E08 también para
Bloque 1. Esa numeración no transfiere semántica al Bloque 2. GitHub PR #3
acredita sólo E01 de Bloque 2; Rovo confirma un handoff reciente de Bloque 1,
no aceptación de este runtime. La ausencia histórica de `HEAD` quedó resuelta
mediante reconciliación no destructiva con `main`; PR #11 es mergeable y su CI
exacto está verde. Estado: `YELLOW / B` para capacidad integrada candidata;
revisión independiente, provider/datos reales, pruebas perceptuales y gate
humano permanecen `INSUFFICIENT EVIDENCE`.
