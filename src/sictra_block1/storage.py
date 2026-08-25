"""Transactional, tamper-detecting SQLite state for bounded operation."""

from __future__ import annotations

from hashlib import sha256
import hmac
import json
from pathlib import Path
import sqlite3
from threading import RLock
from typing import Any, Callable, Mapping

from .common import (
    CapacityExceeded, ContractViolation, Envelope, IdentityCollision,
    immutable_copy, plain_copy,
)


def _encoded(value: Any) -> str:
    return json.dumps(plain_copy(value), sort_keys=True, separators=(",", ":"))


def _decoded_envelope(raw: str) -> Envelope:
    try:
        return Envelope.from_dict(json.loads(raw))
    except ContractViolation:
        raise
    except (KeyError, TypeError, ValueError) as error:
        raise ContractViolation("terminal envelope is malformed") from error


class OperationalStore:
    def __init__(self, path: str | Path = ":memory:", max_records: int = 100_000,
                 max_attempts: int | None = None) -> None:
        effective_attempts = max_records if max_attempts is None else max_attempts
        if max_records < 1 or effective_attempts < 1:
            raise ContractViolation("storage capacities must be positive")
        self.path, self.max_records = str(path), max_records
        self.max_attempts = effective_attempts
        self.failure_injector: Callable[[str], None] | None = None
        self._lock = RLock()
        self._db = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys = ON")
        if self.path != ":memory:":
            self._db.execute("PRAGMA journal_mode = WAL")
            self._db.execute("PRAGMA synchronous = FULL")
        version = self._db.execute("PRAGMA user_version").fetchone()[0]
        if version == 0:
            existing = {
                row["name"] for row in self._db.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            protected = {"memory_candidates", "terminal_runs", "execution_journal"}
            if existing & protected:
                self._db.close()
                raise ContractViolation("unversioned operational tables cannot be promoted implicitly")
        elif version != 5:
            self._db.close()
            raise ContractViolation(f"unsupported SQLite schema version: {version}")
        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS memory_candidates (
                task_id TEXT NOT NULL,
                run_id TEXT NOT NULL UNIQUE,
                version INTEGER NOT NULL,
                candidate_fingerprint TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                record_hash TEXT NOT NULL,
                record_json TEXT NOT NULL,
                PRIMARY KEY (task_id, version)
            );
            CREATE TABLE IF NOT EXISTS terminal_runs (
                request_fingerprint TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                result_fingerprint TEXT NOT NULL,
                terminal_hash TEXT NOT NULL,
                effect_committed INTEGER NOT NULL CHECK(effect_committed IN (0, 1)),
                envelope_json TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS one_committed_effect_per_run
                ON terminal_runs(run_id) WHERE effect_committed = 1;
            CREATE TABLE IF NOT EXISTS execution_journal (
                attempt_fingerprint TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                state TEXT NOT NULL,
                reason TEXT NOT NULL,
                updated_at INTEGER NOT NULL
            );
            PRAGMA user_version = 5;
        """)
        expected_columns = {
            "memory_candidates": (
                ("task_id", "TEXT", 1, 1), ("run_id", "TEXT", 1, 0),
                ("version", "INTEGER", 1, 2), ("candidate_fingerprint", "TEXT", 1, 0),
                ("previous_hash", "TEXT", 1, 0), ("record_hash", "TEXT", 1, 0),
                ("record_json", "TEXT", 1, 0),
            ),
            "terminal_runs": (
                ("request_fingerprint", "TEXT", 0, 1), ("run_id", "TEXT", 1, 0),
                ("result_fingerprint", "TEXT", 1, 0), ("terminal_hash", "TEXT", 1, 0),
                ("effect_committed", "INTEGER", 1, 0), ("envelope_json", "TEXT", 1, 0),
            ),
            "execution_journal": (
                ("attempt_fingerprint", "TEXT", 0, 1), ("run_id", "TEXT", 1, 0),
                ("state", "TEXT", 1, 0), ("reason", "TEXT", 1, 0),
                ("updated_at", "INTEGER", 1, 0),
            ),
        }
        for table, expected in expected_columns.items():
            actual = tuple(
                (row["name"], row["type"], row["notnull"], row["pk"])
                for row in self._db.execute(f"PRAGMA table_info({table})").fetchall()
            )
            if actual != expected:
                self._db.close()
                raise ContractViolation(f"operational table schema mismatch: {table}")
        index_signatures = set()
        for table in expected_columns:
            for index in self._db.execute(f"PRAGMA index_list({table})").fetchall():
                columns = tuple(
                    row["name"] for row in self._db.execute(
                        f"PRAGMA index_info({index['name']})"
                    ).fetchall()
                )
                index_signatures.add((table, columns, index["unique"], index["origin"], index["partial"]))
        required_indexes = {
            ("memory_candidates", ("task_id", "version"), 1, "pk", 0),
            ("memory_candidates", ("run_id",), 1, "u", 0),
            ("terminal_runs", ("request_fingerprint",), 1, "pk", 0),
            ("terminal_runs", ("run_id",), 1, "c", 1),
            ("execution_journal", ("attempt_fingerprint",), 1, "pk", 0),
        }
        if not required_indexes.issubset(index_signatures):
            self._db.close()
            raise ContractViolation("operational schema indexes are incomplete")

    def healthcheck(self, *, write_required: bool = False) -> bool:
        try:
            with self._lock:
                if self._db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                    return False
                if write_required:
                    count = self._db.execute(
                        "SELECT COUNT(*) AS count FROM memory_candidates"
                    ).fetchone()["count"]
                    return count < self.max_records
                return True
        except sqlite3.Error:
            return False

    def record_state(self, attempt_fingerprint: str, run_id: str,
                     state: str, reason: str, now: int) -> None:
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                exists = self._db.execute(
                    "SELECT 1 FROM execution_journal WHERE attempt_fingerprint = ?",
                    (attempt_fingerprint,),
                ).fetchone()
                if exists is None:
                    count = self._db.execute(
                        "SELECT COUNT(*) AS count FROM execution_journal"
                    ).fetchone()["count"]
                    if count >= self.max_attempts:
                        raise CapacityExceeded("execution journal capacity exhausted")
                self._db.execute(
                    """INSERT INTO execution_journal(attempt_fingerprint, run_id, state, reason, updated_at)
                       VALUES (?, ?, ?, ?, ?)
                       ON CONFLICT(attempt_fingerprint) DO UPDATE SET
                       state=excluded.state, reason=excluded.reason, updated_at=excluded.updated_at""",
                    (attempt_fingerprint, run_id, state, reason, now),
                )
                self._db.execute("COMMIT")
            except Exception:
                self._db.execute("ROLLBACK")
                raise

    def journal(self, run_id: str) -> tuple[Mapping[str, Any], ...]:
        with self._lock:
            rows = self._db.execute(
                "SELECT attempt_fingerprint, run_id, state, reason, updated_at FROM execution_journal WHERE run_id = ? ORDER BY updated_at, attempt_fingerprint",
                (run_id,),
            ).fetchall()
        return tuple(immutable_copy(dict(row)) for row in rows)

    def _validated_terminal(self, row: sqlite3.Row, run_id: str) -> tuple[str, Envelope]:
        envelope = _decoded_envelope(row["envelope_json"])
        expected_hash = sha256((
            row["request_fingerprint"] + row["result_fingerprint"]
            + str(row["effect_committed"]) + row["envelope_json"]
        ).encode()).hexdigest()
        enforcement = envelope.payload.get("enforcement")
        expected_status = "COMMITTED" if row["effect_committed"] else "NOT_EXECUTED"
        if (envelope.run_id != run_id or envelope.fingerprint != row["result_fingerprint"]
                or not hmac.compare_digest(expected_hash, row["terminal_hash"])
                or not isinstance(enforcement, Mapping)
                or enforcement.get("status") != expected_status):
            raise ContractViolation("terminal integrity verification failed")
        if row["effect_committed"]:
            memory = self._db.execute(
                """SELECT version, record_hash FROM memory_candidates
                   WHERE run_id = ?""", (run_id,)
            ).fetchone()
            if (memory is None or memory["version"] != enforcement.get("record_version")
                    or memory["record_hash"] != enforcement.get("record_hash")):
                raise ContractViolation("terminal effect coherence verification failed")
        return row["request_fingerprint"], envelope

    def get_terminal(self, run_id: str,
                     request_fingerprint: str | None = None) -> tuple[str, Envelope] | None:
        with self._lock:
            if request_fingerprint is None:
                row = self._db.execute(
                    """SELECT request_fingerprint, result_fingerprint, terminal_hash,
                              effect_committed, envelope_json
                       FROM terminal_runs WHERE run_id = ?
                       ORDER BY effect_committed DESC, rowid DESC LIMIT 1""", (run_id,)
                ).fetchone()
            else:
                row = self._db.execute(
                    """SELECT request_fingerprint, result_fingerprint, terminal_hash,
                              effect_committed, envelope_json
                       FROM terminal_runs WHERE run_id = ? AND request_fingerprint = ?""",
                    (run_id, request_fingerprint),
                ).fetchone()
        if row is None:
            return None
        with self._lock:
            return self._validated_terminal(row, run_id)

    def get_committed_terminal(self, run_id: str) -> tuple[str, Envelope] | None:
        with self._lock:
            row = self._db.execute(
                """SELECT request_fingerprint, result_fingerprint, terminal_hash,
                          effect_committed, envelope_json
                   FROM terminal_runs WHERE run_id = ? AND effect_committed = 1""",
                (run_id,),
            ).fetchone()
            return None if row is None else self._validated_terminal(row, run_id)

    def commit_effect_and_terminal(self, *, request_fingerprint: str,
                                   decision_envelope: Envelope,
                                   candidate_fingerprint: str,
                                   record: Mapping[str, Any],
                                   action: str) -> Envelope:
        if action != "store_candidate":
            raise ContractViolation("unsupported action has no operational effect handler")
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                terminal = self._db.execute(
                    """SELECT request_fingerprint, result_fingerprint, terminal_hash,
                              effect_committed, envelope_json
                       FROM terminal_runs WHERE request_fingerprint = ?""",
                    (request_fingerprint,),
                ).fetchone()
                if terminal:
                    _, result = self._validated_terminal(terminal, decision_envelope.run_id)
                    self._db.execute("COMMIT")
                    return result
                committed = self._db.execute(
                    "SELECT 1 FROM terminal_runs WHERE run_id = ? AND effect_committed = 1",
                    (decision_envelope.run_id,),
                ).fetchone()
                if committed:
                    raise IdentityCollision("run identity reused with different committed request")

                existing = self._db.execute(
                    """SELECT candidate_fingerprint, record_json, record_hash
                       FROM memory_candidates WHERE run_id = ?""",
                    (decision_envelope.run_id,),
                ).fetchone()
                if existing:
                    if existing["candidate_fingerprint"] != candidate_fingerprint:
                        raise IdentityCollision("run identity reused for a different memory candidate")
                    stored = json.loads(existing["record_json"])
                else:
                    count = self._db.execute("SELECT COUNT(*) AS count FROM memory_candidates").fetchone()["count"]
                    if count >= self.max_records:
                        raise CapacityExceeded("operational memory capacity exhausted")
                    latest = self._db.execute(
                        """SELECT version, record_hash FROM memory_candidates
                           WHERE task_id = ? ORDER BY version DESC LIMIT 1""",
                        (decision_envelope.task_id,),
                    ).fetchone()
                    version = 1 if latest is None else latest["version"] + 1
                    previous_hash = "GENESIS" if latest is None else latest["record_hash"]
                    stored = {**plain_copy(record), "version": version, "previous_hash": previous_hash}
                    record_hash = sha256((previous_hash + _encoded(stored)).encode()).hexdigest()
                    stored["record_hash"] = record_hash
                    self._db.execute(
                        """INSERT INTO memory_candidates(
                           task_id, run_id, version, candidate_fingerprint,
                           previous_hash, record_hash, record_json
                           ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            decision_envelope.task_id, decision_envelope.run_id, version,
                            candidate_fingerprint, previous_hash, record_hash, _encoded(stored),
                        ),
                    )
                if self.failure_injector:
                    self.failure_injector("AFTER_EFFECT_BEFORE_TERMINAL")
                enforcement = {
                    "action": action, "status": "COMMITTED", "effect_engine": "E06",
                    "record_version": stored["version"], "record_hash": stored["record_hash"],
                    "runtime_effect_observed": True,
                }
                final = decision_envelope.handoff(
                    "RUNTIME", "CALLER",
                    {**decision_envelope.payload, "enforcement": enforcement},
                    restrictions=decision_envelope.restrictions + ("AT_LEAST_ONCE_IDEMPOTENT_EFFECTS",),
                )
                self._db.execute(
                    """INSERT INTO terminal_runs(
                       request_fingerprint, run_id, result_fingerprint, terminal_hash,
                       effect_committed, envelope_json
                       ) VALUES (?, ?, ?, ?, 1, ?)""",
                    (
                        request_fingerprint, final.run_id, final.fingerprint,
                        sha256((
                            request_fingerprint + final.fingerprint + "1"
                            + _encoded(final.to_dict())
                        ).encode()).hexdigest(),
                        _encoded(final.to_dict()),
                    ),
                )
                self._db.execute(
                    """UPDATE execution_journal SET state = ?, reason = ?
                       WHERE attempt_fingerprint = ?""",
                    ("EFFECT_AND_TERMINAL_COMMITTED", "COMMITTED", request_fingerprint),
                )
                self._db.execute("COMMIT")
                return final
            except Exception:
                self._db.execute("ROLLBACK")
                raise

    def commit_no_effect_terminal(self, *, request_fingerprint: str,
                                  envelope: Envelope) -> Envelope:
        encoded = _encoded(envelope.to_dict())
        terminal_hash = sha256((
            request_fingerprint + envelope.fingerprint + "0" + encoded
        ).encode()).hexdigest()
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                self._db.execute(
                    """INSERT INTO terminal_runs(
                       request_fingerprint, run_id, result_fingerprint, terminal_hash,
                       effect_committed, envelope_json
                       ) VALUES (?, ?, ?, ?, 0, ?)
                       ON CONFLICT(request_fingerprint) DO NOTHING""",
                    (
                        request_fingerprint, envelope.run_id, envelope.fingerprint,
                        terminal_hash, encoded,
                    ),
                )
                self._db.execute(
                    """UPDATE execution_journal SET state = ?, reason = ?
                       WHERE attempt_fingerprint = ?""",
                    ("TERMINAL_NO_EFFECT", envelope.payload["governance"]["decision"],
                     request_fingerprint),
                )
                row = self._db.execute(
                    """SELECT request_fingerprint, result_fingerprint, terminal_hash,
                              effect_committed, envelope_json
                       FROM terminal_runs WHERE request_fingerprint = ?""",
                    (request_fingerprint,),
                ).fetchone()
                _, result = self._validated_terminal(row, envelope.run_id)
                self._db.execute("COMMIT")
                return result
            except Exception:
                self._db.execute("ROLLBACK")
                raise

    def history(self, task_id: str) -> tuple[Mapping[str, Any], ...]:
        with self._lock:
            rows = self._db.execute(
                """SELECT task_id, run_id, version, previous_hash, record_hash, record_json
                   FROM memory_candidates WHERE task_id = ? ORDER BY version""",
                (task_id,),
            ).fetchall()
        expected_previous = "GENESIS"
        result = []
        for expected_version, row in enumerate(rows, start=1):
            try:
                record = json.loads(row["record_json"])
            except (TypeError, ValueError) as error:
                raise ContractViolation("memory history record is malformed") from error
            claimed_hash = record.pop("record_hash", None)
            calculated = sha256((expected_previous + _encoded(record)).encode()).hexdigest()
            if (
                row["version"] != expected_version
                or record.get("task_id") != row["task_id"]
                or record.get("run_id") != row["run_id"]
                or row["previous_hash"] != expected_previous
                or record.get("previous_hash") != expected_previous
                or row["record_hash"] != calculated
                or claimed_hash != calculated
            ):
                raise ContractViolation("memory history integrity verification failed")
            record["record_hash"] = claimed_hash
            result.append(immutable_copy(record))
            expected_previous = calculated
        return tuple(result)

    def close(self) -> None:
        with self._lock:
            self._db.close()

