# Block 2 E01–E04 — Ciclo de contratos candidatos

> Fecha: `2026-08-27`  
> Estado: `DESIGNED / CANDIDATE`; implementación e integración: `NOT CLAIMED`.

## Closure delta

Se crearon dos contratos candidatos que separan el contexto inmutable de
Design de la autorización sobre referencias: 

- `contracts/block2_design_context_envelope_contract_v0.1.md`;
- `contracts/block2_reference_rights_manifest_contract_v0.1.md`.

También se creó un plan que reduce el siguiente corte ejecutable a E02:
`docs/superpowers/plans/2026-08-27-block2-e01-e04-contract-first-plan.md`.
No se creó runtime, renderer, conexión externa, publicación ni gate.

Como delta adicional se creó
`contracts/block2_e02_creative_direction_contract_v0.1.md`. Define la matriz
de diferencia estructural y un oráculo independiente futuro. El modelo formal
verificó que cero o un eje material, y cualquier cambio prohibido, son
inadmisibles; dos ejes materiales sin cambio prohibido son admisibles. Sigue
siendo una regla de contrato, no evidencia de creatividad real.

Se completaron además los contratos candidatos
`contracts/block2_e03_design_system_contract_v0.1.md` y
`contracts/block2_e04_information_design_contract_v0.1.md`. Un segundo modelo
formal comprobó: selección sin autoridad bloquea E03; un blueprint sin mapa
claim→element bloquea E04; y falta de autoridad de publicación bloquea salida
publicada. Las cuatro especificaciones siguen `NOT IMPLEMENTED / NOT ACCEPTED`.

## Reconciliación de fuentes

| Fuente | Hecho usado | Certeza / confianza | Límite |
|---|---|---|---|
| Reglas protegidas y AGENTS locales | contrato primero, fail-closed, procedencia y autoridad separadas. | `VERIFIED / A` | gobierna el diseño; no valida ejecución. |
| GitHub PR #3 | E01 posee mecanismos acotados y CI en rama abierta. | `VERIFIED / A` para el PR | no fusionado ni aceptación global. |
| Rovo SI-1 | Design crea activos desde handoffs tipados sin autoridad de Intelligence. | `VERIFIED / A` | alcance operativo, no contrato canónico. |
| Notion/Slack | límites de E01 y falta de registros de E02–E04. | `VERIFIED / A` para fuentes; E02–E04 `INSUFFICIENT EVIDENCE` | no promueven arquitectura. |
| Wolfram | modelo booleano de gates. | `VERIFIED / A` para el modelo | no es runtime ni evidencia de derechos. |

## Validación formal acotada

El modelo evaluó:

```text
eligibleE01 = upstreamCurrent ∧ facts ∧ evidence ∧ certaintyGoverned
             ∧ audience ∧ decision ∧ authority ∧ provenance
eligibleE03E04 = eligibleE01 ∧ rightsManifestValid ∧ channelSupported
acceptedArtifact = eligibleE03E04 ∧ candidateBlueprint
                   ∧ independentReview ∧ acceptanceGate
```

Resultados observados:

- `authority = false` ⇒ `eligibleE01 = false`;
- `rightsManifestValid = false` ⇒ `eligibleE03E04 = false`;
- `acceptanceGate = false` ⇒ `acceptedArtifact = false`;
- requisitos completos ⇒ candidate eligibility `true`.

Esto reduce el riesgo de modelar derechos y aceptación como rutas opcionales.
No demuestra enforcement en código ni el estado real de una licencia.

## Riesgos y límites

1. La reconciliación entre workspace local, `main` remoto y PR #3 sigue abierta.
2. El `ReferenceRightsManifest` requiere owner, política y, cuando aplique,
   asesoría jurídica externa.
3. E02–E04 no tienen implementación ni evidencia propia.
4. Un contrato conforme no prueba calidad visual, accesibilidad real ni
   comprensión humana.

## Siguiente ataque

Tras Master Architecture Review y un objeto upstream autorizado, construir un
SUT mínimo de E02 con oráculo independiente para verificar solamente:
preservación de claims/certeza/contradicciones y diferencia estructural entre
direcciones. Si falta el objeto o la autoridad, emitir `RETURN_UPSTREAM`.
