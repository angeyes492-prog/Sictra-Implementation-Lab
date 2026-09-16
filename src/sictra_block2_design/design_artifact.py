"""Block 2 content-design artifacts built from a typed Block 1 handoff.

Block 2 owns information architecture, visual components and presentation
constraints.  It preserves, but never reinterprets, Block 1 observations.
"""
from copy import deepcopy
from hashlib import sha256
from html import escape
import json
import math


class DesignArtifactError(ValueError):
    """A source handoff cannot safely become a design candidate."""


def fingerprint(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _number(value):
    if value is None:
        return "sin dato"
    if type(value) not in (int, float) or not math.isfinite(value):
        raise DesignArtifactError("OBSERVATION_NUMBER_INVALID")
    return format(value, ".12g")


def _block(block_id, kind, title, body, source_claim_ids=()):
    return {"id": block_id, "kind": kind, "title": title, "body": body,
            "source_claim_ids": list(source_claim_ids)}


def compose_content_design(dossier: dict, package: dict) -> dict:
    """Create a reviewable Block 2 design candidate from literal B1 facts.

    The candidate owns *how* evidence is presented: an evidence-first visual
    hierarchy, component order, and fixed use of uncertainty.  The source
    claims remain exact copies and causal or commercial conclusions remain out
    of scope.
    """
    if (dossier.get("dossier_id") != package.get("dossier_id")
            or dossier.get("source", {}).get("content_sha256") != package.get("source_hash")
            or dossier.get("publication_state") != "BLOCKED"
            or dossier.get("contradictions")
            or not dossier.get("facts")):
        raise DesignArtifactError("DOSSIER_NOT_DESIGNABLE")

    claims, change_blocks = [], []
    for fact in dossier["facts"]:
        change = fact["observed_change"]
        if "before_value_thousand_tonnes" in change:
            before = _number(change["before_value_thousand_tonnes"])
            after = _number(change["after_value_thousand_tonnes"])
            delta = _number(change["absolute_delta_thousand_tonnes"])
            subject = f"{change['geo_label']} ({change['geo_code']})"
            period = change["time_period"]
            unit = "miles de toneladas"
            claim_key, claim_value = "geo_code", change["geo_code"]
        elif "before_value_usd_million" in change:
            before = _number(change["before_value_usd_million"])
            after = _number(change["after_value_usd_million"])
            delta = _number(change["absolute_delta_usd_million"])
            subject = change["customs_point"]
            period = f"{change['before_period']} → {change['after_period']}"
            unit = "millones de US$ CIF"
            claim_key, claim_value = "customs_point", change["customs_point"]
        else:
            raise DesignArtifactError("OBSERVATION_UNIT_UNSUPPORTED")
        claim = {
            "id": fact["fact_id"], claim_key: claim_value,
            "observation": deepcopy(change), "evidence": deepcopy(fact["evidence_refs"]),
            "text": (f"{subject}, {period}: {before} → {after} {unit}; "
                     f"diferencia registrada: {delta} {unit}. Tipo: {change['change_type']}.")}
        claims.append(claim)
        change_blocks.append(_block(
            "change-" + fact["fact_id"], "OBSERVED_CHANGE", f"{subject} · {period}",
            claim["text"], (fact["fact_id"],)))

    is_customs = "customs_points" in dossier["affected_scope"]
    geography = ("Honduras" if is_customs else
                 ", ".join(dossier["affected_scope"]["geo_labels"]))
    design = {
        "version": 1,
        "artifact_type": "CONTENT_DESIGN_CANDIDATE",
        "format": "REVIEW_NEWSLETTER",
        "case_id": package["case_id"], "dossier_id": dossier["dossier_id"],
        "title": (f"Cambios en importaciones CIF por aduana: {geography}" if is_customs
                  else f"Cambios en carga marítima: {geography}"),
        "source_hash": package["source_hash"], "evidence_id": package["evidence_id"],
        "source_id": dossier["source"]["source_id"], "expires_at": package["expires_at"],
        "claims": claims,
        "design_system": {
            "id": "TELECARE_EVIDENCE_EDITORIAL_V1", "hierarchy": "EVIDENCE_FIRST",
            "tokens": {"accent": "#00a78f", "ink": "#132449", "surface": "#ffffff", "canvas": "#eef3f8"},
            "accessibility": ["TEXT_EQUIVALENT", "SOURCE_ID_VISIBLE", "UNCERTAINTY_VISIBLE", "NO_COLOR_ONLY_MEANING"],
        },
        "content_blocks": [
            _block("context", "CONTEXT", "Qué se observó",
                   f"La fuente {dossier['source']['source_id']} registra {len(claims)} cambios. "
                   "Este diseño presenta observaciones, no explica sus causas ni impacto comercial."),
            *change_blocks,
            _block("questions", "REVIEW_QUESTIONS", "Preguntas para investigación", "\n".join(dossier["executive_questions"])),
            _block("missing-evidence", "EVIDENCE_GAP", "Evidencia que falta", "\n".join(dossier["next_data_needs"])),
            _block("uncertainty", "UNCERTAINTY", "Incertidumbre", "\n".join(dossier["uncertainties"])),
            _block("limits", "LIMITATION", "Límites de interpretación", "\n".join(dossier["limitations"])),
            _block("provenance", "PROVENANCE", "Procedencia",
                   f"Fuente: {dossier['source']['source_id']}\nDossier: {dossier['dossier_id']}\nEvidencia: {package['evidence_id']}"),
        ],
        "status": "DESIGN_CANDIDATE_NOT_ACCEPTED", "review": "HUMAN_REVIEW_REQUIRED",
        "publication": "BLOCKED", "delivery": "NONE", "acceptance": "NOT_ACCEPTED",
        "generator": "LOCAL_CONTENT_DESIGN_V1",
    }
    design["fingerprint"] = fingerprint(design)
    return design


def render_designed_review_artifact(design: dict, adaptation: dict) -> tuple[str, str]:
    """Render a B2 design candidate after B3 has selected its declared view."""
    if (adaptation.get("artifact_fingerprint") != design.get("fingerprint")
            or adaptation.get("fingerprint") != fingerprint({k: v for k, v in adaptation.items() if k != "fingerprint"})):
        raise DesignArtifactError("ADAPTATION_ARTIFACT_BINDING_INVALID")
    heading = adaptation["heading"]
    blocks = adaptation["content_blocks"]
    plain = heading + "\n\n" + adaptation["framing"] + "\n\n" + "\n\n".join(
        block["title"] + "\n" + block["body"] for block in blocks)
    html = ('<!doctype html><html lang="es"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escape(heading)}</title><style>'
            'body{margin:0;background:#eef3f8;color:#132449;font:17px/1.65 system-ui}'
            'main{max-width:850px;margin:32px auto;background:white;padding:36px;border-top:6px solid #00a78f}'
            '.eyebrow{color:#0b6a5d;font-size:12px;font-weight:700;letter-spacing:.09em}'
            'h1{font-size:32px;line-height:1.2}h2{font-size:21px;color:#074abb}'
            'section{border-top:1px solid #d8e1ea;padding-top:16px;margin-top:18px}'
            'p{white-space:pre-line;overflow-wrap:anywhere}small{color:#526078}'
            '@media(max-width:600px){main{margin:0;padding:20px}}</style></head><body><main>'
            '<p class="eyebrow">TELECARE OS · BOLETÍN DE REVISIÓN · PENDIENTE HUMANA</p>'
            f'<h1>{escape(heading)}</h1><p>{escape(adaptation["framing"])}</p>'
            + ''.join(f'<section data-block-kind="{escape(block["kind"])}"><h2>{escape(block["title"])}</h2>'
                      f'<p>{escape(block["body"])}</p></section>' for block in blocks)
            + '</main></body></html>')
    return html, plain
