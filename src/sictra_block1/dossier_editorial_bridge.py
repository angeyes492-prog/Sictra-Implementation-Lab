"""Conservative composition of durable intelligence dossiers for editorial review."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from .common import ContractViolation
from .editorial import assess_editorial_candidate
from .intelligence_dossier import IntelligenceDossierStore


class DossierEditorialBridgeViolation(ContractViolation):
    """A durable dossier cannot be safely composed as an editorial candidate."""


class DossierEditorialBridge:
    def __init__(self, store: IntelligenceDossierStore) -> None:
        if not isinstance(store, IntelligenceDossierStore):
            raise DossierEditorialBridgeViolation("bridge requires an intelligence dossier store")
        self._store = store

    def candidate(self, dossier_id: object) -> dict[str, Any]:
        if not isinstance(dossier_id, str) or not dossier_id.strip():
            raise DossierEditorialBridgeViolation("dossier_id must be non-empty text")
        matches = [item for item in self._store.list_dossiers()
                   if item.get("dossier_id") == dossier_id.strip()]
        if len(matches) != 1:
            raise DossierEditorialBridgeViolation("dossier identity is unavailable or ambiguous")
        dossier = matches[0]
        source = dossier["source"]
        fact_text = " ".join(fact["statement"] for fact in dossier["facts"])
        geography = ", ".join(dossier["affected_scope"]["geo_codes"])
        candidate = {
            "candidate_id": "ED-DOSSIER-" + sha256(dossier["dossier_id"].encode()).hexdigest()[:16],
            "event_id": dossier["dossier_id"],
            "title": "Eurostat maritime change pending interpretation",
            "state": "RESEARCH_NEEDED",
            "profile": {
                "impact": 0, "relevance": 0, "novelty": 0, "uncertainty": 100,
                "timeliness": 0, "actionability": 0, "evidence_strength": 40,
                "interpretive_value": 0,
            },
            "evidence": {
                "source_ids": [source["source_id"]],
                "root_ids": ["gateway-source:" + source["source_id"]],
                "required_roots": 2,
                "provenance_integrity": True,
                "source_approved": True,
                "scope_authorized": True,
                "freshness": "UNKNOWN",
                "contradictions_bounded": False,
                "license_compatible": True,
                "sensitive_data": False,
            },
            "red_team": "UNKNOWN",
            "stability": "UNKNOWN",
            "dimensions": {
                "geography": geography or "UNSPECIFIED",
                "mode": "MARITIME", "topic": "OBSERVED_DATA_CHANGE",
                "audience": "LOGISTICS_DECISION_MAKER", "horizon": "30D",
            },
            "editorial": {
                "what_changed": fact_text,
                "why_it_matters": "Not established; human interpretation and corroboration are required.",
                "who_is_affected": ["UNSPECIFIED_PENDING_REVIEW"],
                "interpretation": "No interpretation has been approved.",
                "executive_question": dossier["executive_questions"][0],
                "implicit_company_implication": "No company-specific implication has been established.",
                "alternatives": list(dossier["uncertainties"]),
                "limitations": list(dossier["limitations"]),
            },
            "derivations": {
                "global_frame_id": dossier["dossier_id"],
                "segment_frame_ids": ["SEGMENT:" + code for code in dossier["affected_scope"]["geo_codes"]],
                "account_frame_ids": [],
            },
            "watchlist": [
                {"horizon": "7D", "observable": "Independent corroborating source", "trigger": "Second independent root"},
                {"horizon": "30D", "observable": "Persistence of the measured change", "trigger": "New governed release"},
                {"horizon": "90D", "observable": "Revision or structural persistence", "trigger": "Human reassessment"},
            ],
        }
        assessment = assess_editorial_candidate(candidate)
        if assessment["disposition"] != "RESEARCH_NEEDED" or assessment["editorial_readiness"] != "BLOCKED":
            raise DossierEditorialBridgeViolation("unreviewed dossier escaped editorial blocking")
        return {"candidate": candidate, "assessment": assessment,
                "publication_state": "BLOCKED", "handoff": None}
