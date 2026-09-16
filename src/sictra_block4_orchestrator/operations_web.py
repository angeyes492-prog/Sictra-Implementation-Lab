"""Loopback operator controls and review artifacts for the persistent service."""
import base64
import binascii
from hashlib import sha256
from http import HTTPStatus
import json
import secrets
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

from .web import CommandCenterHandler, CommandCenterServer
from .operations_store import OperationsError
from .factsheet import build_factsheet, render_factsheet


class OperationsHandler(CommandCenterHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path not in {"/api/operations", "/health"} and not path.startswith("/api/operations/outputs/"):
            return super().do_GET()
        if not self._allowed():
            return
        try:
            service = self.server.operations
            if path == "/api/operations":
                self._json(HTTPStatus.OK, {**service.snapshot(), "control_token": self.server.control_token})
                return
            if path == "/health":
                status = service.snapshot()
                self._json(HTTPStatus.OK if status["status"] in {"RUNNING", "PAUSED"} else HTTPStatus.SERVICE_UNAVAILABLE,
                           {"status": status["status"], "last_cycle": status["last_cycle"], "scope": status["scope"]})
                return
            suffix = path.removeprefix("/api/operations/outputs/").split("/")
            if len(suffix) != 2 or suffix[1] not in {"html", "text", "json", "factsheet", "factsheet.json"}:
                self._json(HTTPStatus.NOT_FOUND, {"error": "OUTPUT_ROUTE_INVALID"})
                return
            if suffix[1] in {"factsheet", "factsheet.json"}:
                sheet = build_factsheet(service, suffix[0])
                is_json = suffix[1] == 'factsheet.json'
                body = (json.dumps(sheet, ensure_ascii=False, indent=2) if is_json else render_factsheet(sheet)).encode()
                self.send_response(HTTPStatus.OK)
                self.send_header('Content-Type', ('application/json' if is_json else 'text/html') + '; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                if is_json:
                    self.send_header('Content-Disposition', 'attachment; filename="telecare-' + suffix[0] + '.json"')
                self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'; sandbox")
                self._headers(); self.end_headers(); self.wfile.write(body)
                return
            output = service.output(suffix[0])
            if suffix[1] == "json":
                self._json(HTTPStatus.OK, output)
                return
            body = output["html" if suffix[1] == "html" else "plain_text"].encode()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/" + ("html" if suffix[1] == "html" else "plain") + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'; sandbox")
            self._headers()
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return  # Browser cancelled the read; never send a second response.
        except Exception:
            self._json(HTTPStatus.CONFLICT, {"error": "No se pudo verificar la vigencia o integridad del resultado."})

    def do_POST(self):
        path = urlsplit(self.path).path
        if path not in {"/api/operations/control", "/api/operations/profile", "/api/operations/intake", "/api/operations/abstain"}:
            return super().do_POST()
        if not self._allowed():
            return
        expected_origin = f"http://{self.headers.get('Host')}"
        if (self.headers.get("Origin") != expected_origin
                or not secrets.compare_digest(self.headers.get("X-Telecare-Control", ""), self.server.control_token)
                or self.headers.get("Content-Type") != "application/json"
                or self.headers.get("Transfer-Encoding") is not None):
            self._json(HTTPStatus.FORBIDDEN, {"error": "Solicitud de control no autorizada."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= (12_000_000 if path.endswith("/intake") else 16000):
                raise OperationsError("REQUEST_SIZE_INVALID")
            self.connection.settimeout(10)
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise OperationsError("REQUEST_INCOMPLETE")
            value = json.loads(raw)
            service = self.server.operations
            if path.endswith("/control"):
                if not isinstance(value, dict) or set(value) != {"action"} or value["action"] not in {"execute", "pause", "resume", "stop", "watch", "unwatch", "defer-reviews", "require-reviews"}:
                    raise OperationsError("CONTROL_INVALID")
                if value["action"] == "execute":
                    result = service.execute_orchestrated_run()
                elif value['action'] in {'defer-reviews', 'require-reviews'}:
                    service.defer_evidence_reviews(value['action'] == 'defer-reviews')
                    result = {'status': 'REVIEW_POLICY_RECORDED'}
                elif value["action"] in {"watch", "unwatch"}:
                    service.enable_watch(value["action"] == "watch")
                    result = {"status": "RECORDED"}
                elif value["action"] == "stop":
                    (service.root / "STOP").touch()
                    service.stop_event.set()
                    result = {"status": "RECORDED"}
                else:
                    if value["action"] == "resume" and service.stop_event.is_set():
                        raise OperationsError("RESTART_SERVICE_REQUIRED")
                    service.set_paused(value["action"] == "pause")
                    result = {"status": "RECORDED"}
            elif path.endswith("/abstain"):
                if not isinstance(value, dict) or set(value) != {"job_id", "reason"}:
                    raise OperationsError("RECOVERY_REQUEST_INVALID")
                result = service.abstain_intake(value["job_id"], value["reason"])
            elif path.endswith("/profile"):
                service.add_profile(value)
                result = {"status": "PROFILE_CONFIGURED"}
            else:
                if (not isinstance(value, dict)
                        or set(value) not in ({"content", "sha256", "geo_level"},
                                             {"content", "sha256", "geo_level", "source_type"})
                        or value.get("source_type", "EUROSTAT_TRAN_R_MAGO_NM")
                        not in {"EUROSTAT_TRAN_R_MAGO_NM", "HN_CUSTOMS_Q1_V1"}):
                    raise OperationsError("INTAKE_SCHEMA_INVALID")
                content = base64.b64decode(value["content"], validate=True)
                if len(content) > 8_388_608 or sha256(content).hexdigest() != value["sha256"]:
                    raise OperationsError("INPUT_HASH_OR_SIZE_INVALID")
                with tempfile.TemporaryDirectory(prefix="telecare-upload-") as directory:
                    source = Path(directory) / "approved.xlsx"
                    source.write_bytes(content)
                    job_id = service.register_file(
                        source, expected_sha256=value["sha256"], geo_level=value["geo_level"],
                        source_type=value.get("source_type", "EUROSTAT_TRAN_R_MAGO_NM"),
                    )
                result = {"status": "QUEUED", "job_id": job_id}
            self._json(HTTPStatus.OK, result)
        except Exception as error:
            self._json(HTTPStatus.BAD_REQUEST, {"error": "No se admitió la solicitud.", "reason": type(error).__name__})


def create_operations_server(service, *, port=8768):
    server = CommandCenterServer(("127.0.0.1", port), OperationsHandler)
    server.operations = service
    server.store = service.cases
    server.worker = service.intake
    server.control_token = secrets.token_urlsafe(32)
    return server
