from dataclasses import dataclass

@dataclass(frozen=True)
class EvidenceRecord:
    record_id: str
    root_source: str
    provenance_kind: str
    temporal_state: str
    admissible: bool

@dataclass(frozen=True)
class CorroborationResult:
    independent_root_sources: tuple[str, ...]
    independent_evidence_count: int
    rejected_record_ids: tuple[str, ...]

INDEPENDENT_KINDS = {"PRIMARY", "SECONDARY"}

def compute_corroboration(records: tuple[EvidenceRecord, ...]) -> CorroborationResult:
    roots=set(); rejected=[]
    for r in records:
        if not r.admissible or r.temporal_state != "CURRENT" or r.provenance_kind not in INDEPENDENT_KINDS or not r.root_source:
            rejected.append(r.record_id); continue
        roots.add(r.root_source)
    ordered=tuple(sorted(roots))
    return CorroborationResult(ordered,len(ordered),tuple(sorted(rejected)))
