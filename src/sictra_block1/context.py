"""Context selection with epistemic and provenance preservation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

TemporalState = Literal["CURRENT", "HISTORICAL", "STALE"]
Eligibility = Literal["IN_SCOPE", "OUT_OF_SCOPE", "BLOCKED"]
EvidenceClass = Literal["OBSERVED", "SYNTHETIC", "ADVERSARIAL", "DERIVED"]


class ContractViolation(ValueError):
    """A record cannot enter the bounded context path."""


@dataclass(frozen=True, slots=True)
class ContextRecord:
    """A context record whose provenance is immutable through transformation."""

    record_id: str
    agent: str
    layer: str
    temporal_state: TemporalState
    selectable: bool
    context_eligibility: Eligibility | None
    contradiction_state: Literal["NONE", "OPEN", "RESOLVED"] | None
    relation_type: str
    source_identity: str
    root_provenance: str
    derivation_graph: tuple[str, ...]
    temporal_scope: str
    evidence_class: EvidenceClass
    notes: str = ""

    @property
    def is_current_and_in_scope(self) -> bool:
        """Support legacy records without silently treating an explicit block as allowed."""
        return self.temporal_state == "CURRENT" and self.context_eligibility in {
            None,
            "IN_SCOPE",
        }

    def validate(self) -> None:
        required = {
            "record_id": self.record_id,
            "source_identity": self.source_identity,
            "root_provenance": self.root_provenance,
            "temporal_scope": self.temporal_scope,
            "evidence_class": self.evidence_class,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ContractViolation(f"missing required provenance fields: {', '.join(missing)}")
        if not self.derivation_graph:
            raise ContractViolation("derivation_graph must preserve at least the root identity")
        if self.derivation_graph[0] != self.root_provenance:
            raise ContractViolation("derivation_graph must begin at root_provenance")


@dataclass(frozen=True, slots=True)
class ContextPack:
    """Selection result, retaining eligible open contradictions rather than resolving them."""

    target_agent: str
    records: tuple[ContextRecord, ...]
    excluded_record_ids: tuple[str, ...]

    @property
    def open_contradictions(self) -> tuple[ContextRecord, ...]:
        return tuple(record for record in self.records if record.contradiction_state == "OPEN")


def build_context_pack(records: Iterable[ContextRecord], target_agent: str) -> ContextPack:
    """Select current, selectable, in-scope records for exactly one agent.

    Open contradictions are included; selection is not resolution. Historical,
    stale, explicit out-of-scope, blocked, foreign-agent, and unselectable
    records are excluded from the current pack but remain available to callers
    as source records for later reassessment lineage.
    """
    included: list[ContextRecord] = []
    excluded: list[str] = []
    for record in records:
        record.validate()
        if record.agent == target_agent and record.selectable and record.is_current_and_in_scope:
            included.append(record)
        else:
            excluded.append(record.record_id)
    return ContextPack(target_agent, tuple(included), tuple(excluded))
