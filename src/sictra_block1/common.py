"""Security and transport contracts for the bounded operational runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass, replace
from hashlib import sha256
import hmac
import json
import math
import re
import secrets
from types import MappingProxyType
from typing import Any, Literal, Mapping

EpistemicState = Literal[
    "VERIFIED", "PROBABLE", "PLAUSIBLE", "UNCONFIRMED",
    "CONTRADICTED", "INSUFFICIENT EVIDENCE",
]
_VERSION = re.compile(r"0\.3\.\d+")
_SUPPORTED_VERSIONS = {"0.3.0"}
_EPISTEMIC_STATES = {
    "VERIFIED", "PROBABLE", "PLAUSIBLE", "UNCONFIRMED",
    "CONTRADICTED", "INSUFFICIENT EVIDENCE",
}


class ContractViolation(ValueError):
    """Input cannot cross a Block 1 contract boundary."""


class IdentityCollision(ContractViolation):
    """One identity was reused for materially different content."""


class CapacityExceeded(ContractViolation):
    """A bounded operational store or cache reached its configured capacity."""


def _freeze(value: Any, *, depth: int = 0) -> Any:
    if depth > 32:
        raise ContractViolation("payload nesting exceeds 32 levels")
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ContractViolation("payload contains non-finite number")
        return value
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise ContractViolation("payload keys must be strings")
        return MappingProxyType({key: _freeze(item, depth=depth + 1) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item, depth=depth + 1) for item in value)
    raise ContractViolation(f"payload type is not contract-safe: {type(value).__name__}")


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _canonical(value: Any) -> str:
    return json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True, slots=True)
class AuthorityContext:
    issuer: str
    audience: str
    task_id: str
    run_id: str
    actions: tuple[str, ...]
    epoch: int
    issued_at: int
    not_before: int
    expires_at: int
    nonce: str
    committed: bool
    signature: str

    def __post_init__(self) -> None:
        if isinstance(self.actions, (str, bytes)):
            raise ContractViolation("authority actions must be a collection of strings")
        object.__setattr__(self, "actions", tuple(self.actions))
        text_fields = (self.issuer, self.audience, self.task_id, self.run_id, self.nonce)
        if any(not isinstance(item, str) or not item.strip() for item in text_fields):
            raise ContractViolation("authority identities and nonce must be non-empty strings")
        if not self.actions or any(not isinstance(item, str) or not item for item in self.actions):
            raise ContractViolation("authority actions must be non-empty strings")
        if any(not isinstance(item, int) or isinstance(item, bool) for item in (
            self.epoch, self.issued_at, self.not_before, self.expires_at
        )):
            raise ContractViolation("authority epoch and times must be integers")
        if not isinstance(self.committed, bool):
            raise ContractViolation("authority committed must be boolean")
        if not isinstance(self.signature, str) or not re.fullmatch(r"[0-9a-f]{64}", self.signature):
            raise ContractViolation("authority signature must be 64 lowercase hex characters")

    def signing_material(self) -> str:
        return _canonical({key: value for key, value in asdict(self).items() if key != "signature"})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AuthorityContext":
        payload = dict(value)
        payload["actions"] = tuple(payload["actions"])
        return cls(**payload)


class AuthorityIssuer:
    """Trusted-side HMAC issuer for the bounded adapter; not a production KMS."""

    def __init__(self, issuer: str, secret: bytes, audience: str, epoch: int) -> None:
        if not issuer or len(secret) < 32 or not audience or epoch < 1:
            raise ContractViolation("issuer requires identity, 32-byte key, audience, and positive epoch")
        self.issuer, self._secret, self.audience, self.epoch = issuer, bytes(secret), audience, epoch

    def issue(self, *, task_id: str, run_id: str, actions: tuple[str, ...], now: int,
              ttl: int, committed: bool = True, nonce: str | None = None,
              not_before: int | None = None) -> AuthorityContext:
        if not task_id or not run_id or not actions or ttl < 1:
            raise ContractViolation("authority scope, identities, and positive ttl are required")
        effective_from = now if not_before is None else not_before
        unsigned = AuthorityContext(self.issuer, self.audience, task_id, run_id, actions,
            self.epoch, now, effective_from, now + ttl,
            nonce or secrets.token_hex(16), committed, "0" * 64)
        signature = hmac.new(self._secret, unsigned.signing_material().encode(), sha256).hexdigest()
        return replace(unsigned, signature=signature)


class AuthorityVerifier:
    def __init__(self, trusted_keys: Mapping[str, bytes], audience: str, known_epoch: int,
                 revoked_nonces: frozenset[str] = frozenset()) -> None:
        if not audience or known_epoch < 1:
            raise ContractViolation("verifier audience and positive epoch are required")
        self._trusted_keys = {issuer: bytes(key) for issuer, key in trusted_keys.items()}
        self.audience, self.known_epoch, self.revoked_nonces = audience, known_epoch, revoked_nonces

    def verify(self, authority: AuthorityContext | None, envelope: "Envelope",
               action: str, now: int) -> tuple[bool, str]:
        if authority is None:
            return False, "AUTHORITY_MISSING"
        key = self._trusted_keys.get(authority.issuer)
        if key is None or len(key) < 32:
            return False, "ISSUER_UNTRUSTED"
        expected = hmac.new(key, authority.signing_material().encode(), sha256).hexdigest()
        checks = (
            (hmac.compare_digest(expected, authority.signature), "SIGNATURE_INVALID"),
            (authority.audience == self.audience, "AUDIENCE_MISMATCH"),
            (authority.task_id == envelope.task_id, "TASK_BINDING_MISMATCH"),
            (authority.run_id == envelope.run_id, "RUN_BINDING_MISMATCH"),
            (authority.epoch == self.known_epoch, "EPOCH_INVALID"),
            (authority.issued_at <= authority.not_before <= authority.expires_at, "TIME_WINDOW_INVALID"),
            (authority.not_before <= now <= authority.expires_at, "AUTHORITY_NOT_CURRENT"),
            (authority.nonce not in self.revoked_nonces, "AUTHORITY_REVOKED"),
            (authority.committed, "AUTHORITY_NOT_COMMITTED"),
            (action in authority.actions, "ACTION_OUT_OF_SCOPE"),
        )
        for valid, reason in checks:
            if not valid:
                return False, reason
        return True, "AUTHORITY_VERIFIED"


@dataclass(frozen=True, slots=True)
class Envelope:
    message_id: str
    task_id: str
    run_id: str
    producer: str
    consumer: str
    contract_version: str
    logical_time: int
    payload: Mapping[str, Any]
    root_provenance: str
    lineage: tuple[str, ...]
    epistemic_state: EpistemicState = "UNCONFIRMED"
    uncertainty: tuple[str, ...] = ()
    restrictions: tuple[str, ...] = ()
    authority: AuthorityContext | None = None
    trace: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", _freeze(dict(self.payload)))
        object.__setattr__(self, "lineage", tuple(self.lineage))
        object.__setattr__(self, "uncertainty", tuple(self.uncertainty))
        object.__setattr__(self, "restrictions", tuple(self.restrictions))
        object.__setattr__(self, "trace", tuple(self.trace))
        for field_name in ("lineage", "uncertainty", "restrictions", "trace"):
            values = getattr(self, field_name)
            if any(not isinstance(item, str) or not item for item in values):
                raise ContractViolation(f"{field_name} must contain non-empty strings")
        required = (self.message_id, self.task_id, self.run_id, self.producer,
                    self.consumer, self.contract_version, self.root_provenance)
        if any(not isinstance(item, str) or not item.strip() for item in required):
            raise ContractViolation("required envelope identity is missing or invalid")
        if not _VERSION.fullmatch(self.contract_version) or self.contract_version not in _SUPPORTED_VERSIONS:
            raise ContractViolation("unsupported or malformed contract version")
        if (not isinstance(self.logical_time, int) or isinstance(self.logical_time, bool)
                or self.logical_time < 0):
            raise ContractViolation("logical_time cannot be negative")
        if self.epistemic_state not in _EPISTEMIC_STATES:
            raise ContractViolation("epistemic_state is outside the governed vocabulary")
        if not self.lineage or self.lineage[0] != self.root_provenance:
            raise ContractViolation("lineage must begin at root_provenance")
        if len(_canonical(self.payload).encode()) > 5_000_000:
            raise ContractViolation("payload exceeds 5 MB")

    @property
    def fingerprint(self) -> str:
        return sha256(_canonical(self.to_dict()).encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id, "task_id": self.task_id, "run_id": self.run_id,
            "producer": self.producer, "consumer": self.consumer,
            "contract_version": self.contract_version, "logical_time": self.logical_time,
            "payload": _plain(self.payload), "root_provenance": self.root_provenance,
            "lineage": list(self.lineage), "epistemic_state": self.epistemic_state,
            "uncertainty": list(self.uncertainty), "restrictions": list(self.restrictions),
            "authority": self.authority.to_dict() if self.authority else None,
            "trace": list(self.trace),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Envelope":
        payload = dict(value)
        payload["lineage"] = tuple(payload["lineage"])
        payload["uncertainty"] = tuple(payload.get("uncertainty", ()))
        payload["restrictions"] = tuple(payload.get("restrictions", ()))
        payload["trace"] = tuple(payload.get("trace", ()))
        if payload.get("authority"):
            payload["authority"] = AuthorityContext.from_dict(payload["authority"])
        return cls(**payload)

    def handoff(self, producer: str, consumer: str, payload: Mapping[str, Any],
                *, state: EpistemicState | None = None,
                uncertainty: tuple[str, ...] | None = None,
                restrictions: tuple[str, ...] | None = None) -> "Envelope":
        if self.consumer != producer:
            raise ContractViolation(f"handoff producer {producer} does not own consumer boundary {self.consumer}")
        return replace(
            self, message_id=(
                f"{self.task_id}:{self.run_id}:"
                f"{sha256(self.root_provenance.encode()).hexdigest()[:16]}:"
                f"{len(self.trace)+1}:{consumer}"
            ),
            producer=producer, consumer=consumer, logical_time=self.logical_time + 1,
            payload=dict(payload), lineage=self.lineage + (self.message_id,),
            epistemic_state=state or self.epistemic_state,
            uncertainty=self.uncertainty if uncertainty is None else uncertainty,
            restrictions=self.restrictions if restrictions is None else restrictions,
            trace=self.trace + (f"{producer}->{consumer}",),
        )


def immutable_copy(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return _freeze(_plain(value))


def plain_copy(value: Any) -> Any:
    return _plain(value)
