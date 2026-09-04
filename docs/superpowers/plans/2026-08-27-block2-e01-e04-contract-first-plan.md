# Plan de implementación acotado — Block 2 E01–E04

> Estado: `PLAN CANDIDATE / NO IMPLEMENTATION AUTHORITY`  
> Basado en: diseño E01–E04 v0.1 y contratos candidatos v0.1.

## Objetivo inmediato

Obtener evidencia ejecutable de un único corte: **E02 Direction Set con
preservación de claims y diferencia estructural**, sin renderer, integrations,
memoria creativa, publicación ni aceptación.

## Precondiciones de inicio

1. Master Architecture Review decide cómo se reconcilian el PR #3, `main` y el
   workspace local.
2. Se acepta o revisa el `DesignContextEnvelope` y el `ReferenceRightsManifest`.
3. Existe un objeto upstream actual y autorizado, distinto del intake Sales
   Navigator rechazado anteriormente.
4. Se decide una única audiencia, decisión y canal de prueba.

## Secuencia propuesta

1. **Contrato/oráculo E02.** Especificar `VisualThesisSet`, `DirectionSet` y
   un oráculo declarativo que no invoque el evaluador de producción.
2. **SUT mínimo E02.** Implementar sólo validación de claim binding,
   conservación de certainty/contradictions y diversidad de dos ejes.
3. **Vectores adversariales.** Cubrir duplicación cosmética, certeza inflada,
   claim sin evidencia, contradicción borrada, dirección estereotipada y
   retorno al productor correcto.
4. **CI y revisión independiente.** Vincular test, run y logs a un SHA exacto;
   no interpretar pass como calidad creativa.
5. **Contrato E03.** Sólo después de E02, definir tokens semánticos, fallback,
   excepciones y pruebas de accesibilidad sin renderer.
6. **Contrato E04.** Definir mapa claim→element y blueprint de un canal único;
   probar trazabilidad y faltas de atribución.
7. **Caso externo autorizado.** Crear un fixture de revisión humana únicamente
   tras pasar preflight E01 y revisiones independientes de derechos/entrada.

## Criterios de parada

- Falta de autoridad, facts, evidencia, audiencia, decisión o derechos:
  `RETURN_UPSTREAM`/`QUARANTINE`, no implementación aproximada.
- Cualquier contradicción de contratos compartidos: Master Architecture Review.
- Un pass local/CI sin independencia, integración o caso real: conservar estado
  acotado; no promover E02–E04 ni Block 2.

## Entregables verificables por fase

| Fase | Artefacto | Evidencia mínima |
|---|---|---|
| 0 | contratos v0.1 | revisión de esquema, rechazo y no-claims. |
| 1 | E02 SUT + oráculo | vectores directos, mutación y CI en SHA exacto. |
| 2 | perfil E03 | pruebas de token/fallback/excepción. |
| 3 | blueprint E04 | pruebas claim→element y canal. |
| 4 | integración limitada | caso autorizado, reviewer independiente y límites de reutilización. |

## No-claims

Este plan no autoriza software de producción, generación de imágenes,
integración con Figma/Canva/Adobe, entrenamiento con fuentes externas,
publicación, ni aceptación de ningún motor.

