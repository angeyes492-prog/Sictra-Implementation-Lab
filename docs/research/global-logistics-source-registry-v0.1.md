# Registro inicial de fuentes globales de logística — v0.1

**Estado:** PROPOSED — investigación de fuentes; no es integración ni autorización de ingestión.  
**Fecha de investigación:** 2026-08-29  
**Propósito:** establecer el conjunto inicial de fuentes de alta confianza que Block 1 puede evaluar para investigación logística global.

## Decisión de diseño

Ninguna fuente única demuestra por sí sola una condición logística global. Intelligence debe triangular: una señal de comercio o conectividad, una medida de desempeño o capacidad y, cuando exista, una fuente contextual del modo de transporte. Los informes son evidencia contextual; no sustituyen evidencia de una operación, una empresa o una ruta concreta.

Una fuente sólo puede pasar de `PROPOSED` a `BOUND` después de revisar su licencia, método de acceso, frecuencia real, campos, límites de tasa, atribución, retención y mecanismo de revocación. El paso a `EXECUTED` requiere una fuente autorizada, un adaptador versionado y evidencia de ejecución. Ninguna de estas fuentes queda conectada por este registro.

## Criterios de admisión

- Editor primario público, intergubernamental, regulador o asociación sectorial con método publicado.
- Cobertura internacional o comparabilidad multilateral explícita.
- Fecha de publicación, alcance y metodología identificables.
- Datos o informe rastreables a una URL canónica.
- Restricciones de uso conocidas antes de cualquier automatización.

## Portafolio recomendado

| Prioridad | Fuente canónica | Uso para Intelligence | Recurrencia observada | Límites que deben conservarse |
| --- | --- | --- | --- | --- |
| 1 | [UN Trade and Development — UNCTAD Data Hub](https://unctadstat.unctad.org/insights/theme/246) y [Review of Maritime Transport](https://unctad.org/RMT) | Conectividad marítima país/puerto, capacidad, llamadas y contexto de puertos y transporte marítimo. | LSCI mensual; otros índices trimestrales; Review anual. | Es conectividad, no ETA, inventario ni congestión en tiempo real. Parte de la metodología usa proveedor externo; conservar versión y metadatos. |
| 1 | [WTO Statistics](https://www.wto.org/english/res_e/statis_e/Statis_e.htm) y [Global Trade Outlook](https://data.wto.org/en/dataset/wto_gtos) | Comercio mundial por región/sector, series mensuales/trimestrales/anuales y pronóstico macro de comercio. | Series con frecuencia mensual, trimestral y anual; Outlook semestral. | Las estadísticas tienen revisiones y no prueban movimientos físicos ni desempeño de un proveedor. API/cuenta y términos se revisan antes de uso automatizado. |
| 1 | [UN Comtrade](https://comtradeplus.un.org/TradeFlow?Frequency=A) | Flujos importación/exportación por país, socio y clasificación HS/SITC/BEC. | Mensual o anual según país reportante. | No hay calendario fijo de publicación por país; tratar la fecha de actualización y los metadatos nacionales como obligatorios. Requiere cuenta/API para volúmenes elevados. |
| 1 | [IMF International Trade in Goods by Partner Country (IMTS)](https://data.imf.org/en/datasets/IMF.STA%3AIMTS) | Contraste de comercio bilateral y agregados regionales. | Actualizaciones y calendario propios del FMI. | Es estadística de comercio, no manifiestos ni visibilidad de embarques. Mantener referencia de versión y revisiones. |
| 1 | [World Bank Logistics Performance Indicators 2.0](https://lpi.worldbank.org/en/about) | Comparación estructural de velocidad y conectividad de cadenas internacionales por país y modo. | Datos disponibles para 2023 y 2024; no equivale a un feed continuo. | No usar para rankings simplistas: el LPI 2.0 tiene 21 indicadores y no un ranking único. El LPI histórico basado en encuestas no se actualiza tras 2023. |
| 1 | [World Bank Container Port Performance Index](https://www.worldbank.org/en/topic/transport/publication/cppi) | Benchmark global anual de eficiencia portuaria basada en tiempo de buque en puerto. | Anual. | El CPPI es producido con S&P Global Market Intelligence; confirmar las condiciones del conjunto y no inferir causalidad de cambios de puntaje. |
| 2 | [IATA Air Cargo Market Analysis](https://www.iata.org/en/publications/economics/economics-library/?EconomicsL2=147) | Demanda, capacidad, factores de carga y rendimiento del transporte aéreo de carga. | Mensual. | Es una asociación sectorial, no un organismo estadístico público; sirve para corroboración por modo, no como única evidencia. Revisar derechos de redistribución del informe. |
| 2 | [World Customs Organization — Time Release Study](https://www.wcoomd.org/en/topics/facilitation/instrument-and-tools/tools/time-release-study.aspx) | Marco para evaluar tiempos de liberación y desempeño fronterizo; referencia para fuentes aduaneras nacionales. | Guía metodológica; no feed global central. | No es una base global de resultados operativos. Los estudios publicados por cada administración se incorporan por separado y con su método. |
| 2 | [International Transport Forum / OECD — Transport Outlook](https://www.itf-oecd.org/publication-type/transport-outlook) | Escenarios, tendencias de demanda, resiliencia y política de transporte global. | Ediciones periódicas, no señal operativa. | Es prospectiva y modelado; etiquetar como forecast, nunca como hecho actual de una ruta o empresa. |

## Orden de incorporación recomendado

1. **Manual y trazable:** UNCTAD, WTO, UN Comtrade, IMF y World Bank. Crear source bundles con URL canónica, fecha, metadatos, extracto y hash.
2. **Comparación por modo:** IATA para aviación; informes de WCO o autoridades aduaneras para frontera. Toda afirmación debe llevar su alcance modal.
3. **Automatización limitada:** sólo tras aprobar el Source Gateway, los contratos de importación y las condiciones de uso de cada endpoint.

## Política de confianza y uso

- Estas fuentes reciben confianza inicial **A** como editor y método publicados, pero cada dato individual conserva su propia fecha, alcance, actualización y limitaciones.
- La confianza no se transfiere a una inferencia. Ejemplo: un aumento del LSCI no demuestra que una empresa concreta tenga capacidad disponible.
- Se exige al menos una corroboración independiente para insights de impacto alto, salvo que se presente explícitamente como un dato descriptivo de su fuente.
- No almacenar ni redistribuir texto, gráficos o datasets de terceros fuera de los derechos concedidos. Para World Bank, la licencia se valida por dataset: gran parte de sus datos abiertos usan CC BY 4.0, pero hay excepciones y condiciones de proveedores externos.

## Brechas deliberadamente abiertas

- Señales de operación intradía: congestión, AIS, tarifas spot, schedules y cierres de puertos requieren proveedores autorizados o autoridades específicas; no se han seleccionado aquí.
- Datos de empresa, importador/exportador o decisor de compras requieren fuentes separadas, base legal, derechos de uso y controles de privacidad.
- Clima y disrupciones deben venir de autoridades meteorológicas y marítimas autorizadas, con un contrato independiente de latencia y cobertura.

## Evidencia consultada

- [UNCTAD Data Hub — conectividad marítima](https://unctadstat.unctad.org/insights/theme/246), consultado 2026-08-29.
- [UNCTAD Review of Maritime Transport](https://unctad.org/RMT), consultado 2026-08-29.
- [WTO Global Trade Statistics](https://www.wto.org/english/res_e/statis_e/Statis_e.htm), consultado 2026-08-29.
- [WTO Global Trade Outlook dataset](https://data.wto.org/en/dataset/wto_gtos), consultado 2026-08-29.
- [UN Comtrade Trade Data](https://comtradeplus.un.org/TradeFlow?Frequency=A), consultado 2026-08-29.
- [IMF IMTS dataset](https://data.imf.org/en/datasets/IMF.STA%3AIMTS), consultado 2026-08-29.
- [World Bank LPI methodology](https://lpi.worldbank.org/en/about/methodology) y [LPI publications](https://lpi.worldbank.org/en/resources/lpi-publications), consultados 2026-08-29.
- [World Bank CPPI](https://www.worldbank.org/en/topic/transport/publication/cppi), consultado 2026-08-29.
- [IATA Air Cargo Market Analysis](https://www.iata.org/en/publications/economics/reports/air-cargo-market-analysis-may-2026/), consultado 2026-08-29.
- [WCO Time Release Study Guide](https://www.wcoomd.org/en/topics/facilitation/instrument-and-tools/tools/time-release-study.aspx), consultado 2026-08-29.
- [ITF Transport Outlook](https://www.itf-oecd.org/publication-type/transport-outlook), consultado 2026-08-29.
- [World Bank data access and licensing](https://datacatalog.worldbank.org/public-licenses), consultado 2026-08-29.
