def expected_orchestration(items):
    scoped=[x for x in items if x.agent=="Orchestration"]; ids={x.item_id for x in scoped}
    mapping={"STATE":"current_state","WORK":"open_work","DEPENDENCY":"dependencies","BLOCKER":"blockers","CAPABILITY":"capabilities","EVIDENCE":"evidence","REASSESSMENT":"reassessment_requirements","DECISION":"pending_decisions"}
    out={"current_state":[],"open_work":[],"dependencies":[],"blockers":[],"historical_blockers":[],"capabilities":[],"evidence":[],"reassessment_requirements":[],"pending_decisions":[]}; missing=set(); authority=[]
    for x in scoped:
        if x.authority_requested: authority.append(x.item_id)
        missing.update(d for d in x.dependency_ids if d not in ids)
        if x.kind=="ACTION": continue
        if x.kind=="BLOCKER" and x.temporal_state!="CURRENT": out["historical_blockers"].append(x.item_id)
        elif x.temporal_state=="CURRENT" and x.kind in mapping: out[mapping[x.kind]].append(x.item_id)
    return {**{k:tuple(sorted(v)) for k,v in out.items()},"missing_dependencies":tuple(sorted(missing)),"authority_violations":tuple(sorted(authority))}
