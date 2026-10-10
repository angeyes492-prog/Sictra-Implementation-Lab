"""Loopback operator controls and review artifacts for the persistent service."""
import base64
import binascii
from hashlib import sha256
from http import HTTPStatus
import json
import re
import secrets
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit

from .web import CommandCenterHandler, CommandCenterServer
from .operations_store import OperationsError
from .factsheet import build_factsheet, render_factsheet
from sictra_block1.research_review import ResearchReview, render_research_review


class OperationsHandler(CommandCenterHandler):
    def _discard_rejected_body(self):
        lengths = self.headers.get_all("Content-Length", [])
        if (len(lengths) != 1 or self.headers.get("Transfer-Encoding") is not None
                or not re.fullmatch(r"[0-9]{1,5}", lengths[0]) or int(lengths[0]) > 16000):
            return
        remaining = int(lengths[0])
        deadline = time.monotonic() + 1
        previous_timeout = self.connection.gettimeout()
        try:
            while remaining:
                allowance = deadline - time.monotonic()
                if allowance <= 0:
                    break
                self.connection.settimeout(allowance)
                chunk = self.rfile.read1(min(4096, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
        except OSError:
            pass  # Denied/cancelled body: no parsing, retry or second response.
        finally:
            try:
                self.connection.settimeout(previous_timeout)
            except OSError:
                pass  # The denied peer may have already closed the socket.

    def _json(self, status, payload, *, before_send=None):
        if before_send is not None:
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            before_send()  # Final fence after serialization, before success headers.
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self._headers(); self.end_headers(); self.wfile.write(body)
            return
        if self.command != "POST" or status != HTTPStatus.FORBIDDEN:
            return super()._json(status, payload)
        self.close_connection = True
        try:
            super()._json(status, payload)
            self.wfile.flush()
            # Closing with unread incoming bytes can reset TCP before the
            # client receives 403. Discard a small framed body, never execute it.
            self._discard_rejected_body()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return

    def do_GET(self):
        path = urlsplit(self.path).path
        if path in {"/research", "/api/research"}:
            if not self._allowed():
                return
            try:
                review = self.server.research_review
                if review is None:
                    self._json(HTTPStatus.NOT_FOUND, {"availability": "NOT_CONFIGURED",
                        "message": "No hay una selección de investigación oficial configurada."})
                    return
                report = review.read()
                if path == "/api/research":
                    review.verify_current(report)
                    self._json(HTTPStatus.OK, report)
                else:
                    body = render_research_review(report).encode("utf-8")
                    review.verify_current(report)
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'; sandbox")
                    self._headers(); self.end_headers(); self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                return
            except Exception:
                self._json(HTTPStatus.CONFLICT, {"availability": "UNAVAILABLE",
                    "message": "La selección no está vigente o no se pudo verificar; sus datos se retiraron."})
            return
        if path not in {"/api/operations", "/health"} and not path.startswith("/api/operations/outputs/"):
            return super().do_GET()
        if not self._allowed():
            return
        try:
            service = self.server.operations
            if path == "/api/operations":
                snapshot = service.snapshot()
                def verify_snapshot():
                    if service.snapshot() != snapshot:
                        raise OperationsError("OPERATIONS_SNAPSHOT_CHANGED_DURING_RENDER")
                self._json(HTTPStatus.OK, {**snapshot, "control_token": self.server.control_token},
                           before_send=verify_snapshot)
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
                # Rendering is not a validity lease. Recheck after the bytes
                # exist and before a success status/header can escape.
                current = build_factsheet(service, suffix[0])
                stable = lambda value: {key: item for key, item in value.items()
                                        if key not in {"observed_at", "sha256"}}
                if stable(current) != stable(sheet):
                    raise OperationsError("FACTSHEET_CHANGED_DURING_RENDER")
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
                def verify_output():
                    if service.output(suffix[0]) != output:
                        raise OperationsError("OUTPUT_CHANGED_DURING_RENDER")
                self._json(HTTPStatus.OK, output, before_send=verify_output)
                return
            body = output["html" if suffix[1] == "html" else "plain_text"].encode()
            if service.output(suffix[0]) != output:
                raise OperationsError("OUTPUT_CHANGED_DURING_RENDER")
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
        if path not in {"/api/operations/control", "/api/operations/profile", "/api/operations/intake", "/api/operations/abstain", "/api/operations/tasks/review", "/api/operations/tasks/link", "/api/operations/tasks/reassess"}:
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
            elif path.endswith("/tasks/review"):
                if not isinstance(value, dict) or set(value) != {"task_id", "reviewer_id", "rationale"}:
                    raise OperationsError("AUTONOMY_TASK_REVIEW_INVALID")
                result = service.acknowledge_autonomy_task(
                    value["task_id"], reviewer_id=value["reviewer_id"], rationale=value["rationale"],
                )
            elif path.endswith("/tasks/link"):
                if not isinstance(value, dict) or set(value) != {"task_id", "evidence_dossier_id"}:
                    raise OperationsError("AUTONOMY_TASK_LINK_INVALID")
                result = service.link_autonomy_task_evidence(value["task_id"], value["evidence_dossier_id"])
            elif path.endswith("/tasks/reassess"):
                if not isinstance(value, dict) or set(value) != {"task_id", "reviewer_id", "rationale", "decision"}:
                    raise OperationsError("AUTONOMY_TASK_REASSESSMENT_INVALID")
                result = service.reassess_autonomy_task(
                    value["task_id"], reviewer_id=value["reviewer_id"],
                    rationale=value["rationale"], decision=value["decision"],
                )
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


def create_operations_server(service, *, port=8768, research_review=None):
    if research_review is not None and not isinstance(research_review, ResearchReview):
        raise OperationsError("RESEARCH_REVIEW_CONFIGURATION_INVALID")
    server = CommandCenterServer(("127.0.0.1", port), OperationsHandler)
    server.operations = service
    server.store = service.cases
    server.worker = service.intake
    server.control_token = secrets.token_urlsafe(32)
    server.research_review = research_review
    return server
