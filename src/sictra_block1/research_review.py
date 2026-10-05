"""Read-only review of exact official candidates; never admission or resolution."""
from hashlib import sha256
from html import escape
import re
import time

from .research_acquisition import ResearchAcquisitionError, ResearchQuarantine, canonical
from .research_admission import prepare_admission_review
from .national_methodology import review_national_methodology


class ResearchReview:
    def __init__(self, quarantine, data_id, metadata_id, *, national_id=None,
                 clock=lambda: int(time.time())):
        if (not isinstance(quarantine, ResearchQuarantine) or not callable(clock)
                or any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
                       for value in (data_id, metadata_id))
                or national_id is not None and
                (not isinstance(national_id, str) or not re.fullmatch(r"[0-9a-f]{64}", national_id))):
            raise ResearchAcquisitionError("RESEARCH_REVIEW_CONFIGURATION_INVALID")
        self.quarantine, self.data_id, self.metadata_id = quarantine, data_id, metadata_id
        self.national_id, self.clock = national_id, clock

    def _time(self):
        now = self.clock()
        if type(now) is not int or now < 0:
            raise ResearchAcquisitionError("RESEARCH_REVIEW_CLOCK_INVALID")
        return now

    def _inputs(self, now):
        admission = prepare_admission_review(self.quarantine, self.data_id,
                                            self.metadata_id, clock=lambda: now)
        national = (review_national_methodology(self.quarantine, self.national_id,
                    clock=lambda: now) if self.national_id else None)
        if national and (national["terms_candidate_id"] != admission["terms"]["candidate_id"]
                         or national["terms_content_sha256"] != admission["terms"]["content_sha256"]):
            raise ResearchAcquisitionError("RESEARCH_REVIEW_TERMS_MISMATCH")
        return admission, national

    def read(self):
        started = self._time()
        admission, national = self._inputs(started)
        finish = self._time()
        if finish < started:
            raise ResearchAcquisitionError("RESEARCH_REVIEW_CLOCK_REGRESSED")
        if canonical((admission, national)) != canonical(self._inputs(finish)):
            raise ResearchAcquisitionError("RESEARCH_REVIEW_INPUT_CHANGED")
        expires = min(admission["expires_at"], national["expires_at"] if national else admission["expires_at"])
        final = self._time()
        if final < finish or final >= expires:
            raise ResearchAcquisitionError("RESEARCH_REVIEW_NOT_CURRENT")
        report = {
            "version": "0.1.0", "scope": "LABORATORY_INTERNAL_SUPERVISED",
            "availability": "CURRENT_CANDIDATES", "checked_at": final, "expires_at": expires,
            "admission_review": admission, "national_methodology": national,
            "needs": [
                {"kind": "INDEPENDENT_CORROBORATION", "state": "INSUFFICIENT EVIDENCE",
                 "reason": "No independently established root for the same metric, unit, place, period and coverage.",
                 "next_action": "REQUEST_COMPARABLE_APPROVED_SOURCE"},
                {"kind": "SOURCE_METHODOLOGY", "state": "INSUFFICIENT EVIDENCE",
                 "reason": "General official methodology is retained; no release-specific revision explanation is established.",
                 "next_action": "REQUEST_RELEASE_SPECIFIC_EXPLANATION"},
                {"kind": "COMPANY_EXPOSURE", "state": "INSUFFICIENT EVIDENCE",
                 "reason": "Publisher statistics contain no authorized company exposure data.",
                 "next_action": "REQUEST_AUTHORIZED_COMPANY_EXPOSURE"},
            ],
            "resolution": "NOT_RESOLVED", "acceptance": "NOT_ACCEPTED",
            "runtime_effect": "NONE", "publication": "BLOCKED", "admission": "NOT_ADMITTED",
        }
        report["fingerprint"] = sha256(canonical(report)).hexdigest()
        return report

    def verify_current(self, report):
        """Fence current bytes and expiry again after response preparation."""
        now = self._time()
        if (not isinstance(report, dict) or report.get("fingerprint") != sha256(canonical(
                {key: value for key, value in report.items() if key != "fingerprint"})).hexdigest()
                or not report["checked_at"] <= now < report["expires_at"]):
            raise ResearchAcquisitionError("RESEARCH_REVIEW_NOT_CURRENT")
        if canonical(self._inputs(now)) != canonical((report["admission_review"], report["national_methodology"])):
            raise ResearchAcquisitionError("RESEARCH_REVIEW_INPUT_CHANGED")
        final = self._time()
        if not now <= final < report["expires_at"]:
            raise ResearchAcquisitionError("RESEARCH_REVIEW_NOT_CURRENT")


def render_research_review(report):
    """Render application-owned escaped text, not publisher HTML."""
    admission = report["admission_review"]
    data = admission["data"]
    e = lambda value: escape(str(value), quote=True)
    rows = "".join(
        f'<tr><td>{e(row["geo_code"])}</td><td>{e(row["time_period"])}</td>'
        f'<td>{"No disponible" if row["missing"] else e(row["value_thousand_tonnes"])}</td>'
        f'<td>{e(row["status_flag"] or "—")}</td></tr>' for row in data["observations"])
    needs = "".join(f'<li><strong>{e(n["kind"])} · {e(n["state"])}</strong><p>{e(n["reason"])}</p>'
                    f'<p>Siguiente dato: {e(n["next_action"])}</p></li>' for n in report["needs"])
    sections = "".join(f'<details><summary>{e(section["anchor"])}</summary><p>{e(section["text"])}</p></details>'
                       for section in admission["methodology"]["sections"])
    national = report["national_methodology"]
    national_html = ""
    if national:
        national_html = ('<h2>Origen y método nacional</h2><p>Documento alojado por Eurostat; '
            'no aporta por sí solo otra raíz independiente.</p>' +
            "".join(f'<details><summary>{e(s["anchor"])}</summary><p>{e(s["text"])}</p></details>'
                    for s in national["sections"]))
    return ('<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        '<title>Telecare OS · Investigación oficial</title><style>body{font:17px system-ui;max-width:960px;'
        'margin:2rem auto;padding:0 1rem;color:#16333a;background:#f5faf9}table{border-collapse:collapse;width:100%}'
        'th,td{text-align:left;padding:.7rem;border-bottom:1px solid #bdd3ce}details{padding:.7rem;background:white;'
        'margin:.5rem 0}p{white-space:pre-wrap;overflow-wrap:anywhere}li{margin:1.2rem 0}code{overflow-wrap:anywhere}</style>'
        '<main><h1>Investigación oficial retenida</h1><p>Laboratorio supervisado · candidatos en cuarentena · admisión pendiente.</p>'
        f'<h2>{e(data["dataset_title"])}</h2><p>Bélgica · carga marítima cargada y descargada · miles de toneladas · 2023–2024.</p>'
        '<p>Son dos años distintos de una publicación, no dos versiones ni una revisión estadística demostrada.</p>'
        '<table><caption>Valores publicados aún no admitidos</caption><thead><tr><th>Geografía</th><th>Año</th>'
        '<th>Miles de toneladas</th><th>Bandera de estado</th></tr></thead><tbody>' + rows + '</tbody></table>'
        f'<p>Actualización del editor: {e(data["publisher_updated_raw"])}</p>'
        f'<p>Vigencia local de esta selección: hasta UTC epoch {e(report["expires_at"])}; cada lectura verifica de nuevo los originales.</p>'
        f'<p>Fuente oficial: <a href="{e(data["source_url"])}" rel="noreferrer">Eurostat</a></p>'
        f'<p>SHA-256 de bytes originales: <code>{e(data["content_sha256"])}</code></p>'
        f'<p>Aviso de reutilización retenido: <code>{e(admission["terms"]["candidate_id"])}</code></p>'
        '<h2>Necesidades que siguen abiertas</h2><ul>' + needs + '</ul><h2>Metodología oficial general</h2>' + sections + national_html +
        '<h2>Frontera de esta revisión</h2><p>NOT_ADMITTED · NOT_RESOLVED · NOT_ACCEPTED · Publicación BLOCKED.</p>'
        '<p>No se ha creado aprobación, evidencia atestada, tarea resuelta ni efecto en otro bloque.</p>'
        '<p><a href="/api/research">Leer revisión JSON con procedencia y requisitos de admisión</a></p></main></html>')
