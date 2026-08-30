"""Governed manual source ingress; deliberately no network capability."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import hmac
import ipaddress
import json
from typing import Any, Mapping
from urllib.parse import urlsplit

from .common import ContractViolation
from .evidence import EvidenceIssuer


MAX_REGISTERED_SOURCES = 50
_FIELDS = frozenset(("source_id", "source_url", "content", "observed_at", "claim_key", "polarity", "correlation_id"))


def _text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractViolation(f"{name} must be non-empty text")
    return value.strip()


def _host(value: object) -> str:
    raw = _text("host", value)
    try:
        parsed = urlsplit(f"//{raw}")
        port = parsed.port
    except ValueError as error:
        raise ContractViolation("host is invalid") from error
    if parsed.username or parsed.password or port is not None or parsed.path or parsed.query or parsed.fragment or not parsed.hostname:
        raise ContractViolation("host must be a bare DNS name")
    host = parsed.hostname.rstrip(".").lower()
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ContractViolation("host must not be an IP address")
    if host == "localhost" or host.endswith(".localhost"):
        raise ContractViolation("host must not be local")
    return host


def _material(value: Mapping[str, Any]) -> bytes:
    return json.dumps({key: item for key, item in value.items() if key != "signature"}, sort_keys=True, separators=(",", ":")).encode()


@dataclass(frozen=True, slots=True)
class SourceRegistration:
    source_id: str
    publisher: str
    scope: str
    allowed_hosts: tuple[str, ...]
    claim_keys: frozenset[str]
    max_content_bytes: int = 1_000_000
    status: str = "PROPOSED"

    def __post_init__(self) -> None:
        for name in ("source_id", "publisher", "scope"):
            object.__setattr__(self, name, _text(name, getattr(self, name)))
        hosts = tuple(sorted({_host(host) for host in self.allowed_hosts}))
        claims = frozenset(_text("claim_key", claim) for claim in self.claim_keys)
        if not hosts or not claims or self.status not in {"PROPOSED", "BOUND", "SUSPENDED", "RETIRED"}:
            raise ContractViolation("source registration is invalid")
        if not isinstance(self.max_content_bytes, int) or isinstance(self.max_content_bytes, bool) or self.max_content_bytes < 1:
            raise ContractViolation("source content limit is invalid")
        object.__setattr__(self, "allowed_hosts", hosts)
        object.__setattr__(self, "claim_keys", claims)


@dataclass(frozen=True, slots=True)
class SourceApprovalRecord:
    source_id: str
    reviewer_id: str
    reviewed_at: int
    terms_evidence_ref: str
    allowed_hosts: tuple[str, ...]
    claim_keys: frozenset[str]
    max_content_bytes: int
    decision: str

    def __post_init__(self) -> None:
        for name in ("source_id", "reviewer_id", "terms_evidence_ref"):
            object.__setattr__(self, name, _text(name, getattr(self, name)))
        hosts = tuple(sorted({_host(host) for host in self.allowed_hosts}))
        claims = frozenset(_text("claim_key", claim) for claim in self.claim_keys)
        if not hosts or not claims or self.decision not in {"APPROVED", "REJECTED"} or not isinstance(self.reviewed_at, int) or isinstance(self.reviewed_at, bool) or self.reviewed_at < 0 or not isinstance(self.max_content_bytes, int) or isinstance(self.max_content_bytes, bool) or self.max_content_bytes < 1:
            raise ContractViolation("source approval record is invalid")
        object.__setattr__(self, "allowed_hosts", hosts)
        object.__setattr__(self, "claim_keys", claims)


class SourceBindingIssuer:
    def __init__(self, issuer: str, secret: bytes) -> None:
        self.issuer, self._secret = _text("issuer", issuer), bytes(secret)
        if len(self._secret) < 32:
            raise ContractViolation("binding issuer requires a 32-byte key")

    def issue(self, registration: SourceRegistration, approval: SourceApprovalRecord, *, now: int, ttl: int) -> dict[str, Any]:
        if registration.status != "BOUND" or not isinstance(now, int) or isinstance(now, bool) or now < 0 or not isinstance(ttl, int) or ttl < 1:
            raise ContractViolation("binding requires BOUND registration, time, and ttl")
        if approval.decision != "APPROVED" or approval.reviewed_at > now or approval.source_id != registration.source_id or approval.allowed_hosts != registration.allowed_hosts or approval.claim_keys != registration.claim_keys or approval.max_content_bytes != registration.max_content_bytes:
            raise ContractViolation("binding requires a current matching approved source record")
        payload = {"issuer": self.issuer, "source_id": registration.source_id, "scope": registration.scope, "allowed_hosts": list(registration.allowed_hosts), "claim_keys": sorted(registration.claim_keys), "max_content_bytes": registration.max_content_bytes, "issued_at": now, "expires_at": now + ttl}
        payload["signature"] = hmac.new(self._secret, _material(payload), sha256).hexdigest()
        return payload


class SourceGateway:
    def __init__(self, *, registrations: tuple[SourceRegistration, ...], issuer: EvidenceIssuer,
                 binding_keys: Mapping[str, bytes], bindings: Mapping[str, Mapping[str, Any]], now: int) -> None:
        if not isinstance(issuer, EvidenceIssuer) or len(registrations) > MAX_REGISTERED_SOURCES or not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise ContractViolation("gateway configuration is invalid")
        if any(not isinstance(item, SourceRegistration) for item in registrations):
            raise ContractViolation("gateway registrations are invalid")
        self._registrations = {item.source_id: item for item in registrations}
        if len(self._registrations) != len(registrations):
            raise ContractViolation("gateway source IDs must be unique")
        self._issuer, self._keys, self._bindings = issuer, {key: bytes(value) for key, value in binding_keys.items()}, {key: dict(value) for key, value in bindings.items()}
        bound = {item.source_id for item in registrations if item.status == "BOUND"}
        if set(self._bindings) != bound:
            raise ContractViolation("every BOUND source needs exactly one binding")
        self._assert_bindings(now)

    def _assert_bindings(self, now: int) -> None:
        for source_id, binding in self._bindings.items():
            registration = self._registrations[source_id]
            required = {"issuer", "source_id", "scope", "allowed_hosts", "claim_keys", "max_content_bytes", "issued_at", "expires_at", "signature"}
            if set(binding) != required or not isinstance(binding.get("issuer"), str) or not isinstance(binding.get("signature"), str):
                raise ContractViolation("source binding shape is invalid")
            key = self._keys.get(binding["issuer"])
            if key is None or len(key) < 32 or not hmac.compare_digest(hmac.new(key, _material(binding), sha256).hexdigest(), binding["signature"]):
                raise ContractViolation("source binding signature is invalid")
            if binding["source_id"] != registration.source_id or binding["scope"] != registration.scope or tuple(binding["allowed_hosts"]) != registration.allowed_hosts or frozenset(binding["claim_keys"]) != registration.claim_keys or binding["max_content_bytes"] != registration.max_content_bytes or not isinstance(binding["issued_at"], int) or not isinstance(binding["expires_at"], int) or not binding["issued_at"] <= now <= binding["expires_at"]:
                raise ContractViolation("source binding does not match active registration")

    def attest_manual_bundle(self, bundle: Mapping[str, Any], *, now: int) -> dict[str, Any]:
        if not isinstance(bundle, Mapping) or frozenset(bundle) != _FIELDS or not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise ContractViolation("manual source bundle is invalid")
        self._assert_bindings(now)
        source_id = _text("source_id", bundle["source_id"])
        registration = self._registrations.get(source_id)
        if registration is None or registration.status != "BOUND":
            raise ContractViolation("source is not bound")
        url = _text("source_url", bundle["source_url"])
        parsed = urlsplit(url)
        if parsed.scheme.lower() != "https" or parsed.username or parsed.password or parsed.port is not None or parsed.fragment or _host(parsed.hostname or "") not in registration.allowed_hosts:
            raise ContractViolation("source URL is not allowed")
        content = _text("content", bundle["content"])
        observed_at, polarity = bundle["observed_at"], bundle["polarity"]
        claim_key, correlation = _text("claim_key", bundle["claim_key"]), _text("correlation_id", bundle["correlation_id"])
        if len(content.encode()) > registration.max_content_bytes or not isinstance(observed_at, int) or isinstance(observed_at, bool) or not 0 <= observed_at <= now or claim_key not in registration.claim_keys or polarity not in {-1, 1} or isinstance(polarity, bool):
            raise ContractViolation("manual source bundle values are invalid")
        return self._issuer.attest({"source_id": source_id, "content": content, "observed_at": observed_at, "root_provenance": f"gateway-source:{source_id}", "evidence_class": "OBSERVED", "scope": registration.scope, "correlation_id": correlation, "claim_key": claim_key, "polarity": polarity, "source_url": url, "publisher": registration.publisher, "content_sha256": sha256(content.encode()).hexdigest(), "ingestion_method": "MANUAL_SOURCE_BUNDLE"})

    def fetch_network_source(self, *_: object, **__: object) -> None:
        raise ContractViolation("network acquisition is not implemented")
