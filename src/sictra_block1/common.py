"""Shared, authority-safe contracts for the Block 1 reference runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass, replace
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Any, Literal, Mapping

EpistemicState = Literal[
    "VERIFIED", "PROBABLE", "PLAUSIBLE", "UNCONFIRMED",
    "CONTRADICTED", "INSUFFICIENT EVIDENCE",
]


class ContractViolation(ValueError):
    pass


class IdentityCollision(ContractViolation):
    pass


@dataclass(frozen=True, slots=True)
class AuthorityContext:
    issuer: str
    epoch: int
    scope: tuple[str, ...]
    expires_at: int
    committed: bool = False

    def permits(self, action: str, now: int, known_epoch: int) -> bool:
        return (
            bool(self.issuer)
            and self.committed
            and self.epoch == known_epoch
            and now <= self.expires_at
            and action in self.scope
        )


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set):
        return tuple(sorted(_freeze(item) for item in value))
    return value


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _canonical(value: Any) -> str:
    return json.dumps(_plain(value), sort_keys=True, separators=(",", ":"))


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
        required = (self.message_id, self.task_id, self.run_id, self.producer,
                    self.consumer, self.contract_version, self.root_provenance)
        if any(not item for item in required):
            raise ContractViolation("required envelope identity is missing")
        if not self.contract_version.startswith("0.2."):
            raise ContractViolation("unsupported contract version")
        if not self.lineage or self.lineage[0] != self.root_provenance:
            raise ContractViolation("lineage must begin at root_provenance")

    @property
    def fingerprint(self) -> str:
        material = {
            "message_id": self.message_id, "task_id": self.task_id,
            "run_id": self.run_id, "producer": self.producer,
            "consumer": self.consumer, "contract_version": self.contract_version,
            "logical_time": self.logical_time, "payload": self.payload,
            "root_provenance": self.root_provenance, "lineage": self.lineage,
            "epistemic_state": self.epistemic_state,
            "uncertainty": self.uncertainty, "restrictions": self.restrictions,
            "authority": self.authority, "trace": self.trace,
        }
        return sha256(_canonical(material).encode()).hexdigest()

    def handoff(self, producer: str, consumer: str, payload: Mapping[str, Any],
                *, state: EpistemicState | None = None,
                uncertainty: tuple[str, ...] | None = None,
                restrictions: tuple[str, ...] | None = None) -> "Envelope":
        step = f"{producer}->{consumer}"
        return replace(
            self, message_id=f"{self.run_id}:{len(self.trace)+1}:{consumer}",
            producer=producer, consumer=consumer, logical_time=self.logical_time + 1,
            payload=dict(payload), lineage=self.lineage + (self.message_id,),
            epistemic_state=state or self.epistemic_state,
            uncertainty=self.uncertainty if uncertainty is None else uncertainty,
            restrictions=self.restrictions if restrictions is None else restrictions,
            trace=self.trace + (step,),
        )
