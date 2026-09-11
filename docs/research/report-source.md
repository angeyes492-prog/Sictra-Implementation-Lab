# Block 1 Intelligence — capacidad recomendada para una Source Fabric de 50 fuentes

**Estado:** PROPOSED — diseño de capacidad respaldado por investigación; no es una integración ni una autorización para recolectar datos.  
**Fecha:** 2026-08-29  
**Audiencia:** propietario de producto y arquitectura de Telecare OS.

## Respuesta ejecutiva

Block 1 debe ser diseñado para **registrar y gobernar 50 fuentes diferenciadas** en su primera versión operativa. No debe intentar consultar las 50 en cada ejecución: el límite seguro y útil es **8 a 12 fuentes activas por investigación**, y **hasta 10 watchlists de alta frecuencia** cuando haya una necesidad, permiso y presupuesto explícitos.

El límite de 50 es un límite operativo inicial, no una limitación técnica permanente. Da cobertura suficiente por región, modo e industria sin convertir Intelligence en un agregador opaco, caro o imposible de validar. La arquitectura debe poder crecer a 100 fuentes registradas sin cambiar contratos; una promoción de 50 a más fuentes requiere evidencia de calidad, observabilidad y costo.

## Por qué 50, y no una cifra mayor o menor

- Menos de 25 deja huecos previsibles: comercio global, puertos, aduanas, aviación, corredores regionales, riesgo climático y señales sectoriales no caben en un conjunto único.
- Cincuenta permite diversidad real y redundancia razonable sin degradar la trazabilidad humana. La evidencia regional consultada muestra que existen fuentes institucionales separadas y especializadas: CEPAL para puertos y logística latinoamericana, Eurostat para transporte europeo, ADB para Asia-Pacífico y BITRE para carga multimodal australiana.
- Más de 50 fuentes conectadas no mejora por sí mismo los insights. Sin control de cadencia, alcance, duplicidad, derechos de uso y contradicciones, sólo multiplica ruido y costo.

## Modelo de capacidad

| Capa | Límite inicial | Función |
| --- | ---: | --- |
| Registro de fuentes | 50 | Catálogo versionado de fuentes autorizables, incluidas las temporalmente desactivadas. |
| Fuentes `BOUND` | 20 | Fuentes cuyo contrato, licencia, datos esperados y estrategia de recuperación ya fueron revisados. |
| Fuentes activas por investigación | 8–12 | Selección contextual de fuentes pertinentes a una pregunta, ruta, país o industria. |
| Evidencias por insight de alto impacto | 2–4 | Una evidencia primaria cuando sea posible y al menos una corroboración independiente. |
| Watchlists de alta frecuencia | 10 | Seguimiento programado, sólo para fuentes con cadencia, derechos y valor operativo demostrados. |
| Ejecuciones simultáneas | 4 conectores | Aislamiento por conector, límites de tasa y control de fallos; no se debe paralelizar sin límite. |

## Distribución objetivo de las 50 fuentes registradas

| Dominio | Cupo | Rol |
| --- | ---: | --- |
| Global multilateral | 10 | Comercio, conectividad, desempeño portuario, logística y prospectiva. |
| América Latina y Norteamérica | 8 | Puertos, comercio, cruces fronterizos, corredores y logística regional. |
| Europa | 8 | Transporte marítimo, carretera, ferrocarril, comercio y regulación. |
| Asia-Pacífico | 8 | Puertos, aviación, corredores, conectividad e infraestructura. |
| África y Medio Oriente | 8 | Corredores, fronteras, puertos, integración comercial y riesgo de rutas. |
| Oceanía | 4 | Carga multimodal, puertos y desempeño interno/exportador. |
| Modo e industria transversal | 4 | Carga aérea, navieras, forwarding, estándares de datos y resiliencia sectorial. |

Los cupos no son una cuota burocrática: son límites de diversidad. Una misma fuente no puede ocupar varios cupos sólo por publicar muchas páginas. Cada entrada necesita un propósito diferente, una cobertura declarada y una razón de no-duplicidad.

## Arquitectura de cada fuente

Cada fuente registrada debe tener estos campos obligatorios:

- `source_id`, editor, URL canónica, región, países, modo, industria y tipo de señal.
- Estado: `PROPOSED`, `BOUND`, `EXECUTED`, `VALIDATED`, `SUSPENDED` o `RETIRED`.
- Método de acceso: manual, descarga, API, RSS, boletín o proveedor bajo contrato.
- Cadencia declarada y latencia aceptable; una fuente anual no puede alimentar una alerta intradía.
- Licencia, atribución, límites de tasa, costo, credenciales y fecha de revisión legal.
- Esquema de extracción, hash de artefacto, timestamp, cobertura, versión/metodología y política de retención.
- Estrategia de validación, fuentes de corroboración y condiciones de suspensión.

## Reglas que preservan la calidad

1. La consulta comienza con una pregunta y un alcance; no con una ejecución masiva del catálogo.
2. Un insight operacional no puede basarse sólo en un informe anual o forecast.
3. Fuentes profesionales privadas pueden complementar el sistema, pero no desplazan una fuente pública o primaria cuando ésta existe.
4. Toda contradicción entre fuentes se conserva; Block 1 no elige silenciosamente la cifra más conveniente.
5. Una tasa de fallo, una licencia revocada, una fecha vencida o una desviación de esquema suspenden la fuente y degradan las conclusiones que dependían de ella.
6. La selección de fuentes por industria (electrónica, automotriz, alimentos, salud, etc.) debe añadirse por necesidad demostrada y derechos explícitos, no por scraping generalizado.

## Fases realistas de incorporación

1. **Fundación — 12 fuentes:** las multilaterales priorizadas en el registro global y cuatro regionales de alta confianza. Carga manual, con paquetes de evidencia y validación de contratos.
2. **Cobertura — 25 fuentes:** al menos tres regiones cubiertas con comparadores por modo; prueba de deduplicación, recuperación y presupuesto.
3. **Red operativa — 50 fuentes:** cobertura de los seis dominios anteriores, métricas de confiabilidad por conector y watchlists limitadas.
4. **Escala posterior:** sólo después de demostrar que los insights mejoran, que los costos son sostenibles y que la revisión humana no se vuelve cuello de botella.

## Evidencia de disponibilidad regional

- [CEPAL Maritime and Logistics Profile](https://perfil.cepal.org/l/en/about.html) mantiene datos y referencias sobre puertos, transporte y logística de América Latina y el Caribe, con series de throughput desde 2000 hasta 2024.
- [Eurostat](https://ec.europa.eu/eurostat/documents/d/transport/reference-manual-maritime-july-2026) publica series marítimas europeas; sus datos trimestrales y anuales tienen rezagos de publicación definidos y no distribuye datos puerto-a-puerto.
- [Asian Transport Observatory](https://www.adb.org/what-we-do/topics/transport/asian-transport-outlook) reúne más de 490 indicadores de transporte de 52 economías de Asia-Pacífico.
- [BITRE Freight Statistics](https://www.bitre.gov.au/statistics/freight) cubre carga marítima, aérea, carretera y ferrocarril de Australia con tableros y publicaciones sectoriales.
- [UNCTAD Data Hub](https://unctadstat.unctad.org/insights/theme/246), [WTO Statistics](https://www.wto.org/english/res_e/statis_e/Statis_e.htm), [UN Comtrade](https://comtradeplus.un.org/TradeFlow?Frequency=A), [IMF IMTS](https://data.imf.org/en/datasets/IMF.STA%3AIMTS), [World Bank LPI](https://lpi.worldbank.org/en/about) y [CPPI](https://www.worldbank.org/en/topic/transport/publication/cppi) forman el núcleo multilateral propuesto.

## Limitaciones y decisiones pendientes

- Esta investigación confirma capacidad de cobertura, no el derecho de automatizar todas las fuentes. Las condiciones se revisan por fuente y endpoint.
- Para señales intradía (AIS, tarifas spot, disponibilidad de navieras, congestión o cierres) se necesitarán contratos o autoridades específicas. No se eligieron proveedores privados en esta fase.
- El registro anterior de fuentes globales sigue siendo el catálogo inicial de candidatos: `docs/research/global-logistics-source-registry-v0.1.md`.
- La decisión de implementar Source Gateway es una ampliación arquitectónica y requiere revisar los contratos, el ledger de gates y los tests aplicables antes de programación.
