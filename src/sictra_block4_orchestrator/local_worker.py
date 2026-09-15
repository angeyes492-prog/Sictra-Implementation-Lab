"""Candidate single-pipeline worker for explicitly queued local Eurostat files.

No network, arbitrary callable dispatch, source approval, publication or implicit
B2/B3 execution. A crash after claiming work requires recovery, never blind replay.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import hmac
import json
from pathlib import Path
import sqlite3
import tempfile
import time
from typing import Callable

from sictra_block1.operator_pipeline import ingest_eurostat_workbook, load_operator_pipeline, pipeline_snapshot


class WorkerViolation(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


@dataclass(frozen=True, slots=True)
class RecoveryReceipt:
    job_id: str
    source_sha256: str
    pipeline_fingerprint: str
    decision: str
    actor_id: str
    reason: str
    issued_at: int
    signature: str = ""


def sign_recovery_receipt(receipt: RecoveryReceipt, key: bytes) -> RecoveryReceipt:
    if not isinstance(key, bytes) or len(key) < 32:
        raise WorkerViolation("RECOVERY_KEY_INVALID")
    if receipt.signature:
        raise WorkerViolation("RECOVERY_RECEIPT_ALREADY_SIGNED")
    material = {name: value for name, value in asdict(receipt).items() if name != "signature"}
    return replace(receipt, signature=hmac.new(key, canonical(material), "sha256").hexdigest())


def verify_recovery_receipt(receipt: RecoveryReceipt, key: bytes, *, now: int) -> None:
    if not isinstance(receipt, RecoveryReceipt):
        raise WorkerViolation("RECOVERY_RECEIPT_TYPE_INVALID")
    if receipt.decision not in {"ABSTAIN", "CONFIRM_COMPLETED", "REQUEUE_EXACT_INPUT"}:
        raise WorkerViolation("RECOVERY_DECISION_INVALID")
    if (any(not isinstance(value, str) or not value.strip() for value in
            (receipt.job_id, receipt.actor_id, receipt.reason, receipt.signature))
            or len(receipt.actor_id) > 128 or len(receipt.reason) > 1000
            or any(len(value) != 64 or any(character not in "0123456789abcdef" for character in value)
                   for value in (receipt.source_sha256, receipt.pipeline_fingerprint))):
        raise WorkerViolation("RECOVERY_RECEIPT_CONTENT_INVALID")
    if type(receipt.issued_at) is not int or receipt.issued_at > now or receipt.issued_at < now - 900:
        raise WorkerViolation("RECOVERY_RECEIPT_TIME_INVALID")
    if not isinstance(key, bytes) or len(key) < 32:
        raise WorkerViolation("RECOVERY_KEY_INVALID")
    material = {name: value for name, value in asdict(receipt).items() if name != "signature"}
    expected = hmac.new(key, canonical(material), "sha256").hexdigest()
    if not hmac.compare_digest(expected, receipt.signature):
        raise WorkerViolation("RECOVERY_RECEIPT_SIGNATURE_INVALID")


class LocalIntakeWorker:
    """HMAC-bound bounded queue. Keep the queue key outside the inbox."""

    def __init__(self, path: Path, *, inbox: Path, pipeline: Path, key: bytes,
                 clock: Callable[[], int] = lambda: int(time.time())):
        if not isinstance(key, bytes) or len(key) < 32:
            raise WorkerViolation("WORKER_KEY_INVALID")
        if inbox.is_symlink() or not inbox.is_dir() or pipeline.is_symlink() or not pipeline.is_dir():
            raise WorkerViolation("WORKSPACE_INVALID")
        self.path, self.inbox, self.pipeline = Path(path), inbox.resolve(), pipeline.resolve()
        if self.pipeline.is_relative_to(self.inbox) or self.inbox.is_relative_to(self.pipeline):
            raise WorkerViolation("INBOX_AND_STATE_MUST_BE_SEPARATE")
        if self.path.is_symlink() or self.path.resolve().is_relative_to(self.inbox):
            raise WorkerViolation("QUEUE_MUST_BE_OUTSIDE_INBOX")
        self.key, self.clock = key, clock
        self.path.parent.mkdir(parents=True, exist_ok=True)
        existed = self.path.exists()
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("CREATE TABLE IF NOT EXISTS worker (id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL, signature TEXT NOT NULL)")
            if db.execute("SELECT 1 FROM worker").fetchone() is None:
                if existed:
                    raise WorkerViolation("QUEUE_MISSING")
                self._save(db, {"version": 1, "inbox": str(self.inbox), "pipeline": str(self.pipeline),
                                "paused": False, "jobs": [], "events": []})
            self._read(db)
            db.commit()

    def _connect(self):
        return sqlite3.connect(self.path, timeout=5)

    def _read(self, db):
        row = db.execute("SELECT body,signature FROM worker WHERE id=1").fetchone()
        if row is None:
            raise WorkerViolation("QUEUE_MISSING")
        expected = hmac.new(self.key, row[0].encode(), "sha256").hexdigest()
        if not hmac.compare_digest(expected, row[1]):
            raise WorkerViolation("QUEUE_INTEGRITY_ERROR")
        value = json.loads(row[0])
        if value["version"] != 1 or value["inbox"] != str(self.inbox) or value["pipeline"] != str(self.pipeline):
            raise WorkerViolation("QUEUE_SCOPE_MISMATCH")
        return value

    def _save(self, db, value):
        body = canonical(value)
        signature = hmac.new(self.key, body, "sha256").hexdigest()
        db.execute("INSERT OR REPLACE INTO worker(id,body,signature) VALUES(1,?,?)", (body.decode(), signature))

    def snapshot(self):
        with closing(self._connect()) as db:
            return self._read(db)

    def _event(self, state, event, job_id=None, **details):
        if len(state["events"]) >= 2048:
            raise WorkerViolation("EVENT_BUDGET_EXHAUSTED")
        state["events"].append({"event": event, "job_id": job_id, "at": self.clock(), **details})

    def set_paused(self, paused: bool):
        if type(paused) is not bool:
            raise WorkerViolation("PAUSE_VALUE_INVALID")
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            state = self._read(db)
            if state["paused"] != paused:
                state["paused"] = paused
                self._event(state, "PAUSED" if paused else "RESUMED")
                self._save(db, state)
            db.commit()

    def _source(self, filename):
        if not isinstance(filename, str) or not filename or "/" in filename or "\\" in filename or ":" in filename:
            raise WorkerViolation("INPUT_NAME_INVALID")
        source = self.inbox / filename
        if source.is_symlink() or source.suffix.lower() != ".xlsx" or not source.is_file():
            raise WorkerViolation("INPUT_NOT_ALLOWED")
        if source.resolve().parent != self.inbox:
            raise WorkerViolation("INPUT_ESCAPES_INBOX")
        with source.open("rb") as stream:
            content = stream.read(8_388_609)
        if len(content) > 8_388_608:
            raise WorkerViolation("INPUT_SIZE_EXCEEDED")
        return content

    def enqueue(self, filename: str, *, expected_sha256: str, geo_level="COUNTRY"):
        if geo_level not in {"COUNTRY", "NUTS1", "NUTS2"}:
            raise WorkerViolation("GEO_LEVEL_INVALID")
        content = self._source(filename)
        digest = sha256(content).hexdigest()
        if digest != expected_sha256:
            raise WorkerViolation("INPUT_HASH_MISMATCH")
        # Authority is checked by the existing pipeline; enqueue grants none.
        load_operator_pipeline(self.pipeline, clock=self.clock)
        job_id = sha256(canonical([digest, geo_level])).hexdigest()
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            state = self._read(db)
            if any(job["job_id"] == job_id for job in state["jobs"]):
                return job_id
            if len(state["jobs"]) >= 128:
                raise WorkerViolation("JOB_BUDGET_EXHAUSTED")
            state["jobs"].append({"job_id": job_id, "filename": filename, "sha256": digest,
                                  "geo_level": geo_level, "state": "QUEUED", "result": None})
            self._event(state, "ENQUEUED", job_id)
            self._save(db, state)
            db.commit()
        return job_id

    def process_one(self):
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            state = self._read(db)
            if state["paused"]:
                return {"state": "PAUSED"}
            if any(job["state"] == "RUNNING" for job in state["jobs"]):
                return {"state": "RECOVERY_REQUIRED", "reason": "An active or interrupted job must be reconciled; no replay."}
            if any(job["state"] == "REVIEW_REQUIRED" for job in state["jobs"]):
                return {"state": "REVIEW_REQUIRED", "reason": "Unresolved evidence or a failed execution stops the queue."}
            job = next((job for job in state["jobs"] if job["state"] == "QUEUED"), None)
            if job is None:
                return {"state": "IDLE"}
            if len(state["events"]) > 2046:
                raise WorkerViolation("EVENT_BUDGET_EXHAUSTED")
            job["state"] = "RUNNING"
            self._event(state, "CLAIMED", job["job_id"])
            self._save(db, state)
            db.commit()
        try:
            content = self._source(job["filename"])
            if sha256(content).hexdigest() != job["sha256"]:
                raise WorkerViolation("INPUT_HASH_MISMATCH")
            # Execute exactly the bytes whose hash was checked, not a mutable inbox path.
            with tempfile.TemporaryDirectory(prefix="sictra-approved-intake-") as directory:
                staged = Path(directory) / job["filename"]
                staged.write_bytes(content)
                result = ingest_eurostat_workbook(self.pipeline, staged,
                    geo_level=job["geo_level"], clock=self.clock)
            status = "REVIEW_REQUIRED" if result["watchlist"]["next_state"] == "REQUIRES_REVIEW" else "COMPLETED"
        except Exception as error:
            # Pipeline stages may already have committed. Never auto-retry or
            # label partial effects as a clean rejection.
            result = {"error_type": type(error).__name__, "reason": str(error), "publication_authority": "NONE"}
            status = "REVIEW_REQUIRED"
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            state = self._read(db)
            saved = next(item for item in state["jobs"] if item["job_id"] == job["job_id"])
            if saved["state"] != "RUNNING":
                raise WorkerViolation("JOB_STATE_CHANGED")
            saved["state"], saved["result"] = status, result
            self._event(state, status, job["job_id"])
            self._save(db, state)
            db.commit()
        return {"state": status, "job_id": job["job_id"], "result": result}

    def run(self, *, max_jobs=1):
        if type(max_jobs) is not int or not 1 <= max_jobs <= 32:
            raise WorkerViolation("RUN_BUDGET_INVALID")
        results = []
        for _ in range(max_jobs):
            result = self.process_one()
            results.append(result)
            if result["state"] != "COMPLETED":
                break
        return results

    def watch(self, *, cycles=1, interval_seconds=5, max_jobs=1, sleep=time.sleep):
        """Bounded polling; pause/review/recovery ends the session immediately."""
        if type(cycles) is not int or not 1 <= cycles <= 120:
            raise WorkerViolation("CYCLE_BUDGET_INVALID")
        if type(interval_seconds) is not int or not 1 <= interval_seconds <= 60:
            raise WorkerViolation("INTERVAL_INVALID")
        if type(max_jobs) is not int or not 1 <= max_jobs <= 32:
            raise WorkerViolation("RUN_BUDGET_INVALID")
        results = []
        for index in range(cycles):
            batch = self.run(max_jobs=max_jobs)
            results.extend(batch)
            if batch[-1]["state"] not in {"COMPLETED", "IDLE"}:
                break
            if index + 1 < cycles:
                sleep(interval_seconds)
        return results

    def recovery_receipt(self, job_id: str, *, decision: str, actor_id: str,
                         reason: str, recovery_key: bytes) -> RecoveryReceipt:
        """Create a short-lived receipt bound to the current upstream snapshot."""
        if recovery_key == self.key:
            raise WorkerViolation("RECOVERY_KEY_MUST_BE_SEPARATE")
        state = self.snapshot()
        job = next((item for item in state["jobs"] if item["job_id"] == job_id), None)
        if job is None:
            raise WorkerViolation("RECOVERY_JOB_NOT_FOUND")
        if job["state"] not in {"RUNNING", "REVIEW_REQUIRED"}:
            raise WorkerViolation("RECOVERY_JOB_STATE_INVALID")
        pipeline_fingerprint = sha256(canonical(pipeline_snapshot(self.pipeline, clock=self.clock))).hexdigest()
        return sign_recovery_receipt(RecoveryReceipt(job_id, job["sha256"], pipeline_fingerprint,
            decision, actor_id, reason, self.clock()), recovery_key)

    def recover(self, receipt: RecoveryReceipt, *, recovery_key: bytes):
        """Apply an authenticated, snapshot-bound decision; never infer success."""
        if recovery_key == self.key:
            raise WorkerViolation("RECOVERY_KEY_MUST_BE_SEPARATE")
        now = self.clock()
        verify_recovery_receipt(receipt, recovery_key, now=now)
        current_pipeline = sha256(canonical(pipeline_snapshot(self.pipeline, clock=self.clock))).hexdigest()
        if current_pipeline != receipt.pipeline_fingerprint:
            raise WorkerViolation("RECOVERY_PIPELINE_CHANGED")
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            state = self._read(db)
            job = next((item for item in state["jobs"] if item["job_id"] == receipt.job_id), None)
            if job is None:
                raise WorkerViolation("RECOVERY_JOB_NOT_FOUND")
            if job["state"] not in {"RUNNING", "REVIEW_REQUIRED"}:
                raise WorkerViolation("RECOVERY_JOB_STATE_INVALID")
            if job["sha256"] != receipt.source_sha256:
                raise WorkerViolation("RECOVERY_SOURCE_IDENTITY_MISMATCH")
            if receipt.decision == "REQUEUE_EXACT_INPUT":
                content = self._source(job["filename"])
                if sha256(content).hexdigest() != job["sha256"]:
                    raise WorkerViolation("INPUT_HASH_MISMATCH")
                next_state = "QUEUED"
            elif receipt.decision == "CONFIRM_COMPLETED":
                next_state = "COMPLETED"
            else:
                next_state = "ABSTAINED"
            receipt_material = asdict(receipt)
            job["state"] = next_state
            job["result"] = {"recovery_receipt": receipt_material, "publication_authority": "NONE"}
            self._event(state, "RECOVERED_" + receipt.decision, job["job_id"],
                        actor_id=receipt.actor_id,
                        receipt_fingerprint=sha256(canonical(receipt_material)).hexdigest())
            self._save(db, state)
            db.commit()
        return {"state": next_state, "job_id": receipt.job_id}

    def create_backup(self, destination: Path):
        """Create a verified, signed queue backup without copying either key."""
        target = Path(destination)
        if target.exists() or target.is_symlink() or not target.name:
            raise WorkerViolation("BACKUP_DESTINATION_INVALID")
        resolved = target.resolve()
        if (resolved.is_relative_to(self.inbox) or resolved.is_relative_to(self.pipeline)
                or resolved == self.path.resolve()):
            raise WorkerViolation("BACKUP_DESTINATION_INVALID")
        self.snapshot()
        target.mkdir(parents=True)
        backup_db = target / "queue.sqlite"
        with closing(self._connect()) as source, closing(sqlite3.connect(backup_db)) as backup:
            source.backup(backup)
        queue_sha256 = sha256(backup_db.read_bytes()).hexdigest()
        manifest = {"version": 1, "scope": "TELECARE_LOCAL_WORKER_QUEUE_BACKUP",
                    "created_at": self.clock(), "queue_sha256": queue_sha256,
                    "pipeline_fingerprint": sha256(canonical(
                        pipeline_snapshot(self.pipeline, clock=self.clock))).hexdigest()}
        manifest["signature"] = hmac.new(self.key, canonical(manifest), "sha256").hexdigest()
        (target / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2), encoding="utf-8")
        self.verify_backup(target)
        return {"destination": str(resolved), "queue_sha256": queue_sha256,
                "pipeline_fingerprint": manifest["pipeline_fingerprint"]}

    def verify_backup(self, source: Path):
        """Verify manifest, queue state and current pipeline recovery boundary."""
        root = Path(source)
        if root.is_symlink() or not root.is_dir():
            raise WorkerViolation("BACKUP_SOURCE_INVALID")
        try:
            manifest_path, queue_path = root / "manifest.json", root / "queue.sqlite"
            if (manifest_path.is_symlink() or queue_path.is_symlink()
                    or not manifest_path.is_file() or not queue_path.is_file()
                    or manifest_path.stat().st_size > 65_536 or queue_path.stat().st_size > 16_777_216):
                raise WorkerViolation("BACKUP_SOURCE_INVALID")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            queue_bytes = queue_path.read_bytes()
        except (OSError, json.JSONDecodeError) as error:
            raise WorkerViolation("BACKUP_SOURCE_INVALID") from error
        if set(manifest) != {"version", "scope", "created_at", "queue_sha256",
                            "pipeline_fingerprint", "signature"}:
            raise WorkerViolation("BACKUP_MANIFEST_INVALID")
        material = {key: value for key, value in manifest.items() if key != "signature"}
        if (not isinstance(manifest["signature"], str)
                or type(manifest["created_at"]) is not int
                or any(not isinstance(manifest[name], str) for name in
                       ("scope", "queue_sha256", "pipeline_fingerprint"))):
            raise WorkerViolation("BACKUP_MANIFEST_INVALID")
        expected = hmac.new(self.key, canonical(material), "sha256").hexdigest()
        if not hmac.compare_digest(expected, manifest["signature"]):
            raise WorkerViolation("BACKUP_SIGNATURE_INVALID")
        if (manifest["version"] != 1 or manifest["scope"] != "TELECARE_LOCAL_WORKER_QUEUE_BACKUP"
                or sha256(queue_bytes).hexdigest() != manifest["queue_sha256"]):
            raise WorkerViolation("BACKUP_INTEGRITY_ERROR")
        current_pipeline = sha256(canonical(pipeline_snapshot(self.pipeline, clock=self.clock))).hexdigest()
        if current_pipeline != manifest["pipeline_fingerprint"]:
            raise WorkerViolation("BACKUP_PIPELINE_CHANGED")
        with closing(sqlite3.connect(root / "queue.sqlite")) as db:
            self._read(db)
        return {"status": "VERIFIED", "queue_sha256": manifest["queue_sha256"],
                "pipeline_fingerprint": manifest["pipeline_fingerprint"]}

    def restore_backup(self, source: Path, target_queue: Path):
        """Restore only to a new queue path; never overwrite live state."""
        self.verify_backup(source)
        target = Path(target_queue)
        if (target.exists() or target.is_symlink() or target.resolve().is_relative_to(self.inbox)
                or target.resolve().is_relative_to(self.pipeline)):
            raise WorkerViolation("RESTORE_TARGET_INVALID")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((Path(source) / "queue.sqlite").read_bytes())
        restored = LocalIntakeWorker(target, inbox=self.inbox, pipeline=self.pipeline,
                                     key=self.key, clock=self.clock)
        return {"status": "RESTORED_TO_NEW_PATH", "queue": str(target.resolve()),
                "jobs": len(restored.snapshot()["jobs"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--inbox", type=Path, required=True)
    parser.add_argument("--pipeline", type=Path, required=True)
    parser.add_argument("--key-file", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    submit = commands.add_parser("enqueue")
    submit.add_argument("filename")
    submit.add_argument("--sha256", required=True)
    submit.add_argument("--geo-level", default="COUNTRY")
    run = commands.add_parser("run")
    run.add_argument("--max-jobs", type=int, default=1)
    watch = commands.add_parser("watch")
    watch.add_argument("--max-jobs", type=int, default=1)
    watch.add_argument("--cycles", type=int, default=12)
    watch.add_argument("--interval-seconds", type=int, default=5)
    for name in ("status", "pause", "resume"):
        commands.add_parser(name)
    recover = commands.add_parser("recover")
    recover.add_argument("job_id")
    recover.add_argument("--decision", required=True,
                         choices=("ABSTAIN", "CONFIRM_COMPLETED", "REQUEUE_EXACT_INPUT"))
    recover.add_argument("--actor-id", required=True)
    recover.add_argument("--reason", required=True)
    recover.add_argument("--recovery-key-file", type=Path, required=True)
    backup = commands.add_parser("backup")
    backup.add_argument("destination", type=Path)
    verify_backup = commands.add_parser("verify-backup")
    verify_backup.add_argument("source", type=Path)
    restore_backup = commands.add_parser("restore-backup")
    restore_backup.add_argument("source", type=Path)
    restore_backup.add_argument("target_queue", type=Path)
    args = parser.parse_args()
    if args.key_file.is_symlink() or args.key_file.resolve().is_relative_to(args.inbox.resolve()):
        raise WorkerViolation("KEY_MUST_BE_OUTSIDE_INBOX")
    worker = LocalIntakeWorker(args.queue, inbox=args.inbox, pipeline=args.pipeline, key=args.key_file.read_bytes())
    if args.command == "enqueue":
        result = {"job_id": worker.enqueue(args.filename, expected_sha256=args.sha256, geo_level=args.geo_level)}
    elif args.command == "run":
        result = worker.run(max_jobs=args.max_jobs)
    elif args.command == "watch":
        result = worker.watch(max_jobs=args.max_jobs, cycles=args.cycles, interval_seconds=args.interval_seconds)
    elif args.command in {"pause", "resume"}:
        worker.set_paused(args.command == "pause")
        result = {"paused": args.command == "pause"}
    elif args.command == "recover":
        if (args.recovery_key_file.is_symlink()
                or args.recovery_key_file.resolve().is_relative_to(args.inbox.resolve())):
            raise WorkerViolation("RECOVERY_KEY_MUST_BE_OUTSIDE_INBOX")
        recovery_key = args.recovery_key_file.read_bytes()
        receipt = worker.recovery_receipt(args.job_id, decision=args.decision,
            actor_id=args.actor_id, reason=args.reason, recovery_key=recovery_key)
        result = worker.recover(receipt, recovery_key=recovery_key)
    elif args.command == "backup":
        result = worker.create_backup(args.destination)
    elif args.command == "verify-backup":
        result = worker.verify_backup(args.source)
    elif args.command == "restore-backup":
        result = worker.restore_backup(args.source, args.target_queue)
    else:
        result = worker.snapshot()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
