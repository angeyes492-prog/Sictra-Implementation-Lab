def expected_context_ids(items):
    expected = {
        "facts": [], "evidence": [], "uncertainties": [], "contradictions": [],
        "hypotheses": [], "dependencies": [], "historical": []
    }
    mapping = {
        "FACT":"facts", "EVIDENCE":"evidence", "UNCERTAINTY":"uncertainties",
        "CONTRADICTION":"contradictions", "HYPOTHESIS":"hypotheses", "DEPENDENCY":"dependencies"
    }
    for i in items:
        if i.temporal_state == "HISTORICAL":
            expected["historical"].append(i.item_id)
        elif i.knowledge_class == "FACT" and i.provenance == "FORMAL":
            expected["evidence"].append(i.item_id)
        elif i.knowledge_class in mapping:
            expected[mapping[i.knowledge_class]].append(i.item_id)
    return {k: tuple(sorted(v)) for k,v in expected.items()}
