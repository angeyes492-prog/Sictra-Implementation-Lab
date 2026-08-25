def expected_independent_count(records):
    return len({r.root_source for r in records if r.admissible and r.temporal_state=="CURRENT" and r.provenance_kind in {"PRIMARY","SECONDARY"} and r.root_source})
