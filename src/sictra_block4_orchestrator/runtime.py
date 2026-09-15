"""Append-only, supervised federation of local Block 1–3 handoffs.

This module intentionally coordinates a controlled package rather than calling
neighbouring HTTP APIs or sharing their secret stores.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from contextlib import closing
import hmac
import json
from pathlib import Path
import sqlite3
from typing import Any


CONTRACT_VERSION = "0.1.0"
PRODUCERS = frozenset(("BLOCK1", "BLOCK2", "BLOCK3"))
CERTAINTIES = frozenset(("VERIFIED", "PROBABLE", "PLAUSIBLE", "UNCONFIRMED", "CONTRADICTED", "INSUFFICIENT EVIDENCE"))
STAGES = ("BLOCK1_ATTESTED", "BLOCK2_CANDIDATE", "BLOCK3_GOVERNED", "HUMAN_REVIEW_REQUIRED")
TERMINAL = frozenset(("HUMAN_REVIEW_REQUIRED", "ABSTAINED", "RETURN_UPSTREAM", "REJECTED"))
REQUIRED = frozenset((
    "case_id", "run_id", "message_id", "evidence_id", "dossier_id", "producer",
    "contract_version", "source_hash", "provenance_root", "observed_at", "expires_at",
    "currentness", "certainty", "uncertainty", "disposition", "lineage", "payload", "signature",
))


class FederatedContractError(ValueError):
    """A package or state transition crossed a declared federation boundary."""


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _fingerprint(value: Any) -> str:
    return sha256(_canonical(value)).hexdigest()


def _without_signature(package: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in package.items() if key != "signature"}


def _iso(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as error:
        raise FederatedContractError("TIMESTAMP_INVALID") from error
    if parsed.tzinfo is None:
        raise FederatedContractError("TIMESTAMP_NOT_TIMEZONE_AWARE")
    return parsed.astimezone(timezone.utc)


def _now(value: datetime | None) -> datetime:
    return (value or datetime.now(timezone.utc)).astimezone(timezone.utc)


def _validate_package(package: dict[str, Any], integrity_key: bytes, now: datetime) -> None:
    if not isinstance(package, dict) or set(package) != REQUIRED:
        raise FederatedContractError("SCHEMA_NOT_ALLOWLISTED")
    if any(not isinstance(package[key], str) or not package[key].strip() for key in REQUIRED - {"uncertainty", "lineage", "payload"}):
        raise FederatedContractError("REQUIRED_STRING_INVALID")
    if not isinstance(package["uncertainty"], list) or not all(isinstance(item, str) and item for item in package["uncertainty"]):
        raise FederatedContractError("UNCERTAINTY_NOT_ALLOWLISTED")
    if not isinstance(package["lineage"], list) or not all(item in PRODUCERS for item in package["lineage"]):
        raise FederatedContractError("LINEAGE_NOT_ALLOWLISTED")
    if not isinstance(package["payload"], dict) or set(package["payload"]) != {"summary", "limitations"}:
        raise FederatedContractError("PAYLOAD_NOT_ALLOWLISTED")
    if package["producer"] != "BLOCK1" or package["lineage"] != ["BLOCK1"]:
        raise FederatedContractError("INITIAL_PRODUCER_OR_LINEAGE_INVALID")
    if package["contract_version"] != CONTRACT_VERSION:
        raise FederatedContractError("CONTRACT_VERSION_UNSUPPORTED")
    if package["certainty"] not in CERTAINTIES or package["currentness"] not in {"CURRENT", "STALE"}:
        raise FederatedContractError("EPISTEMIC_STATE_INVALID")
    observed, expires = _iso(package["observed_at"]), _iso(package["expires_at"])
    if observed > now or expires <= observed:
        raise FederatedContractError("TEMPORAL_ORDER_INVALID")
    expected = hmac.new(integrity_key, _canonical(_without_signature(package)), "sha256").hexdigest()
    if not hmac.compare_digest(expected, package["signature"]):
        raise FederatedContractError("PACKAGE_SIGNATURE_INVALID")


def build_controlled_block1_package(*, integrity_key: bytes, case_id: str = "CASE-DEMO-001", run_id: str = "RUN-DEMO-001", now: datetime | None = None, expires_at: datetime | None = None, certainty: str = "PROBABLE", disposition: str = "REVIEW_REQUIRED", source_hash: str | None = None, provenance_root: str = "ROOT-DEMO-001") -> dict[str, Any]:
    """Build a deterministic, explicitly synthetic package for local operation."""
    current = _now(now)
    expiry = expires_at or current.replace(year=current.year + 1)
    package: dict[str, Any] = {
        "case_id": case_id, "run_id": run_id, "message_id": "MSG-" + case_id,
        "evidence_id": "EVID-" + case_id, "dossier_id": "DOSSIER-" + case_id,
        "producer": "BLOCK1", "contract_version": CONTRACT_VERSION,
        "source_hash": source_hash or sha256(("source|" + case_id).encode()).hexdigest(),
        "provenance_root": provenance_root, "observed_at": current.isoformat(),
        "expires_at": expiry.astimezone(timezone.utc).isoformat(), "currentness": "CURRENT",
        "certainty": certainty, "uncertainty": ["SYNTHETIC_FIELD_TEST_NOT_EVIDENCE"],
        "disposition": disposition, "lineage": ["BLOCK1"],
        "payload": {"summary": "Paquete local controlado para evaluación humana.", "limitations": ["NO_NETWORK", "NO_PUBLICATION"]},
    }
    package["signature"] = hmac.new(integrity_key, _canonical(package), "sha256").hexdigest()
    return package


@dataclass(frozen=True)
class FederatedCase:
    case_id: str
    run_id: str
    state: str
    retry_count: int
    fingerprint: str
    source_hash: str
    provenance_root: str
    certainty: str
    disposition: str
    expires_at: str
    lineage: tuple[str, ...]
    restrictions: tuple[str, ...]


class FederatedOrchestratorStore:
    """A local HMAC-attested journal with bounded autonomous progression."""

    def __init__(self, path: str | Path, *, integrity_key: bytes):
        if not isinstance(integrity_key, bytes) or len(integrity_key) < 16:
            raise ValueError("integrity_key must contain at least 16 bytes")
        self.path = Path(path)
        self.key = integrity_key
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()
        self._verify_chain()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init(self) -> None:
        with closing(self._connect()) as db:
            db.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS cases (case_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, fingerprint TEXT NOT NULL, state TEXT NOT NULL, retry_count INTEGER NOT NULL, package_json TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS events (sequence INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT UNIQUE NOT NULL, case_id TEXT NOT NULL, event_type TEXT NOT NULL, state TEXT NOT NULL, payload_json TEXT NOT NULL, prior_hash TEXT NOT NULL, event_hash TEXT NOT NULL, created_at TEXT NOT NULL)")
            key_id = sha256(self.key).hexdigest()
            previous = db.execute("SELECT value FROM metadata WHERE key='key_id'").fetchone()
            if previous is None:
                db.execute("INSERT INTO metadata(key,value) VALUES('key_id',?)", (key_id,))
            elif previous["value"] != key_id:
                raise FederatedContractError("INTEGRITY_KEY_ID_MISMATCH")
            db.commit()

    def _verify_chain(self) -> None:
        prior = "GENESIS"
        with closing(self._connect()) as db:
            for row in db.execute("SELECT * FROM events ORDER BY sequence"):
                material = {"event_id": row["event_id"], "case_id": row["case_id"], "event_type": row["event_type"], "state": row["state"], "payload": json.loads(row["payload_json"]), "prior_hash": prior, "created_at": row["created_at"]}
                expected = hmac.new(self.key, _canonical(material), "sha256").hexdigest()
                if row["prior_hash"] != prior or not hmac.compare_digest(expected, row["event_hash"]):
                    raise FederatedContractError("JOURNAL_INTEGRITY_ERROR")
                prior = row["event_hash"]

    def _append(self, db: sqlite3.Connection, *, case_id: str, event_type: str, state: str, payload: dict[str, Any], now: datetime) -> None:
        prior_row = db.execute("SELECT event_hash FROM events ORDER BY sequence DESC LIMIT 1").fetchone()
        prior = "GENESIS" if prior_row is None else prior_row["event_hash"]
        event_id = sha256((case_id + "|" + event_type + "|" + state + "|" + prior).encode()).hexdigest()[:32]
        material = {"event_id": event_id, "case_id": case_id, "event_type": event_type, "state": state, "payload": payload, "prior_hash": prior, "created_at": now.isoformat()}
        event_hash = hmac.new(self.key, _canonical(material), "sha256").hexdigest()
        db.execute("INSERT INTO events(event_id,case_id,event_type,state,payload_json,prior_hash,event_hash,created_at) VALUES(?,?,?,?,?,?,?,?)", (event_id, case_id, event_type, state, json.dumps(payload,sort_keys=True,separators=(",",":")), prior, event_hash, now.isoformat()))

    def _snapshot_row(self, row: sqlite3.Row) -> FederatedCase:
        package = json.loads(row["package_json"])
        route = ["BLOCK1"]
        if row["state"] in {"BLOCK2_CANDIDATE", "BLOCK3_GOVERNED", "HUMAN_REVIEW_REQUIRED"}: route.append("BLOCK2")
        if row["state"] in {"BLOCK3_GOVERNED", "HUMAN_REVIEW_REQUIRED"}: route.append("BLOCK3")
        return FederatedCase(row["case_id"], row["run_id"], row["state"], row["retry_count"], row["fingerprint"], package["source_hash"], package["provenance_root"], package["certainty"], package["disposition"], package["expires_at"], tuple(route), tuple(package["payload"]["limitations"]))

    def get_case(self, case_id: str) -> FederatedCase:
        self._verify_chain()
        with closing(self._connect()) as db:
            row = db.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
        if row is None:
            raise FederatedContractError("CASE_NOT_FOUND")
        return self._snapshot_row(row)

    def list_cases(self) -> tuple[FederatedCase, ...]:
        self._verify_chain()
        with closing(self._connect()) as db:
            rows = db.execute("SELECT * FROM cases ORDER BY updated_at DESC, case_id").fetchall()
        return tuple(self._snapshot_row(row) for row in rows)

    def ingest(self, package: dict[str, Any], *, now: datetime | None = None) -> FederatedCase:
        current = _now(now); _validate_package(package, self.key, current)
        fingerprint = _fingerprint(_without_signature(package))
        state = "RETURN_UPSTREAM" if package["currentness"] != "CURRENT" or _iso(package["expires_at"]) <= current or package["certainty"] in {"CONTRADICTED", "INSUFFICIENT EVIDENCE"} else "BLOCK1_ATTESTED"
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM cases WHERE case_id=?", (package["case_id"],)).fetchone()
            if row is not None:
                if row["fingerprint"] != fingerprint:
                    raise FederatedContractError("CASE_IDENTITY_COLLISION")
                db.rollback(); return self._snapshot_row(row)
            db.execute("INSERT INTO cases(case_id,run_id,fingerprint,state,retry_count,package_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)", (package["case_id"], package["run_id"], fingerprint, state, 0, json.dumps(package,sort_keys=True,separators=(",",":")), current.isoformat(), current.isoformat()))
            self._append(db, case_id=package["case_id"], event_type="INGESTED", state=state, payload={"fingerprint": fingerprint, "producer": "BLOCK1"}, now=current)
            db.commit()
        return self.get_case(package["case_id"])

    def _advance(self, case_id: str, *, now: datetime) -> FederatedCase:
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
            if row is None: raise FederatedContractError("CASE_NOT_FOUND")
            package = json.loads(row["package_json"])
            if _iso(package["expires_at"]) <= now:
                next_state, event = "RETURN_UPSTREAM", "EXPIRED"
            elif row["state"] == "BLOCK1_ATTESTED":
                next_state, event = "BLOCK2_CANDIDATE", "BLOCK2_COORDINATION_RECEIPT"
            elif row["state"] == "BLOCK2_CANDIDATE":
                next_state, event = "BLOCK3_GOVERNED", "BLOCK3_COORDINATION_RECEIPT"
            elif row["state"] == "BLOCK3_GOVERNED":
                next_state, event = "HUMAN_REVIEW_REQUIRED", "HUMAN_GATE_REACHED"
            else:
                db.rollback(); return self._snapshot_row(row)
            db.execute("UPDATE cases SET state=?,updated_at=? WHERE case_id=?", (next_state, now.isoformat(), case_id))
            self._append(db, case_id=case_id, event_type=event, state=next_state, payload={"source_hash": package["source_hash"], "provenance_root": package["provenance_root"]}, now=now)
            db.commit()
        return self.get_case(case_id)

    def process_to_human_gate(self, case_id: str, *, now: datetime | None = None) -> FederatedCase:
        current = _now(now)
        snapshot = self.get_case(case_id)
        while snapshot.state not in TERMINAL:
            snapshot = self._advance(case_id, now=current)
        return snapshot

    def process_pending(self, *, now: datetime | None = None) -> tuple[FederatedCase, ...]:
        current = _now(now)
        return tuple(self.process_to_human_gate(item.case_id, now=current) for item in self.list_cases() if item.state not in TERMINAL)

    def invalidate(self, case_id: str, reason: str, *, now: datetime | None = None) -> FederatedCase:
        if not isinstance(reason, str) or not reason.strip(): raise FederatedContractError("INVALIDATION_REASON_REQUIRED")
        current = _now(now)
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
            if row is None: raise FederatedContractError("CASE_NOT_FOUND")
            db.execute("UPDATE cases SET state='RETURN_UPSTREAM',updated_at=? WHERE case_id=?", (current.isoformat(), case_id))
            self._append(db, case_id=case_id, event_type="INVALIDATED", state="RETURN_UPSTREAM", payload={"reason": reason}, now=current)
            db.commit()
        return self.get_case(case_id)

    def retry(self, case_id: str, *, now: datetime | None = None) -> FederatedCase:
        current = _now(now)
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
            if row is None: raise FederatedContractError("CASE_NOT_FOUND")
            if row["retry_count"] >= 3: raise FederatedContractError("RETRY_LIMIT_EXHAUSTED")
            if row["state"] not in {"RETURN_UPSTREAM", "REJECTED"}: raise FederatedContractError("RETRY_STATE_INVALID")
            next_count = row["retry_count"] + 1
            db.execute("UPDATE cases SET retry_count=?,state='BLOCK1_ATTESTED',updated_at=? WHERE case_id=?", (next_count, current.isoformat(), case_id))
            self._append(db, case_id=case_id, event_type="RETRY", state="BLOCK1_ATTESTED", payload={"retry_count": next_count}, now=current)
            db.commit()
        return self.process_to_human_gate(case_id, now=current)

    def audit_events(self, case_id: str) -> tuple[dict[str, Any], ...]:
        self._verify_chain()
        with closing(self._connect()) as db:
            rows = db.execute("SELECT event_type,state,created_at,payload_json FROM events WHERE case_id=? ORDER BY sequence", (case_id,)).fetchall()
        return tuple({"event_type": row["event_type"], "state": row["state"], "created_at": row["created_at"], "payload": json.loads(row["payload_json"])} for row in rows)
