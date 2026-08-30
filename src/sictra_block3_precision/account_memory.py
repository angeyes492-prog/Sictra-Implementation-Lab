"""Tamper-evident, tenant-scoped durable memory for official-site evidence."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from hashlib import sha256
import hmac
import json
from pathlib import Path
import re
import sqlite3
from threading import RLock
from typing import Any

from .account_knowledge import AccountKnowledgeDossier
from .contracts import PrecisionCapacityExceeded, PrecisionContractViolation, require_text


_QUERY_TOKEN = re.compile(r"[a-z0-9][a-z0-9_-]{1,}", re.IGNORECASE)


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def _encoded(value: Any) -> str:
    return json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class AccountKnowledgeStore:
    """Append-only evidence and snapshot store; expired/tombstoned data is unreadable.

    The store uses HMAC chains for integrity, not encryption. Deployment-grade
    encryption, key custody and physical erasure remain external requirements.
    """

    _VERSION = 2

    def __init__(self, path: str | Path = ":memory:", *, integrity_key: bytes, max_records: int = 100_000) -> None:
        if len(integrity_key) < 32 or max_records < 1:
            raise PrecisionContractViolation("account memory requires 32-byte integrity key and positive capacity")
        self.path = str(path)
        self._key = bytes(integrity_key)
        self._max_records = max_records
        self._lock = RLock()
        self._db = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        try:
            self._db.execute("PRAGMA foreign_keys = ON")
            if self.path != ":memory:":
                self._db.execute("PRAGMA journal_mode = WAL")
                self._db.execute("PRAGMA synchronous = FULL")
            self._initialize()
        except Exception:
            self._db.close()
            raise

    def close(self) -> None:
        self._db.close()

    def _mac(self, material: str) -> str:
        return hmac.new(self._key, material.encode("utf-8"), sha256).hexdigest()

    def _initialize(self) -> None:
        self._db.execute("BEGIN IMMEDIATE")
        try:
            version = self._db.execute("PRAGMA user_version").fetchone()[0]
            if version == 0:
                existing = self._db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ).fetchall()
                if existing:
                    raise PrecisionContractViolation("unversioned account memory database must be empty")
                self._db.execute("""CREATE TABLE account_evidence (
                    tenant_id TEXT NOT NULL, account_id TEXT NOT NULL, sequence INTEGER NOT NULL,
                    evidence_id TEXT NOT NULL, captured_at INTEGER NOT NULL, expires_at INTEGER NOT NULL,
                    record_json TEXT NOT NULL, previous_hash TEXT NOT NULL, record_hash TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, account_id, sequence), UNIQUE (tenant_id, evidence_id)
                )""")
                self._db.execute("""CREATE TABLE account_snapshots (
                    tenant_id TEXT NOT NULL, account_id TEXT NOT NULL, sequence INTEGER NOT NULL,
                    dossier_id TEXT NOT NULL, created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL,
                    dossier_fingerprint TEXT NOT NULL, record_json TEXT NOT NULL,
                    previous_hash TEXT NOT NULL, record_hash TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, account_id, sequence), UNIQUE (tenant_id, dossier_id)
                )""")
                self._db.execute("""CREATE TABLE account_tombstones (
                    tenant_id TEXT NOT NULL, account_id TEXT NOT NULL, tombstoned_at INTEGER NOT NULL,
                    reason TEXT NOT NULL, previous_hash TEXT NOT NULL, record_hash TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, account_id)
                )""")
                self._db.execute("""CREATE TABLE account_heads (
                    tenant_id TEXT NOT NULL, account_id TEXT NOT NULL,
                    evidence_count INTEGER NOT NULL, evidence_head TEXT NOT NULL,
                    snapshot_count INTEGER NOT NULL, snapshot_head TEXT NOT NULL,
                    tombstone_hash TEXT, head_mac TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, account_id)
                )""")
                self._db.execute("""CREATE TABLE account_memory_metadata (
                    singleton INTEGER PRIMARY KEY CHECK(singleton = 1), max_records INTEGER NOT NULL,
                    key_check TEXT NOT NULL
                )""")
                self._db.execute("INSERT INTO account_memory_metadata VALUES (1, ?, ?)", (
                    self._max_records, self._mac(f"account-memory-v{self._VERSION}:{self._max_records}"),
                ))
                self._db.execute(f"PRAGMA user_version = {self._VERSION}")
            elif version != self._VERSION:
                raise PrecisionContractViolation("unsupported account memory schema version")
            self._assert_allowed_schema_objects()
            self._assert_metadata()
            self._db.execute("COMMIT")
        except Exception:
            self._db.execute("ROLLBACK")
            raise

    def _assert_metadata(self) -> None:
        row = self._db.execute("SELECT max_records, key_check FROM account_memory_metadata WHERE singleton=1").fetchone()
        expected = self._mac(f"account-memory-v{self._VERSION}:{self._max_records}")
        if row is None or row["max_records"] != self._max_records or not hmac.compare_digest(row["key_check"], expected):
            raise PrecisionContractViolation("account memory capacity or integrity key mismatch")

    def _assert_allowed_schema_objects(self) -> None:
        actual = {
            (row["type"], row["name"])
            for row in self._db.execute(
                "SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        expected = {
            ("table", "account_evidence"), ("table", "account_snapshots"),
            ("table", "account_tombstones"), ("table", "account_heads"),
            ("table", "account_memory_metadata"),
        }
        if actual != expected:
            raise PrecisionContractViolation("account memory contains unapproved schema objects")

    def _head_mac(self, *, tenant_id: str, account_id: str, evidence_count: int,
                  evidence_head: str, snapshot_count: int, snapshot_head: str,
                  tombstone_hash: str | None) -> str:
        return self._mac("account-head-v2:" + _encoded((
            tenant_id, account_id, evidence_count, evidence_head,
            snapshot_count, snapshot_head, tombstone_hash,
        )))

    def _head(self, tenant_id: str, account_id: str) -> tuple[int, str, int, str, str | None]:
        row = self._db.execute(
            """SELECT evidence_count, evidence_head, snapshot_count, snapshot_head,
                      tombstone_hash, head_mac FROM account_heads WHERE tenant_id=? AND account_id=?""",
            (tenant_id, account_id),
        ).fetchone()
        if row is None:
            return 0, "GENESIS", 0, "GENESIS", None
        values = (
            int(row["evidence_count"]), str(row["evidence_head"]),
            int(row["snapshot_count"]), str(row["snapshot_head"]), row["tombstone_hash"],
        )
        expected = self._head_mac(
            tenant_id=tenant_id, account_id=account_id, evidence_count=values[0],
            evidence_head=values[1], snapshot_count=values[2], snapshot_head=values[3],
            tombstone_hash=values[4],
        )
        if not hmac.compare_digest(row["head_mac"], expected):
            raise PrecisionContractViolation("account memory head integrity verification failed")
        return values

    def _write_head(self, *, tenant_id: str, account_id: str, evidence_count: int,
                    evidence_head: str, snapshot_count: int, snapshot_head: str,
                    tombstone_hash: str | None) -> None:
        mac = self._head_mac(
            tenant_id=tenant_id, account_id=account_id, evidence_count=evidence_count,
            evidence_head=evidence_head, snapshot_count=snapshot_count,
            snapshot_head=snapshot_head, tombstone_hash=tombstone_hash,
        )
        self._db.execute(
            """INSERT INTO account_heads VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(tenant_id, account_id) DO UPDATE SET
               evidence_count=excluded.evidence_count, evidence_head=excluded.evidence_head,
               snapshot_count=excluded.snapshot_count, snapshot_head=excluded.snapshot_head,
               tombstone_hash=excluded.tombstone_hash, head_mac=excluded.head_mac""",
            (tenant_id, account_id, evidence_count, evidence_head, snapshot_count,
             snapshot_head, tombstone_hash, mac),
        )

    def _previous_hash(self, table: str, tenant_id: str, account_id: str) -> tuple[int, str]:
        row = self._db.execute(
            f"SELECT sequence, record_hash FROM {table} WHERE tenant_id=? AND account_id=? ORDER BY sequence DESC LIMIT 1",
            (tenant_id, account_id),
        ).fetchone()
        return (0, "GENESIS") if row is None else (int(row["sequence"]), str(row["record_hash"]))

    def _evidence_hash(self, *, previous_hash: str, record_json: str) -> str:
        return self._mac("account-evidence-v1:" + previous_hash + ":" + record_json)

    def _snapshot_hash(self, *, previous_hash: str, record_json: str) -> str:
        return self._mac("account-snapshot-v1:" + previous_hash + ":" + record_json)

    def _assert_active(self, tenant_id: str, account_id: str, now: int) -> None:
        row = self._db.execute(
            "SELECT tombstoned_at, reason, previous_hash, record_hash FROM account_tombstones WHERE tenant_id=? AND account_id=?",
            (tenant_id, account_id),
        ).fetchone()
        *_, tombstone_hash = self._head(tenant_id, account_id)
        if row is None and tombstone_hash is not None:
            raise PrecisionContractViolation("account tombstone deletion detected")
        if row is not None:
            expected = self._mac(
                f"account-tombstone-v1:{row['previous_hash']}:{tenant_id}:{account_id}:{row['tombstoned_at']}:{row['reason']}"
            )
            if tombstone_hash != row["record_hash"] or not hmac.compare_digest(row["record_hash"], expected):
                raise PrecisionContractViolation("account tombstone integrity verification failed")
            raise PrecisionContractViolation("account memory is tombstoned")

    def _verify_chain(self, table: str, tenant_id: str, account_id: str, *, kind: str,
                      expected_count: int, expected_head: str) -> None:
        previous = "GENESIS"
        rows = self._db.execute(
            f"SELECT sequence, record_json, previous_hash, record_hash FROM {table} WHERE tenant_id=? AND account_id=? ORDER BY sequence",
            (tenant_id, account_id),
        ).fetchall()
        for expected_sequence, row in enumerate(rows, start=1):
            if row["sequence"] != expected_sequence or row["previous_hash"] != previous:
                raise PrecisionContractViolation(f"{kind} memory chain sequence is invalid")
            expected = self._evidence_hash(previous_hash=previous, record_json=row["record_json"]) if kind == "evidence" else self._snapshot_hash(previous_hash=previous, record_json=row["record_json"])
            if not hmac.compare_digest(row["record_hash"], expected):
                raise PrecisionContractViolation(f"{kind} memory chain integrity verification failed")
            previous = row["record_hash"]
        if len(rows) != expected_count or previous != expected_head:
            raise PrecisionContractViolation(f"{kind} memory head mismatch")

    def _verify_account(self, tenant_id: str, account_id: str) -> None:
        evidence_count, evidence_head, snapshot_count, snapshot_head, _ = self._head(tenant_id, account_id)
        self._verify_chain(
            "account_evidence", tenant_id, account_id, kind="evidence",
            expected_count=evidence_count, expected_head=evidence_head,
        )
        self._verify_chain(
            "account_snapshots", tenant_id, account_id, kind="snapshot",
            expected_count=snapshot_count, expected_head=snapshot_head,
        )

    def append_dossier(self, dossier: AccountKnowledgeDossier) -> str:
        require_text("tenant_id", dossier.tenant_id)
        require_text("account_id", dossier.account_id)
        if any(item.tenant_id != dossier.tenant_id or item.account_id != dossier.account_id for item in dossier.observations):
            raise PrecisionContractViolation("dossier contains cross-tenant or cross-account evidence")
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                self._assert_allowed_schema_objects()
                self._assert_metadata()
                self._verify_account(dossier.tenant_id, dossier.account_id)
                self._assert_active(dossier.tenant_id, dossier.account_id, dossier.captured_at)
                count = self._db.execute("SELECT COUNT(*) AS n FROM account_evidence").fetchone()["n"]
                new_records = sum(
                    self._db.execute(
                        "SELECT 1 FROM account_evidence WHERE tenant_id=? AND evidence_id=?",
                        (dossier.tenant_id, item.evidence.evidence_id),
                    ).fetchone() is None
                    for item in dossier.observations
                )
                if count + new_records > self._max_records:
                    raise PrecisionCapacityExceeded("account evidence memory capacity exhausted")
                for observation in dossier.observations:
                    record_json = _encoded(observation)
                    existing = self._db.execute(
                        "SELECT record_json FROM account_evidence WHERE tenant_id=? AND evidence_id=?",
                        (dossier.tenant_id, observation.evidence.evidence_id),
                    ).fetchone()
                    if existing is not None:
                        if existing["record_json"] != record_json:
                            raise PrecisionContractViolation("account evidence identity collision")
                        continue
                    sequence, previous = self._previous_hash("account_evidence", dossier.tenant_id, dossier.account_id)
                    record_hash = self._evidence_hash(previous_hash=previous, record_json=record_json)
                    self._db.execute(
                        "INSERT INTO account_evidence VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (dossier.tenant_id, dossier.account_id, sequence + 1, observation.evidence.evidence_id,
                         observation.captured_at, observation.expires_at, record_json, previous, record_hash),
                    )
                snapshot_json = _encoded(dossier)
                existing_snapshot = self._db.execute(
                    "SELECT record_json FROM account_snapshots WHERE tenant_id=? AND dossier_id=?",
                    (dossier.tenant_id, dossier.dossier_id),
                ).fetchone()
                if existing_snapshot is not None:
                    if existing_snapshot["record_json"] != snapshot_json:
                        raise PrecisionContractViolation("account dossier identity collision")
                else:
                    sequence, previous = self._previous_hash("account_snapshots", dossier.tenant_id, dossier.account_id)
                    record_hash = self._snapshot_hash(previous_hash=previous, record_json=snapshot_json)
                    self._db.execute(
                        "INSERT INTO account_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (dossier.tenant_id, dossier.account_id, sequence + 1, dossier.dossier_id,
                         dossier.captured_at, dossier.expires_at, dossier.output_fingerprint,
                         snapshot_json, previous, record_hash),
                    )
                evidence_count, evidence_head = self._previous_hash(
                    "account_evidence", dossier.tenant_id, dossier.account_id,
                )
                snapshot_count, snapshot_head = self._previous_hash(
                    "account_snapshots", dossier.tenant_id, dossier.account_id,
                )
                self._write_head(
                    tenant_id=dossier.tenant_id, account_id=dossier.account_id,
                    evidence_count=evidence_count, evidence_head=evidence_head,
                    snapshot_count=snapshot_count, snapshot_head=snapshot_head,
                    tombstone_hash=None,
                )
                self._db.execute("COMMIT")
                return dossier.dossier_id
            except Exception:
                self._db.execute("ROLLBACK")
                raise

    def observations(self, *, tenant_id: str, account_id: str, now: int) -> tuple[dict[str, Any], ...]:
        for value in (tenant_id, account_id):
            require_text("memory identity", value)
        with self._lock:
            self._assert_allowed_schema_objects()
            self._assert_metadata()
            self._verify_account(tenant_id, account_id)
            self._assert_active(tenant_id, account_id, now)
            rows = self._db.execute(
                "SELECT record_json FROM account_evidence WHERE tenant_id=? AND account_id=? AND expires_at>=? ORDER BY sequence",
                (tenant_id, account_id, now),
            ).fetchall()
            return tuple(json.loads(row["record_json"]) for row in rows)

    def latest_snapshot(self, *, tenant_id: str, account_id: str, now: int) -> dict[str, Any] | None:
        for value in (tenant_id, account_id):
            require_text("memory identity", value)
        with self._lock:
            self._assert_allowed_schema_objects()
            self._assert_metadata()
            self._verify_account(tenant_id, account_id)
            self._assert_active(tenant_id, account_id, now)
            row = self._db.execute(
                "SELECT record_json FROM account_snapshots WHERE tenant_id=? AND account_id=? AND expires_at>=? ORDER BY sequence DESC LIMIT 1",
                (tenant_id, account_id, now),
            ).fetchone()
            return None if row is None else json.loads(row["record_json"])

    def search(self, *, tenant_id: str, account_id: str, query: str, now: int, limit: int = 8) -> tuple[dict[str, Any], ...]:
        """Deterministic discovery aid. Returned entries remain source evidence, not facts."""
        tokens = set(token.casefold() for token in _QUERY_TOKEN.findall(query))
        if not tokens or limit < 1:
            raise PrecisionContractViolation("memory search requires tokens and positive limit")
        candidates = self.observations(tenant_id=tenant_id, account_id=account_id, now=now)
        ranked = []
        for item in candidates:
            excerpt_tokens = {token.casefold() for token in _QUERY_TOKEN.findall(item.get("excerpt", ""))}
            score = len(tokens.intersection(set(item.get("tags", ())) | excerpt_tokens))
            if score:
                ranked.append((-score, item["observation_id"], item))
        return tuple(item for _, _, item in sorted(ranked)[:limit])

    def tombstone_account(self, *, tenant_id: str, account_id: str, now: int, reason: str) -> None:
        for value in (tenant_id, account_id, reason):
            require_text("tombstone field", value)
        if not isinstance(now, int) or now < 0:
            raise PrecisionContractViolation("tombstone time is invalid")
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                self._assert_allowed_schema_objects()
                self._assert_metadata()
                self._verify_account(tenant_id, account_id)
                existing = self._db.execute(
                    "SELECT tombstoned_at, reason FROM account_tombstones WHERE tenant_id=? AND account_id=?",
                    (tenant_id, account_id),
                ).fetchone()
                if existing is not None:
                    if existing["tombstoned_at"] != now or existing["reason"] != reason:
                        raise PrecisionContractViolation("account tombstone is immutable")
                    self._db.execute("COMMIT")
                    return
                evidence_sequence, evidence_hash = self._previous_hash("account_evidence", tenant_id, account_id)
                snapshot_sequence, snapshot_hash = self._previous_hash("account_snapshots", tenant_id, account_id)
                previous = sha256(f"{evidence_sequence}:{evidence_hash}:{snapshot_sequence}:{snapshot_hash}".encode()).hexdigest()
                record_hash = self._mac(f"account-tombstone-v1:{previous}:{tenant_id}:{account_id}:{now}:{reason}")
                self._db.execute(
                    "INSERT INTO account_tombstones VALUES (?, ?, ?, ?, ?, ?)",
                    (tenant_id, account_id, now, reason, previous, record_hash),
                )
                evidence_count, evidence_head, snapshot_count, snapshot_head, _ = self._head(tenant_id, account_id)
                self._write_head(
                    tenant_id=tenant_id, account_id=account_id,
                    evidence_count=evidence_count, evidence_head=evidence_head,
                    snapshot_count=snapshot_count, snapshot_head=snapshot_head,
                    tombstone_hash=record_hash,
                )
                self._db.execute("COMMIT")
            except Exception:
                self._db.execute("ROLLBACK")
                raise

