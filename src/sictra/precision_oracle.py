def expected_precision(records, claim_id):
    scoped=[r for r in records if r.claim_id==claim_id]
    current=tuple(sorted((r.record_id for r in scoped if r.temporal_state=="CURRENT")))
    stale=tuple(sorted((r.record_id for r in scoped if r.temporal_state!="CURRENT")))
    counters=tuple(sorted((r.record_id for r in scoped if r.temporal_state=="CURRENT" and r.contradiction)))
    uncertainties=tuple(sorted((r.record_id for r in scoped if r.temporal_state=="CURRENT" and r.evidence_class=="UNCERTAINTY")))
    source_count=len({r.source_id for r in scoped if r.temporal_state=="CURRENT" and r.source_id and r.evidence_class!="UNCERTAINTY"})
    return {"current":current,"stale":stale,"counters":counters,"uncertainties":uncertainties,"source_count":source_count}
