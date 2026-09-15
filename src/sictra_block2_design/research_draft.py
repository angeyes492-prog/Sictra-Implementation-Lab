"""Source-preserving research copy for local review, separate from E01-E08 fixtures."""
from copy import deepcopy
from hashlib import sha256
from html import escape
import json
import math


class ResearchDraftError(ValueError):
    pass


def fingerprint(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _number(value):
    if value is None:
        return "sin dato"
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ResearchDraftError("OBSERVATION_NUMBER_INVALID")
    return format(value, ".12g")


def compose_research_draft(dossier: dict, package: dict) -> dict:
    """Caller must export the current signed package from the verified B1 store.

    This copies all source claims and limitations. It cannot approve the
    editorial shortlist, assert causes or supply independent corroboration.
    """
    if (dossier.get("dossier_id") != package.get("dossier_id")
            or dossier.get("source", {}).get("content_sha256") != package.get("source_hash")
            or dossier.get("publication_state") != "BLOCKED"
            or dossier.get("contradictions")
            or not dossier.get("facts")):
        raise ResearchDraftError("DOSSIER_NOT_REVIEWABLE")
    claims = []
    for fact in dossier["facts"]:
        change = fact["observed_change"]
        before = _number(change["before_value_thousand_tonnes"])
        after = _number(change["after_value_thousand_tonnes"])
        delta = _number(change["absolute_delta_thousand_tonnes"])
        text = (f"{change['geo_label']} ({change['geo_code']}), {change['time_period']}: "
                f"el registro anterior indica {before}; el nuevo, {after} miles de toneladas. "
                f"Diferencia registrada: {delta} miles de toneladas. "
                f"Tipo de cambio: {change['change_type']}.")
        if change['before_status_flag'] or change['after_status_flag']:
            text += (f" Indicadores de calidad: {change['before_status_flag'] or 'ninguno'} → "
                     f"{change['after_status_flag'] or 'ninguno'}.")
        claims.append({"id": fact["fact_id"], "text": text,
                       "geo_code": change["geo_code"], "evidence": deepcopy(fact["evidence_refs"]),
                       "observation": deepcopy(change)})
    geography = ", ".join(dossier["affected_scope"]["geo_labels"])
    draft = {
        "version": 1, "case_id": package["case_id"], "dossier_id": dossier["dossier_id"],
        "title": f"Cambios en carga marítima: {geography}",
        "lead": f"Eurostat presenta {len(claims)} cambios en el conjunto marítimo observado. "
                "Este borrador describe diferencias entre registros; su causa y efecto empresarial requieren investigación.",
        "claims": claims, "certainty": dossier["certainty"],
        "uncertainties": list(dossier["uncertainties"]), "limitations": list(dossier["limitations"]),
        "questions": list(dossier["executive_questions"]), "next_data": list(dossier["next_data_needs"]),
        "source_hash": package["source_hash"], "evidence_id": package["evidence_id"],
        "source_id": dossier["source"]["source_id"], "expires_at": package["expires_at"],
        "status": "RESEARCH_NEEDED", "publication": "BLOCKED",
        "generator": "LOCAL_SOURCE_TEMPLATE_V1", "acceptance": "NOT_ACCEPTED",
    }
    draft["fingerprint"] = fingerprint(draft)
    return draft


def render_research_brief(draft: dict, adaptation: dict) -> tuple[str, str]:
    """Render already constructed content as inert HTML and accessible text."""
    heading = adaptation["heading"]
    sections = [("Qué cambió", "\n\n".join(x["text"] for x in adaptation["claims"])),
                ("Enfoque de lectura", adaptation["framing"]),
                ("Preguntas para investigar", "\n".join(adaptation["questions"])),
                ("Evidencia que falta", "\n".join(draft["next_data"])),
                ("Incertidumbre", "\n".join(draft["uncertainties"])),
                ("Límites de interpretación", "\n".join(draft["limitations"]))]
    plain = heading + "\n\n" + draft["lead"] + "\n\n" + "\n\n".join(h + "\n" + t for h, t in sections)
    plain += f"\n\nFuente: {draft['source_id']}\nDossier: {draft['dossier_id']}\nEvidencia: {draft['evidence_id']}"
    html = ('<!doctype html><html lang="es"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escape(heading)}</title><style>'
            'body{margin:0;background:#eef3f8;color:#132449;font:17px/1.65 system-ui}'
            'main{max-width:850px;margin:32px auto;background:white;padding:36px;border-top:6px solid #00a78f}'
            'h1{font-size:32px;line-height:1.2}h2{font-size:21px;color:#074abb}'
            'p{white-space:pre-line;overflow-wrap:anywhere}small{color:#526078}'
            '@media(max-width:600px){main{margin:0;padding:20px}}</style></head><body><main>'
            '<small>Telecare OS · Borrador de investigación · Revisión pendiente</small>'
            f'<h1>{escape(heading)}</h1><p>{escape(draft["lead"])}</p>'
            + ''.join(f'<section><h2>{escape(h)}</h2><p>{escape(t)}</p></section>' for h, t in sections)
            + f'<footer><p>Fuente: {escape(draft["source_id"])}<br>Dossier: {escape(draft["dossier_id"])}'
              f'<br>Evidencia: {escape(draft["evidence_id"])}</p></footer></main></body></html>')
    return html, plain
