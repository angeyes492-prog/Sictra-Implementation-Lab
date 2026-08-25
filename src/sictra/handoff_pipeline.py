from dataclasses import dataclass
from .context_integrity import MaterialContextRecord, handoff, validate_integrity
from .context_fabric import FabricRelation, prepare_agent_context, fabric_signature
from .confidence_enforcement import EvidenceRecord, compute_corroboration

@dataclass(frozen=True)
class PipelineResult:
    target_agent: str
    fabric_signature: tuple
    independent_evidence_count: int
    reassessment_status: str
    orchestration_candidate: str
    confidence_authority_layer: str
    promotion_authorized: bool = False


def execute_handoff(records: tuple[MaterialContextRecord,...], relations: tuple[FabricRelation,...], evidence: tuple[EvidenceRecord,...], target_agent: str) -> PipelineResult:
    transformed=[]
    for record in records:
        ok,_=validate_integrity(record)
        if not ok:
            continue
        transformed.append(handoff(record))
    pack=prepare_agent_context(tuple(transformed),relations,target_agent)
    corroboration=compute_corroboration(evidence)
    reassessment_status="VALIDATED" if all(validate_integrity(r)[0] for r in transformed) and not pack.promotion_authority and not pack.verification_authority else "REJECTED"
    candidate="REASSESS_NEXT_ACTION" if reassessment_status=="VALIDATED" else "HOLD"
    return PipelineResult(target_agent,fabric_signature(pack),corroboration.independent_evidence_count,reassessment_status,candidate,"PRECISION_REASSESSMENT",False)
