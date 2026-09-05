"""Durable public source-control artifacts with external verification keys."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock
from typing import Any, Callable, Mapping

from .common import ContractViolation
from .evidence import EvidenceIssuer
from .source_gateway import (
    MAX_REGISTERED_SOURCES,
    SourceApprovalRecord,
    SourceGateway,
    SourceRegistration,
    source_approval_fingerprint,
    validate_source_binding,
)


_VERSION = 1
_RECORD_FIELDS = frozenset((
    "binding_id", "stored_at", "previous_hash", "record_hash",
    "registration", "approval", "binding",
))
_REGISTRATION_FIELDS = frozenset((
    "source_id", "publisher", "scope", "allowed_hosts", "claim_keys",
    "access_method", "max_content_bytes", "status",
))
_APPROVAL_FIELDS = frozenset((
    "source_id", "reviewer_id", "reviewed_at", "terms_evidence_ref",
    "allowed_hosts", "claim_keys", "access_method", "max_content_bytes", "decision",
))


class SourceControlStoreViolation(ContractViolation):
    """Durable source authority artifacts are malformed or unavailable."""


def _encoded(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _registration_dict(value: SourceRegistration) -> dict[str, Any]:
    return {
        "source_id": value.source_id, "publisher": value.publisher,
        "scope": value.scope, "allowed_hosts": list(value.allowed_hosts),
        "claim_keys": sorted(value.claim_keys), "access_method": value.access_method,
        "max_content_bytes": value.max_content_bytes, "status": value.status,
    }


def _approval_dict(value: SourceApprovalRecord) -> dict[str, Any]:
    return {
        "source_id": value.source_id, "reviewer_id": value.reviewer_id,
        "reviewed_at": value.reviewed_at, "terms_evidence_ref": value.terms_evidence_ref,
        "allowed_hosts": list(value.allowed_hosts), "claim_keys": sorted(value.claim_keys),
        "access_method": value.access_method, "max_content_bytes": value.max_content_bytes,
        "decision": value.decision,
    }


def _registration(value: object) -> SourceRegistration:
    if not isinstance(value, Mapping) or frozenset(value) != _REGISTRATION_FIELDS:
        raise SourceControlStoreViolation("stored source registration shape is invalid")
    try:
        return SourceRegistration(
            value["source_id"], value["publisher"], value["scope"],
            tuple(value["allowed_hosts"]), frozenset(value["claim_keys"]),
            value["access_method"], value["max_content_bytes"], value["status"],
        )
    except (ContractViolation, TypeError, ValueError) as error:
        raise SourceControlStoreViolation("stored source registration is invalid") from error


def _approval(value: object) -> SourceApprovalRecord:
    if not isinstance(value, Mapping) or frozenset(value) != _APPROVAL_FIELDS:
        raise SourceControlStoreViolation("stored source approval shape is invalid")
    try:
        return SourceApprovalRecord(
            value["source_id"], value["reviewer_id"], value["reviewed_at"],
            value["terms_evidence_ref"], tuple(value["allowed_hosts"]),
            frozenset(value["claim_keys"]), value["access_method"],
            value["max_content_bytes"], value["decision"],
        )
    except (ContractViolation, TypeError, ValueError) as error:
        raise SourceControlStoreViolation("stored source approval is invalid") from error


def _matching_approval(registration: SourceRegistration, approval: SourceApprovalRecord) -> bool:
    return (
        registration.status == "BOUND" and approval.decision == "APPROVED"
        and approval.source_id == registration.source_id
        and approval.allowed_hosts == registration.allowed_hosts
        and approval.claim_keys == registration.claim_keys
        and approval.access_method == registration.access_method
        and approval.max_content_bytes == registration.max_content_bytes
    )


class SourceControlStore:
    """Append-only local source authority history; secret material stays external."""

    def __init__(
        self, path: str | Path, *, binding_keys: Mapping[str, bytes],
        integrity_key: bytes, clock: Callable[[], int],
        max_records: int = MAX_REGISTERED_SOURCES,
    ) -> None:
        self.path = Path(path)
        try:
            keys = {issuer: bytes(key) for issuer, key in binding_keys.items()}
        except (AttributeError, TypeError, ValueError) as error:
            raise SourceControlStoreViolation("binding key configuration is invalid") from error
        if (
            not self.path.name or not keys or any(not issuer or len(key) < 32 for issuer, key in keys.items())
            or not isinstance(integrity_key, bytes) or len(integrity_key) < 32
            or not isinstance(max_records, int) or isinstance(max_records, bool)
            or not 1 <= max_records <= MAX_REGISTERED_SOURCES
        ):
            raise SourceControlStoreViolation("source control configuration is invalid")
        self._binding_keys = keys
        self._integrity_key = bytes(integrity_key)
        self._clock = clock
        self._capacity = max_records
        self._lock = Lock()
        self.failure_injector: Callable[[str], None] | None = None

    def _mac(self, material: str) -> str:
        return hmac.new(self._integrity_key, material.encode("utf-8"), sha256).hexdigest()

    def _key_check(self) -> str:
        return self._mac(f"source-control-store-v{_VERSION}:{self._capacity}")

    def _binding_id(self, binding: Mapping[str, Any]) -> str:
        return f"{binding['source_id']}:{sha256(_encoded(binding).encode('utf-8')).hexdigest()}"

    def _record_hash(self, record: Mapping[str, Any]) -> str:
        material = {field: record[field] for field in _RECORD_FIELDS - {"record_hash"}}
        return self._mac("source-control-record-v1:" + _encoded(material))

    def _validate_artifacts(
        self, registration: SourceRegistration, approval: SourceApprovalRecord,
        binding: Mapping[str, Any], *, now: int, require_current: bool,
    ) -> dict[str, Any]:
        if not isinstance(registration, SourceRegistration) or not isinstance(approval, SourceApprovalRecord):
            raise SourceControlStoreViolation("source control artifacts have invalid types")
        if not _matching_approval(registration, approval):
            raise SourceControlStoreViolation("approval does not match bound registration")
        try:
            token = validate_source_binding(
                registration, binding, self._binding_keys,
                now=now, require_current=require_current,
            )
        except ContractViolation as error:
            raise SourceControlStoreViolation("signed source binding is invalid") from error
        if token["approval_fingerprint"] != source_approval_fingerprint(approval):
            raise SourceControlStoreViolation("binding approval lineage does not match")
        return token

    def _load_unlocked(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise SourceControlStoreViolation("source control store cannot be read") from error
        if (
            not isinstance(document, Mapping)
            or set(document) != {"version", "capacity", "key_check", "records"}
            or document["version"] != _VERSION or document["capacity"] != self._capacity
            or not isinstance(document["key_check"], str)
            or not hmac.compare_digest(document["key_check"], self._key_check())
            or not isinstance(document["records"], list)
            or len(document["records"]) > self._capacity
        ):
            raise SourceControlStoreViolation("source control schema or key configuration is invalid")
        verified = []
        previous_hash = "GENESIS"
        previous_time = -1
        latest_issued: dict[str, int] = {}
        identities: set[str] = set()
        for record in document["records"]:
            if not isinstance(record, Mapping) or frozenset(record) != _RECORD_FIELDS:
                raise SourceControlStoreViolation("source control record shape is invalid")
            registration = _registration(record["registration"])
            approval = _approval(record["approval"])
            stored_at = record["stored_at"]
            if not isinstance(stored_at, int) or isinstance(stored_at, bool) or stored_at < 0:
                raise SourceControlStoreViolation("source control record time is invalid")
            binding = self._validate_artifacts(
                registration, approval, record["binding"],
                now=stored_at, require_current=True,
            )
            binding_id = self._binding_id(binding)
            if (
                record["registration"] != _registration_dict(registration)
                or record["approval"] != _approval_dict(approval)
                or record["binding"] != binding or record["binding_id"] != binding_id
                or binding_id in identities or stored_at < previous_time
                or binding["issued_at"] <= latest_issued.get(registration.source_id, -1)
                or record["previous_hash"] != previous_hash
                or not isinstance(record["record_hash"], str)
                or not hmac.compare_digest(record["record_hash"], self._record_hash(record))
            ):
                raise SourceControlStoreViolation("source control history integrity failed")
            verified.append(dict(record))
            identities.add(binding_id)
            latest_issued[registration.source_id] = binding["issued_at"]
            previous_hash = record["record_hash"]
            previous_time = stored_at
        return verified

    def _save_unlocked(self, records: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_name: str | None = None
        try:
            with NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent, delete=False) as temporary:
                temporary_name = temporary.name
                json.dump(
                    {"version": _VERSION, "capacity": self._capacity, "key_check": self._key_check(), "records": records},
                    temporary, ensure_ascii=False, separators=(",", ":"), sort_keys=True,
                )
                temporary.flush()
                os.fsync(temporary.fileno())
            if self.failure_injector:
                self.failure_injector("BEFORE_ATOMIC_REPLACE")
            os.replace(temporary_name, self.path)
        except OSError as error:
            if temporary_name:
                Path(temporary_name).unlink(missing_ok=True)
            raise SourceControlStoreViolation("source control store cannot be written") from error

    @staticmethod
    def _receipt(record: Mapping[str, Any], *, now: int, replay: bool = False) -> dict[str, Any]:
        binding = record["binding"]
        return {
            "scope": "BLOCK1_LOCAL_SOURCE_CONTROL_STORE",
            "binding_id": record["binding_id"],
            "source_id": binding["source_id"],
            "approval_fingerprint": binding["approval_fingerprint"],
            "issued_at": binding["issued_at"],
            "expires_at": binding["expires_at"],
            "stored_at": record["stored_at"],
            "record_hash": record["record_hash"],
            "status": "ACTIVE" if binding["issued_at"] <= now <= binding["expires_at"] else "NOT_CURRENT",
            "replay": replay,
            "evidence_state": "NOT_EVIDENCE",
        }

    def persist(
        self, registration: SourceRegistration, approval: SourceApprovalRecord,
        binding: Mapping[str, Any],
    ) -> dict[str, Any]:
        now = self._clock()
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise SourceControlStoreViolation("source control clock is invalid")
        token = self._validate_artifacts(
            registration, approval, binding, now=now, require_current=True,
        )
        binding_id = self._binding_id(token)
        with self._lock:
            records = self._load_unlocked()
            for record in records:
                if record["binding_id"] == binding_id:
                    return self._receipt(record, now=now, replay=True)
            if len(records) >= self._capacity:
                raise SourceControlStoreViolation("source control capacity exhausted")
            prior_for_source = [
                record for record in records
                if record["registration"]["source_id"] == registration.source_id
            ]
            if prior_for_source and token["issued_at"] <= prior_for_source[-1]["binding"]["issued_at"]:
                raise SourceControlStoreViolation("source binding rotation is not monotonic")
            if records and now < records[-1]["stored_at"]:
                raise SourceControlStoreViolation("source control logical time regressed")
            record = {
                "binding_id": binding_id,
                "stored_at": now,
                "previous_hash": "GENESIS" if not records else records[-1]["record_hash"],
                "record_hash": "",
                "registration": _registration_dict(registration),
                "approval": _approval_dict(approval),
                "binding": token,
            }
            record["record_hash"] = self._record_hash(record)
            records.append(record)
            self._save_unlocked(records)
            return self._receipt(record, now=now)

    def list_records(self, *, now: int) -> list[dict[str, Any]]:
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise SourceControlStoreViolation("source control read time is invalid")
        with self._lock:
            return [self._receipt(record, now=now) for record in self._load_unlocked()]

    def active_record(self, source_id: str, *, now: int) -> dict[str, Any] | None:
        if not isinstance(source_id, str) or not source_id.strip() or not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise SourceControlStoreViolation("active source lookup is invalid")
        with self._lock:
            matches = [
                record for record in self._load_unlocked()
                if record["registration"]["source_id"] == source_id
                and record["binding"]["issued_at"] <= now <= record["binding"]["expires_at"]
            ]
            return None if not matches else deepcopy(matches[-1])

    def build_gateway(
        self, source_id: str, *, evidence_issuer: EvidenceIssuer, now: int,
    ) -> SourceGateway:
        record = self.active_record(source_id, now=now)
        if record is None:
            raise SourceControlStoreViolation("source has no active durable binding")
        registration = _registration(record["registration"])
        approval = _approval(record["approval"])
        self._validate_artifacts(
            registration, approval, record["binding"], now=now, require_current=True,
        )
        return SourceGateway(
            registrations=(registration,), issuer=evidence_issuer,
            binding_keys=self._binding_keys,
            bindings={source_id: record["binding"]}, now=now,
        )
