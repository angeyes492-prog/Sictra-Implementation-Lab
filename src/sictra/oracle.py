def expected_set(records, *, engine_id: str, contract_id: str, agent: str, temporal_state: str, relation: str) -> tuple[str, ...]:
    return tuple(sorted({
        r.event_id for r in records
        if (r.engine_id, r.contract_id, r.agent, r.temporal_state, r.relation)
        == (engine_id, contract_id, agent, temporal_state, relation)
        and bool(r.provenance)
        and r.contradiction in {"none", "explicit"}
    }))
