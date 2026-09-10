"""Governed Editorial Engine composition for Block 1 Intelligence.

The module evaluates synthetic or already-governed candidate mappings.  It has
no network client, publication action, CRM integration, credential access, or
gate-promotion authority.
"""

from __future__ import annotations

from copy import deepcopy
import math
from typing import Any, Iterable, Mapping


EDITORIAL_SCOPE = "BLOCK1_GOVERNED_EDITORIAL_ENGINE"
FIXTURE_CLASS = "SYNTHETIC_FIELD_TEST"
EDITORIAL_METHOD = "ELIGIBILITY_PARETO_DIVERSITY_V0.1"
MAX_CANDIDATES_PER_CYCLE = 500

_CANDIDATE_FIELDS = {
    "candidate_id", "event_id", "title", "state", "profile", "evidence",
    "red_team", "stability", "dimensions", "editorial", "derivations",
    "watchlist",
}
_PROFILE_FIELDS = {
    "impact", "relevance", "novelty", "uncertainty", "timeliness",
    "actionability", "evidence_strength", "interpretive_value",
}
_EVIDENCE_FIELDS = {
    "source_ids", "root_ids", "required_roots", "provenance_integrity",
    "source_approved", "scope_authorized", "freshness",
    "contradictions_bounded", "license_compatible", "sensitive_data",
}
_DIMENSION_FIELDS = {"geography", "mode", "topic", "audience", "horizon"}
_EDITORIAL_FIELDS = {
    "what_changed", "why_it_matters", "who_is_affected", "interpretation",
    "executive_question", "implicit_company_implication", "alternatives",
    "limitations",
}
_DERIVATION_FIELDS = {
    "global_frame_id", "segment_frame_ids", "account_frame_ids",
}
_WATCH_FIELDS = {"horizon", "observable", "trigger"}
_STATES = {
    "DRAFT", "RESEARCH_NEEDED", "DELIVERABLE_BOUNDED", "QUARANTINED",
    "SUPERSEDED",
}
_HORIZONS = {"7D", "30D", "90D"}
_MAXIMIZE = (
    "impact", "relevance", "novelty", "timeliness", "actionability",
    "evidence_strength", "interpretive_value",
)
_MINIMIZE = ("uncertainty",)


class EditorialContractViolation(ValueError):
    """Raised when an editorial object violates the bounded contract."""


def _exact(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise EditorialContractViolation(f"{label} fields do not match contract")


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EditorialContractViolation(f"{label} must be non-empty text")
    return value.strip()


def _text_list(
    value: Any, label: str, *, allow_empty: bool = False,
    allow_duplicates: bool = False,
) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise EditorialContractViolation(f"{label} must be a text list")
    normalized = [_text(item, label) for item in value]
    if not allow_duplicates and len(normalized) != len(set(normalized)):
        raise EditorialContractViolation(f"{label} contains duplicate identities")
    return normalized


def _normalize_candidate(value: Mapping[str, Any]) -> dict[str, Any]:
    _exact(value, _CANDIDATE_FIELDS, "candidate")
    normalized: dict[str, Any] = {
        key: _text(value[key], key) for key in ("candidate_id", "event_id", "title")
    }
    state = value["state"]
    if state not in _STATES:
        raise EditorialContractViolation("unsupported candidate state")
    normalized["state"] = state

    profile = value["profile"]
    _exact(profile, _PROFILE_FIELDS, "profile")
    normalized_profile: dict[str, float] = {}
    for key in sorted(_PROFILE_FIELDS):
        raw = profile[key]
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(raw):
            raise EditorialContractViolation(f"profile {key} must be finite numeric data")
        number = float(raw)
        if number < 0 or number > 100:
            raise EditorialContractViolation(f"profile {key} must be between 0 and 100")
        normalized_profile[key] = number
    normalized["profile"] = normalized_profile

    evidence = value["evidence"]
    _exact(evidence, _EVIDENCE_FIELDS, "evidence")
    source_ids = _text_list(evidence["source_ids"], "source_ids")
    root_ids = _text_list(
        evidence["root_ids"], "root_ids", allow_empty=False,
        allow_duplicates=True,
    )
    if len(source_ids) != len(root_ids):
        raise EditorialContractViolation("source_ids and root_ids must align")
    required_roots = evidence["required_roots"]
    if isinstance(required_roots, bool) or not isinstance(required_roots, int) or required_roots < 1:
        raise EditorialContractViolation("required_roots must be a positive integer")
    normalized_evidence: dict[str, Any] = {
        "source_ids": source_ids,
        "root_ids": root_ids,
        "required_roots": required_roots,
    }
    for key in (
        "provenance_integrity", "source_approved", "scope_authorized",
        "contradictions_bounded", "license_compatible", "sensitive_data",
    ):
        if not isinstance(evidence[key], bool):
            raise EditorialContractViolation(f"evidence {key} must be boolean")
        normalized_evidence[key] = evidence[key]
    if evidence["freshness"] not in {"CURRENT", "STALE", "UNKNOWN"}:
        raise EditorialContractViolation("unsupported evidence freshness")
    normalized_evidence["freshness"] = evidence["freshness"]
    normalized["evidence"] = normalized_evidence

    if value["red_team"] not in {"PASS", "FAIL", "UNKNOWN"}:
        raise EditorialContractViolation("unsupported red-team state")
    if value["stability"] not in {"STABLE", "AT_RISK", "DEGRADED", "UNKNOWN"}:
        raise EditorialContractViolation("unsupported stability state")
    normalized["red_team"] = value["red_team"]
    normalized["stability"] = value["stability"]

    dimensions = value["dimensions"]
    _exact(dimensions, _DIMENSION_FIELDS, "dimensions")
    normalized["dimensions"] = {
        key: _text(dimensions[key], f"dimensions.{key}") for key in sorted(_DIMENSION_FIELDS)
    }

    editorial = value["editorial"]
    _exact(editorial, _EDITORIAL_FIELDS, "editorial")
    normalized_editorial = {
        key: _text(editorial[key], f"editorial.{key}")
        for key in (
            "what_changed", "why_it_matters", "interpretation",
            "executive_question", "implicit_company_implication",
        )
    }
    normalized_editorial["who_is_affected"] = _text_list(
        editorial["who_is_affected"], "who_is_affected"
    )
    normalized_editorial["alternatives"] = _text_list(
        editorial["alternatives"], "alternatives"
    )
    normalized_editorial["limitations"] = _text_list(
        editorial["limitations"], "limitations"
    )
    normalized["editorial"] = normalized_editorial

    derivations = value["derivations"]
    _exact(derivations, _DERIVATION_FIELDS, "derivations")
    normalized["derivations"] = {
        "global_frame_id": _text(derivations["global_frame_id"], "global_frame_id"),
        "segment_frame_ids": _text_list(
            derivations["segment_frame_ids"], "segment_frame_ids"
        ),
        "account_frame_ids": _text_list(
            derivations["account_frame_ids"], "account_frame_ids", allow_empty=True
        ),
    }

    watchlist = value["watchlist"]
    if not isinstance(watchlist, list) or len(watchlist) != 3:
        raise EditorialContractViolation("watchlist must contain exactly 7D, 30D, and 90D")
    normalized_watchlist = []
    for item in watchlist:
        _exact(item, _WATCH_FIELDS, "watchlist item")
        if item["horizon"] not in _HORIZONS:
            raise EditorialContractViolation("unsupported watchlist horizon")
        normalized_watchlist.append({
            "horizon": item["horizon"],
            "observable": _text(item["observable"], "watchlist observable"),
            "trigger": _text(item["trigger"], "watchlist trigger"),
        })
    if {item["horizon"] for item in normalized_watchlist} != _HORIZONS:
        raise EditorialContractViolation("watchlist horizons must be unique and complete")
    normalized["watchlist"] = normalized_watchlist
    return normalized


def _research_priority(profile: Mapping[str, float]) -> str:
    if profile["impact"] >= 70 and (
        profile["novelty"] >= 60 or profile["uncertainty"] >= 60
    ):
        return "HIGH"
    if profile["impact"] >= 40 or profile["relevance"] >= 60:
        return "MEDIUM"
    return "LOW"


def assess_editorial_candidate(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and assess one candidate without producing a scalar score."""

    candidate = _normalize_candidate(value)
    evidence = candidate["evidence"]
    profile = candidate["profile"]
    independent_roots = len(set(evidence["root_ids"]))

    quarantine_reasons = []
    if not evidence["provenance_integrity"]:
        quarantine_reasons.append("PROVENANCE_INTEGRITY_FAILURE")
    if not evidence["source_approved"]:
        quarantine_reasons.append("UNAPPROVED_SOURCE")
    if not evidence["scope_authorized"]:
        quarantine_reasons.append("UNAUTHORIZED_SCOPE")
    if not evidence["license_compatible"]:
        quarantine_reasons.append("LICENSE_INCOMPATIBLE")
    if evidence["sensitive_data"]:
        quarantine_reasons.append("SENSITIVE_DATA_NOT_AUTHORIZED")

    research_reasons = []
    if evidence["freshness"] != "CURRENT":
        research_reasons.append("EVIDENCE_NOT_CURRENT")
    if independent_roots < evidence["required_roots"]:
        research_reasons.append("INSUFFICIENT_INDEPENDENT_ROOTS")
    if not evidence["contradictions_bounded"]:
        research_reasons.append("MATERIAL_CONTRADICTION_OPEN")
    if candidate["red_team"] != "PASS":
        research_reasons.append("RED_TEAM_NOT_PASS")
    if candidate["stability"] != "STABLE":
        research_reasons.append("STABILITY_NOT_STABLE")
    if profile["evidence_strength"] < 60:
        research_reasons.append("WEAK_EVIDENCE")
    if profile["uncertainty"] > 40:
        research_reasons.append("MATERIAL_UNCERTAINTY")
    if candidate["state"] not in {"DELIVERABLE_BOUNDED", "QUARANTINED", "SUPERSEDED"}:
        research_reasons.append("STATE_NOT_DELIVERABLE")

    if candidate["state"] == "SUPERSEDED":
        disposition = "SUPERSEDED"
        reasons = ["CANDIDATE_SUPERSEDED"]
    elif quarantine_reasons or candidate["state"] == "QUARANTINED":
        disposition = "QUARANTINED"
        reasons = quarantine_reasons or ["CANDIDATE_QUARANTINED"]
    elif research_reasons:
        disposition = "RESEARCH_NEEDED"
        reasons = research_reasons
    else:
        disposition = "DELIVERABLE_BOUNDED"
        reasons = []

    return {
        "candidate_id": candidate["candidate_id"],
        "event_id": candidate["event_id"],
        "title": candidate["title"],
        "disposition": disposition,
        "eligibility": "ELIGIBLE" if disposition == "DELIVERABLE_BOUNDED" else "BLOCKED",
        "research_priority": _research_priority(profile),
        "editorial_readiness": "READY" if disposition == "DELIVERABLE_BOUNDED" else "BLOCKED",
        "independent_roots": independent_roots,
        "required_roots": evidence["required_roots"],
        "reasons": reasons,
        "profile": deepcopy(profile),
        "dimensions": deepcopy(candidate["dimensions"]),
        "method": EDITORIAL_METHOD,
    }


def _dominates(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    left_profile, right_profile = left["profile"], right["profile"]
    no_worse = all(left_profile[key] >= right_profile[key] for key in _MAXIMIZE)
    no_worse = no_worse and all(left_profile[key] <= right_profile[key] for key in _MINIMIZE)
    strictly = any(left_profile[key] > right_profile[key] for key in _MAXIMIZE)
    strictly = strictly or any(left_profile[key] < right_profile[key] for key in _MINIMIZE)
    return no_worse and strictly


def _frontier(eligible: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        item for item in eligible
        if not any(
            other["candidate_id"] != item["candidate_id"] and _dominates(other, item)
            for other in eligible
        )
    ]


def _quality_tie_key(item: Mapping[str, Any]) -> tuple[Any, ...]:
    profile = item["profile"]
    return (
        -profile["evidence_strength"],
        -profile["timeliness"],
        -profile["interpretive_value"],
        item["candidate_id"],
    )


def _diverse_shortlist(frontier: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    remaining = sorted(frontier, key=_quality_tie_key)
    selected: list[dict[str, Any]] = []
    used = {key: set() for key in _DIMENSION_FIELDS}
    while remaining and len(selected) < limit:
        if not selected:
            choice = remaining[0]
        else:
            ranked = sorted(
                remaining,
                key=lambda item: (
                    -sum(
                        item["dimensions"][key] not in used[key]
                        for key in _DIMENSION_FIELDS
                    ),
                    *_quality_tie_key(item),
                ),
            )
            choice = ranked[0]
        selected.append(choice)
        remaining.remove(choice)
        for key in _DIMENSION_FIELDS:
            used[key].add(choice["dimensions"][key])
    return selected


def editorial_cycle(
    values: Iterable[Mapping[str, Any]], *, min_candidates: int = 3,
    max_candidates: int = 5,
) -> dict[str, Any]:
    """Produce a governed weekly shortlist from validated candidate mappings."""

    if (
        isinstance(min_candidates, bool) or isinstance(max_candidates, bool)
        or not isinstance(min_candidates, int) or not isinstance(max_candidates, int)
        or min_candidates < 1 or max_candidates < min_candidates or max_candidates > 5
    ):
        raise EditorialContractViolation("candidate bounds must satisfy 1 <= min <= max <= 5")
    if isinstance(values, (str, bytes, Mapping)):
        raise EditorialContractViolation("candidates must be an iterable of mappings")
    normalized = []
    for value in values:
        if len(normalized) >= MAX_CANDIDATES_PER_CYCLE:
            raise EditorialContractViolation("editorial cycle capacity exceeded")
        normalized.append(_normalize_candidate(value))
    ids = [item["candidate_id"] for item in normalized]
    if len(ids) != len(set(ids)):
        raise EditorialContractViolation("duplicate editorial candidate identity")
    event_ids = [item["event_id"] for item in normalized]
    if len(event_ids) != len(set(event_ids)):
        raise EditorialContractViolation("duplicate editorial event identity")
    assessments = [assess_editorial_candidate(item) for item in normalized]
    eligible = [item for item in assessments if item["eligibility"] == "ELIGIBLE"]
    frontier = _frontier(eligible)
    if len(eligible) < min_candidates:
        shortlist: list[dict[str, Any]] = []
        status = "INSUFFICIENT_ELIGIBLE_CANDIDATES"
    else:
        shortlist = _diverse_shortlist(frontier, max_candidates)
        if len(shortlist) < min_candidates:
            # Dominated candidates are not silently promoted merely to fill a quota.
            status = "INSUFFICIENT_NONDOMINATED_CANDIDATES"
            shortlist = []
        else:
            status = "SHORTLIST_READY"
    shortlist_ids = [item["candidate_id"] for item in shortlist]
    plural = {
        "geography": "geographies", "mode": "modes", "topic": "topics",
        "audience": "audiences", "horizon": "horizons",
    }
    diversity = {
        plural[key]: len({item["dimensions"][key] for item in shortlist})
        for key in _DIMENSION_FIELDS
    }
    return {
        "scope": EDITORIAL_SCOPE,
        "status": status,
        "method": EDITORIAL_METHOD,
        "candidate_count": len(normalized),
        "min_candidates": min_candidates,
        "max_candidates": max_candidates,
        "eligible_count": len(eligible),
        "pareto_frontier_ids": [item["candidate_id"] for item in sorted(frontier, key=_quality_tie_key)],
        "shortlist_ids": shortlist_ids,
        "diversity": diversity,
        "assessments": deepcopy(assessments),
        "candidates": deepcopy(normalized),
        "non_claims": [
            "No universal editorial score.",
            "No autonomous publication or outreach.",
            "No global gate promotion.",
        ],
    }


def _verify_cycle(cycle: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(cycle, Mapping) or cycle.get("scope") != EDITORIAL_SCOPE:
        raise EditorialContractViolation("invalid editorial cycle")
    candidates = cycle.get("candidates")
    if not isinstance(candidates, list):
        raise EditorialContractViolation("cycle candidates are unavailable")
    min_candidates = cycle.get("min_candidates")
    max_candidates = cycle.get("max_candidates")
    try:
        verified_cycle = editorial_cycle(
            candidates,
            min_candidates=min_candidates,
            max_candidates=max_candidates,
        )
    except (EditorialContractViolation, TypeError) as error:
        raise EditorialContractViolation("editorial cycle cannot be reverified") from error
    if (
        cycle.get("status") != verified_cycle["status"]
        or cycle.get("shortlist_ids") != verified_cycle["shortlist_ids"]
        or cycle.get("assessments") != verified_cycle["assessments"]
    ):
        raise EditorialContractViolation("editorial cycle integrity mismatch")
    return verified_cycle


def _rationale(value: Any) -> str:
    normalized = _text(value, "rationale")
    if len(normalized) < 20 or len(normalized) > 1000:
        raise EditorialContractViolation("rationale must contain 20 to 1000 characters")
    return normalized


def select_flagship(
    cycle: Mapping[str, Any], candidate_id: str, *, selected_by: str,
    rationale: str,
) -> dict[str, Any]:
    """Create a bounded Block 2 handoff for a human-selected shortlisted item."""

    candidate_id = _text(candidate_id, "candidate_id")
    selected_by = _text(selected_by, "selected_by")
    rationale = _rationale(rationale)
    verified_cycle = _verify_cycle(cycle)
    candidates = verified_cycle["candidates"]
    shortlist = verified_cycle["shortlist_ids"]
    if candidate_id not in shortlist:
        raise EditorialContractViolation("flagship must be selected from the shortlist")
    candidate = next((item for item in candidates if item.get("candidate_id") == candidate_id), None)
    if candidate is None:
        raise EditorialContractViolation("shortlisted candidate payload is unavailable")
    assessment = next(
        (item for item in verified_cycle["assessments"] if item.get("candidate_id") == candidate_id),
        None,
    )
    if assessment is None or assessment.get("editorial_readiness") != "READY":
        raise EditorialContractViolation("flagship is not editorially ready")
    return {
        "scope": EDITORIAL_SCOPE,
        "selected_candidate_id": candidate_id,
        "selection": {
            "authority": "HUMAN_EDITORIAL_CHOICE",
            "selected_by": selected_by,
            "rationale": rationale,
            "persistence": "EPHEMERAL",
        },
        "dossier": {
            "title": candidate["title"],
            **deepcopy(candidate["editorial"]),
            "evidence": deepcopy(candidate["evidence"]),
            "profile": deepcopy(candidate["profile"]),
            "derivations": deepcopy(candidate["derivations"]),
            "watchlist_7_30_90": deepcopy(candidate["watchlist"]),
            "disposition": assessment["disposition"],
        },
        "handoff": {
            "type": "BLOCK2_DESIGN_HANDOFF_CANDIDATE_V0.1",
            "consumer": "BLOCK2_DESIGN",
            "authority": "BOUNDED_REVIEW_ONLY",
            "non_claims": [
                "Not a production artifact.",
                "Not authorization for distribution or outreach.",
                "Not global gate acceptance.",
            ],
        },
    }


def abstain_from_flagship(
    cycle: Mapping[str, Any], *, selected_by: str, rationale: str,
) -> dict[str, Any]:
    """Record a bounded human decision that no weekly flagship should advance."""

    selected_by = _text(selected_by, "selected_by")
    rationale = _rationale(rationale)
    verified_cycle = _verify_cycle(cycle)
    return {
        "scope": EDITORIAL_SCOPE,
        "decision": "NO_FLAGSHIP_SELECTED",
        "selected_candidate_id": None,
        "selection": {
            "authority": "HUMAN_EDITORIAL_CHOICE",
            "selected_by": selected_by,
            "rationale": rationale,
            "persistence": "EPHEMERAL",
        },
        "considered_shortlist_ids": deepcopy(verified_cycle["shortlist_ids"]),
        "handoff": None,
        "non_claims": [
            "No candidate was promoted.",
            "No publication or distribution action occurred.",
            "No global gate changed.",
        ],
    }


def _fixture_candidate(
    candidate_id: str, title: str, profile: tuple[int, ...],
    dimensions: tuple[str, ...], *, uncertainty_block: bool = False,
    quarantine: bool = False,
) -> dict[str, Any]:
    profile_map = dict(zip(
        (
            "impact", "relevance", "novelty", "uncertainty", "timeliness",
            "actionability", "evidence_strength", "interpretive_value",
        ),
        profile,
    ))
    if uncertainty_block:
        profile_map["uncertainty"] = 78
    return {
        "candidate_id": candidate_id,
        "event_id": f"EV-{candidate_id}",
        "title": title,
        "state": "DELIVERABLE_BOUNDED",
        "profile": profile_map,
        "evidence": {
            "source_ids": [f"SRC-{candidate_id}-A", f"SRC-{candidate_id}-B"],
            "root_ids": [f"ROOT-{candidate_id}-A", f"ROOT-{candidate_id}-B"],
            "required_roots": 2,
            "provenance_integrity": not quarantine,
            "source_approved": True,
            "scope_authorized": True,
            "freshness": "CURRENT",
            "contradictions_bounded": True,
            "license_compatible": True,
            "sensitive_data": False,
        },
        "red_team": "PASS",
        "stability": "STABLE",
        "dimensions": dict(zip(
            ("geography", "mode", "topic", "audience", "horizon"), dimensions
        )),
        "editorial": {
            "what_changed": f"El fixture {candidate_id} registra un cambio logístico sintético.",
            "why_it_matters": "Puede alterar el valor relativo de una decisión de planificación.",
            "who_is_affected": [dimensions[3]],
            "interpretation": "La señal importa por el supuesto que obliga a revalidar, no por su volumen aislado.",
            "executive_question": "¿Qué supuesto operativo perdería validez si esta señal persiste?",
            "implicit_company_implication": "Revisar exposición antes de convertir la señal en acción.",
            "alternatives": ["El cambio puede ser temporal o explicado por estacionalidad."],
            "limitations": ["Fixture sintético; no representa un acontecimiento real."],
        },
        "derivations": {
            "global_frame_id": f"GLOBAL-{candidate_id}",
            "segment_frame_ids": [f"SEGMENT-{candidate_id}"],
            "account_frame_ids": [],
        },
        "watchlist": [
            {"horizon": "7D", "observable": "Confirmación en segunda raíz", "trigger": "2 raíces"},
            {"horizon": "30D", "observable": "Persistencia de la señal", "trigger": "2 ciclos"},
            {"horizon": "90D", "observable": "Cambio estructural", "trigger": "revisión completa"},
        ],
    }


_FIXTURES = (
    _fixture_candidate(
        "ED-PORT-01", "Reequilibrio sintético de confiabilidad portuaria",
        (92, 78, 64, 22, 80, 70, 82, 78),
        ("GLOBAL", "MARITIME", "PORTS", "IMPORTER", "30D"),
    ),
    _fixture_candidate(
        "ED-AIR-02", "Sustitución modal sintética bajo presión de tiempo",
        (76, 88, 86, 28, 92, 75, 76, 82),
        ("AMERICAS", "AIR", "CAPACITY", "EXPORTER", "7D"),
    ),
    _fixture_candidate(
        "ED-CUSTOMS-03", "Fricción aduanera sintética y costo de inventario",
        (74, 90, 68, 18, 76, 88, 92, 80),
        ("CENTRAL_AMERICA", "ROAD", "CUSTOMS", "PROCUREMENT", "30D"),
    ),
    _fixture_candidate(
        "ED-RISK-04", "Dependencia sintética de corredor y opciones de resiliencia",
        (86, 72, 92, 34, 74, 82, 72, 94),
        ("ASIA_PACIFIC", "RAIL", "RISK", "MANUFACTURER", "90D"),
    ),
    _fixture_candidate(
        "ED-UNCERTAIN-05", "Señal sintética de alto impacto sin resolución suficiente",
        (94, 84, 90, 20, 88, 78, 68, 86),
        ("EUROPE", "MARITIME", "TRADE", "IMPORTER", "7D"),
        uncertainty_block=True,
    ),
    _fixture_candidate(
        "ED-QUARANTINE-06", "Señal sintética con procedencia rota",
        (96, 90, 88, 15, 94, 90, 90, 90),
        ("GLOBAL", "PORT", "INFRASTRUCTURE", "EXPORTER", "30D"),
        quarantine=True,
    ),
)


def editorial_fixture_cycle() -> dict[str, Any]:
    """Return a defensive, deterministic weekly synthetic editorial cycle."""

    result = editorial_cycle(deepcopy(_FIXTURES), min_candidates=3, max_candidates=5)
    result["fixture_class"] = FIXTURE_CLASS
    result["cycle_id"] = "SYNTHETIC-WEEK-001"
    return result
