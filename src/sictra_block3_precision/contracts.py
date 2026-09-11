"""Shared contracts for the bounded Precision Intelligence M01-M05 runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import json
from typing import Any, Literal, Mapping


EpistemicState = Literal[
    "VERIFIED", "PROBABLE", "PLAUSIBLE", "UNCONFIRMED",
    "CONTRADICTED", "INSUFFICIENT EVIDENCE",
]
Confidence = Literal["A", "B", "C", "D", "E"]
TemporalState = Literal["CURRENT", "HISTORICAL", "STALE", "SUPERSEDED"]
Disposition = Literal["ACCEPTED", "PARTIAL", "CONTRADICTED", "RETURN_UPSTREAM"]

EPISTEMIC_STATES = frozenset(EpistemicState.__args__)
CONFIDENCE_VALUES = frozenset(Confidence.__args__)
TEMPORAL_STATES = frozenset(TemporalState.__args__)
CONFIDENCE_RANK = {value: index for index, value in enumerate(("A", "B", "C", "D", "E"))}


class PrecisionContractViolation(ValueError):
    """An object cannot safely cross a Precision Intelligence boundary."""


class PrecisionIdentityCollision(PrecisionContractViolation):
    """An identity was reused for materially different content."""


class PrecisionCapacityExceeded(PrecisionContractViolation):
    """A bounded engine received more objects than its contract permits."""


def require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise PrecisionContractViolation(f"{name} must be a non-empty string")


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def fingerprint(value: Any) -> str:
    material = json.dumps(
        _plain(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    )
    return sha256(material.encode("utf-8")).hexdigest()


def weakest_confidence(values: tuple[str, ...]) -> Confidence:
    if not values or any(value not in CONFIDENCE_VALUES for value in values):
        return "E"
    return max(values, key=CONFIDENCE_RANK.__getitem__)  # type: ignore[return-value]


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    """Immutable identity and epistemic metadata for one supporting record."""

    evidence_id: str
    source_identity: str
    root_provenance: str
    observed_at: int
    temporal_state: TemporalState
    epistemic_state: EpistemicState
    confidence: Confidence
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("evidence_id", "source_identity", "root_provenance"):
            require_text(name, getattr(self, name))
        if not isinstance(self.observed_at, int) or isinstance(self.observed_at, bool):
            raise PrecisionContractViolation("observed_at must be an integer timestamp")
        if self.observed_at < 0:
            raise PrecisionContractViolation("observed_at cannot be negative")
        if self.temporal_state not in TEMPORAL_STATES:
            raise PrecisionContractViolation("temporal_state is not governed")
        if self.epistemic_state not in EPISTEMIC_STATES:
            raise PrecisionContractViolation("epistemic_state is not governed")
        if self.confidence not in CONFIDENCE_VALUES:
            raise PrecisionContractViolation("confidence is not governed")
        object.__setattr__(self, "provenance_refs", tuple(self.provenance_refs))
        if not self.provenance_refs or any(
            not isinstance(item, str) or not item.strip() for item in self.provenance_refs
        ):
            raise PrecisionContractViolation("provenance_refs must preserve source lineage")
        if self.provenance_refs[0] != self.root_provenance:
            raise PrecisionContractViolation("provenance_refs must begin at root_provenance")

    def current_at(self, now: int) -> bool:
        return self.temporal_state == "CURRENT" and self.observed_at <= now


@dataclass(frozen=True, slots=True)
class EngineAssessment:
    engine: str
    disposition: Disposition
    reasons: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    output_fingerprint: str | None

    def __post_init__(self) -> None:
        require_text("engine", self.engine)
        object.__setattr__(self, "reasons", tuple(self.reasons))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


def validate_identity_set(items: tuple[Any, ...], *, id_attribute: str, limit: int) -> None:
    if len(items) > limit:
        raise PrecisionCapacityExceeded(f"record count exceeds bounded limit {limit}")
    seen: dict[str, str] = {}
    for item in items:
        identity = getattr(item, id_attribute, None)
        require_text(id_attribute, identity)
        current = fingerprint(item)
        prior = seen.get(identity)
        if prior is not None and prior != current:
            raise PrecisionIdentityCollision(
                f"{id_attribute} {identity!r} was reused for different content"
            )
        seen[identity] = current
