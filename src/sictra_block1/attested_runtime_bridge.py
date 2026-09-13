"""Bounded handoff of current durable evidence into the E01–E08 runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .attested_evidence_store import AttestedEvidenceStore
from .common import AuthorityContext, ContractViolation, Envelope, plain_copy
from .runtime import IntelligenceRuntime


class AttestedRuntimeBridgeViolation(ContractViolation):
    """A runtime invocation is not safely bound to current stored evidence."""


@dataclass(frozen=True, slots=True)
class AttestedRuntimeResult:
    """Runtime result accompanied by receipt summaries for its evidence input."""

    envelope: Envelope
    evidence_receipts: tuple[Mapping[str, Any], ...]


class AttestedRuntimeBridge:
    """Read current evidence once, then hand off precisely that set to runtime."""

    def __init__(self, evidence_store: AttestedEvidenceStore, runtime: IntelligenceRuntime) -> None:
        if not isinstance(evidence_store, AttestedEvidenceStore) or not isinstance(runtime, IntelligenceRuntime):
            raise AttestedRuntimeBridgeViolation("bridge requires an evidence store and intelligence runtime")
        self._evidence_store = evidence_store
        self._runtime = runtime

    @staticmethod
    def _text(name: str, value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise AttestedRuntimeBridgeViolation(f"{name} must be a non-empty string")
        return value.strip()

    @staticmethod
    def _time(value: object) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise AttestedRuntimeBridgeViolation("bridge time must be a non-negative integer")
        return value

    def run(
        self, *, task_id: object, run_id: object, objective: object,
        authority: AuthorityContext | None, now: object,
    ) -> AttestedRuntimeResult:
        trusted_now = self._time(now)
        if self._runtime._trusted_now() != trusted_now:
            raise AttestedRuntimeBridgeViolation("runtime and evidence-store clocks disagree")
        evidence = self._evidence_store.runtime_records(now=trusted_now)
        receipts = self._evidence_store.list_receipts(now=trusted_now)
        current_receipts = [receipt for receipt in receipts if receipt["status"] == "CURRENT"]
        if not evidence:
            raise AttestedRuntimeBridgeViolation("no current attested evidence is available")
        if len(evidence) != len(current_receipts):
            raise AttestedRuntimeBridgeViolation("evidence-store current receipt set is inconsistent")
        envelope = self._runtime.run(
            task_id=self._text("task_id", task_id), run_id=self._text("run_id", run_id),
            objective=self._text("objective", objective), sources=evidence, authority=authority,
        )
        return AttestedRuntimeResult(
            envelope=envelope,
            evidence_receipts=tuple(plain_copy(receipt) for receipt in current_receipts),
        )
