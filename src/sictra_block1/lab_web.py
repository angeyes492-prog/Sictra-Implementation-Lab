"""Local-only product workspace for bounded Block 1 field tests."""

from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit
import webbrowser
from typing import Any

from .editorial import (
    EditorialContractViolation,
    editorial_fixture_cycle,
    select_flagship,
)
from .lab import LAB_SCOPE, SCENARIOS, execute_scenario
from .logistics import (
    FIXTURE_CLASS,
    WORKSPACE_SCOPE,
    LogisticsContractViolation,
    compare_investigation_strategies,
    get_investigation,
    workspace_catalog,
)
from .source_portfolio import source_readiness

UI_SCOPE = "BLOCK1_LOCAL_INTELLIGENCE_PRODUCT_UI"
_WEB_ROOT = Path(__file__).with_name("web")
_STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.css": ("app.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}
_MAX_REJECTED_PAYLOAD_BYTES = 65_536


def _summary(report: dict[str, Any]) -> dict[str, str]:
    enforcement = report["result"]["enforcement"]["status"]
    records = report["memory_record_count"]
    scenario = report["scenario"]
    if scenario == "valid" and enforcement == "COMMITTED" and records == 1:
        return {"status": "COMMITTED", "title": "Efecto controlado registrado", "message": "La prueba válida completó un único efecto local y controlado."}
    if scenario != "valid" and enforcement == "NOT_EXECUTED" and records == 0:
        return {"status": "BLOCKED_CORRECTLY", "title": "Bloqueado correctamente", "message": "El sistema no registró ningún efecto ante esta condición de prueba."}
    return {"status": "UNEXPECTED", "title": "Resultado inesperado", "message": "El resultado no cumple el patrón esperado; revisa el detalle técnico."}


class LabWebHandler(BaseHTTPRequestHandler):
    server_version = "SICTrAIntelligenceWorkspace/0.3"

    def log_message(self, format: str, *args: object) -> None:
        return

    def _base_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self._base_headers()
        self.end_headers()
        self.wfile.write(encoded)

    def _guard_local_request(self) -> bool:
        port = self.server.server_port
        allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        host = self.headers.get("Host")
        origin = self.headers.get("Origin")
        fetch_site = self.headers.get("Sec-Fetch-Site")
        allowed_origins = {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}
        if host not in allowed_hosts:
            self._send_json(HTTPStatus.FORBIDDEN, {"error": "Host local no autorizado."})
            return False
        if origin is not None and origin not in allowed_origins:
            self._send_json(HTTPStatus.FORBIDDEN, {"error": "Origen no autorizado."})
            return False
        if fetch_site == "cross-site":
            self._send_json(HTTPStatus.FORBIDDEN, {"error": "Solicitud cross-site rechazada."})
            return False
        return True

    def _send_static(self, path: str) -> bool:
        target = _STATIC_FILES.get(path)
        if target is None:
            return False
        filename, content_type = target
        encoded = (_WEB_ROOT / filename).read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; connect-src 'self'; style-src 'self'; "
            "script-src 'self'; img-src 'self'; font-src 'self'; base-uri 'none'; "
            "frame-ancestors 'none'; form-action 'none'",
        )
        self._base_headers()
        self.end_headers()
        self.wfile.write(encoded)
        return True

    def _has_forbidden_payload(self) -> bool:
        """Drain small rejected bodies so a local client reliably receives 400."""

        if self.headers.get("Transfer-Encoding") is not None:
            self.close_connection = True
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Este endpoint no acepta payload."})
            return True
        raw_length = self.headers.get("Content-Length")
        if raw_length in {None, "0"}:
            return False
        try:
            length = int(raw_length)
        except ValueError:
            self.close_connection = True
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Este endpoint no acepta payload."})
            return True
        if length < 1 or length > _MAX_REJECTED_PAYLOAD_BYTES:
            self.close_connection = True
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Este endpoint no acepta payload."})
            return True
        self.rfile.read(length)
        self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Este endpoint no acepta payload."})
        return True

    def do_GET(self) -> None:
        if not self._guard_local_request():
            return
        parsed = urlsplit(self.path)
        if parsed.path == "/health":
            self._send_json(HTTPStatus.OK, {
                "status": "ok", "scope": UI_SCOPE,
                "workspace_scope": WORKSPACE_SCOPE, "fixture_class": FIXTURE_CLASS,
            })
            return
        if parsed.path == "/api/workspace":
            self._send_json(HTTPStatus.OK, workspace_catalog())
            return
        if parsed.path == "/api/source-readiness":
            query = parse_qs(parsed.query, strict_parsing=False)
            region, domain = query.get("region", []), query.get("domain", [])
            if set(query) != {"region", "domain"} or len(region) != 1 or len(domain) != 1:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Se requieren region y domain una sola vez."})
                return
            try:
                self._send_json(HTTPStatus.OK, source_readiness(region=region[0], domain=domain[0]))
            except ContractViolation as error:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return
        if parsed.path == "/api/editorial":
            if parsed.query:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Este endpoint no acepta query string."})
                return
            self._send_json(HTTPStatus.OK, editorial_fixture_cycle())
            return
        editorial_candidate_prefix = "/api/editorial/candidates/"
        if parsed.path.startswith(editorial_candidate_prefix):
            suffix = unquote(parsed.path[len(editorial_candidate_prefix):])
            if not suffix or "/" in suffix or parsed.query:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Candidato editorial no disponible."})
                return
            cycle = editorial_fixture_cycle()
            candidate = next(
                (item for item in cycle["candidates"] if item["candidate_id"] == suffix),
                None,
            )
            assessment = next(
                (item for item in cycle["assessments"] if item["candidate_id"] == suffix),
                None,
            )
            if candidate is None or assessment is None:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Candidato editorial no disponible."})
            else:
                self._send_json(HTTPStatus.OK, {
                    "scope": cycle["scope"],
                    "fixture_class": cycle["fixture_class"],
                    "shortlisted": suffix in cycle["shortlist_ids"],
                    "candidate": candidate,
                    "assessment": assessment,
                })
            return
        comparison_prefix = "/api/comparisons/"
        if parsed.path.startswith(comparison_prefix):
            investigation_id = unquote(parsed.path[len(comparison_prefix):])
            query = parse_qs(parsed.query, strict_parsing=False)
            left, right = query.get("left", []), query.get("right", [])
            if set(query) != {"left", "right"} or len(left) != 1 or len(right) != 1:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Se requieren left y right una sola vez."})
                return
            if get_investigation(investigation_id) is None:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Investigación no disponible."})
                return
            try:
                result = compare_investigation_strategies(investigation_id, left[0], right[0])
            except LogisticsContractViolation as error:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            else:
                self._send_json(HTTPStatus.OK, result)
            return
        prefix = "/api/investigations/"
        if parsed.path.startswith(prefix):
            suffix = unquote(parsed.path[len(prefix):])
            if not suffix or "/" in suffix:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Investigación no disponible."})
                return
            investigation = get_investigation(suffix)
            if investigation is None:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Investigación no disponible."})
            else:
                self._send_json(HTTPStatus.OK, investigation)
            return
        if self._send_static(parsed.path):
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Ruta no disponible."})

    def do_POST(self) -> None:
        if not self._guard_local_request():
            return
        parsed = urlsplit(self.path)
        editorial_prefix = "/api/editorial/selections/"
        if parsed.path.startswith(editorial_prefix):
            candidate_id = unquote(parsed.path[len(editorial_prefix):])
            if not candidate_id or "/" in candidate_id or parsed.query:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Candidato editorial no disponible."})
                return
            cycle = editorial_fixture_cycle()
            if candidate_id not in {item["candidate_id"] for item in cycle["candidates"]}:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Candidato editorial no disponible."})
                return
            if self._has_forbidden_payload():
                return
            try:
                result = select_flagship(
                    cycle, candidate_id, selected_by="LOCAL_HUMAN_OPERATOR"
                )
            except EditorialContractViolation as error:
                self._send_json(HTTPStatus.CONFLICT, {"error": str(error)})
            else:
                self._send_json(HTTPStatus.OK, result)
            return
        prefix = "/api/scenarios/"
        if not parsed.path.startswith(prefix):
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Ruta no disponible."})
            return
        scenario = parsed.path[len(prefix):]
        if scenario not in SCENARIOS or "/" in scenario:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Escenario no disponible."})
            return
        if self._has_forbidden_payload():
            return
        try:
            report = dict(execute_scenario(scenario, store_path=":memory:"))
            self._send_json(HTTPStatus.OK, {
                "scope": UI_SCOPE, "lab_scope": LAB_SCOPE, "scenario": scenario,
                "summary": _summary(report), "report": report,
            })
        except Exception as error:
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {
                "error": f"Error local del laboratorio: {type(error).__name__}"
            })

    def _method_not_allowed(self) -> None:
        if not self._guard_local_request():
            return
        self._send_json(HTTPStatus.METHOD_NOT_ALLOWED, {"error": "Método no disponible."})

    do_DELETE = _method_not_allowed
    do_OPTIONS = _method_not_allowed
    do_PATCH = _method_not_allowed
    do_PUT = _method_not_allowed


def create_server(*, host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    if host != "127.0.0.1":
        raise ValueError("the product workspace may only bind to 127.0.0.1")
    return ThreadingHTTPServer((host, port), LabWebHandler)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true", help="Open the local workspace.")
    args = parser.parse_args()
    server = create_server(port=args.port)
    address = f"http://127.0.0.1:{server.server_port}/"
    print(f"Intelligence Workspace disponible en {address}")
    if args.open:
        webbrowser.open(address)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
