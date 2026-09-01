from dataclasses import dataclass
from .runtime import Observation

@dataclass(frozen=True)
class Reassessment:
    result: str
    reason: str

def reassess(observation: Observation, expected: tuple[str, ...]) -> Reassessment:
    if observation.status != "EXECUTED":
        return Reassessment("REJECTED", "OBSERVATION_NOT_EXECUTED")
    if not observation.engine_id or not observation.contract_id:
        return Reassessment("REJECTED", "IDENTITY_INCOMPLETE")
    if tuple(sorted(observation.selected_ids)) != tuple(sorted(expected)):
        return Reassessment("REJECTED", "EXPECTED_OBSERVED_MISMATCH")
    return Reassessment("VALIDATED", "INDEPENDENT_ORACLE_MATCH")

def promotion_decision(reassessment: Reassessment, *, ci_executed: bool, cross_engine_observed: bool) -> str:
    if reassessment.result != "VALIDATED" or not ci_executed or not cross_engine_observed:
        return "DO_NOT_PROMOTE"
    return "CANDIDATE_FOR_ACCEPTANCE"
