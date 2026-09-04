"""Signed, bounded authorization for a Source Gateway configuration."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import hmac
import json
import re
from typing import TYPE_CHECKING, Any, Mapping

from .common import ContractViolation
from .source_approval import SourceApprovalRecord
from .source_portfolio import SourceCandidate
from .source_primitives import normalized_dns_host as _host, required_text as _required_text

if TYPE_CHECKING:
    from .source_gateway import SourceRegistration


BINDING_VERSION = "0.1.0"


def _material(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        {key: item for key, item in value.items() if key != "signature"},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode()


@dataclass(frozen=True, slots=True)
class SourceBindingAuthorization:
    issuer: str
    source_id: str
    scope: str
    approval_ref: str
    approved_hosts: tuple[str, ...]
    approved_claim_keys: tuple[str, ...]
    max_content_bytes: int
    issued_at: int
    expires_at: int
    signature: str

    def __post_init__(self) -> None:
        for name in ("issuer", "source_id", "scope", "approval_ref"):
            object.__setattr__(self, name, _required_text(name, getattr(self, name)))
        hosts = tuple(sorted({_host(host) for host in self.approved_hosts}))
        if not hosts:
            raise ContractViolation("binding authorization requires approved hosts")
        object.__setattr__(self, "approved_hosts", hosts)
        claims = tuple(sorted({_required_text("approved_claim_key", value) for value in self.approved_claim_keys}))
        if not claims:
            raise ContractViolation("binding authorization requires approved claims")
        object.__setattr__(self, "approved_claim_keys", claims)
        if not isinstance(self.max_content_bytes, int) or isinstance(self.max_content_bytes, bool) or self.max_content_bytes < 1:
            raise ContractViolation("binding authorization content limit is invalid")
        if any(not isinstance(value, int) or isinstance(value, bool) for value in (self.issued_at, self.expires_at)):
            raise ContractViolation("binding authorization times must be integers")
        if self.issued_at < 0 or self.expires_at < self.issued_at:
            raise ContractViolation("binding authorization time window is invalid")
        if not isinstance(self.signature, str) or not re.fullmatch(r"[0-9a-f]{64}", self.signature):
            raise ContractViolation("binding authorization signature is invalid")

    def unsigned(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if key != "signature"}


class SourceBindingIssuer:
    """Configuration-side signer; it is not a production identity system."""

    def __init__(self, issuer: str, secret: bytes) -> None:
        if not isinstance(issuer, str) or not issuer.strip() or len(secret) < 32:
            raise ContractViolation("binding issuer requires identity and 32-byte key")
        self.issuer, self._secret = issuer.strip(), bytes(secret)

    def issue(self, *, approval: SourceApprovalRecord, candidate: SourceCandidate,
              scope: str, now: int, ttl: int) -> SourceBindingAuthorization:
        if not isinstance(now, int) or isinstance(now, bool) or now < 0 or not isinstance(ttl, int) or isinstance(ttl, bool) or ttl < 1:
            raise ContractViolation("binding issue requires non-negative now and positive ttl")
        readiness = approval.readiness_for(candidate, now=now)
        if readiness["status"] != "READY_FOR_GATEWAY_CONFIGURATION_REVIEW":
            raise ContractViolation("source approval is not eligible for binding")
        unsigned = SourceBindingAuthorization(
            issuer=self.issuer,
            source_id=approval.source_id,
            scope=_required_text("scope", scope),
            approval_ref=approval.terms_evidence_ref,
            approved_hosts=approval.approved_hosts,
            approved_claim_keys=tuple(approval.approved_claim_keys),
            max_content_bytes=approval.max_content_bytes,
            issued_at=now,
            expires_at=now + ttl,
            signature="0" * 64,
        )
        signature = hmac.new(self._secret, _material(unsigned.unsigned()), sha256).hexdigest()
        return replace(unsigned, signature=signature)


class SourceBindingVerifier:
    def __init__(self, trusted_keys: Mapping[str, bytes], scope: str) -> None:
        self._trusted_keys = {issuer: bytes(key) for issuer, key in trusted_keys.items()}
        self.scope = _required_text("scope", scope)

    def verify(self, authorization: SourceBindingAuthorization | None,
               registration: "SourceRegistration", *, now: int) -> tuple[bool, str]:
        if authorization is None:
            return False, "SOURCE_BINDING_MISSING"
        if not all(hasattr(registration, field) for field in (
            "source_id", "allowed_hosts", "claim_keys", "max_content_bytes",
        )):
            return False, "SOURCE_BINDING_REGISTRATION_INVALID"
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            return False, "SOURCE_BINDING_TIME_INVALID"
        key = self._trusted_keys.get(authorization.issuer)
        if key is None or len(key) < 32:
            return False, "SOURCE_BINDING_ISSUER_UNTRUSTED"
        expected = hmac.new(key, _material(authorization.unsigned()), sha256).hexdigest()
        checks = (
            (hmac.compare_digest(expected, authorization.signature), "SOURCE_BINDING_SIGNATURE_INVALID"),
            (authorization.scope == self.scope, "SOURCE_BINDING_SCOPE_MISMATCH"),
            (authorization.source_id == registration.source_id, "SOURCE_BINDING_SOURCE_MISMATCH"),
            (authorization.approved_hosts == registration.allowed_hosts, "SOURCE_BINDING_HOST_MISMATCH"),
            (frozenset(authorization.approved_claim_keys) == registration.claim_keys, "SOURCE_BINDING_CLAIM_MISMATCH"),
            (authorization.max_content_bytes == registration.max_content_bytes, "SOURCE_BINDING_LIMIT_MISMATCH"),
            (authorization.issued_at <= now <= authorization.expires_at, "SOURCE_BINDING_NOT_CURRENT"),
        )
        for valid, reason in checks:
            if not valid:
                return False, reason
        return True, "SOURCE_BINDING_VERIFIED"
