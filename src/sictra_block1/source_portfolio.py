"""Governed planning catalogue for Block 1 source candidates.

This module is not a connector and cannot turn a candidate into an operational
SourceGateway registration. It preserves the boundary between discovery and
evidence admissibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .common import ContractViolation
from .source_primitives import (
    MAX_SOURCE_REGISTRATIONS as MAX_REGISTERED_SOURCES,
    normalized_dns_host as _host,
    required_text as _required_text,
)


PORTFOLIO_VERSION = "0.1.0"
PORTFOLIO_STATUS = "PROPOSED_CATALOG"
REGIONS = frozenset(("GLOBAL", "AMERICAS", "EUROPE", "ASIA_PACIFIC", "OCEANIA"))
DOMAINS = frozenset(("TRADE", "MARITIME", "AIR", "PORTS", "CUSTOMS", "INFRASTRUCTURE", "MACRO"))
CADENCES = frozenset(("ANNUAL", "QUARTERLY", "MONTHLY", "EVENT_DRIVEN"))


def _canonical_set(name: str, values: Iterable[str], permitted: frozenset[str]) -> frozenset[str]:
    try:
        normalized = frozenset(_required_text(name, value).upper() for value in values)
    except TypeError as error:
        raise ContractViolation(f"{name} must be iterable") from error
    if not normalized or not normalized <= permitted:
        raise ContractViolation(f"{name} contains unsupported values")
    return normalized


@dataclass(frozen=True, slots=True)
class SourceCandidate:
    source_id: str
    publisher: str
    candidate_hosts: tuple[str, ...]
    regions: frozenset[str]
    domains: frozenset[str]
    cadence: str
    status: str = "PROPOSED"

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _required_text("source_id", self.source_id))
        object.__setattr__(self, "publisher", _required_text("publisher", self.publisher))
        hosts = tuple(sorted({_host(host) for host in self.candidate_hosts}))
        if not hosts:
            raise ContractViolation("candidate source requires at least one host")
        object.__setattr__(self, "candidate_hosts", hosts)
        object.__setattr__(self, "regions", _canonical_set("regions", self.regions, REGIONS))
        object.__setattr__(self, "domains", _canonical_set("domains", self.domains, DOMAINS))
        cadence = _required_text("cadence", self.cadence).upper()
        if cadence not in CADENCES:
            raise ContractViolation("cadence is unsupported")
        object.__setattr__(self, "cadence", cadence)
        if self.status != "PROPOSED":
            raise ContractViolation("source portfolio v0.1 only accepts PROPOSED candidates")

    def snapshot(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "publisher": self.publisher,
            "candidate_hosts": list(self.candidate_hosts),
            "regions": sorted(self.regions),
            "domains": sorted(self.domains),
            "cadence": self.cadence,
            "status": self.status,
        }


class SourcePortfolio:
    """Immutable candidate portfolio with no acquisition capability."""

    def __init__(self, candidates: Iterable[SourceCandidate]) -> None:
        values = tuple(candidates)
        if len(values) > MAX_REGISTERED_SOURCES:
            raise ContractViolation(f"source portfolio exceeds {MAX_REGISTERED_SOURCES}")
        if any(not isinstance(value, SourceCandidate) for value in values):
            raise ContractViolation("portfolio requires SourceCandidate values")
        ids = [value.source_id for value in values]
        if len(ids) != len(set(ids)):
            raise ContractViolation("source portfolio contains duplicate source_id")
        hosts = [host for value in values for host in value.candidate_hosts]
        if len(hosts) != len(set(hosts)):
            raise ContractViolation("source portfolio contains duplicate candidate host")
        self._candidates = tuple(sorted(values, key=lambda value: value.source_id))

    @property
    def count(self) -> int:
        return len(self._candidates)

    def summary(self) -> dict[str, object]:
        region_counts = {region: 0 for region in sorted(REGIONS)}
        domain_counts = {domain: 0 for domain in sorted(DOMAINS)}
        for candidate in self._candidates:
            for region in candidate.regions:
                region_counts[region] += 1
            for domain in candidate.domains:
                domain_counts[domain] += 1
        return {
            "portfolio_version": PORTFOLIO_VERSION,
            "status": PORTFOLIO_STATUS,
            "candidate_count": self.count,
            "capacity": MAX_REGISTERED_SOURCES,
            "region_counts": region_counts,
            "domain_counts": domain_counts,
            "promotion_blockers": [
                "LICENSE_OR_TERMS_NOT_VERIFIED",
                "ACCESS_METHOD_NOT_APPROVED",
                "HOST_ALLOWLIST_NOT_APPROVED",
                "CLAIM_AUTHORIZATION_NOT_APPROVED",
            ],
        }

    def candidates_for(self, *, regions: Iterable[str], domains: Iterable[str]) -> list[dict[str, object]]:
        requested_regions = _canonical_set("regions", regions, REGIONS - {"GLOBAL"})
        requested_domains = _canonical_set("domains", domains, DOMAINS)
        return [
            candidate.snapshot()
            for candidate in self._candidates
            if candidate.domains & requested_domains
            and (candidate.regions & requested_regions or "GLOBAL" in candidate.regions)
        ]


def default_source_portfolio() -> SourcePortfolio:
    """Return a shape-validated, not use-approved, twelve-source catalog."""
    return SourcePortfolio((
        SourceCandidate("adb", "Asian Development Bank", ("adb.org",), frozenset(("ASIA_PACIFIC",)), frozenset(("TRADE", "INFRASTRUCTURE", "MACRO")), "QUARTERLY"),
        SourceCandidate("bitre", "Bureau of Infrastructure and Transport Research Economics", ("bitre.gov.au",), frozenset(("OCEANIA",)), frozenset(("INFRASTRUCTURE", "PORTS", "AIR")), "QUARTERLY"),
        SourceCandidate("cepal", "CEPAL", ("cepal.org",), frozenset(("AMERICAS",)), frozenset(("TRADE", "INFRASTRUCTURE", "MACRO")), "QUARTERLY"),
        SourceCandidate("eurostat", "Eurostat", ("ec.europa.eu",), frozenset(("EUROPE",)), frozenset(("TRADE", "INFRASTRUCTURE", "MACRO")), "MONTHLY"),
        SourceCandidate("iata", "International Air Transport Association", ("iata.org",), frozenset(("GLOBAL",)), frozenset(("AIR",)), "EVENT_DRIVEN"),
        SourceCandidate("imf", "International Monetary Fund", ("imf.org",), frozenset(("GLOBAL",)), frozenset(("MACRO", "TRADE")), "QUARTERLY"),
        SourceCandidate("itf-oecd", "International Transport Forum", ("itf-oecd.org",), frozenset(("GLOBAL",)), frozenset(("INFRASTRUCTURE", "MARITIME")), "ANNUAL"),
        SourceCandidate("uncomtrade", "UN Comtrade", ("comtradeapi.un.org",), frozenset(("GLOBAL",)), frozenset(("TRADE",)), "MONTHLY"),
        SourceCandidate("unctad", "UN Trade and Development", ("unctad.org",), frozenset(("GLOBAL",)), frozenset(("TRADE", "MARITIME", "PORTS")), "ANNUAL"),
        SourceCandidate("wco", "World Customs Organization", ("wcoomd.org",), frozenset(("GLOBAL",)), frozenset(("CUSTOMS", "TRADE")), "EVENT_DRIVEN"),
        SourceCandidate("world-bank", "World Bank", ("worldbank.org",), frozenset(("GLOBAL",)), frozenset(("INFRASTRUCTURE", "PORTS", "MACRO")), "ANNUAL"),
        SourceCandidate("wto", "World Trade Organization", ("wto.org",), frozenset(("GLOBAL",)), frozenset(("TRADE", "CUSTOMS")), "MONTHLY"),
    ))
