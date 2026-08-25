from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class ContextRecord:
    event_id: str
    engine_id: str
    contract_id: str
    agent: str
    temporal_state: str
    relation: str
    provenance: str
    contradiction: str = "none"

@dataclass(frozen=True)
class Observation:
    execution_id: str
    engine_id: str
    contract_id: str
    selected_ids: tuple[str, ...]
    status: str

class ContextEngine:
    def __init__(self, engine_id: str):
        if not engine_id:
            raise ValueError("engine_id required")
        self.engine_id = engine_id

    def execute(self, execution_id: str, contract_id: str, records: Iterable[ContextRecord], *, agent: str, temporal_state: str, relation: str) -> Observation:
        if not execution_id or not contract_id:
            raise ValueError("execution_id and contract_id required")
        selected = tuple(sorted(
            r.event_id for r in records
            if r.engine_id == self.engine_id
            and r.contract_id == contract_id
            and r.agent == agent
            and r.temporal_state == temporal_state
            and r.relation == relation
            and bool(r.provenance)
            and r.contradiction in {"none", "explicit"}
        ))
        return Observation(execution_id, self.engine_id, contract_id, selected, "EXECUTED")
