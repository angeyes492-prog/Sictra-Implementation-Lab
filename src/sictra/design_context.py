from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class DesignItem:
    item_id: str
    agent: str
    category: str
    temporal_state: str
    provenance: str
    content: str

@dataclass(frozen=True)
class DesignContextPack:
    architecture: tuple[DesignItem, ...]
    contracts: tuple[DesignItem, ...]
    dependencies: tuple[DesignItem, ...]
    constraints: tuple[DesignItem, ...]
    historical_decisions: tuple[DesignItem, ...]
    contradictions: tuple[DesignItem, ...]
    open_questions: tuple[DesignItem, ...]
    implementation_implications: tuple[DesignItem, ...]
    unknowns: tuple[DesignItem, ...]
    acceptance_authority: bool = False

MAP = {"ARCHITECTURE":"architecture", "CONTRACT":"contracts", "DEPENDENCY":"dependencies", "CONSTRAINT":"constraints", "CONTRADICTION":"contradictions", "QUESTION":"open_questions", "IMPLICATION":"implementation_implications", "UNKNOWN":"unknowns"}

def assemble_design_context(items: Iterable[DesignItem]) -> DesignContextPack:
    buckets={k:[] for k in (*MAP.values(),"historical_decisions")}
    for item in items:
        if item.agent != "Design": continue
        if item.category == "DECISION":
            if item.temporal_state in {"HISTORICAL","STALE","SUPERSEDED"}: buckets["historical_decisions"].append(item)
            continue
        target=MAP.get(item.category)
        if target and item.temporal_state == "CURRENT": buckets[target].append(item)
    return DesignContextPack(**{k:tuple(sorted(v,key=lambda x:x.item_id)) for k,v in buckets.items()})
