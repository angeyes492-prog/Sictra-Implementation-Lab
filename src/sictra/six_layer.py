from dataclasses import dataclass

@dataclass(frozen=True)
class LayerObject:
    object_id: str
    logical_key: str
    layer: str
    agent: str
    temporal_state: str
    epistemic_class: str
    provenance_root: str
    version: int = 1
    parent_ids: tuple[str, ...] = ()

@dataclass(frozen=True)
class LayerEdge:
    source_id: str
    target_id: str
    relation_type: str
    temporal_state: str = "CURRENT"

@dataclass(frozen=True)
class SixLayerResult:
    selected_ids: tuple[str, ...]
    dependency_ids: tuple[str, ...]
    historical_ids: tuple[str, ...]
    independent_roots: tuple[str, ...]
    promotion_authorized: bool = False


def temporal_partitions(objects):
    current=tuple(sorted((o for o in objects if o.temporal_state=="CURRENT"),key=lambda x:x.object_id))
    historical=tuple(sorted((o for o in objects if o.temporal_state!="CURRENT"),key=lambda x:x.object_id))
    return current,historical


def latest_current(objects):
    current,_=temporal_partitions(objects)
    best={}
    for obj in current:
        prior=best.get(obj.logical_key)
        if prior is None or obj.version>prior.version:
            best[obj.logical_key]=obj
    return tuple(sorted(best.values(),key=lambda x:x.object_id))


def epistemic_is_fact(obj: LayerObject) -> bool:
    return obj.epistemic_class=="FACT"


def dependency_closure(seed_ids, edges):
    reached=set(seed_ids); dependencies=set(); changed=True
    while changed:
        changed=False
        for edge in edges:
            if edge.temporal_state!="CURRENT" or edge.relation_type!="REQUIRES":
                continue
            if edge.source_id in reached and edge.target_id not in reached:
                reached.add(edge.target_id); dependencies.add(edge.target_id); changed=True
    return tuple(sorted(dependencies))


def lineage_descendants(seed_ids, objects):
    current=latest_current(objects); impacted=set(seed_ids); changed=True
    while changed:
        changed=False
        for obj in current:
            if obj.object_id not in impacted and any(parent in impacted for parent in obj.parent_ids):
                impacted.add(obj.object_id); changed=True
    return tuple(sorted(impacted-set(seed_ids)))


def proactive_context(objects, edges, agent, changed_ids):
    current=latest_current(objects)
    current_ids={o.object_id for o in current}
    seeds={x for x in changed_ids if x in current_ids}
    impacted=set(seeds)
    impacted.update(lineage_descendants(tuple(seeds),current))
    impacted.update(dependency_closure(tuple(impacted),edges))
    candidates=[o for o in current if o.object_id in impacted and o.agent in {agent,"SHARED"}]
    # Repeated/contextual records from the same logical signal and provenance root collapse.
    unique={}
    for obj in candidates:
        key=(obj.logical_key,obj.provenance_root)
        prior=unique.get(key)
        if prior is None or obj.version>prior.version:
            unique[key]=obj
    return tuple(sorted(unique.values(),key=lambda x:x.object_id))


def evaluate_six_layer(objects, edges, agent, changed_ids):
    selected=proactive_context(objects,edges,agent,changed_ids)
    _,historical=temporal_partitions(objects)
    selected_ids=tuple(o.object_id for o in selected)
    deps=dependency_closure(selected_ids,edges)
    roots=tuple(sorted({o.provenance_root for o in selected if o.epistemic_class in {"FACT","EVIDENCE"} and o.provenance_root}))
    return SixLayerResult(selected_ids,deps,tuple(o.object_id for o in historical),roots,False)
