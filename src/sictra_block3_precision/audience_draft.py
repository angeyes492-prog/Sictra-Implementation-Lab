"""Explicit generic audience presentation policy; no person/intent inference."""
from copy import deepcopy
from sictra_block2_design.research_draft import fingerprint


class AudiencePolicyError(ValueError):
    pass


PROFILE_FIELDS = {"id", "label", "role", "depth", "tone", "geo_codes", "questions", "expires_at"}


def validate_profile(profile, *, now):
    if not isinstance(profile, dict) or set(profile) != PROFILE_FIELDS:
        raise AudiencePolicyError("PROFILE_SCHEMA_INVALID")
    for key in ("id", "label", "role"):
        if not isinstance(profile[key], str) or not profile[key].strip() or len(profile[key]) > 150:
            raise AudiencePolicyError("PROFILE_TEXT_INVALID")
    if profile["depth"] not in {"BRIEF", "DETAILED"} or profile["tone"] not in {"EXECUTIVE", "TECHNICAL"}:
        raise AudiencePolicyError("PROFILE_PRESENTATION_INVALID")
    for field in ("geo_codes", "questions"):
        if (not isinstance(profile[field], list) or len(profile[field]) > 20
                or any(not isinstance(x, str) or not x.strip() or len(x) > 500 for x in profile[field])):
            raise AudiencePolicyError("PROFILE_LIST_INVALID")
    if type(profile["expires_at"]) is not int or profile["expires_at"] <= now:
        raise AudiencePolicyError("PROFILE_EXPIRED")


def adapt_research_draft(draft, profile, *, now):
    validate_profile(profile, now=now)
    if draft.get("fingerprint") != fingerprint({k: v for k, v in draft.items() if k != "fingerprint"}):
        raise AudiencePolicyError("DRAFT_FINGERPRINT_INVALID")
    selected = [deepcopy(c) for c in draft["claims"]
                if not profile["geo_codes"] or c["geo_code"] in profile["geo_codes"]]
    if not selected:
        raise AudiencePolicyError("NO_GEOGRAPHIC_MATCH")
    total = len(selected)
    if profile["depth"] == "BRIEF":
        selected = selected[:3]
    heading = ("Resumen ejecutivo" if profile["tone"] == "EXECUTIVE" else "Nota técnica") + ": " + draft["title"]
    framing = f"Lectura preparada para el perfil editorial «{profile['label']}», función declarada: {profile['role']}. "
    framing += ("Priorice las preguntas de decisión y contraste la exposición de su organización con datos propios."
                if profile["tone"] == "EXECUTIVE" else
                "Contraste unidades, periodos, cobertura e indicadores de calidad antes de comparar series.")
    if total > len(selected):
        framing += f" Se muestran {len(selected)} de {total} observaciones relevantes; el dossier conserva todas."
    result = {"version": 1, "profile_id": profile["id"], "profile_fingerprint": fingerprint(profile),
              "draft_fingerprint": draft["fingerprint"], "heading": heading, "framing": framing,
              "claims": selected, "questions": list(profile["questions"]) + list(draft["questions"]),
              "channel": "LOCAL_REVIEW", "level": "DECLARED_GENERIC_AUDIENCE",
              "status": "RESEARCH_NEEDED", "publication": "BLOCKED", "delivery": "NONE"}
    result["fingerprint"] = fingerprint(result)
    return result
