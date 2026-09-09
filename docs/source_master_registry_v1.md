# Source Master Registry v1

## Decision boundary

This is a discovery and governance artifact for the Block 1 laboratory. It
does not approve a source, grant a license, permit automated acquisition, or
turn a public page into evidence. Every entry remains `PROPOSED` and must pass
separate terms review, approval, binding and manual-bundle controls before it
can reach E01–E08.

The registry contains 18 candidates out of a bounded capacity of 50. The
remaining capacity is deliberately empty: an unresearched source is safer than
a generic or guessed entry.

## Official-source findings

| Candidate | Official finding retained | Registry treatment |
| --- | --- | --- |
| SAT Guatemala | The SAT page offers monthly ZIP/tab-delimited import/export files with customs office, tariff fraction, origin, CIF/FOB and weight fields. [SAT](https://portal.sat.gob.gt/portal/operador-economico-autorizado/informacion-comercio-internacional/) | `E1_CANDIDATE`; `PUBLIC_TERMS_UNCLEAR`; manual review only. |
| SIECA | Its SEC covers Central American foreign trade, and its commercial-intelligence tool describes monthly regional/tránsito updates. [SIECA statistics](https://www.sieca.int/estadisticas-integracion-economica-centroamericana/) · [tool announcement](https://www.sieca.int/noticias/conectando-centroamerica-sieca-presenta-nueva-herramienta-inteligencia-comercial-estadisticas-detalladas-comercio-intrarregional/) | `E2_CANDIDATE`; monthly review planning; no terms conclusion. |
| INE Honduras | The published foreign-trade annual includes downloadable XLS tables for imports, exports, countries and products. [INE Honduras](https://ine.gob.hn/2025/10/14/anuario-estadistico-de-comercio-exterior-2020-2024/) | `E1_CANDIDATE`; annual cadence; terms still unclear. |
| COCATRAM | An official SIEMPCA manual carries a reserved-rights notice. [COCATRAM manual](https://www.cocatram.org.ni/estadisticas/static/manual.pdf) | `E2_CANDIDATE`; `RESTRICTED`; discovery/review only. |
| GACC China | The official monthly page says later data can differ after verification and the latest release is more accurate. [GACC monthly bulletin](https://english.customs.gov.cn/statics/report/monthly.html) | `E1_CANDIDATE`; `PUBLISHED_REVISIONS`; retain versions rather than overwrite. |
| DataComex Spain | The official site describes monthly data by country, product, transport and period; its API help requires a registered security token. [DataComex metadata](https://datacomex.comercio.es/Metadata/Comex) · [API help](https://datacomex.comercio.es/Data/AyudaApi) | `E1_CANDIDATE`; `REGISTERED_ACCESS`; credentials are never placed in Block 1. |
| Puertos del Estado | The official monthly summary is published as XLSX/PDF and describes monthly validation/aggregation of goods, containers, ships and passengers. [Puertos del Estado](https://www.puertos.es/datos/estadisticas/mensuales) | `E1_CANDIDATE`; monthly cadence; reuse terms need review. |
| U.S. Census Port HS | The official API exposes monthly port/HS imports, value, weight and transport totals. Its current examples state that API queries require a key. [Census endpoint](https://api.census.gov/data/timeseries/intltrade/imports/porths.html) · [examples](https://api.census.gov/data/timeseries/intltrade/exports/porths/examples.html) | `E1_CANDIDATE`; `REGISTERED_ACCESS`; only an operator-supplied, approved output could enter later. |

The registry also preserves current candidates for Eurostat, CEPAL, ADB, BITRE,
UN Comtrade, WTO statistics, WTO ePing, WCO, World Bank and IATA. Those with
`DISCOVERY_PENDING` have no legal, availability or data-quality conclusion in
this version.

## Recommended roles and cadence

| Research layer | Initial candidates | Expected review behavior |
| --- | --- | --- |
| National customs/trade | SAT Guatemala, INE Honduras, GACC, DataComex, U.S. Census Port HS | Compare a new operator-provided release against the retained parent version. Provisional/revised publishers retain both versions. |
| Central American context | SIECA, COCATRAM, CEPAL | Use as corroboration or context unless a separate approval defines a narrower E1 claim. |
| Port operations | Puertos del Estado, COCATRAM, Eurostat, BITRE | Keep port movement distinct from trade value; agreement is corroboration, not causal proof. |
| Regulatory scouting | WTO ePing, WCO | Open a research/watchlist item only. A notification does not prove enterprise, route or port impact. |
| Structural benchmarks | World Bank, ADB, CEPAL | Event-driven or annual context; never classify as stale simply because it lacks a monthly release. |

## Watchlist policy

`review_window` is not a universal expiry. It must be determined from
`expected_source_cadence` and any publisher revision behavior:

- daily/event sources: review when a defined event or notice occurs;
- monthly sources: compare the next expected published version;
- quarterly/annual sources: retain as context and revisit on the publisher's
  schedule;
- GACC-style revised sources: retain the preliminary and revised artifacts,
  then calculate the change explicitly.

## Required approval packet before ingestion

For any candidate, the human approval packet must contain the legal publisher,
canonical location, selected host(s), exact dataset/scope/grain, terms evidence
reference, intended claims, access method, maximum bytes, known revision policy
and expiry. The approved packet then binds to the existing Source Gateway
contract. A dashboard, newsletter, API key or downstream platform is never an
approver.

## Deliberate exclusions

- UNCTAD remains excluded by owner decision, even though it was proposed in
  earlier research.
- Flexport remains excluded by owner decision.
- No commercial benchmark, social signal, Google Trends-style signal, or
  presentation platform is evidence by itself.
- No source is acquired from the network by the product.

## Sources

1. Superintendencia de Administración Tributaria de Guatemala, [Información Comercio Internacional](https://portal.sat.gob.gt/portal/operador-economico-autorizado/informacion-comercio-internacional/), accessed 2026-09-08.
2. SIECA, [Estadísticas y publicaciones](https://www.sieca.int/estadisticas-integracion-economica-centroamericana/) and [Herramienta de Inteligencia Comercial](https://www.sieca.int/noticias/conectando-centroamerica-sieca-presenta-nueva-herramienta-inteligencia-comercial-estadisticas-detalladas-comercio-intrarregional/), accessed 2026-09-08.
3. Instituto Nacional de Estadística de Honduras, [Anuario Estadístico de Comercio Exterior 2020–2024](https://ine.gob.hn/2025/10/14/anuario-estadistico-de-comercio-exterior-2020-2024/), accessed 2026-09-08.
4. COCATRAM, [Manual SIEMPCA](https://www.cocatram.org.ni/estadisticas/static/manual.pdf), accessed 2026-09-08.
5. General Administration of Customs of China, [Monthly Bulletin](https://english.customs.gov.cn/statics/report/monthly.html), accessed 2026-09-08.
6. Secretaría de Estado de Comercio de España, [DataComex metadata](https://datacomex.comercio.es/Metadata/Comex) and [API help](https://datacomex.comercio.es/Data/AyudaApi), accessed 2026-09-08.
7. Puertos del Estado, [Monthly statistics](https://www.puertos.es/datos/estadisticas/mensuales), accessed 2026-09-08.
8. U.S. Census Bureau, [International Trade Port HS API](https://api.census.gov/data/timeseries/intltrade/imports/porths.html), accessed 2026-09-08.
