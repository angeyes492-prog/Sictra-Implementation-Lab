from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class KnowledgeItem:
    item_id: str
    knowledge_class: str
    provenance: str
    temporal_state: str
    claim_key: str
    content: str

@dataclass(frozen=True)
class IntelligenceContextPack:
    facts: tuple[KnowledgeItem, ...]
    evidence: tuple[KnowledgeItem, ...]
    uncertainties: tuple[KnowledgeItem, ...]
    contradictions: tuple[KnowledgeItem, ...]
    hypotheses: tuple[KnowledgeItem, ...]
    dependencies: tuple[KnowledgeItem, ...]
    historical: tuple[KnowledgeItem, ...]

_BUCKETS = {
    "FACT": "facts",
    "EVIDENCE": "evidence",
    "UNCERTAINTY": "uncertainties",
    "CONTRADICTION": "contradictions",
    "HYPOTHESIS": "hypotheses",
    "DEPENDENCY": "dependencies",
}

def assemble_intelligence_context(items: Iterable[KnowledgeItem]) -> IntelligenceContextPack:
    buckets = {name: [] for name in (*_BUCKETS.values(), "historical")}
    for item in items:
        if item.temporal_state == "HISTORICAL":
            buckets["historical"].append(item)
            continue
        if item.knowledge_class == "FACT" and item.provenance == "FORMAL":
            buckets["evidence"].append(item)
            continue
        target = _BUCKETS.get(item.knowledge_class)
        if target:
            buckets[target].append(item)
    return IntelligenceContextPack(**{
        key: tuple(sorted(value, key=lambda x: x.item_id)) for key, value in buckets.items()
    })
