def oracle_latest(objects):
    groups={}
    for o in objects:
        if o.temporal_state!="CURRENT": continue
        current=groups.get(o.logical_key)
        if current is None or o.version>current.version: groups[o.logical_key]=o
    return tuple(sorted(groups.values(),key=lambda x:x.object_id))

def oracle_dependency(seed_ids,edges):
    known=set(seed_ids); out=set()
    while True:
        additions={e.target_id for e in edges if e.temporal_state=="CURRENT" and e.relation_type=="REQUIRES" and e.source_id in known and e.target_id not in known}
        if not additions: break
        known|=additions; out|=additions
    return tuple(sorted(out))

def oracle_proactive(objects,edges,agent,changed_ids):
    current=oracle_latest(objects); ids={o.object_id for o in current}; impacted={x for x in changed_ids if x in ids}
    while True:
        additions={o.object_id for o in current if any(p in impacted for p in o.parent_ids)} | set(oracle_dependency(tuple(impacted),edges))
        new=additions-impacted
        if not new: break
        impacted|=new
    scoped=[o for o in current if o.object_id in impacted and o.agent in {agent,"SHARED"}]
    keys={}
    for o in scoped:
        k=(o.logical_key,o.provenance_root); p=keys.get(k)
        if p is None or o.version>p.version: keys[k]=o
    return tuple(sorted(o.object_id for o in keys.values()))
