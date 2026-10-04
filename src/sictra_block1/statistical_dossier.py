"""Candidate review dossiers from independently rechecked statistical views."""
from copy import deepcopy
from hashlib import sha256

from .common import ContractViolation
from .editorial import assess_editorial_candidate
from .research_acquisition import canonical
from .research_admission import _time
from .statistical_watchlist import StatisticalWatchlist


class StatisticalDossierViolation(ContractViolation):
    pass


def _require(condition, reason):
    if not condition:
        raise StatisticalDossierViolation(reason)


class StatisticalDossierProducer:
    """Owns literal dossier composition, never storage or editorial acceptance."""
    def __init__(self, watchlist):
        _require(isinstance(watchlist, StatisticalWatchlist), "DOSSIER_TRUSTED_WATCHLIST_REQUIRED")
        self.watchlist = watchlist
        self.clock = watchlist._store._clock

    @staticmethod
    def _compose(projection):
        _require(projection["source_state"] == "CURRENT" and projection["expires_at"] is not None,
                 "DOSSIER_CURRENT_INPUT_REQUIRED")
        fields = ("input_fingerprint", "custody_checkpoints", "evidence_refs", "facts", "comparison",
                  "interpretations", "hypotheses", "uncertainty", "contradictions", "affected_scope",
                  "executive_questions", "next_data_needs", "independent_corroboration", "resolution",
                  "editorial_state", "runtime_effect", "publication", "acceptance", "expires_at")
        dossier = {key: deepcopy(projection[key]) for key in fields}
        dossier.update(schema_version="0.1.0", scope="BLOCK1_STATISTICAL_REVIEW_DOSSIER_CANDIDATE",
            projection_id=projection["projection_id"], certainty="UNCONFIRMED", confidence="C",
            review_state="REQUIRES_HUMAN_INTERPRETATION",
            limitations=deepcopy(projection["limitations"]) + [
                "This journal candidate is not an accepted or federated Intelligence dossier",
                "Storage and source verification do not establish interpretation or editorial quality"])
        dossier["dossier_id"] = "STAT-DOSSIER-" + sha256(canonical(dossier)).hexdigest()
        return dossier

    def read(self):
        projection = self.watchlist.read()
        dossier = self._compose(projection)
        self.watchlist.verify_projection(projection)
        _require(_time(self.clock) < dossier["expires_at"], "DOSSIER_READ_EXPIRED")
        return deepcopy(dossier)

    def verify_dossier(self, value):
        _require(type(value) is dict, "DOSSIER_CONTENT_INVALID")
        try:
            submitted = canonical(value)
        except (TypeError, ValueError, OverflowError, RecursionError) as error:
            raise StatisticalDossierViolation("DOSSIER_CONTENT_INVALID") from error
        current = self.read()
        _require(submitted == canonical(current), "DOSSIER_CURRENT_CONTENT_MISMATCH")
        return {"dossier_id": current["dossier_id"], "status": "VERIFIED_LOCAL_EQUIVALENCE",
                "runtime_effect": "NONE", "acceptance": "NOT_ACCEPTED"}

    def editorial_candidate(self, dossier):
        self.verify_dossier(dossier)
        candidate = {
            "candidate_id": "ED-" + dossier["dossier_id"], "event_id": dossier["dossier_id"],
            "title": "Eurostat maritime observations pending interpretation", "state": "RESEARCH_NEEDED",
            "profile": {"impact": 0, "relevance": 0, "novelty": 0, "uncertainty": 100,
                        "timeliness": 0, "actionability": 0, "evidence_strength": 0, "interpretive_value": 0},
            "evidence": {"source_ids": ["eurostat"], "root_ids": ["gateway-source:eurostat"],
                "required_roots": 2, "provenance_integrity": True, "source_approved": True,
                "scope_authorized": True, "freshness": "CURRENT", "contradictions_bounded": False,
                "license_compatible": True, "sensitive_data": False},
            "red_team": "UNKNOWN", "stability": "UNKNOWN",
            "dimensions": {"geography": "BE", "mode": "MARITIME", "topic": "PUBLISHER_MEASUREMENT",
                           "audience": "LOGISTICS_DECISION_MAKER", "horizon": "30D"},
            "editorial": {
                "what_changed": " ".join(
                    f"Publisher reports {f['value']} THS_T for {f['geo_code']} in {f['time_period']} "
                    f"(status flag {f['status_flag']!r})." for f in dossier["facts"]),
                "why_it_matters": "Business significance requires interpretation and independent evidence.",
                "who_is_affected": ["UNSPECIFIED_PENDING_REVIEW"],
                "interpretation": "No interpretation has been approved.",
                "executive_question": dossier["executive_questions"][0],
                "implicit_company_implication": "No account exposure has been established.",
                "alternatives": ["Statistical revision, coverage and operational change remain unresolved."],
                "limitations": deepcopy(dossier["limitations"])},
            "derivations": {"global_frame_id": dossier["dossier_id"], "segment_frame_ids": ["SEGMENT:BE"],
                            "account_frame_ids": []},
            "watchlist": [{"horizon": "7D", "observable": "Independent comparable evidence",
                           "trigger": "Governed source review"},
                          {"horizon": "30D", "observable": "New release of the same observations",
                           "trigger": "Current admitted publisher release"},
                          {"horizon": "90D", "observable": "Source-specific explanation of revisions",
                           "trigger": "Governed methodological reassessment"}]}
        assessment = assess_editorial_candidate(candidate)
        _require(assessment["disposition"] == "RESEARCH_NEEDED" and assessment["editorial_readiness"] == "BLOCKED",
                 "DOSSIER_EDITORIAL_BOUNDARY_VIOLATION")
        self.verify_dossier(dossier)
        _require(_time(self.clock) < dossier["expires_at"], "DOSSIER_EDITORIAL_EXPIRED")
        return {"candidate": candidate, "assessment": assessment, "dossier_id": dossier["dossier_id"],
                "evidence_refs": deepcopy(dossier["evidence_refs"]), "expires_at": dossier["expires_at"],
                "publication_state": "BLOCKED", "handoff": None}
