"""Candidate single-pipeline worker for explicitly queued local Eurostat files.

No network, arbitrary callable dispatch, source approval, publication or implicit
B2/B3 execution. A crash after claiming work requires recovery, never blind replay.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from hashlib import sha256
import hmac
import json
from pathlib import Path
import sqlite3
import tempfile
import time
from typing import Callable

from sictra_block1.operator_pipeline import ingest_eurostat_workbook, load_operator_pipeline


class WorkerViolation(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


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

    def _event(self, state, event, job_id=None):
        if len(state["events"]) >= 2048:
            raise WorkerViolation("EVENT_BUDGET_EXHAUSTED")
        state["events"].append({"event": event, "job_id": job_id, "at": self.clock()})

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
    else:
        result = worker.snapshot()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
