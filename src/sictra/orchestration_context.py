from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class OrchestrationItem:
    item_id: str
    agent: str
    kind: str
    temporal_state: str
    provenance: str
    authority_requested: bool
    dependency_ids: tuple[str, ...]
    content: str

@dataclass(frozen=True)
class OrchestrationContextPack:
    current_state: tuple[OrchestrationItem, ...]
    open_work: tuple[OrchestrationItem, ...]
    dependencies: tuple[OrchestrationItem, ...]
    blockers: tuple[OrchestrationItem, ...]
    historical_blockers: tuple[OrchestrationItem, ...]
    capabilities: tuple[OrchestrationItem, ...]
    evidence: tuple[OrchestrationItem, ...]
    reassessment_requirements: tuple[OrchestrationItem, ...]
    pending_decisions: tuple[OrchestrationItem, ...]
    missing_dependencies: tuple[str, ...]
    authority_violations: tuple[str, ...]
    execution_authorized: bool = False
    gate_promotion_authorized: bool = False

MAP={"STATE":"current_state","WORK":"open_work","DEPENDENCY":"dependencies","BLOCKER":"blockers","CAPABILITY":"capabilities","EVIDENCE":"evidence","REASSESSMENT":"reassessment_requirements","DECISION":"pending_decisions"}

def assemble_orchestration_context(items: Iterable[OrchestrationItem]) -> OrchestrationContextPack:
    scoped=[x for x in items if x.agent=="Orchestration"]
    ids={x.item_id for x in scoped}; buckets={k:[] for k in (*MAP.values(),"historical_blockers")}; missing=set(); authority=[]
    for x in scoped:
        if x.authority_requested: authority.append(x.item_id)
        for dep in x.dependency_ids:
            if dep not in ids: missing.add(dep)
        if x.kind=="ACTION": continue
        if x.kind=="BLOCKER" and x.temporal_state!="CURRENT": buckets["historical_blockers"].append(x); continue
        target=MAP.get(x.kind)
        if target and x.temporal_state=="CURRENT": buckets[target].append(x)
    return OrchestrationContextPack(**{k:tuple(sorted(v,key=lambda x:x.item_id)) for k,v in buckets.items()},missing_dependencies=tuple(sorted(missing)),authority_violations=tuple(sorted(authority)))
