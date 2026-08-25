from dataclasses import dataclass, replace

REQUIRED_CONTEXT_FIELDS = (
    "what", "why", "source", "when", "version", "scope", "status", "confidence",
    "contradictions", "dependencies", "unknowns", "reassessment_state", "related_agents", "related_tools"
)

@dataclass(frozen=True)
class ProvenancePayload:
    source_identity: str
    root_provenance: str
    derivation_graph: tuple[str, ...]
    temporal_scope: str
    evidence_class: str

@dataclass(frozen=True)
class MaterialContextRecord:
    record_id: str
    what: str
    why: str
    source: str
    when: str
    version: str
    scope: str
    status: str
    confidence: str
    contradictions: tuple[str, ...]
    dependencies: tuple[str, ...]
    unknowns: tuple[str, ...]
    reassessment_state: str
    related_agents: tuple[str, ...]
    related_tools: tuple[str, ...]
    provenance: ProvenancePayload


def validate_integrity(record: MaterialContextRecord) -> tuple[bool, tuple[str, ...]]:
    missing=[]
    for field in REQUIRED_CONTEXT_FIELDS:
        value=getattr(record, field)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(field)
    p=record.provenance
    for field in ("source_identity","root_provenance","temporal_scope","evidence_class"):
        value=getattr(p, field)
        if value is None or not str(value).strip():
            missing.append("provenance."+field)
    if p.derivation_graph is None:
        missing.append("provenance.derivation_graph")
    return (not missing, tuple(sorted(missing)))


def handoff(record: MaterialContextRecord, *, scope: str | None = None, related_agents: tuple[str,...] | None = None) -> MaterialContextRecord:
    ok, missing=validate_integrity(record)
    if not ok:
        raise ValueError("INTEGRITY_MISSING:"+",".join(missing))
    original=record.provenance
    transformed=replace(record, scope=scope or record.scope, related_agents=related_agents or record.related_agents)
    if transformed.provenance != original:
        raise AssertionError("PROVENANCE_REWRITE")
    return transformed


def independent_evidence_count(records: tuple[MaterialContextRecord, ...]) -> int:
    roots=set()
    for record in records:
        ok,_=validate_integrity(record)
        if not ok:
            continue
        p=record.provenance
        if p.temporal_scope != "CURRENT":
            continue
        if p.evidence_class not in {"RUNTIME","OBSERVED"}:
            continue
        roots.add((p.source_identity,p.root_provenance))
    return len(roots)
