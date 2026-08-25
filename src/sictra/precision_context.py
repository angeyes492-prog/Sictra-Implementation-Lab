from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class ClaimRecord:
    record_id: str
    claim_id: str
    source_id: str
    evidence_class: str
    provenance: str
    confidence: str
    temporal_state: str
    contradiction: bool
    content: str

@dataclass(frozen=True)
class PrecisionContextPack:
    claim_id: str
    current_records: tuple[ClaimRecord, ...]
    stale_records: tuple[ClaimRecord, ...]
    counterclaims: tuple[ClaimRecord, ...]
    uncertainties: tuple[ClaimRecord, ...]
    independent_source_count: int
    precision_judgement: None = None

def assemble_precision_context(records: Iterable[ClaimRecord], claim_id: str) -> PrecisionContextPack:
    scoped=[r for r in records if r.claim_id == claim_id]
    current=[]; stale=[]; counters=[]; uncertainties=[]
    for r in scoped:
        if r.temporal_state != "CURRENT": stale.append(r); continue
        current.append(r)
        if r.contradiction: counters.append(r)
        if r.evidence_class == "UNCERTAINTY": uncertainties.append(r)
    sources={r.source_id for r in current if r.source_id and r.evidence_class != "UNCERTAINTY"}
    return PrecisionContextPack(claim_id, tuple(sorted(current,key=lambda x:x.record_id)), tuple(sorted(stale,key=lambda x:x.record_id)), tuple(sorted(counters,key=lambda x:x.record_id)), tuple(sorted(uncertainties,key=lambda x:x.record_id)), len(sources))
