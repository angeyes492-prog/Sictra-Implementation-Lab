"""Loopback-only read model for the Block 3 Precision laboratory."""

from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import webbrowser
from typing import Any, Callable


UI_SCOPE = "BLOCK3_LOCAL_PRECISION_CONSOLE_READ_MODEL"
_WEB_ROOT = Path(__file__).with_name("precision_console")
_STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.css": ("app.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}


def synthetic_workspace() -> dict[str, Any]:
    """Return a transparent demo projection; it is not runtime evidence."""
    return {
        "scope": UI_SCOPE,
        "fixture": "SYNTHETIC_DETERMINISTIC_NOT_EVIDENCE",
        "authority": {"acceptance": "NOT_ACCEPTED", "delivery": "PROHIBITED", "crm_write": "PROHIBITED"},
        "account": {"tenant_id": "TENANT-DEMO", "account_id": "ACCOUNT-DEMO", "official_host": "example.com", "purpose": "SUPERVISED_SHADOW_REVIEW"},
        "dossier": {
            "dossier_id": "DOSSIER-DEMO-001", "state": "OFFICIAL_SITE_DECLARATIONS",
            "captured_at": 1788900000, "expires_at": 1820436000,
            "fingerprint": "3f4f04d33cc9e67a5e602ac4b4c619f3b4a216cc8532548330b8899236463e99",
            "observations": 3, "quarantined": 1,
            "limitations": ["OFFICIAL_WEBSITE_DECLARATION_NOT_INDEPENDENT_FACT", "NO_CRM_WRITE", "NO_DELIVERY"],
        },
        "admission": {
            "disposition": "CONTINUE", "issuer_id": "BLOCK3-ACCOUNT-CONTEXT-INGRESS",
            "policy_id": "account-context-policy:1", "attestation": "VERIFIED_FOR_DEMO_PROJECTION",
            "evidence_state": "CURRENT", "reasons": [],
        },
        "signals": [
            {"dimension": "ACCOUNT", "value": "SUPPLY_CHAIN_COMPLEXITY", "kind": "HYPOTHESIS", "state": "REVIEW_REQUIRED"},
            {"dimension": "DECISION", "value": "OPERATIONAL_CONTINUITY", "kind": "GOVERNED_SIGNAL", "state": "CANDIDATE_NOT_ACCEPTED"},
        ],
        "controls": [
            {"name": "Official-domain boundary", "state": "ENFORCED"},
            {"name": "Context attestation", "state": "VERIFIED_DEMO"},
            {"name": "Human review", "state": "REQUIRED"},
            {"name": "CRM write", "state": "PROHIBITED"},
            {"name": "Message delivery", "state": "PROHIBITED"},
        ],
    }


class PrecisionConsoleServer(ThreadingHTTPServer):
    workspace_loader: Callable[[], dict[str, Any]]


class PrecisionConsoleHandler(BaseHTTPRequestHandler):
    server_version = "SICTrAPrecisionConsole/0.1"

    def log_message(self, format: str, *args: object) -> None:
        return

    def _headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")

    def _json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._headers(); self.end_headers(); self.wfile.write(body)

    def _allowed(self) -> bool:
        port = self.server.server_port
        if self.headers.get("Host") not in {f"127.0.0.1:{port}", f"localhost:{port}"}:
            self._json(HTTPStatus.FORBIDDEN, {"error": "Host local no autorizado."}); return False
        if self.headers.get("Origin") not in {None, f"http://127.0.0.1:{port}", f"http://localhost:{port}"}:
            self._json(HTTPStatus.FORBIDDEN, {"error": "Origen no autorizado."}); return False
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            self._json(HTTPStatus.FORBIDDEN, {"error": "Solicitud cross-site rechazada."}); return False
        return True

    def do_GET(self) -> None:
        if not self._allowed(): return
        path = self.path.split("?", 1)[0]
        if path == "/health":
            self._json(HTTPStatus.OK, {"status": "ok", "scope": UI_SCOPE}); return
        if path == "/api/workspace":
            try: payload = self.server.workspace_loader()
            except Exception:
                self._json(HTTPStatus.CONFLICT, {"error": "La evidencia local no pudo verificarse."}); return
            self._json(HTTPStatus.OK, payload); return
        target = _STATIC.get(path)
        if target is None:
            self._json(HTTPStatus.NOT_FOUND, {"error": "Ruta no disponible."}); return
        filename, content_type = target; body = (_WEB_ROOT / filename).read_bytes()
        self.send_response(HTTPStatus.OK); self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
        self._headers(); self.end_headers(); self.wfile.write(body)

    def _reject_mutation(self) -> None:
        if self._allowed(): self._json(HTTPStatus.METHOD_NOT_ALLOWED, {"error": "La consola de precisión es sólo lectura."})

    do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = _reject_mutation


def create_server(*, host: str = "127.0.0.1", port: int = 8767, workspace_loader: Callable[[], dict[str, Any]] = synthetic_workspace) -> PrecisionConsoleServer:
    if host != "127.0.0.1": raise ValueError("the Precision Console may only bind to 127.0.0.1")
    server = PrecisionConsoleServer((host, port), PrecisionConsoleHandler)
    server.workspace_loader = workspace_loader
    return server


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--port", type=int, default=8767); parser.add_argument("--open", action="store_true")
    args = parser.parse_args(); server = create_server(port=args.port); address = f"http://127.0.0.1:{server.server_port}/"
    print(f"Precision Console disponible en {address}")
    if args.open: webbrowser.open(address)
    try: server.serve_forever()
    except KeyboardInterrupt: return 0
    finally: server.server_close()
    return 0


if __name__ == "__main__": raise SystemExit(main())
