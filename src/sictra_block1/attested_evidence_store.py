"""Durable local retention for fully verified gateway evidence records."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from threading import Lock
from typing import Any, Callable, Mapping

from .common import ContractViolation
from .evidence import EvidenceVerifier
from .manual_bundle_ledger import (
    ManualBundleLedgerViolation,
    validate_unattested_manual_bundle,
)


_VERSION = 1
_MAX_RECORDS = 1_000
_RECORD_FIELDS = frozenset((
    "evidence_id", "admitted_at", "previous_hash", "record_hash", "evidence",
))
_EVIDENCE_FIELDS = frozenset((
    "source_id", "content", "observed_at", "root_provenance",
    "evidence_class", "scope", "correlation_id", "claim_key", "polarity",
    "source_url", "publisher", "content_sha256", "ingestion_method",
    "source_approval_fingerprint", "source_binding_fingerprint",
    "schema_version", "attestation_issuer", "attestation",
))
_SHA256 = re.compile(r"[0-9a-f]{64}$")


class AttestedEvidenceStoreViolation(ContractViolation):
    """Signed evidence or its durable history is invalid."""


def _encoded(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


class AttestedEvidenceStore:
    """HMAC-chained evidence history with separate current-runtime retrieval."""

    def __init__(
        self, path: str | Path, *, evidence_keys: Mapping[str, bytes],
        evidence_scope: str, evidence_max_age: int,
        evidence_claims: frozenset[str], integrity_key: bytes,
        clock: Callable[[], int], max_records: int = _MAX_RECORDS,
    ) -> None:
        self.path = Path(path)
        try:
            keys = {issuer: bytes(key) for issuer, key in evidence_keys.items()}
        except (AttributeError, TypeError, ValueError) as error:
            raise AttestedEvidenceStoreViolation("evidence key configuration is invalid") from error
        if (
            not self.path.name or not keys or any(not issuer or len(key) < 32 for issuer, key in keys.items())
            or not isinstance(evidence_scope, str) or not evidence_scope.strip()
            or not isinstance(evidence_max_age, int) or isinstance(evidence_max_age, bool)
            or evidence_max_age < 0 or not isinstance(evidence_claims, frozenset)
            or not evidence_claims or any(not isinstance(claim, str) or not claim for claim in evidence_claims)
            or not isinstance(integrity_key, bytes) or len(integrity_key) < 32
            or not isinstance(max_records, int) or isinstance(max_records, bool)
            or not 1 <= max_records <= _MAX_RECORDS
        ):
            raise AttestedEvidenceStoreViolation("evidence store configuration is invalid")
        self._keys = keys
        self._scope = evidence_scope.strip()
        self._max_age = evidence_max_age
        self._claims = evidence_claims
        self._integrity_key = bytes(integrity_key)
        self._clock = clock
        self._capacity = max_records
        self._verifier = EvidenceVerifier(keys, self._scope, self._max_age, self._claims)
        self._lock = Lock()
        self.failure_injector: Callable[[str], None] | None = None

    def _mac(self, material: str) -> str:
        return hmac.new(self._integrity_key, material.encode("utf-8"), sha256).hexdigest()

    def _config_check(self) -> str:
        return self._mac(_encoded({
            "version": _VERSION, "capacity": self._capacity,
            "scope": self._scope, "max_age": self._max_age,
            "claims": sorted(self._claims), "issuers": sorted(self._keys),
        }))

    @staticmethod
    def _evidence_id(evidence: Mapping[str, Any]) -> str:
        return f"{evidence['source_id']}:{sha256(_encoded(evidence).encode('utf-8')).hexdigest()}"

    def _record_hash(self, record: Mapping[str, Any]) -> str:
        material = {field: record[field] for field in _RECORD_FIELDS - {"record_hash"}}
        return self._mac("attested-evidence-record-v1:" + _encoded(material))

    def _validate_evidence(self, value: object, *, now: int) -> dict[str, Any]:
        if not isinstance(value, Mapping) or frozenset(value) != _EVIDENCE_FIELDS:
            raise AttestedEvidenceStoreViolation("gateway evidence shape is invalid")
        evidence = dict(value)
        valid, reason = self._verifier.verify(evidence, now=now)
        if not valid:
            raise AttestedEvidenceStoreViolation(f"gateway evidence rejected: {reason}")
        content = evidence["content"]
        if (
            evidence["root_provenance"] != f"gateway-source:{evidence['source_id']}"
            or evidence["source_id"] != "eurostat"
            or evidence["publisher"] != "Eurostat / European Commission"
            or evidence["ingestion_method"] != "MANUAL_SOURCE_BUNDLE"
            or evidence["content_sha256"] != sha256(content.encode("utf-8")).hexdigest()
            or _SHA256.fullmatch(evidence["source_approval_fingerprint"]) is None
            or _SHA256.fullmatch(evidence["source_binding_fingerprint"]) is None
        ):
            raise AttestedEvidenceStoreViolation("gateway evidence lineage extensions are invalid")
        bundle = {
            "source_id": evidence["source_id"],
            "source_url": evidence["source_url"],
            "content": evidence["content"],
            "observed_at": evidence["observed_at"],
            "claim_key": evidence["claim_key"],
            "polarity": evidence["polarity"],
            "correlation_id": evidence["correlation_id"],
        }
        try:
            validate_unattested_manual_bundle(bundle)
        except ManualBundleLedgerViolation as error:
            raise AttestedEvidenceStoreViolation("attested content is not a valid Eurostat bundle") from error
        return deepcopy(evidence)

    def _load_unlocked(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise AttestedEvidenceStoreViolation("evidence store cannot be read") from error
        if (
            not isinstance(document, Mapping)
            or set(document) != {"version", "capacity", "config_check", "records"}
            or document["version"] != _VERSION or document["capacity"] != self._capacity
            or not isinstance(document["config_check"], str)
            or not hmac.compare_digest(document["config_check"], self._config_check())
            or not isinstance(document["records"], list)
            or len(document["records"]) > self._capacity
        ):
            raise AttestedEvidenceStoreViolation("evidence schema or key configuration is invalid")
        verified = []
        previous_hash = "GENESIS"
        previous_time = -1
        identities: set[str] = set()
        for record in document["records"]:
            if not isinstance(record, Mapping) or frozenset(record) != _RECORD_FIELDS:
                raise AttestedEvidenceStoreViolation("evidence record shape is invalid")
            admitted_at = record["admitted_at"]
            if not isinstance(admitted_at, int) or isinstance(admitted_at, bool) or admitted_at < 0:
                raise AttestedEvidenceStoreViolation("evidence admission time is invalid")
            evidence = self._validate_evidence(record["evidence"], now=admitted_at)
            evidence_id = self._evidence_id(evidence)
            if (
                record["evidence"] != evidence or record["evidence_id"] != evidence_id
                or evidence_id in identities or admitted_at < previous_time
                or record["previous_hash"] != previous_hash
                or not isinstance(record["record_hash"], str)
                or not hmac.compare_digest(record["record_hash"], self._record_hash(record))
            ):
                raise AttestedEvidenceStoreViolation("evidence history integrity failed")
            verified.append(dict(record))
            identities.add(evidence_id)
            previous_hash = record["record_hash"]
            previous_time = admitted_at
        return verified

    def _save_unlocked(self, records: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_name: str | None = None
        try:
            with NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent, delete=False) as temporary:
                temporary_name = temporary.name
                json.dump(
                    {"version": _VERSION, "capacity": self._capacity, "config_check": self._config_check(), "records": records},
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
            raise AttestedEvidenceStoreViolation("evidence store cannot be written") from error

    def _current_ids(self, records: list[dict[str, Any]], *, now: int) -> set[str]:
        """Return one unambiguous newest valid record per source.

        Retention is historical, but a versioned source may contribute only its
        newest observed release to a live run.  Equal observation times with
        different signed content fail closed rather than making an arbitrary
        version current.
        """
        selected: dict[str, tuple[str, str, int, str]] = {}
        ambiguous: set[str] = set()
        for record in records:
            evidence = record["evidence"]
            if not self._verifier.verify(evidence, now=now)[0]:
                continue
            source_id, observed_at, evidence_id = (
                evidence["source_id"], evidence["observed_at"], record["evidence_id"],
            )
            provenance = json.loads(evidence["content"])["provenance"]
            release_time, source_hash = provenance["dataset_last_updated"], provenance["source_file_sha256"]
            prior = selected.get(source_id)
            if prior is None or release_time > prior[0]:
                selected[source_id] = (release_time, source_hash, observed_at, evidence_id)
                ambiguous.discard(source_id)
            elif release_time == prior[0]:
                if source_hash != prior[1]:
                    ambiguous.add(source_id)
                elif observed_at > prior[2]:
                    selected[source_id] = (release_time, source_hash, observed_at, evidence_id)
        return {entry[3] for source_id, entry in selected.items() if source_id not in ambiguous}

    def _receipt(self, record: Mapping[str, Any], *, now: int, replay: bool = False) -> dict[str, Any]:
        valid, reason = self._verifier.verify(record["evidence"], now=now)
        current_ids = self._current_ids(self._load_unlocked(), now=now)
        status = "CURRENT" if record["evidence_id"] in current_ids else "NOT_CURRENT"
        if valid and status != "CURRENT":
            reason = "SOURCE_SUPERSEDED_OR_AMBIGUOUS"
        return {
            "scope": "BLOCK1_LOCAL_ATTESTED_EVIDENCE_STORE",
            "evidence_id": record["evidence_id"],
            "source_id": record["evidence"]["source_id"],
            "admitted_at": record["admitted_at"],
            "observed_at": record["evidence"]["observed_at"],
            "record_hash": record["record_hash"],
            "status": status,
            "verification_reason": reason,
            "replay": replay,
        }

    def persist(self, evidence: Mapping[str, Any]) -> dict[str, Any]:
        now = self._clock()
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise AttestedEvidenceStoreViolation("evidence store clock is invalid")
        normalized = self._validate_evidence(evidence, now=now)
        evidence_id = self._evidence_id(normalized)
        with self._lock:
            records = self._load_unlocked()
            for record in records:
                if record["evidence_id"] == evidence_id:
                    return self._receipt(record, now=now, replay=True)
            if len(records) >= self._capacity:
                raise AttestedEvidenceStoreViolation("evidence store capacity exhausted")
            if records and now < records[-1]["admitted_at"]:
                raise AttestedEvidenceStoreViolation("evidence admission time regressed")
            record = {
                "evidence_id": evidence_id,
                "admitted_at": now,
                "previous_hash": "GENESIS" if not records else records[-1]["record_hash"],
                "record_hash": "",
                "evidence": normalized,
            }
            record["record_hash"] = self._record_hash(record)
            records.append(record)
            self._save_unlocked(records)
            return self._receipt(record, now=now)

    def list_receipts(self, *, now: int) -> list[dict[str, Any]]:
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise AttestedEvidenceStoreViolation("evidence read time is invalid")
        with self._lock:
            return [self._receipt(record, now=now) for record in self._load_unlocked()]

    def runtime_records(self, *, now: int) -> list[dict[str, Any]]:
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise AttestedEvidenceStoreViolation("evidence runtime time is invalid")
        with self._lock:
            records = self._load_unlocked()
            current_ids = self._current_ids(records, now=now)
            return [
                deepcopy(record["evidence"]) for record in records
                if record["evidence_id"] in current_ids
            ]
