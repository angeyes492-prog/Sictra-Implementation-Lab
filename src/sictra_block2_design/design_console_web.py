"""Local-only Design Console read model for Block 2 trace evidence."""

from __future__ import annotations

import argparse
from datetime import datetime
from hashlib import sha256
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
from urllib.parse import urlsplit
import webbrowser
from typing import Any

from .project_graph import ProjectGraphStore
from .document_evolution import (
    DocumentEditProposal, DocumentEvolutionViolation, ElementEdit,
    persist_document_evolution,
)
from .reference_fixture import reference_run_input
from .traceable_runtime import execute_traceable_block2
from .engine_registry import default_engine_registry, persist_engine_registry
from .design_context import (
    CreateDesignRequest, DesignContextViolation, compile_design_context,
    persist_create_assessment,
)


UI_SCOPE = "BLOCK2_LOCAL_DESIGN_CONSOLE_READ_MODEL"
_WEB_ROOT = Path(__file__).with_name("design_console")
_STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.css": ("app.css", "text/css; charset=utf-8"),
    "/ops.css": ("ops.css", "text/css; charset=utf-8"),
    "/create.css": ("create.css", "text/css; charset=utf-8"),
    "/history.css": ("history.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}


class DesignConsoleServer(ThreadingHTTPServer):
    graph_path: Path
    project_id: str
    edit_token: str


class DesignConsoleHandler(BaseHTTPRequestHandler):
    server_version = "SICTrADesignConsole/0.1"

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
        allowed_origins = {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}
        if self.headers.get("Host") not in allowed_hosts:
            self._send_json(HTTPStatus.FORBIDDEN, {"error": "Host local no autorizado."})
            return False
        origin = self.headers.get("Origin")
        if origin is not None and origin not in allowed_origins:
            self._send_json(HTTPStatus.FORBIDDEN, {"error": "Origen no autorizado."})
            return False
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
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
            "default-src 'self'; connect-src 'self'; style-src 'self'; script-src 'self'; "
            "img-src 'self' data:; font-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'",
        )
        self._base_headers()
        self.end_headers()
        self.wfile.write(encoded)
        return True

    def do_GET(self) -> None:
        if not self._guard_local_request():
            return
        path = urlsplit(self.path).path
        if path == "/health":
            self._send_json(HTTPStatus.OK, {
                "status": "ok", "scope": UI_SCOPE, "project_id": self.server.project_id,
                "publication": "NOT_PUBLISHED", "acceptance": "NOT_ACCEPTED",
            })
            return
        if path == "/api/project":
            with ProjectGraphStore(self.server.graph_path) as graph:
                snapshot = graph.snapshot(self.server.project_id)
            if snapshot is None:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Proyecto no disponible en el grafo local."})
            else:
                self._send_json(HTTPStatus.OK, snapshot)
            return
        if path == "/api/session":
            self._send_json(HTTPStatus.OK, {
                "scope": UI_SCOPE, "edit_token": self.server.edit_token,
                "authority": "CDD_EDIT_PROPOSAL_ONLY",
            })
            return
        if self._send_static(path):
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Ruta no disponible."})

    def do_POST(self) -> None:
        if not self._guard_local_request():
            return
        path = urlsplit(self.path).path
        if path == "/api/create":
            self._handle_create()
            return
        if path != "/api/edits":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Ruta no disponible."})
            return
        if self.headers.get("X-SICTrA-Edit-Token") != self.server.edit_token:
            self._send_json(HTTPStatus.FORBIDDEN, {"error": "Token de edición ausente o inválido."})
            return
        if self.headers.get_content_type() != "application/json":
            self._send_json(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {"error": "Se requiere application/json."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length < 2 or length > 16_384:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Payload de edición vacío o demasiado grande."})
            return
        try:
            payload = json.loads(self.rfile.read(length))
            required = {
                "edit_id", "base_version_id", "base_content_hash", "element_id",
                "field", "value", "actor_id", "created_at",
            }
            if not isinstance(payload, dict) or set(payload) != required:
                raise DocumentEvolutionViolation("SCHEMA_NOT_ALLOWLISTED")
            if payload["field"] not in {"content", "accessibility_label"}:
                raise DocumentEvolutionViolation("UI_FIELD_NOT_ALLOWLISTED")
            created_at = datetime.fromisoformat(payload["created_at"].replace("Z", "+00:00"))
            edit_identity = sha256(
                (payload["edit_id"] + "|" + payload["base_content_hash"]).encode("utf-8")
            ).hexdigest()[:20]
            with ProjectGraphStore(self.server.graph_path) as graph:
                base = graph.load_document(self.server.project_id, payload["base_version_id"])
                if base is None:
                    raise DocumentEvolutionViolation("BASE_VERSION_NOT_FOUND")
                proposal = DocumentEditProposal(
                    payload["edit_id"], "0.1.0", self.server.project_id,
                    base.document_id, payload["base_version_id"], payload["base_content_hash"],
                    "CDD-EDIT-" + edit_identity, payload["actor_id"], created_at,
                    (ElementEdit(
                        "OP-" + payload["edit_id"], payload["element_id"],
                        payload["field"], payload["value"],
                    ),),
                )
                result = persist_document_evolution(graph, proposal)
        except (DocumentEvolutionViolation, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            self._send_json(HTTPStatus.CONFLICT, {"error": str(error) or type(error).__name__})
            return
        self._send_json(HTTPStatus.CREATED if result.store_action == "APPENDED" else HTTPStatus.OK, {
            "store_action": result.store_action,
            "document": {
                "version_id": result.document.version_id,
                "content_hash": result.document.content_hash,
                "state": result.document.state,
            },
            "diff": {
                "diff_id": result.diff.diff_id,
                "domains": list(result.invalidation.reason_domains),
                "entries": len(result.diff.entries),
            },
            "invalidation": {
                "plan_id": result.invalidation.plan_id,
                "preserved": list(result.invalidation.preserved_engines),
                "reexecute": list(result.invalidation.invalidated_engines),
                "state": result.invalidation.state,
            },
            "authority": {"publication": "NOT_PUBLISHED", "acceptance": "NOT_ACCEPTED"},
        })

    def _handle_create(self) -> None:
        if self.headers.get("X-SICTrA-Edit-Token") != self.server.edit_token:
            self._send_json(HTTPStatus.FORBIDDEN, {"error": "Token de Create ausente o inválido."})
            return
        if self.headers.get_content_type() != "application/json":
            self._send_json(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {"error": "Se requiere application/json."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length < 2 or length > 32_768:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Payload de Create vacío o demasiado grande."})
            return
        required = {
            "create_id", "object_id", "source_identity", "fact_ids",
            "evidence_refs", "certainty", "contradictions", "authority_reference",
            "temporal_state", "provenance_refs", "audience", "decision", "task",
            "channel", "success_criterion", "accessibility_requirements",
            "legal_constraints", "channel_constraints", "references_declared",
            "brand_manifest_ref", "reference_rights_manifest_ref", "uncertainty",
            "non_claims", "created_at",
        }
        try:
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict) or set(payload) != required:
                raise DesignContextViolation("CREATE_SCHEMA_NOT_ALLOWLISTED")
            list_fields = {
                "fact_ids", "evidence_refs", "contradictions", "provenance_refs",
                "accessibility_requirements", "legal_constraints", "channel_constraints",
                "uncertainty", "non_claims",
            }
            if any(not isinstance(payload[field], list) for field in list_fields):
                raise DesignContextViolation("CREATE_COLLECTION_NOT_ARRAY")
            if not isinstance(payload["references_declared"], bool):
                raise DesignContextViolation("REFERENCES_DECLARED_NOT_BOOLEAN")
            created_at = datetime.fromisoformat(payload["created_at"].replace("Z", "+00:00"))
            identity = sha256(payload["create_id"].encode("utf-8")).hexdigest()[:20]
            request = CreateDesignRequest(
                payload["create_id"], "0.1.0", self.server.project_id,
                "MESSAGE-" + identity, "TASK-" + identity, "RUN-" + identity,
                "DESIGN-CONSOLE-CREATE", "BLOCK2-E01", "HUMAN-LOCAL-CREATE",
                created_at, payload["object_id"], payload["source_identity"],
                tuple(payload["fact_ids"]), tuple(payload["evidence_refs"]),
                payload["certainty"], tuple(payload["contradictions"]),
                payload["authority_reference"], payload["temporal_state"],
                tuple(payload["provenance_refs"]), payload["audience"],
                payload["decision"], payload["task"], (payload["channel"],),
                payload["success_criterion"], tuple(payload["accessibility_requirements"]),
                tuple(payload["legal_constraints"]), tuple(payload["channel_constraints"]),
                payload["references_declared"], payload["brand_manifest_ref"],
                payload["reference_rights_manifest_ref"], tuple(payload["uncertainty"]),
                tuple(payload["non_claims"]),
            )
            assessment = compile_design_context(request)
            with ProjectGraphStore(self.server.graph_path) as graph:
                action = persist_create_assessment(graph, assessment, created_at=created_at)
        except (DesignContextViolation, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            self._send_json(HTTPStatus.CONFLICT, {"error": str(error) or type(error).__name__})
            return
        envelope = assessment.envelope
        self._send_json(HTTPStatus.CREATED if action == "APPENDED" else HTTPStatus.OK, {
            "store_action": action,
            "disposition": assessment.disposition,
            "reasons": list(assessment.reasons),
            "envelope": None if envelope is None else {
                "message_id": envelope.message_id,
                "fingerprint": envelope.fingerprint,
                "channels": list(envelope.channel_set),
                "state": envelope.state,
            },
            "authority": {"publication": "NOT_PUBLISHED", "acceptance": "NOT_ACCEPTED"},
        })

    def _method_not_allowed(self) -> None:
        if self._guard_local_request():
            self._send_json(HTTPStatus.METHOD_NOT_ALLOWED, {"error": "La consola v0.1 es sólo lectura."})

    do_DELETE = _method_not_allowed
    do_OPTIONS = _method_not_allowed
    do_PATCH = _method_not_allowed
    do_PUT = _method_not_allowed


def create_server(
    graph_path: str | Path,
    project_id: str,
    *,
    host: str = "127.0.0.1",
    port: int = 8766,
) -> DesignConsoleServer:
    if host != "127.0.0.1":
        raise ValueError("the Design Console may only bind to 127.0.0.1")
    server = DesignConsoleServer((host, port), DesignConsoleHandler)
    server.graph_path = Path(graph_path).resolve()
    server.project_id = project_id
    server.edit_token = secrets.token_urlsafe(32)
    return server


def bootstrap_demo(graph_path: str | Path, *, project_id: str = "PROJECT-DEMO") -> None:
    """Write one deterministic synthetic trace; never replace an existing run."""

    now = datetime.fromisoformat("2026-08-30T00:00:00+00:00")
    with ProjectGraphStore(graph_path) as graph:
        persist_engine_registry(
            graph, default_engine_registry(), project_id=project_id, created_at=now,
        )
        execute_traceable_block2(
            reference_run_input(now), graph=graph, project_id=project_id,
            document_id="DOCUMENT-DEMO", actor_id="ACTOR-LOCAL-DEMO",
            run_id="RUN-DESIGN-CONSOLE-DEMO", now=now,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-db", required=True)
    parser.add_argument("--project-id", default="PROJECT-DEMO")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--bootstrap-demo", action="store_true")
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()
    if args.bootstrap_demo:
        bootstrap_demo(args.trace_db, project_id=args.project_id)
    server = create_server(args.trace_db, args.project_id, port=args.port)
    address = f"http://127.0.0.1:{server.server_port}/"
    print(f"Design Console disponible en {address}")
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
