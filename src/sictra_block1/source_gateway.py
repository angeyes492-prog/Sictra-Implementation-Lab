"""Governed manual ingress for Block 1 source evidence.

This module deliberately has no networking capability.  It creates a narrow,
auditable boundary between a registered source and the existing E02 verifier.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Iterable, Mapping
from urllib.parse import urlsplit

from .common import ContractViolation
from .evidence import EvidenceIssuer
from .source_binding import SourceBindingAuthorization, SourceBindingVerifier
from .source_primitives import (
    MAX_SOURCE_REGISTRATIONS,
    normalized_dns_host as _host,
    required_text as _required_text,
)


GATEWAY_VERSION = "0.1.0"
MAX_REGISTERED_SOURCES = MAX_SOURCE_REGISTRATIONS
_BUNDLE_FIELDS = frozenset((
    "source_id", "source_url", "content", "observed_at", "claim_key",
    "polarity", "correlation_id",
))


def _validate_url(value: object, allowed_hosts: frozenset[str]) -> str:
    url = _required_text("source_url", value)
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as error:
        raise ContractViolation("source_url is invalid") from error
    if (
        parsed.scheme.casefold() != "https" or not parsed.hostname or parsed.username
        or parsed.password or port is not None or parsed.fragment
    ):
        raise ContractViolation("source_url must be an HTTPS canonical URL without credentials, port, or fragment")
    host = _host(parsed.hostname)
    if host not in allowed_hosts:
        raise ContractViolation("source_url host is not registered for this source")
    return url


@dataclass(frozen=True, slots=True)
class SourceRegistration:
    source_id: str
    publisher: str
    scope: str
    allowed_hosts: tuple[str, ...]
    claim_keys: frozenset[str]
    status: str = "PROPOSED"
    max_content_bytes: int = 1_000_000

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _required_text("source_id", self.source_id))
        object.__setattr__(self, "publisher", _required_text("publisher", self.publisher))
        object.__setattr__(self, "scope", _required_text("scope", self.scope))
        if self.status not in {"PROPOSED", "BOUND", "SUSPENDED", "RETIRED"}:
            raise ContractViolation("source status is unsupported")
        if not isinstance(self.max_content_bytes, int) or isinstance(self.max_content_bytes, bool) or self.max_content_bytes < 1:
            raise ContractViolation("max_content_bytes must be a positive integer")
        hosts = tuple(sorted({_host(host) for host in self.allowed_hosts}))
        if not hosts:
            raise ContractViolation("at least one source host is required")
        claims = frozenset(_required_text("claim_key", claim) for claim in self.claim_keys)
        if not claims:
            raise ContractViolation("at least one source claim is required")
        object.__setattr__(self, "allowed_hosts", hosts)
        object.__setattr__(self, "claim_keys", claims)


class SourceGateway:
    """Attests manually supplied source bundles from a bounded source registry."""

    def __init__(self, *, registrations: Iterable[SourceRegistration], issuer: EvidenceIssuer,
                 scope: str, binding_authorizations: Mapping[str, SourceBindingAuthorization],
                 binding_verifier: SourceBindingVerifier, now: int) -> None:
        self._scope = _required_text("scope", scope)
        if not isinstance(issuer, EvidenceIssuer):
            raise ContractViolation("gateway requires an EvidenceIssuer")
        if not isinstance(binding_verifier, SourceBindingVerifier):
            raise ContractViolation("gateway requires a SourceBindingVerifier")
        if binding_verifier.scope != self._scope:
            raise ContractViolation("gateway binding verifier scope must match gateway scope")
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise ContractViolation("gateway now must be a non-negative integer")
        registered = tuple(registrations)
        if len(registered) > MAX_REGISTERED_SOURCES:
            raise ContractViolation(f"source registry exceeds {MAX_REGISTERED_SOURCES}")
        if any(not isinstance(item, SourceRegistration) for item in registered):
            raise ContractViolation("registrations must contain SourceRegistration values")
        source_ids = [item.source_id for item in registered]
        if len(source_ids) != len(set(source_ids)):
            raise ContractViolation("source registry contains duplicate source_id")
        if any(item.scope != self._scope for item in registered):
            raise ContractViolation("source registration scope must match gateway scope")
        self._registrations = {item.source_id: item for item in registered}
        self._issuer = issuer
        self._binding_authorizations = dict(binding_authorizations)
        self._binding_verifier = binding_verifier
        bound_ids = {item.source_id for item in registered if item.status == "BOUND"}
        if set(self._binding_authorizations) != bound_ids:
            raise ContractViolation("gateway binding authorizations must match BOUND registrations")
        self._assert_bindings(now)

    @property
    def registered_source_count(self) -> int:
        return len(self._registrations)

    def _assert_bindings(self, now: int) -> None:
        for source_id, registration in self._registrations.items():
            if registration.status != "BOUND":
                continue
            valid, reason = self._binding_verifier.verify(
                self._binding_authorizations.get(source_id), registration, now=now,
            )
            if not valid:
                raise ContractViolation(reason)

    def attest_manual_bundle(self, bundle: Mapping[str, Any], *, now: int) -> dict[str, Any]:
        if not isinstance(bundle, Mapping):
            raise ContractViolation("manual source bundle must be a mapping")
        if frozenset(bundle) != _BUNDLE_FIELDS:
            raise ContractViolation("manual source bundle fields are invalid")
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise ContractViolation("gateway now must be a non-negative integer")
        self._assert_bindings(now)
        source_id = _required_text("source_id", bundle["source_id"])
        registration = self._registrations.get(source_id)
        if registration is None:
            raise ContractViolation("source is not registered")
        if registration.status != "BOUND":
            raise ContractViolation("source is not bound for gateway ingress")
        source_url = _validate_url(bundle["source_url"], frozenset(registration.allowed_hosts))
        content = _required_text("content", bundle["content"])
        if len(content.encode("utf-8")) > registration.max_content_bytes:
            raise ContractViolation("source content exceeds registered limit")
        observed_at = bundle["observed_at"]
        if not isinstance(observed_at, int) or isinstance(observed_at, bool) or observed_at < 0 or observed_at > now:
            raise ContractViolation("source observed_at must be non-negative and not future")
        claim_key = _required_text("claim_key", bundle["claim_key"])
        if claim_key not in registration.claim_keys:
            raise ContractViolation("source claim is not registered")
        polarity = bundle["polarity"]
        if not isinstance(polarity, int) or isinstance(polarity, bool) or polarity not in {-1, 1}:
            raise ContractViolation("source polarity must be -1 or 1")
        correlation_id = _required_text("correlation_id", bundle["correlation_id"])
        content_hash = sha256(content.encode("utf-8")).hexdigest()
        return self._issuer.attest({
            "source_id": source_id,
            "content": content,
            "observed_at": observed_at,
            "root_provenance": f"gateway-source:{source_id}",
            "evidence_class": "OBSERVED",
            "scope": self._scope,
            "correlation_id": correlation_id,
            "claim_key": claim_key,
            "polarity": polarity,
            "source_url": source_url,
            "publisher": registration.publisher,
            "content_sha256": content_hash,
            "ingestion_method": "MANUAL_SOURCE_BUNDLE",
            "gateway_version": GATEWAY_VERSION,
        })

    def fetch_network_source(self, *_: object, **__: object) -> None:
        """Reject network acquisition until a separately governed adapter exists."""
        raise ContractViolation("network acquisition is not implemented by SourceGateway v0.1")
