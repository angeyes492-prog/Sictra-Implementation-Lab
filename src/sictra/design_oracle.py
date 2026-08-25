def expected_design_ids(items):
    out={"architecture":[],"contracts":[],"dependencies":[],"constraints":[],"historical_decisions":[],"contradictions":[],"open_questions":[],"implementation_implications":[],"unknowns":[]}
    mapping={"ARCHITECTURE":"architecture","CONTRACT":"contracts","DEPENDENCY":"dependencies","CONSTRAINT":"constraints","CONTRADICTION":"contradictions","QUESTION":"open_questions","IMPLICATION":"implementation_implications","UNKNOWN":"unknowns"}
    for x in items:
        if x.agent != "Design": continue
        if x.category == "DECISION" and x.temporal_state in {"HISTORICAL","STALE","SUPERSEDED"}: out["historical_decisions"].append(x.item_id)
        elif x.temporal_state == "CURRENT" and x.category in mapping: out[mapping[x.category]].append(x.item_id)
    return {k:tuple(sorted(v)) for k,v in out.items()}
