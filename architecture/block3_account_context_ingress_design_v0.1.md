# Arquitectura — Ingress de Cuenta a Precision v0.1

**Clasificación:** cambio incremental de integración local. **Estado:**
`DESIGNED / IMPLEMENTED / LOCAL EXECUTED`; no es aceptación de arquitectura
común ni runtime de producción.

## Motivo y alcance

El modelo de Block 3 requiere Account Intelligence para M05, pero la ruta
anterior terminaba en un recibo shadow. Esta extensión hace explícita la única
ruta local permitida de dossier oficial durable a contexto de cuenta y después
a señal M02 gobernada. No modifica la jurisdicción de M01–M08 ni introduce un
adaptador con Bloque 1, Bloque 2, CRM o ejecutor.

## Frontera de autoridad

El ingress comprueba integridad y lineage, y sella la admisión exacta con un
HMAC local del issuer configurado. Eso evita que un llamador convierta un
objeto público en admisión para M02, pero no autentica al revisor ni autoriza
la investigación original. El catálogo acepta sólo issuer y policy
configurados, transforma tags mediante una policy declarada y no interpreta
estado psicológico o intención. M05 y M02 conservan sus contratos existentes y
siguen rechazando evidencia faltante o contradictoria.

## Efectos y riesgos

- Directo: se cierran el binding local Account Knowledge→M05 y la producción
  local de `DecisionSignal` por catálogo explícito.
- Segundo orden: cambios de reglas afectan hipótesis M02; por eso una policy
  tiene identidad/autoridad y no hay aprendizaje automático de reglas.
- Tercer orden: usarlo como autorización de contacto sería un atajo de
  gobernanza; las restricciones lo declaran imposible en este límite.

## Contradicción registrada

El modelo canónico v1 menciona Account Intelligence, mientras que el dossier
M01–M05 previo listaba como gaps el binding y catálogo. No son afirmaciones
incompatibles: el primero es diseño aceptado y el segundo describe una falta de
runtime. Esta implementación reduce esos dos gaps sólo a `LOCAL`, sin elevar
los estados `Integrated` global ni `Accepted`.
