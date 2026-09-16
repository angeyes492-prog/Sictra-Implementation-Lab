"""Local persistent operations: source dossiers, design artifacts, audiences."""
from datetime import datetime, timezone
from hashlib import sha256
import argparse
import logging
import json
import os
from pathlib import Path
import threading
import time

from sictra_block1.operator_pipeline import initialize_operator_pipeline, load_operator_pipeline
from sictra_block1.hn_customs_pipeline import (
    HNCustomsPipelineViolation, initialize_hn_customs_pipeline,
    parse_hn_customs_workbook,
)
from sictra_block1.manual_source_preflight import (
    ManualSourcePreflightViolation, preflight_manual_source_file,
)
from sictra_block2_design.design_artifact import (
    DesignArtifactError, compose_content_design, fingerprint, render_designed_review_artifact,
)
from sictra_block3_precision.audience_draft import adapt_content_design, validate_profile, AudiencePolicyError
from .local_worker import LocalIntakeWorker
from .producer_adapters import (
    Block1DossierPackageAdapter, CompositeDossierPackageAdapter,
    HNCustomsDossierPackageAdapter,
)
from .runtime import FederatedContractError, FederatedOrchestratorStore
from .operations_store import OperationsError, OperationsStore, process_lock


def initialize(root, *, now=None):
    root = Path(root).absolute()
    if root.is_symlink():
        raise OperationsError("STATE_PATH_INVALID")
    root.mkdir(parents=True, exist_ok=True)
    for name in ("inbox", "dropbox", "keys", "backups", "catalog"):
        (root / name).mkdir(exist_ok=True)
    # Missing legacy keys in an existing state must never silently generate new
    # identity. The HN key is an explicit additive migration and is created only
    # when its state does not yet exist.
    existing = (root / "operations.sqlite").exists()
    for name in ("operations", "packages", "intake", "recovery"):
        path = root / "keys" / (name + ".key")
        if not path.exists():
            if existing:
                raise OperationsError("EXISTING_STATE_KEY_MISSING")
            with path.open("xb") as stream:
                stream.write(os.urandom(32))
    hn_path = root / "keys" / "hn-customs.key"
    if not hn_path.exists():
        hn_state = root / "hn-customs"
        if hn_state.exists() and (hn_state.is_symlink() or any(hn_state.iterdir())):
            raise OperationsError("EXISTING_HN_CUSTOMS_KEY_MISSING")
        with hn_path.open("xb") as stream:
            stream.write(os.urandom(32))
    initialize_operator_pipeline(root / "pipeline", clock=lambda: int(now if now is not None else time.time()))
    hn_key = (root / "keys" / "hn-customs.key").read_bytes()
    initialize_hn_customs_pipeline(
        root / "hn-customs", key=hn_key,
        clock=lambda: int(now if now is not None else time.time()),
    )
    service = OperationsService(root, clock=(lambda: now) if now is not None else time.time)
    if not service.store.latest("PROFILE"):
        service.add_profile({"id": "logistics-general", "label": "Lectura logística general",
            "role": "Lector de investigación marítima", "depth": "DETAILED", "tone": "TECHNICAL",
            "geo_codes": [], "questions": [], "expires_at": int(service.clock()) + 365 * 86400})
    return service


class OperationsService:
    def __init__(self, root, *, clock=time.time):
        # Keep the operator-selected lexical path.  On packaged Windows
        # runtimes ``resolve()`` can rewrite it into an app-local virtual
        # directory, leaving the operator unable to locate the configured
        # inbox, backup, or recovery boundary.
        self.root = Path(root).absolute()
        if self.root.is_symlink():
            raise OperationsError("STATE_PATH_INVALID")
        self.clock = clock
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.last_cycle = None
        self.last_error = None
        self.thread = None
        self._seen_files = {}
        def key(name):
            path = self.root / "keys" / (name + ".key")
            if path.is_symlink():
                raise OperationsError("KEY_PATH_INVALID")
            return path.read_bytes()
        self.store = OperationsStore(self.root / "operations.sqlite", key("operations"))
        self.pipeline = self.root / "pipeline"
        self.hn_pipeline = self.root / "hn-customs"
        self.hn_key = key("hn-customs")
        self.intake = LocalIntakeWorker(self.root / "intake.sqlite", inbox=self.root / "inbox",
            pipeline=self.pipeline, hn_pipeline=self.hn_pipeline, hn_key=self.hn_key,
            key=key("intake"), clock=lambda: int(self.clock()))
        self.package_key = key("packages")
        self.recovery_key = key("recovery")
        self.cases = FederatedOrchestratorStore(self.root / "cases.sqlite", integrity_key=self.package_key)
        self.exporter = CompositeDossierPackageAdapter(
            eurostat=Block1DossierPackageAdapter(pipeline=self.pipeline, package_key=self.package_key),
            hn_customs=HNCustomsDossierPackageAdapter(
                pipeline=self.hn_pipeline, integrity_key=self.hn_key,
                package_key=self.package_key,
            ),
        )

    def add_profile(self, profile):
        validate_profile(profile, now=int(self.clock()))
        with self.lock:
            self.store.put("PROFILE", profile["id"], profile)

    def register_file(self, source, *, expected_sha256, geo_level="COUNTRY", source_type="EUROSTAT_TRAN_R_MAGO_NM"):
        path = Path(source)
        if path.is_symlink() or path.suffix.lower() != ".xlsx":
            raise OperationsError("INPUT_NOT_ALLOWED")
        with path.open("rb") as stream:
            data = stream.read(8_388_609)
        if len(data) > 8_388_608 or sha256(data).hexdigest() != expected_sha256:
            raise OperationsError("INPUT_HASH_OR_SIZE_INVALID")
        destination = self.root / "inbox" / (expected_sha256 + ".xlsx")
        if destination.is_symlink():
            raise OperationsError("INPUT_PATH_INVALID")
        if destination.exists():
            if destination.read_bytes() != data:
                raise OperationsError("RETAINED_INPUT_CHANGED")
        else:
            with destination.open("xb") as stream:
                stream.write(data)
        with self.lock:
            return self.intake.enqueue(
                destination.name, expected_sha256=expected_sha256,
                geo_level=geo_level, source_type=source_type,
            )

    def retain_context_catalog(self, source, *, expected_sha256, catalog_id):
        """Retain an exact operator-supplied XLSX as context, never observations."""
        if (not isinstance(catalog_id, str) or not catalog_id.strip()
                or len(catalog_id) > 128):
            raise OperationsError("CATALOG_ID_INVALID")
        path = Path(source)
        if path.is_symlink() or not path.is_file() or path.suffix.lower() != ".xlsx":
            raise OperationsError("CATALOG_INPUT_NOT_ALLOWED")
        if path.stat().st_size > 8_388_608:
            raise OperationsError("CATALOG_HASH_OR_SIZE_INVALID")
        with path.open("rb") as stream:
            data = stream.read(8_388_609)
        if len(data) > 8_388_608 or sha256(data).hexdigest() != expected_sha256:
            raise OperationsError("CATALOG_HASH_OR_SIZE_INVALID")
        try:
            preflight = preflight_manual_source_file(path.name, data)
        except ManualSourcePreflightViolation as error:
            raise OperationsError("CATALOG_PREFLIGHT_REJECTED") from error
        if preflight.get("status") != "READY_FOR_SCHEMA_REVIEW" or preflight.get("format") != "XLSX":
            raise OperationsError("CATALOG_PREFLIGHT_REJECTED")
        destination = self.root / "catalog" / (expected_sha256 + ".xlsx")
        if destination.is_symlink():
            raise OperationsError("CATALOG_PATH_INVALID")
        if destination.exists():
            if destination.read_bytes() != data:
                raise OperationsError("CATALOG_RETAINED_BYTES_CHANGED")
        else:
            with destination.open("xb") as stream:
                stream.write(data)
        record = {
            "catalog_id": catalog_id.strip(), "raw_sha256": expected_sha256,
            "retained_file": destination.name, "retained_at": int(self.clock()),
            "classification": "CONTEXT_CATALOG_NOT_OBSERVATIONAL_EVIDENCE",
            "runtime_effect": "NONE", "publication": "BLOCKED",
        }
        self.store.put("SOURCE_CATALOG", record["catalog_id"], record, immutable=True)
        return record

    def _catalog_snapshot(self):
        records = list(self.store.latest("SOURCE_CATALOG").values())
        for record in records:
            path = self.root / "catalog" / record["retained_file"]
            if (path.is_symlink() or not path.is_file()
                    or path.stat().st_size > 8_388_608):
                raise OperationsError("CATALOG_INTEGRITY_ERROR")
            with path.open("rb") as stream:
                payload = stream.read(8_388_609)
            if sha256(payload).hexdigest() != record["raw_sha256"]:
                raise OperationsError("CATALOG_INTEGRITY_ERROR")
        return records

    def set_paused(self, paused):
        if type(paused) is not bool:
            raise OperationsError("PAUSE_INVALID")
        with self.lock:
            self.store.put("CONTROL", "pause", {"paused": paused})
            self.intake.set_paused(paused)

    def is_paused(self):
        return self.store.latest("CONTROL").get("pause", {}).get("paused", False)

    def enable_watch(self, enabled):
        if type(enabled) is not bool:
            raise OperationsError("WATCH_VALUE_INVALID")
        self.store.put("CONTROL", "watch", {"enabled": enabled})

    def execute_orchestrated_run(self):
        """Start one bounded, fully local source-to-review cycle.

        This is the only orchestrator action that enables the approved local
        source monitor and advances all four blocks. It does not clear a human
        pause/stop, fetch a network source, infer a customer, or publish an
        artifact. Future stable files are picked up by the running worker.
        """
        with self.lock:
            now = int(self.clock())
            if self.stop_event.is_set() or (self.root / "STOP").exists():
                self.stop_event.set()
                return {"status": "STOPPED", "reason": "EXPLICIT_STOP_REQUIRES_RESTART"}
            if self.is_paused():
                return {"status": "PAUSED", "reason": "HUMAN_PAUSE_PRESERVED"}
            run_id = sha256((str(now) + os.urandom(16).hex()).encode()).hexdigest()
            request = {"run_id": run_id, "requested_at": now,
                       "source_boundary": "APPROVED_LOCAL_DROPBOX",
                       "route": ["BLOCK1_INTELLIGENCE", "BLOCK2_DESIGN", "BLOCK3_PRECISION", "BLOCK4_ORCHESTRATOR"],
                       "publication": "BLOCKED", "delivery": "NONE"}
            self.store.put("ORCHESTRATION_REQUEST", run_id, request, immutable=True)
            self.enable_watch(True)
            cycle = self.tick(max_cases=32)
            result = {**request, "completed_at": int(self.clock()), "cycle": cycle,
                      "status": "ORCHESTRATION_EXECUTED"}
            self.store.put("ORCHESTRATION_RESULT", run_id, result, immutable=True)
            return result

    def scan_inbox(self):
        """Only the configured local dropbox, never arbitrary or remote paths.

        Require unchanged bytes in two consecutive scans before registration.
        Existing B1 approval/schema checks still apply during ingestion.
        """
        if not self.store.latest("CONTROL").get("watch", {}).get("enabled", False):
            return
        directory = self.root / "dropbox"
        if directory.is_symlink():
            raise OperationsError("WATCH_DIRECTORY_INVALID")
        seen = {}
        paths = sorted(directory.iterdir())
        if len(paths) > 128:
            raise OperationsError("WATCH_DIRECTORY_CAPACITY_EXCEEDED")
        for path in paths:
            if path.is_symlink() or not path.is_file() or path.suffix.lower() != ".xlsx":
                continue
            if path.stat().st_size > 8_388_608:
                continue
            with path.open("rb") as stream:
                data = stream.read(8_388_609)
            if len(data) > 8_388_608:
                continue
            digest = sha256(data).hexdigest()
            seen[path.name] = digest
            if self._seen_files.get(path.name) == digest:
                try:
                    parse_hn_customs_workbook(path.name, data)
                    source_type, geo_level = "HN_CUSTOMS_Q1_V1", "CUSTOMS_POINT"
                except HNCustomsPipelineViolation:
                    source_type, geo_level = "EUROSTAT_TRAN_R_MAGO_NM", "COUNTRY"
                self.register_file(path, expected_sha256=digest, geo_level=geo_level, source_type=source_type)
        self._seen_files = seen

    def abstain_intake(self, job_id, reason):
        with self.lock:
            receipt = self.intake.recovery_receipt(job_id, decision="ABSTAIN", actor_id="local-operator",
                reason=reason, recovery_key=self.recovery_key)
            return self.intake.recover(receipt, recovery_key=self.recovery_key)

    def defer_evidence_reviews(self, enabled):
        if type(enabled) is not bool:
            raise OperationsError('REVIEW_POLICY_INVALID')
        with self.lock:
            self.store.put('CONTROL', 'deferred-evidence-review',
                {'enabled': enabled, 'publication': 'BLOCKED', 'acceptance': 'NOT_ACCEPTED'})

    def _close_review_waits_by_abstention(self):
        if not self.store.latest('CONTROL').get('deferred-evidence-review', {}).get('enabled', False):
            return
        for job in self.intake.snapshot()['jobs']:
            result = job.get('result') or {}
            # Only a successfully retained delta awaiting interpretation is
            # deferrable. Crashes, tamper, expiry and ingestion errors never are.
            if (job['state'] != 'REVIEW_REQUIRED' or 'error_type' in result
                    or result.get('status') != 'DELTA_DETECTED_NOT_EVIDENCE'
                    or result.get('publication_authority') != 'NONE'
                    or result.get('dossier', {}).get('publication_state') != 'BLOCKED'):
                continue
            dossier_id = result['dossier']['dossier_id']
            try:
                package = self.exporter.export(dossier_id, now=datetime.fromtimestamp(self.clock(), timezone.utc))
            except FederatedContractError:
                continue
            if job['job_id'] not in self.store.latest('DEFERRED_REVIEW'):
                self.store.put('DEFERRED_REVIEW', job['job_id'], {
                    'job_id': job['job_id'], 'dossier_id': dossier_id,
                    'at': int(self.clock()), 'state': 'CLOSED_BY_ABSTENTION_EVIDENCE_DEFERRED',
                    'certainty': package['certainty'], 'uncertainty': package.get('uncertainty', []),
                    'publication': 'BLOCKED', 'acceptance': 'NOT_ACCEPTED',
                    'reason': 'Owner-enabled construction mode: retain missing evidence for later review; do not approve content.'}, immutable=True)
            receipt = self.intake.recovery_receipt(job['job_id'], decision='ABSTAIN',
                actor_id='local-deferred-review-policy', reason='Evidence review deferred; content not accepted; next approved source may proceed.',
                recovery_key=self.recovery_key)
            self.intake.recover(receipt, recovery_key=self.recovery_key)

    def tick(self, *, max_cases=16):
        if type(max_cases) is not int or not 1 <= max_cases <= 32:
            raise OperationsError("CASE_BUDGET_INVALID")
        with self.lock:
            now = int(self.clock())
            if self.stop_event.is_set() or (self.root / "STOP").exists():
                self.stop_event.set()
                return {"state": "STOPPED"}
            if self.is_paused():
                self.last_cycle = now
                return {"state": "PAUSED"}
            self.scan_inbox()
            intake_result = self.intake.run(max_jobs=1)
            # Both source adapters verify their own stores and authority before
            # returning a dossier. One source can never stand in for the other.
            dossiers = self.exporter.list_dossiers(now=datetime.fromtimestamp(now, timezone.utc))
            profiles = self.store.latest("PROFILE")
            outputs = self.store.latest("OUTPUT")
            work = [(d, p) for d in dossiers for p in profiles.values()]
            outcome = []
            cursor = self.store.latest("CURSOR").get("designs", {}).get("position", 0)
            if work:
                cursor %= len(work)
                batch = (work[cursor:] + work[:cursor])[:max_cases]
                for dossier, profile in batch:
                    if self.stop_event.is_set() or (self.root / "STOP").exists():
                        self.stop_event.set()
                        break
                    identity = fingerprint([dossier["dossier_id"], fingerprint(profile)])
                    if identity in outputs:
                        continue
                    current = datetime.fromtimestamp(self.clock(), timezone.utc)
                    try:
                        validate_profile(profile, now=int(current.timestamp()))
                        package = self.exporter.export(dossier["dossier_id"], now=current)
                        self.cases.ingest(package, now=current)
                        design = compose_content_design(dossier, package)
                        if self.store.latest("ENV").get("data", {}).get("class") == "SYNTHETIC_PILOT":
                            design["title"] = "PRUEBA SINTÉTICA · " + design["title"]
                            design["content_blocks"][0]["body"] = (
                                "Datos de prueba generados localmente; no representan una publicación real de Eurostat. "
                                + design["content_blocks"][0]["body"])
                            design["fingerprint"] = fingerprint({k: v for k, v in design.items() if k != "fingerprint"})
                        adaptation = adapt_content_design(design, profile, now=int(current.timestamp()))
                        html, plain = render_designed_review_artifact(design, adaptation)
                        # Recheck mutable source controls before committing a completed artifact.
                        if self.exporter.export(dossier["dossier_id"], now=datetime.fromtimestamp(self.clock(), timezone.utc)) != package:
                            raise OperationsError("SOURCE_CHANGED_DURING_EXECUTION")
                        value = {"id": identity, "created_at": int(self.clock()), "case_id": package["case_id"],
                            "dossier_id": dossier["dossier_id"], "profile": profile, "design_artifact": design,
                            "adaptation": adaptation, "html": html, "plain_text": plain,
                            "html_sha256": sha256(html.encode()).hexdigest(),
                            "state": "DESIGN_REVIEW_REQUIRED", "review": "HUMAN_REVIEW_REQUIRED",
                            "stages": ["BLOCK1_DOSSIER_VERIFIED", "BLOCK2_CONTENT_DESIGN", "BLOCK3_AUDIENCE_ADAPTATION"],
                            "publication": "BLOCKED", "delivery": "NONE"}
                        self.store.put("OUTPUT", identity, value, immutable=True)
                        outcome.append({"id": identity, "state": "DESIGN_READY_FOR_REVIEW"})
                    except (FederatedContractError, DesignArtifactError, AudiencePolicyError) as error:
                        self.store.put("WAIT", identity, {"dossier_id": dossier["dossier_id"], "reason": str(error)})
                        outcome.append({"id": identity, "state": "WAITING", "reason": str(error)})
                self.store.put("CURSOR", "designs", {"position": (cursor + len(batch)) % len(work)})
            self._close_review_waits_by_abstention()
            self.last_cycle, self.last_error = int(self.clock()), None
            return {"state": "RUNNING", "intake": intake_result[-1]["state"], "outcomes": outcome}

    def output(self, identity):
        value = self.store.latest("OUTPUT").get(identity)
        if value is None:
            raise OperationsError("OUTPUT_NOT_FOUND")
        # Older source-to-draft records do not satisfy the current Block 2
        # contract.  Refuse them explicitly instead of rendering a partially
        # compatible artifact under the new design boundary.
        if "design_artifact" not in value:
            raise OperationsError("LEGACY_OUTPUT_REQUIRES_MIGRATION")
        now = int(self.clock())
        validate_profile(value["profile"], now=now)
        if self.store.latest("PROFILE").get(value["profile"]["id"]) != value["profile"]:
            raise OperationsError("PROFILE_SUPERSEDED")
        package = self.exporter.export(value["dossier_id"], now=datetime.fromtimestamp(now, timezone.utc))
        if package["source_hash"] != value["design_artifact"]["source_hash"]:
            raise OperationsError("SOURCE_SUPERSEDED")
        return value

    def snapshot(self):
        with self.lock:
            paused = self.is_paused()
            active = self.thread is not None and self.thread.is_alive() and not self.stop_event.is_set()
            status = "ERROR" if self.last_error else "PAUSED" if paused else "RUNNING" if active else "STOPPED"
            summaries = []
            for identity, value in self.store.latest("OUTPUT").items():
                try:
                    self.output(identity)
                    availability = "CURRENT"
                except (OperationsError, FederatedContractError, DesignArtifactError, AudiencePolicyError):
                    availability = "STALE_OR_REVOKED"
                summaries.append({"id": identity, "title": value["adaptation"]["heading"],
                    "profile": value["profile"]["label"], "case_id": value["case_id"], "dossier_id": value["dossier_id"],
                    "created_at": value["created_at"], "availability": availability, "state": value["state"]})
            done = self.store.latest("OUTPUT")
            runs = self.store.latest("ORCHESTRATION_RESULT")
            latest_run = max(runs.values(), key=lambda item: item["requested_at"], default=None)
            return {"status": status, "last_cycle": self.last_cycle, "error": self.last_error,
                    "source_catalogs": self._catalog_snapshot(),
                    "evidence_review_deferred": self.store.latest('CONTROL').get('deferred-evidence-review', {}).get('enabled', False),
                    "deferred_reviews": list(self.store.latest('DEFERRED_REVIEW').values()),
                    "watch_enabled": self.store.latest("CONTROL").get("watch", {}).get("enabled", False),
                    "watch_directory": str(self.root / "dropbox"),
                    "intake_waiting": [{"job_id": j["job_id"], "state": j["state"]} for j in self.intake.snapshot()["jobs"]
                                        if j["state"] in {"RUNNING", "REVIEW_REQUIRED"}],
                    "profiles": list(self.store.latest("PROFILE").values()), "outputs": summaries,
                    "waiting": [v for k, v in self.store.latest("WAIT").items() if k not in done],
                    "scope": "LABORATORY_INTERNAL_SUPERVISED", "publication": "BLOCKED",
                    "data_class": self.store.latest("ENV").get("data", {}).get("class", "OPERATOR_SUPPLIED_FILES"),
                    "generator": "LOCAL_CONTENT_DESIGN_V1",
                    "orchestration": {"source_monitor": "ACTIVE" if self.store.latest("CONTROL").get("watch", {}).get("enabled", False) else "INACTIVE",
                                      "last_run": latest_run}}

    def serve_loop(self, interval=5):
        if type(interval) is not int or not 1 <= interval <= 60:
            raise OperationsError("INTERVAL_INVALID")
        while not self.stop_event.is_set():
            try:
                self.tick()
                today = datetime.fromtimestamp(self.clock(), timezone.utc).date().isoformat()
                directory = self.root / "backups" / today
                if not directory.exists():
                    self.store.backup(directory)
                else:
                    self.store.verify_backup(directory)
            except Exception as error:
                self.last_error = type(error).__name__
                logging.exception("Operations worker stopped; no automatic error recovery")
                self.stop_event.set()
            if self.stop_event.wait(interval):
                break

    def start(self, interval=5):
        if type(interval) is not int or not 1 <= interval <= 60:
            raise OperationsError("INTERVAL_INVALID")
        if self.stop_event.is_set() or (self.root / "STOP").exists():
            raise OperationsError("WORKER_STOP_REQUIRES_EXPLICIT_RESET")
        if self.thread is not None and self.thread.is_alive():
            raise OperationsError("WORKER_ALREADY_RUNNING")
        self.thread = threading.Thread(target=self.serve_loop, args=(interval,), daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=15)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init")
    commands.add_parser("status")
    commands.add_parser("run-once")
    commands.add_parser("pause")
    commands.add_parser("resume")
    commands.add_parser("stop")
    commands.add_parser("reset-stop")
    commands.add_parser("watch-inbox")
    register = commands.add_parser("register")
    register.add_argument("file", type=Path)
    register.add_argument("--sha256", required=True)
    register.add_argument("--geo-level", default="COUNTRY", choices=("COUNTRY", "NUTS1", "NUTS2"))
    profile = commands.add_parser("profile")
    profile.add_argument("file", type=Path)
    backup = commands.add_parser("backup")
    backup.add_argument("directory", type=Path)
    restore = commands.add_parser("restore")
    restore.add_argument("directory", type=Path)
    restore.add_argument("destination", type=Path)
    serve = commands.add_parser("serve")
    serve.add_argument("--port", type=int, default=8768)
    serve.add_argument("--interval", type=int, default=5)
    args = parser.parse_args()
    service = initialize(args.state) if args.command == "init" else OperationsService(args.state)
    if args.command == "serve":
        from .operations_web import create_operations_server
        with process_lock(service.root / "service.lock"):
            server = create_operations_server(service, port=args.port)
            service.start(args.interval)
            print(f"Telecare OS: http://127.0.0.1:{server.server_port}/", flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                service.stop()
                server.server_close()
        return 0
    if args.command == "register":
        print(service.register_file(args.file, expected_sha256=args.sha256, geo_level=args.geo_level))
    elif args.command == "profile":
        service.add_profile(json.loads(args.file.read_text(encoding="utf-8")))
    elif args.command == "run-once":
        with process_lock(service.root / "service.lock"):
            print(json.dumps(service.tick()))
    elif args.command in {"pause", "resume"}:
        service.set_paused(args.command == "pause")
    elif args.command == "stop":
        (service.root / "STOP").touch()
    elif args.command == "reset-stop":
        with process_lock(service.root / "service.lock"):
            (service.root / "STOP").unlink(missing_ok=True)
    elif args.command == "watch-inbox":
        service.enable_watch(True)
    elif args.command == "backup":
        print(json.dumps(service.store.backup(args.directory)))
    elif args.command == "restore":
        service.store.restore(args.directory, args.destination)
    else:
        print(json.dumps(service.snapshot(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
