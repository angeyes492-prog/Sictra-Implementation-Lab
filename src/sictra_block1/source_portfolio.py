"""Bounded source registry for discovery; never a network connector or allowlist."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

from .common import ContractViolation


REGIONS = frozenset(("AMERICAS", "EUROPE", "ASIA_PACIFIC", "OCEANIA"))
DOMAINS = frozenset((
    "TRADE", "MARITIME", "AIR", "PORTS", "CUSTOMS", "INFRASTRUCTURE", "MACRO", "REGULATION",
))
SOURCE_CLASSES = frozenset(("PUBLIC_INSTITUTIONAL", "CORPORATE_FIRST_PARTY"))
SOURCE_ROLES = frozenset(("E1_CANDIDATE", "E2_CANDIDATE", "SIGNAL_ONLY", "PRESENTATION_ONLY"))
LICENSE_STATES = frozenset(("UNREVIEWED", "PUBLIC_TERMS_UNCLEAR", "REGISTERED_ACCESS", "RESTRICTED"))
ACCESS_POSTURES = frozenset(("MANUAL_REVIEW_REQUIRED", "REGISTERED_MANUAL_REVIEW_REQUIRED"))
REVISION_POLICIES = frozenset(("UNKNOWN", "POSSIBLE_REVISIONS", "PUBLISHED_REVISIONS"))
RESEARCH_STATES = frozenset(("OFFICIAL_PAGE_VERIFIED", "DISCOVERY_PENDING"))


def _https_reference(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractViolation("source reference must be non-empty HTTPS text")
    parsed = urlsplit(value.strip())
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.port is not None:
        raise ContractViolation("source reference must be an HTTPS URL without credentials or port")
    return value.strip()


@dataclass(frozen=True, slots=True)
class SourceCandidate:
    """Discovery metadata with no authorization effect whatsoever."""

    source_id: str
    publisher: str
    hosts: tuple[str, ...]
    regions: frozenset[str]
    domains: frozenset[str]
    cadence: str
    source_role: str = "E2_CANDIDATE"
    license_status: str = "UNREVIEWED"
    access_posture: str = "MANUAL_REVIEW_REQUIRED"
    revision_policy: str = "UNKNOWN"
    research_state: str = "DISCOVERY_PENDING"
    reference_url: str = "https://example.invalid/"
    source_class: str = "PUBLIC_INSTITUTIONAL"
    status: str = "PROPOSED"

    def __post_init__(self) -> None:
        if (
            not self.source_id or not self.publisher or not self.hosts
            or self.source_class not in SOURCE_CLASSES or self.status != "PROPOSED"
            or self.source_role not in SOURCE_ROLES or self.license_status not in LICENSE_STATES
            or self.access_posture not in ACCESS_POSTURES or self.revision_policy not in REVISION_POLICIES
            or self.research_state not in RESEARCH_STATES
        ):
            raise ContractViolation("source candidate is invalid")
        if not self.regions <= REGIONS or not self.domains <= DOMAINS or not self.regions or not self.domains:
            raise ContractViolation("source candidate coverage is invalid")
        reference = _https_reference(self.reference_url)
        if reference == "https://example.invalid/" or urlsplit(reference).hostname not in self.hosts:
            raise ContractViolation("source reference must use a declared candidate host")

    def snapshot(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "publisher": self.publisher,
            "candidate_hosts": list(self.hosts),
            "regions": sorted(self.regions),
            "domains": sorted(self.domains),
            "cadence": self.cadence,
            "source_role": self.source_role,
            "license_status": self.license_status,
            "access_posture": self.access_posture,
            "revision_policy": self.revision_policy,
            "research_state": self.research_state,
            "official_reference": self.reference_url,
            "source_class": self.source_class,
            "status": self.status,
            "allowed_actions": ["DISCOVER", "REVIEW"],
        }


def _candidate(
    source_id: str, publisher: str, hosts: tuple[str, ...], regions: frozenset[str], domains: frozenset[str],
    cadence: str, source_role: str, license_status: str, access_posture: str, revision_policy: str,
    research_state: str, reference_url: str, source_class: str = "PUBLIC_INSTITUTIONAL",
) -> SourceCandidate:
    return SourceCandidate(
        source_id, publisher, hosts, regions, domains, cadence, source_role, license_status,
        access_posture, revision_policy, research_state, reference_url, source_class,
    )


_SOURCES = (
    _candidate("sat-guatemala", "Superintendencia de Administración Tributaria de Guatemala", ("portal.sat.gob.gt",), frozenset(("AMERICAS",)), frozenset(("TRADE", "CUSTOMS")), "MONTHLY", "E1_CANDIDATE", "PUBLIC_TERMS_UNCLEAR", "MANUAL_REVIEW_REQUIRED", "UNKNOWN", "OFFICIAL_PAGE_VERIFIED", "https://portal.sat.gob.gt/portal/operador-economico-autorizado/informacion-comercio-internacional/"),
    _candidate("sieca", "SIECA — Secretaría de Integración Económica Centroamericana", ("www.sieca.int", "sieca.int", "oie.sieca.int"), frozenset(("AMERICAS",)), frozenset(("TRADE", "CUSTOMS", "INFRASTRUCTURE")), "MONTHLY", "E2_CANDIDATE", "PUBLIC_TERMS_UNCLEAR", "MANUAL_REVIEW_REQUIRED", "POSSIBLE_REVISIONS", "OFFICIAL_PAGE_VERIFIED", "https://www.sieca.int/estadisticas-integracion-economica-centroamericana/"),
    _candidate("ine-honduras", "Instituto Nacional de Estadística de Honduras", ("ine.gob.hn",), frozenset(("AMERICAS",)), frozenset(("TRADE", "MACRO")), "ANNUAL", "E1_CANDIDATE", "PUBLIC_TERMS_UNCLEAR", "MANUAL_REVIEW_REQUIRED", "UNKNOWN", "OFFICIAL_PAGE_VERIFIED", "https://ine.gob.hn/2025/10/14/anuario-estadistico-de-comercio-exterior-2020-2024/"),
    _candidate("cocatram", "COCATRAM — Comisión Centroamericana de Transporte Marítimo", ("www.cocatram.org.ni",), frozenset(("AMERICAS",)), frozenset(("MARITIME", "PORTS")), "QUARTERLY", "E2_CANDIDATE", "RESTRICTED", "MANUAL_REVIEW_REQUIRED", "UNKNOWN", "OFFICIAL_PAGE_VERIFIED", "https://www.cocatram.org.ni/estadisticas/static/manual.pdf"),
    _candidate("cepal", "CEPAL", ("cepal.org", "www.cepal.org"), frozenset(("AMERICAS",)), frozenset(("TRADE", "INFRASTRUCTURE", "MACRO")), "QUARTERLY", "E2_CANDIDATE", "UNREVIEWED", "MANUAL_REVIEW_REQUIRED", "UNKNOWN", "DISCOVERY_PENDING", "https://www.cepal.org/"),
    _candidate("eurostat", "Eurostat / European Commission", ("ec.europa.eu",), frozenset(("EUROPE",)), frozenset(("TRADE", "MARITIME", "INFRASTRUCTURE", "MACRO")), "MONTHLY", "E2_CANDIDATE", "PUBLIC_TERMS_UNCLEAR", "MANUAL_REVIEW_REQUIRED", "POSSIBLE_REVISIONS", "OFFICIAL_PAGE_VERIFIED", "https://ec.europa.eu/eurostat/databrowser/view/tran_r_mago_nm/default/table"),
    _candidate("datacomex", "Secretaría de Estado de Comercio de España / DataComex", ("datacomex.comercio.es",), frozenset(("EUROPE",)), frozenset(("TRADE", "CUSTOMS")), "MONTHLY", "E1_CANDIDATE", "REGISTERED_ACCESS", "REGISTERED_MANUAL_REVIEW_REQUIRED", "POSSIBLE_REVISIONS", "OFFICIAL_PAGE_VERIFIED", "https://datacomex.comercio.es/Metadata/Comex"),
    _candidate("puertos-del-estado", "Puertos del Estado de España", ("www.puertos.es",), frozenset(("EUROPE",)), frozenset(("MARITIME", "PORTS")), "MONTHLY", "E1_CANDIDATE", "PUBLIC_TERMS_UNCLEAR", "MANUAL_REVIEW_REQUIRED", "POSSIBLE_REVISIONS", "OFFICIAL_PAGE_VERIFIED", "https://www.puertos.es/datos/estadisticas/mensuales"),
    _candidate("adb", "Asian Development Bank", ("adb.org", "www.adb.org"), frozenset(("ASIA_PACIFIC",)), frozenset(("TRADE", "INFRASTRUCTURE", "MACRO")), "QUARTERLY", "E2_CANDIDATE", "UNREVIEWED", "MANUAL_REVIEW_REQUIRED", "UNKNOWN", "DISCOVERY_PENDING", "https://www.adb.org/"),
    _candidate("gacc", "General Administration of Customs of China", ("english.customs.gov.cn",), frozenset(("ASIA_PACIFIC",)), frozenset(("TRADE", "CUSTOMS")), "MONTHLY", "E1_CANDIDATE", "PUBLIC_TERMS_UNCLEAR", "MANUAL_REVIEW_REQUIRED", "PUBLISHED_REVISIONS", "OFFICIAL_PAGE_VERIFIED", "https://english.customs.gov.cn/statics/report/monthly.html"),
    _candidate("bitre", "Bureau of Infrastructure and Transport Research Economics", ("bitre.gov.au", "www.bitre.gov.au"), frozenset(("OCEANIA",)), frozenset(("PORTS", "AIR", "INFRASTRUCTURE")), "QUARTERLY", "E2_CANDIDATE", "UNREVIEWED", "MANUAL_REVIEW_REQUIRED", "UNKNOWN", "DISCOVERY_PENDING", "https://www.bitre.gov.au/"),
    _candidate("uncomtrade", "UN Comtrade", ("comtradeapi.un.org",), frozenset(REGIONS), frozenset(("TRADE",)), "MONTHLY", "E2_CANDIDATE", "PUBLIC_TERMS_UNCLEAR", "MANUAL_REVIEW_REQUIRED", "POSSIBLE_REVISIONS", "DISCOVERY_PENDING", "https://comtradeapi.un.org/"),
    _candidate("wto-statistics", "World Trade Organization", ("www.wto.org",), frozenset(REGIONS), frozenset(("TRADE", "CUSTOMS")), "MONTHLY", "E2_CANDIDATE", "UNREVIEWED", "MANUAL_REVIEW_REQUIRED", "UNKNOWN", "DISCOVERY_PENDING", "https://www.wto.org/"),
    _candidate("wto-eping", "World Trade Organization ePing", ("eping.wto.org",), frozenset(REGIONS), frozenset(("REGULATION", "CUSTOMS")), "DAILY", "E1_CANDIDATE", "PUBLIC_TERMS_UNCLEAR", "MANUAL_REVIEW_REQUIRED", "UNKNOWN", "OFFICIAL_PAGE_VERIFIED", "https://eping.wto.org/"),
    _candidate("wco", "World Customs Organization", ("www.wcoomd.org",), frozenset(REGIONS), frozenset(("CUSTOMS", "TRADE", "REGULATION")), "EVENT_DRIVEN", "E2_CANDIDATE", "UNREVIEWED", "MANUAL_REVIEW_REQUIRED", "UNKNOWN", "DISCOVERY_PENDING", "https://www.wcoomd.org/"),
    _candidate("world-bank", "World Bank", ("worldbank.org", "www.worldbank.org"), frozenset(REGIONS), frozenset(("PORTS", "INFRASTRUCTURE", "MACRO")), "ANNUAL", "E2_CANDIDATE", "UNREVIEWED", "MANUAL_REVIEW_REQUIRED", "UNKNOWN", "DISCOVERY_PENDING", "https://www.worldbank.org/"),
    _candidate("us-census-port-hs", "U.S. Census Bureau International Trade", ("api.census.gov",), frozenset(("AMERICAS",)), frozenset(("TRADE", "MARITIME", "PORTS")), "MONTHLY", "E1_CANDIDATE", "REGISTERED_ACCESS", "REGISTERED_MANUAL_REVIEW_REQUIRED", "POSSIBLE_REVISIONS", "OFFICIAL_PAGE_VERIFIED", "https://api.census.gov/data/timeseries/intltrade/imports/porths.html"),
    _candidate("iata", "International Air Transport Association", ("iata.org", "www.iata.org"), frozenset(REGIONS), frozenset(("AIR",)), "EVENT_DRIVEN", "E2_CANDIDATE", "UNREVIEWED", "MANUAL_REVIEW_REQUIRED", "UNKNOWN", "DISCOVERY_PENDING", "https://www.iata.org/"),
)


def source_readiness(*, region: str, domain: str) -> dict[str, object]:
    if not isinstance(region, str) or not isinstance(domain, str):
        raise ContractViolation("source readiness region and domain must be text")
    region, domain = region.upper(), domain.upper()
    if region not in REGIONS or domain not in DOMAINS:
        raise ContractViolation("source readiness region or domain is unsupported")
    matches = [source.snapshot() for source in _SOURCES if region in source.regions and domain in source.domains]
    return {
        "scope": "BLOCK1_SOURCE_PORTFOLIO_READINESS",
        "query": {"region": region, "domain": domain},
        "candidate_count": len(_SOURCES),
        "capacity": 50,
        "candidates": matches,
        "admissible_source_count": 0,
        "status": "RESEARCH_BLOCKED_PENDING_SOURCE_BINDING",
        "blockers": [
            "LICENSE_OR_TERMS_NOT_VERIFIED", "ACCESS_METHOD_NOT_APPROVED",
            "HOST_ALLOWLIST_NOT_APPROVED", "CLAIM_AUTHORIZATION_NOT_APPROVED",
        ],
        "non_claims": [
            "CANDIDATE_DISCOVERY_IS_NOT_SOURCE_APPROVAL",
            "PUBLIC_ACCESS_IS_NOT_REUSE_PERMISSION",
            "NO_NETWORK_ACQUISITION_OR_AUTOMATIC_IMPORT",
        ],
    }
