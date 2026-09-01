def expected_fabric(records, relations, agent):
    valid=[]
    required=("what","why","source","when","version","scope","status","confidence","contradictions","dependencies","unknowns","reassessment_state","related_agents","related_tools")
    for r in records:
        if any(getattr(r,k) is None or (isinstance(getattr(r,k),str) and not getattr(r,k).strip()) for k in required): continue
        p=r.provenance
        if not p.source_identity or not p.root_provenance or not p.temporal_scope or not p.evidence_class or p.derivation_graph is None: continue
        if agent not in r.related_agents: continue
        valid.append(r)
    current=tuple(sorted(r.record_id for r in valid if r.provenance.temporal_scope=="CURRENT"))
    historical=tuple(sorted(r.record_id for r in valid if r.provenance.temporal_scope!="CURRENT"))
    contradictions=tuple(sorted(r.record_id for r in valid if r.contradictions))
    ids={r.record_id for r in valid}
    dependencies=tuple(sorted((x.source_id,x.target_id,x.relation_type) for x in relations if x.source_id in ids and x.relation_type=="REQUIRES"))
    related=tuple(sorted((x.source_id,x.target_id,x.relation_type) for x in relations if x.source_id in ids and x.relation_type=="RELATED_TO"))
    roots={(r.provenance.source_identity,r.provenance.root_provenance) for r in valid if r.provenance.temporal_scope=="CURRENT" and r.provenance.evidence_class in {"RUNTIME","OBSERVED"}}
    return {"current":current,"historical":historical,"contradictions":contradictions,"dependencies":dependencies,"related":related,"independent_evidence_count":len(roots)}
