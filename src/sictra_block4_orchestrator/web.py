"""Loopback-only Block 4 Command Center for the bounded federation runtime."""

from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .runtime import FederatedContractError, FederatedOrchestratorStore, build_controlled_block1_package


UI_SCOPE = "BLOCK4_LOCAL_FEDERATED_ORCHESTRATOR"
WEB_ROOT = Path(__file__).with_name("command_center")
STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.css": ("app.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}


class CommandCenterServer(ThreadingHTTPServer):
    store: FederatedOrchestratorStore


def _case_payload(item: Any) -> dict[str, Any]:
    return {
        "case_id": item.case_id, "run_id": item.run_id, "state": item.state,
        "retry_count": item.retry_count, "fingerprint": item.fingerprint,
        "source_hash": item.source_hash, "provenance_root": item.provenance_root,
        "certainty": item.certainty, "disposition": item.disposition,
        "expires_at": item.expires_at, "lineage": list(item.lineage),
        "restrictions": list(item.restrictions),
    }


class CommandCenterHandler(BaseHTTPRequestHandler):
    server_version = "SICTrAOrchestrator/0.1"

    def log_message(self, _format: str, *args: object) -> None: return

    def _headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")

    def _allowed(self) -> bool:
        port = self.server.server_port
        if self.headers.get("Host") not in {f"127.0.0.1:{port}", f"localhost:{port}"}:
            self._json(HTTPStatus.FORBIDDEN, {"error": "Host local no autorizado."}); return False
        if self.headers.get("Origin") not in {None, f"http://127.0.0.1:{port}", f"http://localhost:{port}"}:
            self._json(HTTPStatus.FORBIDDEN, {"error": "Origen no autorizado."}); return False
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            self._json(HTTPStatus.FORBIDDEN, {"error": "Solicitud cross-site rechazada."}); return False
        return True

    def _json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body))); self._headers(); self.end_headers(); self.wfile.write(body)

    def _static(self, path: str) -> bool:
        target = STATIC.get(path)
        if target is None: return False
        name, content_type = target; body = (WEB_ROOT / name).read_bytes()
        self.send_response(HTTPStatus.OK); self.send_header("Content-Type", content_type); self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; font-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
        self._headers(); self.end_headers(); self.wfile.write(body); return True

    def do_GET(self) -> None:
        if not self._allowed(): return
        path = urlsplit(self.path).path
        try:
            if path == "/health":
                self._json(HTTPStatus.OK, {"status": "ok", "scope": UI_SCOPE, "authority": "HUMAN_REVIEW_REQUIRED", "publication": "PROHIBITED"}); return
            if path == "/api/cases":
                cases = [_case_payload(item) for item in self.server.store.list_cases()]
                self._json(HTTPStatus.OK, {"scope": UI_SCOPE, "fixture": "CONTROLLED_LOCAL_PACKAGES_ONLY", "cases": cases, "authority": {"publication": "PROHIBITED", "delivery": "PROHIBITED", "acceptance": "NOT_ACCEPTED"}}); return
            if path.startswith("/api/cases/") and path.endswith("/events"):
                case_id = path.removeprefix("/api/cases/").removesuffix("/events").rstrip("/")
                self._json(HTTPStatus.OK, {"case_id": case_id, "events": self.server.store.audit_events(case_id)}); return
            if self._static(path): return
            self._json(HTTPStatus.NOT_FOUND, {"error": "Ruta no disponible."})
        except FederatedContractError as error:
            self._json(HTTPStatus.CONFLICT, {"error": str(error)})
        except Exception:
            self._json(HTTPStatus.CONFLICT, {"error": "El journal local no pudo verificarse."})

    def _reject_mutation(self) -> None:
        if self._allowed(): self._json(HTTPStatus.METHOD_NOT_ALLOWED, {"error": "El Command Center es sólo lectura; la aprobación humana ocurre fuera de esta interfaz."})

    do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = _reject_mutation


def create_server(store: FederatedOrchestratorStore, *, host: str = "127.0.0.1", port: int = 8768) -> CommandCenterServer:
    if host != "127.0.0.1": raise ValueError("the Command Center may only bind to 127.0.0.1")
    server = CommandCenterServer((host, port), CommandCenterHandler); server.store = store; return server


def _read_key(path: Path, *, bootstrap_demo: bool) -> bytes:
    if path.exists(): return path.read_bytes()
    if not bootstrap_demo: raise ValueError("integrity key file is required")
    key = os.urandom(32); path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(key); return key


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", required=True); parser.add_argument("--integrity-key-file", required=True)
    parser.add_argument("--port", type=int, default=8768); parser.add_argument("--bootstrap-demo", action="store_true")
    args = parser.parse_args(); key = _read_key(Path(args.integrity_key_file), bootstrap_demo=args.bootstrap_demo)
    store = FederatedOrchestratorStore(args.store, integrity_key=key)
    if args.bootstrap_demo and not store.list_cases():
        item = store.ingest(build_controlled_block1_package(integrity_key=key)); store.process_to_human_gate(item.case_id)
    server = create_server(store, port=args.port); print(f"Command Center disponible en http://127.0.0.1:{server.server_port}/")
    try: server.serve_forever()
    except KeyboardInterrupt: return 0
    finally: server.server_close()


if __name__ == "__main__": raise SystemExit(main())
