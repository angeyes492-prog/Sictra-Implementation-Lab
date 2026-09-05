# Investigación de licencias reutilizables para SICTrA Block 1

**Audiencia:** gobernanza de fuentes de Telecare OS
**Fecha:** 2026-09-04
**Decisión:** reemplazar UNCTAD como candidato inicial y priorizar activos con
permiso explícito de reutilización comercial verificable.

## Respuesta ejecutiva

La primera fuente que conviene convertir en expediente de admisión es
**Eurostat**, limitada a datos, metadatos y publicaciones de transporte que no
caigan en sus excepciones. Es la opción con el permiso institucional más claro
para reutilización comercial, publicación y visualización con atribución. Para
cobertura complementaria, el pipeline debe considerar World Bank, OECD, BTS y
el Department for Transport del Reino Unido, pero siempre validar la licencia
del activo exacto antes de cada bundle.

## Candidatos priorizados

| Prioridad | Plataforma | Alcance útil | Reutilización comprobada | Control obligatorio |
| --- | --- | --- | --- | --- |
| 1 | [Eurostat](https://ec.europa.eu/eurostat/help/copyright-notice) | Transporte, comercio e infraestructura europeos | Autoriza reutilización comercial/no comercial de datos, metadatos, publicaciones y herramientas con atribución. | Excluir terceros, logos, excepciones por país/dataset; declarar cambios. |
| 2 | [World Bank Data Catalog](https://datacatalog.worldbank.org/public-licenses) / [OKR](https://www.worldbank.org/ext/en/legal/terms-conditions/open-knowledge-repository) | Infraestructura, puertos, desarrollo y logística | Datos propios open-data usan CC BY 4.0 por defecto; trabajos de OKR deben respetar su licencia individual. | Guardar licencia del dataset/obra; no asumir que Documents & Reports general es reutilizable. |
| 3 | [OECD](https://www.oecd.org/en/about/oecd-open-by-default-policy.html) | Economía, comercio, cadenas de suministro y análisis de transporte | Política “open by default”: CC BY 4.0 por defecto para contenido, con excepciones indicadas en cada obra. | Comprobar front/copyright de cada informe, material de terceros, logo y obligación de adaptación/traducción. |
| 4 | [BTS / ROSA P](https://rosap.ntl.bts.gov/cbrowse?parentId=dot%3A35533) | Puertos, carga y transporte de EE. UU. | Informes BTS concretos, incluidos los de desempeño portuario, declaran dominio público y exigen cita. | Capturar la declaración del documento exacto; no generalizar a material de terceros. |
| 5 | [UK Department for Transport](https://www.gov.uk/government/organisations/department-for-transport/about/statistics) | Carretera, mercancías, vehículos y movilidad de Reino Unido | Publicaciones/datasets marcados con Open Government Licence v3.0 permiten reutilización comercial con atribución. | Verificar la marca OGL del activo y excluir información de terceros o datos personales. |

## Exclusiones y límites

- **UNCTAD:** `RETIRED`. El texto general del sitio restringe materiales, aunque
  Data Hub declara CC BY para datos/metadatos; no se resolverá esa tensión por
  inferencia.
- **IDB:** no es candidato libre por defecto: una publicación oficial revisada
  declara CC BY-NC-ND 3.0 IGO, incompatible con adaptación/comercialización.
- **WTO:** útil como señal de investigación, pero no entra hasta verificar los
  términos del dataset/obra exactos.
- Ninguna plataforma autoriza copiar logo, fotografías u otro material de
  terceros solo porque el texto/dato principal sea reutilizable.

## Regla de admisión propuesta

Un activo puede entrar a Source Gateway únicamente si el expediente conserva:

1. URL canónica y host exacto.
2. Licencia o declaración de dominio público del **activo**, no solo del portal.
3. Alcance permitido: dato, texto, gráfico o adaptación.
4. Atribución, fecha de acceso, cambios y disclaimer requeridos.
5. Exclusiones de terceros, marcas, personas/datos sensibles y territorios
   restringidos.
6. Revisión humana y binding manual antes de cualquier bundle.

## Fuentes consultadas

- [Eurostat — Copyright notice and free re-use of data](https://ec.europa.eu/eurostat/help/copyright-notice), consultada 2026-09-04.
- [World Bank — Data access and licensing](https://datacatalog.worldbank.org/public-licenses), consultada 2026-09-04.
- [World Bank — Open Knowledge Repository terms](https://www.worldbank.org/ext/en/legal/terms-conditions/open-knowledge-repository), consultada 2026-09-04.
- [OECD — Open Access Policy](https://www.oecd.org/en/about/oecd-open-by-default-policy.html), consultada 2026-09-04.
- [BTS — Port Performance Freight Statistics 2026](https://rosap.ntl.bts.gov/cbrowse?parentId=dot%3A35533), consultada 2026-09-04.
- [UK DfT — Open Government Licence guidance](https://www.gov.uk/guidance/local-authority-transport-how-to-publish-your-data), consultada 2026-09-04.
- [IDB example with CC BY-NC-ND](https://publications.iadb.org/publications/english/document/Extractive_Sector_and_Civil_Society_When_the_Work_of_Communities_Governments_and_Industries_Leads_to_Development._The_Case_of_Peru_en_en.pdf), consultada 2026-09-04.

## Limitaciones

Este informe no es asesoría legal. Licencias, términos y material de terceros
pueden cambiar o variar por activo; el permiso del portal no sustituye la
validación del asset concreto ni la aprobación de gobernanza.
