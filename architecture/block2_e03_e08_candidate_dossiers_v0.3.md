# Bloque 2 / Design — Dossiers E03–E08 v0.3

> Fecha: `2026-08-28`  
> Estado: arquitectura candidata local. Sustituye v0.2 sólo para el estado de
> E03/E04 y el orden de ataque E05–E08. No promueve contratos ni gates.

## Decisión y prioridad

La autorización humana de este ciclo permite diseñar los motores restantes
desde cero y profundizar técnica profesional. No convierte una hipótesis en
arquitectura aceptada. Para reducir retrabajo, la construcción se ordena así:

1. consolidar E03 y E04 como límites ejecutables;
2. diseñar E05 Reference & Visual Research, incluyendo rights/provenance;
3. diseñar E07 Visual Red Team antes del productor;
4. construir E06 Prototype & Production contra contratos ya atacables;
5. construir E08 Creative Memory sólo para evidencia validada y promovible.

Este orden evita que E06 produzca sin un estándar de evaluación y que E08
aprenda de preferencias o errores no validados.

## E03 — Design System Engine

**Propósito.** Convertir una dirección seleccionada externamente en un perfil
versionado de tokens semánticos, componentes, assets, canales y excepciones.

**Técnicas profesionalizadas.** Tokens por rol y no por valor literal;
fallbacks no cromáticos; variantes y estados `DEFAULT/FOCUS/DISABLED` para
componentes interactivos; notas de accesibilidad; licencias por canal con
vigencia; excepciones con owner, ventana temporal y rollback.

**Estado.** `DESIGNED / LOCAL BOUNDED SUT / EXECUTED / LOCAL DIFFERENTIAL`.
No existe selección E02 real, brand manifest completo, render, auditoría WCAG,
CI externa, integración ni aceptación.

## E04 — Information Design Engine

**Propósito.** Crear un blueprint de orden de lectura, mapping de claims,
encodings, atribución, limitaciones y fallbacks sin producir el artefacto.

**Técnicas profesionalizadas.** Elección de chart según relación; cero para
barras; rechazo de 3D, doble eje y color-only; pie ≤ 5 series; preservación de
unidad/polaridad/incertidumbre; CTA ligado a límites; alt/legend, plain text o
transcript según medio; identidades únicas y output no publicable.

**Estado.** `DESIGNED / LOCAL BOUNDED SUT / EXECUTED / LOCAL DIFFERENTIAL`.
No prueba comprensión humana, calidad editorial, responsive real, render,
delivery, integración ni aceptación.

## E05 — Reference & Visual Research Engine

**Rol candidato.** Recuperar y clasificar referencias profesionales por
problema visual, técnica, medio, audiencia, procedencia, licencia y riesgo de
imitación. Emite un `ReferenceResearchPack`; no crea estilos, no descarga assets
sin permiso y no declara derechos.

**Mecanismo profesional.** Descomponer una referencia en principios
transferibles —jerarquía, ritmo, retícula, tipografía por rol, densidad,
contraste, narrativa, accesibilidad— separándolos de identidad protegida. Las
capturas se usan como evidencia de rasgos observables, no como permiso para
copiar fuente, logo o trade dress.

**Gate previo.** Contrato de intake, `ReferenceRightsManifest`, taxonomía de
técnicas, política de similitud, provenance y prueba de cuarentena.

## E07 — Visual Red Team & Evaluation Engine

**Rol candidato.** Evaluar blueprints y prototipos contra una rúbrica
versionada: comprensión, jerarquía, legibilidad, accesibilidad, fidelidad de
claims, adaptación, marca, rights y riesgo de persuasión engañosa. Emite
hallazgos y recomendación; no corrige, selecciona ni acepta.

**Mecanismo profesional.** Revisión por capas, comparación ciega cuando sea
posible, severidad por impacto, pruebas de lectura rápida, estrés de contenido,
daltonismo/zoom/reflow, contraste entre intención y efecto y explicación
falsable de cada hallazgo.

**Gate previo.** Rúbrica, fixture negativo/positivo, independencia de oráculo,
criterios de severidad y regla explícita de que `PASS != ACCEPTED`.

## E06 — Prototype & Production Engine

**Rol candidato.** Materializar un blueprint aprobado para un adapter
contratado: SVG/PNG/PDF, newsletter HTML+texto, slides o multimedia. Produce un
`ProductionCandidate` reproducible; no publica, envía, despliega ni acepta.

**Mecanismo profesional.** Preflight de assets, layout responsive, tipografía y
fallbacks; render determinista cuando aplique; adaptaciones por canal que
revalidan mapping; exportación con manifest de versión, checksums y rollback.

**Gate previo.** Contrato E06, sandbox, adapters allowlisted, golden fixtures,
pruebas visuales y accesibles, límites de red/credenciales y E07 candidato.

## E08 — Creative Memory, Learning & Evolution Engine

**Rol candidato.** Conservar patrones, fallos, excepciones y resultados como
candidatos versionados con lineage. No reentrena automáticamente, no convierte
preferencias en principios, no actualiza E03/E07 ni promueve reglas.

**Mecanismo profesional.** Memoria estratificada por clase de evidencia;
separación entre observación, interpretación e hipótesis; soporte negativo;
deprecación y rollback; caducidad; deduplicación por raíz; promoción humana y
evaluación fuera de muestra antes de reutilización material.

**Gate previo.** Contrato de memoria, clases de evidencia, owner de promoción,
anti-loop E06→E08→E06, política de privacidad/licencia y pruebas de poisoning,
staleness, correlación y rollback.

## Dependencias y frontera de autoridad

```text
E01 context → E02 directions → external selection → E03 system profile
→ E04 information blueprint → E06 production candidate → E07 assessment
→ external acceptance

E05 supplies quarantinable research to E02/E03/E04.
E07 may evaluate E03/E04 before E06 and must evaluate E06 after production.
E08 observes only validated records and never feeds the same generation.
```

La secuencia de construcción coloca E07 antes de E06 aunque la secuencia de
ejecución evalúe también el output de E06. Ningún motor posee publicación,
aceptación arquitectónica, derechos legales ni autoridad upstream.

## Efectos downstream y próxima revisión

- Directo: E05/E07 requieren contratos candidatos antes de código.
- Segundo orden: E06 dependerá de adapters y aumentará la superficie de
  seguridad, accesibilidad y regresión visual.
- Tercer orden: E08 puede contaminar futuros sistemas si se permite aprendizaje
  circular; por eso se construye último.

El siguiente ataque es E05 contract-first y, en paralelo conceptual pero no de
implementación, la rúbrica de E07. Ambos requieren Master Architecture Review
antes de integración compartida.
