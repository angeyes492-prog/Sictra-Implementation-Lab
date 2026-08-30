"""Bounded proposed-source catalogue; never a network connector."""

from __future__ import annotations

from dataclasses import dataclass

from .common import ContractViolation


REGIONS = frozenset(("AMERICAS", "EUROPE", "ASIA_PACIFIC", "OCEANIA"))
DOMAINS = frozenset(("TRADE", "MARITIME", "AIR", "PORTS", "CUSTOMS", "INFRASTRUCTURE", "MACRO"))


@dataclass(frozen=True, slots=True)
class SourceCandidate:
    source_id: str
    publisher: str
    hosts: tuple[str, ...]
    regions: frozenset[str]
    domains: frozenset[str]
    cadence: str
    status: str = "PROPOSED"

    def __post_init__(self) -> None:
        if not self.source_id or not self.publisher or not self.hosts or self.status != "PROPOSED":
            raise ContractViolation("source candidate is invalid")
        if not self.regions <= REGIONS or not self.domains <= DOMAINS or not self.regions or not self.domains:
            raise ContractViolation("source candidate coverage is invalid")

    def snapshot(self) -> dict[str, object]:
        return {"source_id": self.source_id, "publisher": self.publisher, "candidate_hosts": list(self.hosts), "regions": sorted(self.regions), "domains": sorted(self.domains), "cadence": self.cadence, "status": self.status}


_SOURCES = (
    SourceCandidate("cepal", "CEPAL", ("cepal.org",), frozenset(("AMERICAS",)), frozenset(("TRADE", "INFRASTRUCTURE", "MACRO")), "QUARTERLY"),
    SourceCandidate("eurostat", "Eurostat", ("ec.europa.eu",), frozenset(("EUROPE",)), frozenset(("TRADE", "INFRASTRUCTURE", "MACRO")), "MONTHLY"),
    SourceCandidate("adb", "Asian Development Bank", ("adb.org",), frozenset(("ASIA_PACIFIC",)), frozenset(("TRADE", "INFRASTRUCTURE", "MACRO")), "QUARTERLY"),
    SourceCandidate("bitre", "BITRE", ("bitre.gov.au",), frozenset(("OCEANIA",)), frozenset(("PORTS", "AIR", "INFRASTRUCTURE")), "QUARTERLY"),
    SourceCandidate("unctad", "UN Trade and Development", ("unctad.org",), frozenset(REGIONS), frozenset(("TRADE", "MARITIME", "PORTS")), "ANNUAL"),
    SourceCandidate("uncomtrade", "UN Comtrade", ("comtradeapi.un.org",), frozenset(REGIONS), frozenset(("TRADE",)), "MONTHLY"),
    SourceCandidate("wto", "World Trade Organization", ("wto.org",), frozenset(REGIONS), frozenset(("TRADE", "CUSTOMS")), "MONTHLY"),
    SourceCandidate("wco", "World Customs Organization", ("wcoomd.org",), frozenset(REGIONS), frozenset(("CUSTOMS", "TRADE")), "EVENT_DRIVEN"),
    SourceCandidate("world-bank", "World Bank", ("worldbank.org",), frozenset(REGIONS), frozenset(("PORTS", "INFRASTRUCTURE", "MACRO")), "ANNUAL"),
    SourceCandidate("iata", "IATA", ("iata.org",), frozenset(REGIONS), frozenset(("AIR",)), "EVENT_DRIVEN"),
)


def source_readiness(*, region: str, domain: str) -> dict[str, object]:
    if not isinstance(region, str) or not isinstance(domain, str):
        raise ContractViolation("source readiness region and domain must be text")
    region, domain = region.upper(), domain.upper()
    if region not in REGIONS or domain not in DOMAINS:
        raise ContractViolation("source readiness region or domain is unsupported")
    matches = [source.snapshot() for source in _SOURCES if region in source.regions and domain in source.domains]
    return {"scope": "BLOCK1_SOURCE_PORTFOLIO_READINESS", "query": {"region": region, "domain": domain}, "candidate_count": len(_SOURCES), "capacity": 50, "candidates": matches, "admissible_source_count": 0, "status": "RESEARCH_BLOCKED_PENDING_SOURCE_BINDING", "blockers": ["LICENSE_OR_TERMS_NOT_VERIFIED", "ACCESS_METHOD_NOT_APPROVED", "HOST_ALLOWLIST_NOT_APPROVED", "CLAIM_AUTHORIZATION_NOT_APPROVED"]}
