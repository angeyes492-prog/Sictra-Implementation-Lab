"""Explicit generic audience presentation policy; no person/intent inference."""
from copy import deepcopy
from sictra_block2_design.design_artifact import fingerprint


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


def adapt_content_design(design, profile, *, now):
    validate_profile(profile, now=now)
    if design.get("version") != 1:
        raise AudiencePolicyError("UNSUPPORTED_CONTENT_DESIGN_VERSION")
    if (design.get("artifact_type") != "CONTENT_DESIGN_CANDIDATE"
            or design.get("fingerprint") != fingerprint({k: v for k, v in design.items() if k != "fingerprint"})):
        raise AudiencePolicyError("DESIGN_ARTIFACT_INVALID")
    blocks_by_kind = {block.get("kind") for block in design.get("content_blocks", ()) if isinstance(block, dict)}
    required = {"CONTEXT", "REVIEW_QUESTIONS", "EVIDENCE_GAP", "UNCERTAINTY", "LIMITATION", "PROVENANCE"}
    if not required.issubset(blocks_by_kind):
        raise AudiencePolicyError("DESIGN_ARTIFACT_REQUIRED_BLOCK_MISSING")
    claim_ids = {claim.get("id") for claim in design.get("claims", ()) if isinstance(claim, dict)}
    observed_ids = {claim_id for block in design["content_blocks"] if block["kind"] == "OBSERVED_CHANGE"
                    for claim_id in block.get("source_claim_ids", ())}
    if not claim_ids or observed_ids != claim_ids:
        raise AudiencePolicyError("DESIGN_ARTIFACT_CLAIM_LINEAGE_INVALID")
    selected = [deepcopy(c) for c in design["claims"]
                if not profile["geo_codes"] or c["geo_code"] in profile["geo_codes"]]
    if not selected:
        raise AudiencePolicyError("NO_GEOGRAPHIC_MATCH")
    total = len(selected)
    if profile["depth"] == "BRIEF":
        selected = selected[:3]
    heading = ("Resumen ejecutivo" if profile["tone"] == "EXECUTIVE" else "Nota técnica") + ": " + design["title"]
    framing = f"Lectura preparada para el perfil editorial «{profile['label']}», función declarada: {profile['role']}. "
    framing += ("Priorice las preguntas de decisión y contraste la exposición de su organización con datos propios."
                if profile["tone"] == "EXECUTIVE" else
                "Contraste unidades, periodos, cobertura e indicadores de calidad antes de comparar series.")
    if total > len(selected):
        framing += f" Se muestran {len(selected)} de {total} observaciones relevantes; el dossier conserva todas."
    claim_ids = {claim["id"] for claim in selected}
    blocks = []
    for block in design["content_blocks"]:
        if block["kind"] == "OBSERVED_CHANGE" and not claim_ids.intersection(block["source_claim_ids"]):
            continue
        blocks.append(deepcopy(block))
    question_block = next(block for block in blocks if block["kind"] == "REVIEW_QUESTIONS")
    question_block["body"] = "\n".join(list(profile["questions"]) + question_block["body"].split("\n"))
    if total > len(selected):
        question_block["body"] += f"\nLa vista muestra {len(selected)} de {total} observaciones relevantes; el dossier conserva todas."
    result = {"version": 1, "profile_id": profile["id"], "profile_fingerprint": fingerprint(profile),
              "artifact_fingerprint": design["fingerprint"], "heading": heading, "framing": framing,
              "content_blocks": blocks,
              "channel": "LOCAL_REVIEW", "level": "DECLARED_GENERIC_AUDIENCE",
              "status": "DESIGN_REVIEW_REQUIRED", "publication": "BLOCKED", "delivery": "NONE"}
    result["fingerprint"] = fingerprint(result)
    return result


def adapt_research_draft(draft, profile, *, now):
    """Refuse the retired source-draft handoff in the active design route."""
    raise AudiencePolicyError("LEGACY_RESEARCH_DRAFT_UNSUPPORTED")
