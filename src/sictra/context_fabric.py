from dataclasses import dataclass
from .context_integrity import MaterialContextRecord, validate_integrity, independent_evidence_count

@dataclass(frozen=True)
class FabricRelation:
    source_id: str
    target_id: str
    relation_type: str

@dataclass(frozen=True)
class AgentContextPack:
    agent: str
    current: tuple[MaterialContextRecord, ...]
    historical: tuple[MaterialContextRecord, ...]
    contradictions: tuple[MaterialContextRecord, ...]
    dependencies: tuple[FabricRelation, ...]
    related: tuple[FabricRelation, ...]
    independent_evidence_count: int
    promotion_authority: bool = False
    verification_authority: bool = False


def prepare_agent_context(records: tuple[MaterialContextRecord,...], relations: tuple[FabricRelation,...], agent: str) -> AgentContextPack:
    scoped=[]
    for r in records:
        ok,_=validate_integrity(r)
        if not ok:
            continue
        if agent not in r.related_agents:
            continue
        scoped.append(r)
    current=tuple(sorted((r for r in scoped if r.provenance.temporal_scope=="CURRENT"),key=lambda x:x.record_id))
    historical=tuple(sorted((r for r in scoped if r.provenance.temporal_scope!="CURRENT"),key=lambda x:x.record_id))
    contradictions=tuple(sorted((r for r in scoped if r.contradictions),key=lambda x:x.record_id))
    ids={r.record_id for r in scoped}
    deps=tuple(sorted((x for x in relations if x.relation_type=="REQUIRES" and x.source_id in ids),key=lambda x:(x.source_id,x.target_id)))
    related=tuple(sorted((x for x in relations if x.relation_type=="RELATED_TO" and x.source_id in ids),key=lambda x:(x.source_id,x.target_id)))
    return AgentContextPack(agent,current,historical,contradictions,deps,related,independent_evidence_count(tuple(scoped)))


def fabric_signature(pack: AgentContextPack) -> tuple:
    return (
        pack.agent,
        tuple(r.record_id for r in pack.current),
        tuple(r.record_id for r in pack.historical),
        tuple(r.record_id for r in pack.contradictions),
        tuple((r.source_id,r.target_id,r.relation_type) for r in pack.dependencies),
        tuple((r.source_id,r.target_id,r.relation_type) for r in pack.related),
        pack.independent_evidence_count,
        pack.promotion_authority,
        pack.verification_authority,
    )
