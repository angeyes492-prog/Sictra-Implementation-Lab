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
from typing import Any, Mapping


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
    evidence_id: str
    dossier_id: str
    uncertainty: tuple[str, ...]


class FederatedOrchestratorStore:
    """A local HMAC-attested journal with bounded autonomous progression."""

    def __init__(self, path: str | Path, *, integrity_key: bytes,
                 producer_keys: Mapping[str, bytes] | None = None):
        if not isinstance(integrity_key, bytes) or len(integrity_key) < 16:
            raise ValueError("integrity_key must contain at least 16 bytes")
        self.path = Path(path)
        self.key = integrity_key
        self.producer_keys = dict(producer_keys or {})
        if self.producer_keys:
            if (set(self.producer_keys) != {"BLOCK2", "BLOCK3"}
                    or any(not isinstance(key, bytes) or len(key) < 32 for key in self.producer_keys.values())
                    or len(set(self.producer_keys.values())) != 2
                    or self.key in self.producer_keys.values()):
                raise ValueError("producer_keys must contain distinct BLOCK2 and BLOCK3 keys")
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

    def _verify_chain(self, db: sqlite3.Connection | None = None) -> None:
        if db is None:
            with closing(self._connect()) as connection:
                connection.execute("BEGIN")
                self._verify_chain(connection)
            return
        prior = "GENESIS"
        latest = {}
        fingerprints = {}
        retries = {}
        try:
            for row in db.execute("SELECT * FROM events ORDER BY sequence"):
                material = {"event_id": row["event_id"], "case_id": row["case_id"], "event_type": row["event_type"], "state": row["state"], "payload": json.loads(row["payload_json"]), "prior_hash": prior, "created_at": row["created_at"]}
                expected = hmac.new(self.key, _canonical(material), "sha256").hexdigest()
                if row["prior_hash"] != prior or not hmac.compare_digest(expected, row["event_hash"]):
                    raise FederatedContractError("JOURNAL_INTEGRITY_ERROR")
                prior = row["event_hash"]
                latest[row["case_id"]] = row["state"]
                if row["event_type"] == "INGESTED":
                    fingerprints[row["case_id"]] = material["payload"]["fingerprint"]
                if row["event_type"] == "RETRY":
                    retries[row["case_id"]] = material["payload"]["retry_count"]
            checkpoints = db.execute("SELECT * FROM cases").fetchall()
            if {row["case_id"] for row in checkpoints} != set(latest):
                raise FederatedContractError("CHECKPOINT_INTEGRITY_ERROR")
            for row in checkpoints:
                package = json.loads(row["package_json"])
                fingerprint = _fingerprint(_without_signature(package))
                signature = hmac.new(self.key, _canonical(_without_signature(package)), "sha256").hexdigest()
                if (row["state"] != latest[row["case_id"]]
                    or row["retry_count"] != retries.get(row["case_id"], 0)
                    or row["fingerprint"] != fingerprints.get(row["case_id"])
                    or fingerprint != row["fingerprint"]
                    or package["case_id"] != row["case_id"]
                    or package["run_id"] != row["run_id"]
                    or not hmac.compare_digest(signature, package["signature"])):
                    raise FederatedContractError("CHECKPOINT_INTEGRITY_ERROR")
        except (KeyError, TypeError, json.JSONDecodeError) as error:
            raise FederatedContractError("JOURNAL_INTEGRITY_ERROR") from error

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
        return FederatedCase(row["case_id"], row["run_id"], row["state"], row["retry_count"], row["fingerprint"], package["source_hash"], package["provenance_root"], package["certainty"], package["disposition"], package["expires_at"], tuple(route), tuple(package["payload"]["limitations"]), package["evidence_id"], package["dossier_id"], tuple(package["uncertainty"]))

    def get_case(self, case_id: str) -> FederatedCase:
        with closing(self._connect()) as db:
            db.execute("BEGIN")
            self._verify_chain(db)
            row = db.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
        if row is None:
            raise FederatedContractError("CASE_NOT_FOUND")
        return self._snapshot_row(row)

    def list_cases(self) -> tuple[FederatedCase, ...]:
        with closing(self._connect()) as db:
            db.execute("BEGIN")
            self._verify_chain(db)
            rows = db.execute("SELECT * FROM cases ORDER BY updated_at DESC, case_id").fetchall()
        return tuple(self._snapshot_row(row) for row in rows)

    def ingest(self, package: dict[str, Any], *, now: datetime | None = None) -> FederatedCase:
        current = _now(now); _validate_package(package, self.key, current)
        fingerprint = _fingerprint(_without_signature(package))
        state = "RETURN_UPSTREAM" if package["currentness"] != "CURRENT" or _iso(package["expires_at"]) <= current or package["certainty"] in {"CONTRADICTED", "INSUFFICIENT EVIDENCE"} else "BLOCK1_ATTESTED"
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            self._verify_chain(db)
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
            self._verify_chain(db)
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

    def execution_receipts(self, case_id: str) -> tuple[Any, ...]:
        """Return only producer receipts whose journal and producer signatures verify."""
        from .execution_receipt import ExecutionReceipt, verify_receipt

        receipts = []
        for event in self.audit_events(case_id):
            material = event["payload"].get("execution_receipt")
            if material is None:
                continue
            receipt = ExecutionReceipt(**{
                **material,
                "executed_components": tuple(material["executed_components"]),
                "restrictions": tuple(material["restrictions"]),
            })
            producer_key = self.producer_keys.get(receipt.producer)
            if producer_key is None:
                raise FederatedContractError("PRODUCER_KEYS_NOT_CONFIGURED")
            verify_receipt(receipt, producer_key)
            receipts.append(receipt)
        return tuple(receipts)

    def record_execution(self, receipt: Any, *, now: datetime | None = None) -> FederatedCase:
        """Advance only from a verified receipt emitted by an invoked producer runtime."""
        from dataclasses import asdict
        from .execution_receipt import ExecutionReceipt, verify_receipt

        if not isinstance(receipt, ExecutionReceipt):
            raise FederatedContractError("EXECUTION_RECEIPT_TYPE_INVALID")
        producer_key = self.producer_keys.get(receipt.producer)
        if producer_key is None:
            raise FederatedContractError("PRODUCER_KEYS_NOT_CONFIGURED")
        verify_receipt(receipt, producer_key)
        current = _now(now)
        if _iso(receipt.created_at) > current:
            raise FederatedContractError("EXECUTION_RECEIPT_FROM_FUTURE")
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            self._verify_chain(db)
            row = db.execute("SELECT * FROM cases WHERE case_id=?", (receipt.case_id,)).fetchone()
            if row is None: raise FederatedContractError("CASE_NOT_FOUND")
            package = json.loads(row["package_json"])
            if receipt.run_id != row["run_id"]:
                raise FederatedContractError("EXECUTION_RUN_IDENTITY_MISMATCH")
            if _iso(receipt.created_at) < _iso(package["observed_at"]):
                raise FederatedContractError("EXECUTION_RECEIPT_PREDATES_PACKAGE")
            if _iso(package["expires_at"]) <= current:
                db.execute("UPDATE cases SET state='RETURN_UPSTREAM',updated_at=? WHERE case_id=?", (current.isoformat(), receipt.case_id))
                self._append(db, case_id=receipt.case_id, event_type="EXPIRED_BEFORE_EXECUTION_RECEIPT",
                             state="RETURN_UPSTREAM", payload={"source_hash": package["source_hash"]}, now=current)
                db.commit()
                return self.get_case(receipt.case_id)
            prior_receipts = []
            for event in db.execute("SELECT payload_json FROM events WHERE case_id=? ORDER BY sequence", (receipt.case_id,)):
                payload = json.loads(event["payload_json"])
                if isinstance(payload, dict) and isinstance(payload.get("execution_receipt"), dict):
                    prior_receipts.append(payload["execution_receipt"])
            material = asdict(receipt)
            normalized_receipts = [ExecutionReceipt(**{
                **previous,
                "executed_components": tuple(previous["executed_components"]),
                "restrictions": tuple(previous["restrictions"]),
            }) for previous in prior_receipts]
            if any(asdict(previous) == material for previous in normalized_receipts):
                db.rollback(); return self._snapshot_row(row)
            if any(previous.execution_id == receipt.execution_id for previous in normalized_receipts):
                raise FederatedContractError("EXECUTION_RECEIPT_IDENTITY_COLLISION")
            expected_producer = "BLOCK2" if row["state"] == "BLOCK1_ATTESTED" else "BLOCK3" if row["state"] == "BLOCK2_CANDIDATE" else None
            if receipt.producer != expected_producer:
                raise FederatedContractError("EXECUTION_TRANSITION_INVALID")
            if receipt.producer == "BLOCK2":
                expected_parent = row["fingerprint"]
            else:
                block2 = next((item for item in reversed(normalized_receipts) if item.producer == "BLOCK2"), None)
                if block2 is None: raise FederatedContractError("BLOCK2_EXECUTION_RECEIPT_MISSING")
                expected_parent = block2.fingerprint
            if receipt.parent_fingerprint != expected_parent:
                raise FederatedContractError("EXECUTION_PARENT_MISMATCH")
            if not {"NO_PUBLICATION", "NO_DELIVERY"}.issubset(receipt.restrictions):
                raise FederatedContractError("EXECUTION_AUTHORITY_BOUNDARY_MISSING")
            if receipt.producer == "BLOCK2":
                accepted = (receipt.disposition == "COMPLETED"
                            and receipt.payload.get("completed") is True
                            and receipt.payload.get("publication_state") == "NOT_PUBLISHED"
                            and receipt.payload.get("acceptance_state") == "NOT_ACCEPTED"
                            and receipt.executed_components == tuple(f"E0{number}" for number in range(1, 9)))
                next_state = "BLOCK2_CANDIDATE" if accepted else "RETURN_UPSTREAM"
            else:
                foundation_accepted = (receipt.disposition in {"ACCEPTED", "PARTIAL"}
                            and receipt.payload.get("decision_present") is True
                            and {"M01", "M02", "M03", "M04", "M05"}.issubset(receipt.executed_components))
                adaptive_accepted = (receipt.disposition == "SEND_CANDIDATE"
                            and receipt.payload.get("decision_present") is True
                            and {"M01", "M02", "M03", "M04", "M05", "M06", "M07"}.issubset(receipt.executed_components)
                            and "PROPOSAL_NOT_EXECUTION" in receipt.restrictions)
                accepted = foundation_accepted or adaptive_accepted
                next_state = "BLOCK3_GOVERNED" if accepted else "RETURN_UPSTREAM"
            event_type = receipt.producer + ("_RUNTIME_EXECUTED" if accepted else "_RUNTIME_RETURNED")
            db.execute("UPDATE cases SET state=?,updated_at=? WHERE case_id=?", (next_state, current.isoformat(), receipt.case_id))
            self._append(db, case_id=receipt.case_id, event_type=event_type, state=next_state,
                         payload={"execution_receipt": material, "source_hash": package["source_hash"]}, now=current)
            db.commit()
        return self.get_case(receipt.case_id)

    def stop_for_human_review(self, case_id: str, *, now: datetime | None = None) -> FederatedCase:
        """Enter the human gate only after a verified Block 3 runtime receipt."""
        current = _now(now)
        receipts = self.execution_receipts(case_id)
        if not receipts or receipts[-1].producer != "BLOCK3":
            raise FederatedContractError("BLOCK3_EXECUTION_RECEIPT_MISSING")
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            self._verify_chain(db)
            row = db.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
            if row is None:
                raise FederatedContractError("CASE_NOT_FOUND")
            if row["state"] == "HUMAN_REVIEW_REQUIRED":
                db.rollback()
                return self._snapshot_row(row)
            if row["state"] != "BLOCK3_GOVERNED":
                raise FederatedContractError("HUMAN_GATE_TRANSITION_INVALID")
            package = json.loads(row["package_json"])
            if _iso(package["expires_at"]) <= current:
                next_state, event_type = "RETURN_UPSTREAM", "EXPIRED_BEFORE_HUMAN_GATE"
            else:
                next_state, event_type = "HUMAN_REVIEW_REQUIRED", "HUMAN_GATE_REACHED"
            db.execute("UPDATE cases SET state=?,updated_at=? WHERE case_id=?",
                       (next_state, current.isoformat(), case_id))
            self._append(db, case_id=case_id, event_type=event_type, state=next_state,
                         payload={"source_hash": package["source_hash"],
                                  "block3_receipt_fingerprint": receipts[-1].fingerprint}, now=current)
            db.commit()
        return self.get_case(case_id)

    def invalidate(self, case_id: str, reason: str, *, now: datetime | None = None) -> FederatedCase:
        if not isinstance(reason, str) or not reason.strip(): raise FederatedContractError("INVALIDATION_REASON_REQUIRED")
        current = _now(now)
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            self._verify_chain(db)
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
            self._verify_chain(db)
            row = db.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
            if row is None: raise FederatedContractError("CASE_NOT_FOUND")
            if row["retry_count"] >= 3: raise FederatedContractError("RETRY_LIMIT_EXHAUSTED")
            if row["state"] not in {"RETURN_UPSTREAM", "REJECTED"}: raise FederatedContractError("RETRY_STATE_INVALID")
            next_count = row["retry_count"] + 1
            package = json.loads(row["package_json"])
            invalidated = db.execute("SELECT 1 FROM events WHERE case_id=? AND event_type='INVALIDATED'", (case_id,)).fetchone()
            admissible = (not invalidated and package["currentness"] == "CURRENT"
                          and _iso(package["expires_at"]) > current
                          and package["certainty"] not in {"CONTRADICTED", "INSUFFICIENT EVIDENCE"})
            next_state = "BLOCK1_ATTESTED" if admissible else "RETURN_UPSTREAM"
            db.execute("UPDATE cases SET retry_count=?,state=?,updated_at=? WHERE case_id=?", (next_count, next_state, current.isoformat(), case_id))
            self._append(db, case_id=case_id, event_type="RETRY", state=next_state, payload={"retry_count": next_count}, now=current)
            db.commit()
        return self.process_to_human_gate(case_id, now=current)

    def audit_events(self, case_id: str) -> tuple[dict[str, Any], ...]:
        with closing(self._connect()) as db:
            db.execute("BEGIN")
            self._verify_chain(db)
            rows = db.execute("SELECT event_type,state,created_at,payload_json FROM events WHERE case_id=? ORDER BY sequence", (case_id,)).fetchall()
        return tuple({"event_type": row["event_type"], "state": row["state"], "created_at": row["created_at"], "payload": json.loads(row["payload_json"])} for row in rows)
