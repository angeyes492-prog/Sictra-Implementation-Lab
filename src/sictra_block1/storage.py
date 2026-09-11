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
    _SCHEMA_VERSION = 8
    _SCHEMA_SQL = {
        "memory_candidates": """CREATE TABLE memory_candidates (
                task_id TEXT NOT NULL,
                run_id TEXT NOT NULL UNIQUE,
                version INTEGER NOT NULL,
                candidate_fingerprint TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                record_hash TEXT NOT NULL,
                record_json TEXT NOT NULL,
                PRIMARY KEY (task_id, version)
            )""",
        "terminal_runs": """CREATE TABLE terminal_runs (
                request_fingerprint TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                result_fingerprint TEXT NOT NULL,
                terminal_hash TEXT NOT NULL,
                effect_committed INTEGER NOT NULL CHECK(effect_committed IN (0, 1)),
                envelope_json TEXT NOT NULL
            )""",
        "execution_journal": """CREATE TABLE execution_journal (
                attempt_fingerprint TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                state TEXT NOT NULL,
                reason TEXT NOT NULL,
                updated_at INTEGER NOT NULL,
                journal_hash TEXT NOT NULL
            )""",
        "store_metadata": """CREATE TABLE store_metadata (
                singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
                max_records INTEGER NOT NULL,
                max_attempts INTEGER NOT NULL,
                key_check TEXT NOT NULL
            )""",
        "one_committed_effect_per_run": """CREATE UNIQUE INDEX one_committed_effect_per_run
                ON terminal_runs(run_id) WHERE effect_committed = 1""",
    }

    def __init__(self, path: str | Path = ":memory:", *, integrity_key: bytes,
                 max_records: int = 100_000,
                 max_attempts: int | None = None) -> None:
        effective_attempts = max_records if max_attempts is None else max_attempts
        if max_records < 1 or effective_attempts < 1 or len(integrity_key) < 32:
            raise ContractViolation("storage capacities and 32-byte integrity key are required")
        self.path, self.max_records = str(path), max_records
        self.max_attempts = effective_attempts
        self._integrity_key = bytes(integrity_key)
        self.failure_injector: Callable[[str], None] | None = None
        self._lock = RLock()
        # A cold-start peer may be atomically creating the schema.  Use the
        # same bounded wait for connection and PRAGMA locks rather than making
        # concurrent openers fail spuriously after successful initialization.
        self._db = sqlite3.connect(
            self.path, check_same_thread=False, isolation_level=None, timeout=30.0,
        )
        self._db.row_factory = sqlite3.Row
        try:
            self._db.execute("PRAGMA busy_timeout = 30000")
            self._db.execute("PRAGMA foreign_keys = ON")
            self._initialize_or_verify()
            if self.path != ":memory:":
                self._db.execute("PRAGMA journal_mode = WAL")
                self._db.execute("PRAGMA synchronous = FULL")
        except Exception:
            self._db.close()
            raise
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
                ("updated_at", "INTEGER", 1, 0), ("journal_hash", "TEXT", 1, 0),
            ),
            "store_metadata": (
                ("singleton", "INTEGER", 0, 1),
                ("max_records", "INTEGER", 1, 0),
                ("max_attempts", "INTEGER", 1, 0),
                ("key_check", "TEXT", 1, 0),
            ),
        }
        for table, expected in expected_columns.items():
            actual = tuple(
                (row["name"], row["type"], row["notnull"], row["pk"])
                for row in self._db.execute(f"PRAGMA table_info({table})").fetchall()
            )
            if actual != expected:
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
                raise ContractViolation("operational schema indexes are incomplete")
        self._assert_exact_schema_sql()
        self._assert_metadata()
        self._assert_allowed_schema_objects()

    def _initialize_or_verify(self) -> None:
        """Create an empty store atomically; never mutate a foreign SQLite file."""
        self._db.execute("BEGIN IMMEDIATE")
        try:
            version = self._db.execute("PRAGMA user_version").fetchone()[0]
            objects = self._schema_objects()
            if version == 0:
                if objects:
                    raise ContractViolation("unversioned SQLite must be empty for operational initialization")
                for name in ("memory_candidates", "terminal_runs", "execution_journal", "store_metadata"):
                    self._db.execute(self._SCHEMA_SQL[name])
                self._db.execute(self._SCHEMA_SQL["one_committed_effect_per_run"])
                self._db.execute(f"PRAGMA user_version = {self._SCHEMA_VERSION}")
                self._db.execute(
                    "INSERT INTO store_metadata(singleton, max_records, max_attempts, key_check) VALUES (1, ?, ?, ?)",
                    (self.max_records, self.max_attempts, self._metadata_mac()),
                )
            elif version != self._SCHEMA_VERSION:
                raise ContractViolation(f"unsupported SQLite schema version: {version}")
            self._assert_allowed_schema_objects()
            self._assert_exact_schema_sql()
            self._assert_metadata()
            self._db.execute("COMMIT")
        except Exception:
            self._db.execute("ROLLBACK")
            raise

    def _mac(self, material: str) -> str:
        return hmac.new(self._integrity_key, material.encode(), sha256).hexdigest()

    def _metadata_mac(self) -> str:
        return self._mac(
            f"sictra-store-v{self._SCHEMA_VERSION}:{self.max_records}:{self.max_attempts}"
        )

    @staticmethod
    def _normalize_sql(value: str | None) -> str:
        return "".join((value or "").lower().split())

    def _schema_objects(self) -> set[tuple[str, str]]:
        return {
            (row["type"], row["name"]) for row in self._db.execute(
                "SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }

    def _assert_exact_schema_sql(self) -> None:
        for name, expected in self._SCHEMA_SQL.items():
            row = self._db.execute(
                "SELECT sql FROM sqlite_master WHERE name = ?", (name,)
            ).fetchone()
            if row is None or self._normalize_sql(row["sql"]) != self._normalize_sql(expected):
                raise ContractViolation(f"operational SQLite schema SQL mismatch: {name}")

    def _assert_metadata(self) -> None:
        metadata = self._db.execute(
            "SELECT max_records, max_attempts, key_check FROM store_metadata WHERE singleton = 1"
        ).fetchone()
        if (metadata is None or metadata["max_records"] != self.max_records
                or metadata["max_attempts"] != self.max_attempts
                or not hmac.compare_digest(metadata["key_check"], self._metadata_mac())):
            raise ContractViolation("storage key or durable capacity configuration mismatch")

    def _journal_mac(self, attempt_fingerprint: str, run_id: str,
                     state: str, reason: str, updated_at: int) -> str:
        return self._mac(
            "journal-v8:" + _encoded(
                (attempt_fingerprint, run_id, state, reason, updated_at)
            )
        )

    def _validated_journal(self, row: sqlite3.Row) -> Mapping[str, Any]:
        expected = self._journal_mac(
            row["attempt_fingerprint"], row["run_id"], row["state"],
            row["reason"], row["updated_at"],
        )
        if not hmac.compare_digest(row["journal_hash"], expected):
            raise ContractViolation("execution journal integrity verification failed")
        return immutable_copy({
            key: row[key] for key in (
                "attempt_fingerprint", "run_id", "state", "reason", "updated_at",
            )
        })

    def _assert_write_integrity(self) -> None:
        self._assert_allowed_schema_objects()
        self._assert_exact_schema_sql()
        self._assert_metadata()

    def _require_started_journal(self, attempt_fingerprint: str, run_id: str) -> sqlite3.Row:
        row = self._db.execute(
            """SELECT attempt_fingerprint, run_id, state, reason, updated_at, journal_hash
               FROM execution_journal WHERE attempt_fingerprint = ?""",
            (attempt_fingerprint,),
        ).fetchone()
        if row is None or row["run_id"] != run_id:
            raise ContractViolation("effect terminal requires a matching journal attempt")
        self._validated_journal(row)
        if row["state"] != "STARTED":
            raise ContractViolation("effect terminal requires a STARTED journal attempt")
        return row

    def _finalize_journal(self, row: sqlite3.Row, state: str, reason: str,
                          updated_at: int) -> None:
        if row["state"] in ("EFFECT_AND_TERMINAL_COMMITTED", "TERMINAL_NO_EFFECT"):
            if row["state"] != state:
                raise ContractViolation("terminal journal state cannot change")
            return
        result = self._db.execute(
            """UPDATE execution_journal
               SET state = ?, reason = ?, updated_at = ?, journal_hash = ?
               WHERE attempt_fingerprint = ? AND journal_hash = ?""",
            (
                state, reason, updated_at,
                self._journal_mac(row["attempt_fingerprint"], row["run_id"], state, reason, updated_at),
                row["attempt_fingerprint"], row["journal_hash"],
            ),
        )
        if result.rowcount != 1:
            raise ContractViolation("journal terminal transition was not durable")

    def _assert_allowed_schema_objects(self) -> None:
        objects = self._schema_objects()
        expected = {
            ("table", "memory_candidates"), ("table", "terminal_runs"),
            ("table", "execution_journal"), ("table", "store_metadata"),
            ("index", "one_committed_effect_per_run"),
        }
        if objects != expected:
            raise ContractViolation("operational SQLite contains unapproved schema objects")

    def healthcheck(self, *, write_required: bool = False) -> bool:
        try:
            with self._lock:
                if self._db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                    return False
                self._assert_write_integrity()
                for row in self._db.execute(
                    "SELECT attempt_fingerprint, run_id, state, reason, updated_at, journal_hash FROM execution_journal"
                ).fetchall():
                    self._validated_journal(row)
                for row in self._db.execute(
                    "SELECT DISTINCT task_id FROM memory_candidates"
                ).fetchall():
                    self.history(row["task_id"])
                for row in self._db.execute(
                    "SELECT request_fingerprint, run_id, result_fingerprint, terminal_hash, effect_committed, envelope_json FROM terminal_runs"
                ).fetchall():
                    self._validated_terminal(row, row["run_id"])
                if write_required:
                    count = self._db.execute(
                        "SELECT COUNT(*) AS count FROM memory_candidates"
                    ).fetchone()["count"]
                    return count < self.max_records
                return True
        except (sqlite3.Error, ContractViolation):
            return False

    def record_state(self, attempt_fingerprint: str, run_id: str,
                     state: str, reason: str, now: int) -> str:
        if state not in {"STARTED", "FAILED"}:
            raise ContractViolation("journal state transition is not caller-authorized")
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                self._assert_write_integrity()
                existing = self._db.execute(
                    """SELECT attempt_fingerprint, run_id, state, reason, updated_at, journal_hash
                       FROM execution_journal WHERE attempt_fingerprint = ?""",
                    (attempt_fingerprint,),
                ).fetchone()
                if existing is None:
                    count = self._db.execute(
                        "SELECT COUNT(*) AS count FROM execution_journal"
                    ).fetchone()["count"]
                    if count >= self.max_attempts:
                        raise CapacityExceeded("execution journal capacity exhausted")
                else:
                    validated = self._validated_journal(existing)
                    if validated["state"] in ("EFFECT_AND_TERMINAL_COMMITTED", "TERMINAL_NO_EFFECT"):
                        self._db.execute("COMMIT")
                        return attempt_fingerprint
                    if validated["state"] == "STARTED" and state == "STARTED":
                        self._db.execute("COMMIT")
                        return attempt_fingerprint
                    if validated["state"] == "FAILED" and state == "STARTED":
                        if now < validated["updated_at"]:
                            raise ContractViolation("journal logical time cannot regress")
                        sequence = self._db.execute(
                            "SELECT COUNT(*) FROM execution_journal WHERE run_id = ?", (run_id,)
                        ).fetchone()[0]
                        attempt_fingerprint = sha256(
                            f"{attempt_fingerprint}:retry:{sequence}".encode()
                        ).hexdigest()
                        existing = None
                    elif (validated["state"] != "STARTED" or state != "FAILED"
                          or now < validated["updated_at"]):
                        raise ContractViolation("journal transition is not monotonic")
                if existing is not None and existing["run_id"] != run_id:
                    raise IdentityCollision("attempt identity reused for a different run")
                journal_hash = self._journal_mac(attempt_fingerprint, run_id, state, reason, now)
                self._db.execute(
                    """INSERT INTO execution_journal(
                         attempt_fingerprint, run_id, state, reason, updated_at, journal_hash
                       ) VALUES (?, ?, ?, ?, ?, ?)
                       ON CONFLICT(attempt_fingerprint) DO UPDATE SET
                         state=excluded.state, reason=excluded.reason,
                         updated_at=excluded.updated_at, journal_hash=excluded.journal_hash""",
                    (attempt_fingerprint, run_id, state, reason, now, journal_hash),
                )
                self._db.execute("COMMIT")
                return attempt_fingerprint
            except Exception:
                self._db.execute("ROLLBACK")
                raise

    def journal(self, run_id: str) -> tuple[Mapping[str, Any], ...]:
        with self._lock:
            rows = self._db.execute(
                "SELECT attempt_fingerprint, run_id, state, reason, updated_at, journal_hash FROM execution_journal WHERE run_id = ? ORDER BY updated_at, attempt_fingerprint",
                (run_id,),
            ).fetchall()
            return tuple(self._validated_journal(row) for row in rows)

    def _validated_terminal(self, row: sqlite3.Row, run_id: str) -> tuple[str, Envelope]:
        envelope = _decoded_envelope(row["envelope_json"])
        expected_hash = self._mac(
            row["request_fingerprint"] + row["result_fingerprint"]
            + str(row["effect_committed"]) + row["envelope_json"]
        )
        enforcement = envelope.payload.get("enforcement")
        expected_status = "COMMITTED" if row["effect_committed"] else "NOT_EXECUTED"
        if (envelope.run_id != run_id or envelope.fingerprint != row["result_fingerprint"]
                or not hmac.compare_digest(expected_hash, row["terminal_hash"])
                or not isinstance(enforcement, Mapping)
                or enforcement.get("status") != expected_status):
            raise ContractViolation("terminal integrity verification failed")
        if row["effect_committed"]:
            memory = self._db.execute(
                """SELECT task_id, run_id, version, previous_hash, record_hash,
                          candidate_fingerprint, record_json
                   FROM memory_candidates
                   WHERE run_id = ?""", (run_id,)
            ).fetchone()
            if (memory is None or memory["version"] != enforcement.get("record_version")
                    or memory["record_hash"] != enforcement.get("record_hash")
                    or memory["candidate_fingerprint"] != enforcement.get("candidate_fingerprint")):
                raise ContractViolation("terminal effect coherence verification failed")
            stored = json.loads(memory["record_json"])
            claimed_hash = stored.pop("record_hash", None)
            calculated_hash = self._mac(memory["previous_hash"] + _encoded(stored))
            if (
                memory["task_id"] != envelope.task_id
                or memory["run_id"] != envelope.run_id
                or stored.get("task_id") != memory["task_id"]
                or stored.get("run_id") != memory["run_id"]
                or stored.get("version") != memory["version"]
                or stored.get("previous_hash") != memory["previous_hash"]
                or memory["record_hash"] != calculated_hash
                or claimed_hash != calculated_hash
            ):
                raise ContractViolation("terminal durable effect authentication failed")
            history = self.history(memory["task_id"])
            if (len(history) < memory["version"]
                    or history[memory["version"] - 1]["record_hash"] != memory["record_hash"]):
                raise ContractViolation("terminal effect chain predecessor is invalid")
            candidate = {
                key: value for key, value in stored.items()
                if key not in {"version", "previous_hash"}
            }
            if sha256(_encoded(candidate).encode()).hexdigest() != memory["candidate_fingerprint"]:
                raise ContractViolation("durable candidate binding verification failed")
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

    def resolve_request_terminal(self, run_id: str,
                                 request_fingerprint: str) -> tuple[str, Envelope] | None:
        """Resolve exact replay or a conflicting committed run in one DB snapshot."""
        with self._lock:
            row = self._db.execute(
                """SELECT request_fingerprint, result_fingerprint, terminal_hash,
                          effect_committed, envelope_json
                   FROM terminal_runs
                   WHERE run_id = ? AND (request_fingerprint = ? OR effect_committed = 1)
                   ORDER BY CASE WHEN request_fingerprint = ? THEN 0 ELSE 1 END
                   LIMIT 1""",
                (run_id, request_fingerprint, request_fingerprint),
            ).fetchone()
            if row is None:
                return None
            result = self._validated_terminal(row, run_id)
            if row["request_fingerprint"] != request_fingerprint:
                raise IdentityCollision("run identity reused with different committed request")
            return result

    def commit_effect_and_terminal(self, *, request_fingerprint: str,
                                   decision_envelope: Envelope,
                                   candidate_fingerprint: str,
                                   authorize_effect: Callable[[], tuple[Mapping[str, Any], int]],
                                   action: str, journal_fingerprint: str | None = None) -> Envelope:
        if action != "store_candidate":
            raise ContractViolation("unsupported action has no operational effect handler")
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                self._assert_write_integrity()
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
                journal = self._require_started_journal(
                    journal_fingerprint or request_fingerprint, decision_envelope.run_id
                )

                record, commit_time = authorize_effect()
                if (not isinstance(commit_time, int) or isinstance(commit_time, bool)
                        or commit_time < 0):
                    raise ContractViolation("commit authorization time is invalid")
                if sha256(_encoded(record).encode()).hexdigest() != candidate_fingerprint:
                    raise ContractViolation("authorized candidate fingerprint does not match record")

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
                    history = self.history(decision_envelope.task_id)
                    latest = None if not history else history[-1]
                    version = 1 if latest is None else latest["version"] + 1
                    previous_hash = "GENESIS" if latest is None else latest["record_hash"]
                    stored = {**plain_copy(record), "version": version, "previous_hash": previous_hash}
                    record_hash = self._mac(previous_hash + _encoded(stored))
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
                    "candidate_fingerprint": candidate_fingerprint,
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
                        self._mac(
                            request_fingerprint + final.fingerprint + "1"
                            + _encoded(final.to_dict())
                        ),
                        _encoded(final.to_dict()),
                    ),
                )
                terminal_row = self._db.execute(
                    """SELECT request_fingerprint, result_fingerprint, terminal_hash,
                              effect_committed, envelope_json
                       FROM terminal_runs WHERE request_fingerprint = ?""",
                    (request_fingerprint,),
                ).fetchone()
                _, verified_final = self._validated_terminal(
                    terminal_row, decision_envelope.run_id
                )
                self._finalize_journal(
                    journal, "EFFECT_AND_TERMINAL_COMMITTED", "COMMITTED", commit_time
                )
                terminal_row = self._db.execute(
                    """SELECT request_fingerprint, result_fingerprint, terminal_hash,
                              effect_committed, envelope_json
                       FROM terminal_runs WHERE request_fingerprint = ?""",
                    (request_fingerprint,),
                ).fetchone()
                _, verified_final = self._validated_terminal(
                    terminal_row, decision_envelope.run_id
                )
                self._assert_write_integrity()
                self._db.execute("COMMIT")
                return verified_final
            except Exception:
                self._db.execute("ROLLBACK")
                raise

    def commit_no_effect_terminal(self, *, request_fingerprint: str,
                                  envelope: Envelope, journal_fingerprint: str | None = None) -> Envelope:
        encoded = _encoded(envelope.to_dict())
        terminal_hash = self._mac(
            request_fingerprint + envelope.fingerprint + "0" + encoded
        )
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                self._assert_write_integrity()
                journal = self._require_started_journal(
                    journal_fingerprint or request_fingerprint, envelope.run_id
                )
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
                self._finalize_journal(
                    journal, "TERMINAL_NO_EFFECT",
                    envelope.payload["governance"]["decision"], journal["updated_at"],
                )
                row = self._db.execute(
                    """SELECT request_fingerprint, result_fingerprint, terminal_hash,
                              effect_committed, envelope_json
                       FROM terminal_runs WHERE request_fingerprint = ?""",
                    (request_fingerprint,),
                ).fetchone()
                _, result = self._validated_terminal(row, envelope.run_id)
                self._assert_write_integrity()
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
            calculated = self._mac(expected_previous + _encoded(record))
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

