"""Independent source attestations for the bounded operational adapter."""

from __future__ import annotations

from hashlib import sha256
import hmac
import json
from typing import Any, Mapping

from .common import ContractViolation, plain_copy


def _material(source: Mapping[str, Any]) -> bytes:
    return json.dumps(
        {key: plain_copy(value) for key, value in source.items() if key != "attestation"},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode()


class EvidenceIssuer:
    def __init__(self, issuer: str, secret: bytes) -> None:
        if not issuer or len(secret) < 32:
            raise ContractViolation("evidence issuer requires identity and 32-byte key")
        self.issuer, self._secret = issuer, bytes(secret)

    def attest(self, source: Mapping[str, Any]) -> dict[str, Any]:
        payload = dict(source)
        payload.setdefault("schema_version", "0.3.0")
        payload["attestation_issuer"] = self.issuer
        payload["attestation"] = hmac.new(self._secret, _material(payload), sha256).hexdigest()
        return payload


class EvidenceVerifier:
    def __init__(self, trusted_keys: Mapping[str, bytes], scope: str, max_age: int,
                 canonical_claims: frozenset[str]) -> None:
        if not scope or max_age < 0:
            raise ContractViolation("evidence scope and non-negative max age are required")
        self._trusted_keys = {issuer: bytes(key) for issuer, key in trusted_keys.items()}
        if not canonical_claims:
            raise ContractViolation("at least one governed canonical claim is required")
        self.scope, self.max_age, self.canonical_claims = scope, max_age, canonical_claims

    def verify(self, source: Mapping[str, Any], *, now: int) -> tuple[bool, str]:
        required = {
            "source_id": str, "content": str, "observed_at": int,
            "root_provenance": str, "evidence_class": str, "scope": str,
            "correlation_id": str, "claim_key": str, "polarity": int,
            "attestation_issuer": str, "attestation": str,
            "schema_version": str,
        }
        for field, expected_type in required.items():
            value = source.get(field)
            if not isinstance(value, expected_type) or isinstance(value, bool) or (
                expected_type is str and not value.strip()
            ):
                return False, f"SOURCE_FIELD_INVALID:{field}"
        key = self._trusted_keys.get(source["attestation_issuer"])
        if key is None or len(key) < 32:
            return False, "SOURCE_ISSUER_UNTRUSTED"
        expected = hmac.new(key, _material(source), sha256).hexdigest()
        checks = (
            (hmac.compare_digest(expected, source["attestation"]), "SOURCE_ATTESTATION_INVALID"),
            (source["schema_version"] == "0.3.0", "SOURCE_SCHEMA_UNSUPPORTED"),
            (source["scope"] == self.scope, "SOURCE_SCOPE_MISMATCH"),
            (source["evidence_class"] == "OBSERVED", "SOURCE_CLASS_INADMISSIBLE"),
            (source["polarity"] in (-1, 1), "SOURCE_POLARITY_INVALID"),
            (source["claim_key"] in self.canonical_claims, "SOURCE_CLAIM_UNKNOWN"),
            (0 <= source["observed_at"] <= now, "SOURCE_TIME_INVALID"),
            (now - source["observed_at"] <= self.max_age, "SOURCE_STALE"),
        )
        for valid, reason in checks:
            if not valid:
                return False, reason
        return True, "SOURCE_VERIFIED"
