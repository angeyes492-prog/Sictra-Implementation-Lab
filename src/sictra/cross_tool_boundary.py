from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ToolObservation:
    tool: str
    object_id: str
    source: str
    scope: str
    version: str
    status: str
    confidence: str
    relation: str
    temporal_state: str
    claim_key: str
    claim_value: Any
    authority: str

REQUIRED_LINEAGE=("tool","object_id","source","scope","version","status","confidence","relation","temporal_state","claim_key")
FORBIDDEN_AUTHORITIES={"SOURCE_OF_TRUTH","ACCEPTANCE_AUTHORITY","PROMOTION_AUTHORITY"}
ROLE_AUTHORITY={"Notion":{"CONTEXT_ONLY"},"Slack":{"SIGNAL_ONLY"},"GitHub":{"IMPLEMENTATION_EVIDENCE"},"Wolfram":{"FORMAL_ONLY"}}

def validate_lineage(obs: ToolObservation):
    missing=tuple(k for k in REQUIRED_LINEAGE if not str(getattr(obs,k,"" )).strip())
    return (not missing,missing)

def role_valid(obs: ToolObservation):
    return obs.authority in ROLE_AUTHORITY.get(obs.tool,set()) and obs.authority not in FORBIDDEN_AUTHORITIES

def current_claims(observations,claim_key):
    return tuple(o for o in observations if o.claim_key==claim_key and o.temporal_state=="CURRENT")

def current_contradictions(observations,claim_key):
    current=current_claims(observations,claim_key)
    values={repr(o.claim_value) for o in current}
    return len(values)>1

def historical_transitions(observations,claim_key):
    current=current_claims(observations,claim_key)
    historical=tuple(o for o in observations if o.claim_key==claim_key and o.temporal_state!="CURRENT")
    return tuple((h.claim_value,c.claim_value) for h in historical for c in current if h.claim_value!=c.claim_value)

def reconcile(observations,claim_key):
    scoped=current_claims(observations,claim_key)
    valid=all(validate_lineage(x)[0] and role_valid(x) for x in scoped)
    contradiction=current_contradictions(observations,claim_key)
    return {"valid":valid,"current_contradiction":contradiction,"current_tools":tuple(sorted(x.tool for x in scoped)),"historical_transitions":historical_transitions(observations,claim_key)}
