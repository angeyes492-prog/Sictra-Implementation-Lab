"""Deterministic, durable intelligence dossiers from attested watchlist deltas."""

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


_VERSION = 1
_MAX_DOSSIERS = 100
_SHA = re.compile(r"[0-9a-f]{64}$")
_INPUT_FIELDS = frozenset((
    "scope", "source_id", "observed_at", "content_sha256",
    "source_approval_fingerprint", "source_binding_fingerprint",
    "watchlist_receipt", "delta", "next_state", "evidence_state",
))
_RECORD_FIELDS = frozenset((
    "dossier_id", "recorded_at", "previous_hash", "record_hash", "input", "dossier",
))
_RECEIPT_FIELDS = frozenset((
    "scope", "cycle_id", "recorded_at", "bundle_sha256", "delta_sha256",
    "record_hash", "status", "change_count", "evidence_state", "replay",
))
_DELTA_FIELDS = frozenset((
    "scope", "source_id", "dataset_code", "selected_geo_level", "previous",
    "current", "change_count", "changes", "status", "evidence_state", "next_state",
))
_CHANGE_FIELDS = frozenset((
    "geo_code", "geo_label", "time_period", "change_type",
    "before_value_thousand_tonnes", "after_value_thousand_tonnes",
    "absolute_delta_thousand_tonnes", "before_status_flag", "after_status_flag",
))


class IntelligenceDossierViolation(ContractViolation):
    """A review dossier or its durable history violates the bounded contract."""


def _encoded(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _fingerprint(value: object) -> str:
    return sha256(_encoded(value).encode("utf-8")).hexdigest()


def _validated_input(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping) or frozenset(value) != _INPUT_FIELDS:
        raise IntelligenceDossierViolation("attested watchlist result shape is invalid")
    item = deepcopy(dict(value))
    receipt, delta = item["watchlist_receipt"], item["delta"]
    if (not isinstance(receipt, Mapping) or frozenset(receipt) != _RECEIPT_FIELDS
            or not isinstance(delta, Mapping) or frozenset(delta) != _DELTA_FIELDS):
        raise IntelligenceDossierViolation("watchlist receipt and delta are required")
    hashes = (
        item["content_sha256"], item["source_approval_fingerprint"],
        item["source_binding_fingerprint"], receipt.get("delta_sha256"),
    )
    changes = delta.get("changes")
    if (
        item["scope"] != "BLOCK1_LOCAL_ATTESTED_WATCHLIST_BRIDGE"
        or item["source_id"] != "eurostat"
        or not isinstance(item["observed_at"], int) or isinstance(item["observed_at"], bool)
        or item["observed_at"] < 0
        or any(not isinstance(value, str) or _SHA.fullmatch(value) is None for value in hashes)
        or item["evidence_state"] != "ATTESTED_INPUT_DELTA_NOT_EVIDENCE"
        or item["next_state"] != "REQUIRES_REVIEW"
        or delta.get("source_id") != item["source_id"]
        or delta.get("scope") != "BLOCK1_EUROSTAT_MARITIME_MANUAL_WATCHLIST"
        or delta.get("dataset_code") != "tran_r_mago_nm"
        or delta.get("selected_geo_level") not in {"COUNTRY", "NUTS1", "NUTS2"}
        or delta.get("status") != "DELTA_DETECTED_NOT_EVIDENCE"
        or delta.get("evidence_state") != "NOT_EVIDENCE"
        or delta.get("next_state") != "REQUIRES_SOURCE_ATTESTATION_AND_REVIEW"
        or receipt.get("status") != delta.get("status")
        or receipt.get("scope") != "BLOCK1_LOCAL_MANUAL_WATCHLIST_CYCLE"
        or receipt.get("evidence_state") != "NOT_EVIDENCE"
        or not isinstance(receipt.get("replay"), bool)
        or not isinstance(receipt.get("recorded_at"), int) or isinstance(receipt.get("recorded_at"), bool)
        or not isinstance(receipt.get("cycle_id"), str) or not receipt["cycle_id"].strip()
        or any(_SHA.fullmatch(receipt.get(name, "")) is None for name in ("bundle_sha256", "record_hash"))
        or receipt.get("change_count") != delta.get("change_count")
        or receipt.get("delta_sha256") != _fingerprint(delta)
        or not isinstance(changes, list) or not changes
        or delta.get("change_count") != len(changes)
    ):
        raise IntelligenceDossierViolation("watchlist result is not a linked reviewable delta")
    identities = set()
    for change in changes:
        if not isinstance(change, Mapping) or frozenset(change) != _CHANGE_FIELDS:
            raise IntelligenceDossierViolation("delta change is invalid")
        identity = (change.get("geo_code"), change.get("time_period"))
        if (
            not all(isinstance(change.get(key), str) and change[key].strip()
                    for key in ("geo_code", "geo_label", "change_type"))
            or not isinstance(change.get("time_period"), int) or isinstance(change.get("time_period"), bool)
            or not 1900 <= change["time_period"] <= 2200
            or change["change_type"] not in {"ADDED_OBSERVATION", "REMOVED_OBSERVATION", "VALUE_CHANGED", "FLAG_CHANGED"}
            or any(value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool))
                   for value in (change["before_value_thousand_tonnes"], change["after_value_thousand_tonnes"], change["absolute_delta_thousand_tonnes"]))
            or any(value is not None and not isinstance(value, str)
                   for value in (change["before_status_flag"], change["after_status_flag"]))
            or identity in identities
        ):
            raise IntelligenceDossierViolation("delta change identity is invalid or duplicated")
        identities.add(identity)
    return item


def build_intelligence_dossier(value: object) -> dict[str, Any]:
    """Extract literal facts while deliberately abstaining from interpretation."""

    item = _validated_input(value)
    delta, receipt = item["delta"], item["watchlist_receipt"]
    facts = []
    for index, change in enumerate(delta["changes"], start=1):
        facts.append({
            "fact_id": f"FACT-{index:03d}",
            "statement": (
                f"Eurostat records {change['change_type']} for {change['geo_label']} "
                f"({change['geo_code']}) in {change['time_period']}."
            ),
            "observed_change": deepcopy(change),
            "evidence_refs": {
                "source_id": item["source_id"],
                "content_sha256": item["content_sha256"],
                "delta_sha256": receipt["delta_sha256"],
                "approval_fingerprint": item["source_approval_fingerprint"],
                "binding_fingerprint": item["source_binding_fingerprint"],
            },
            "certainty": "VERIFIED",
            "confidence": "B",
        })
    delta_id = receipt["delta_sha256"]
    return {
        "schema_version": "0.1.0",
        "scope": "BLOCK1_LOCAL_INTELLIGENCE_DOSSIER",
        "dossier_id": f"eurostat:{delta_id}",
        "source": {
            "source_id": item["source_id"], "observed_at": item["observed_at"],
            "content_sha256": item["content_sha256"], "delta_sha256": delta_id,
            "approval_fingerprint": item["source_approval_fingerprint"],
            "binding_fingerprint": item["source_binding_fingerprint"],
        },
        "facts": facts,
        "interpretations": [],
        "hypotheses": [],
        "uncertainties": [
            "No independent source corroboration is attached.",
            "The delta may reflect operational change, statistical revision, or coverage change.",
            "No causal or company-specific implication has been established.",
        ],
        "contradictions": [],
        "limitations": [
            "One bounded Eurostat maritime dataset and selected geography level only.",
            "Technical change detection is not validation of real-world causality.",
        ],
        "affected_scope": {
            "geo_codes": sorted({change["geo_code"] for change in delta["changes"]}),
            "geo_labels": sorted({change["geo_label"] for change in delta["changes"]}),
            "time_periods": sorted({change["time_period"] for change in delta["changes"]}),
        },
        "executive_questions": [
            "Does this change reflect operations, a statistical revision, or changed coverage?",
            "What independent evidence is required before applying this change to a business decision?",
        ],
        "next_data_needs": [
            "Independent corroborating source for the same geography and period.",
            "Source metadata explaining revisions and coverage changes.",
            "Company-specific exposure data before estimating impact.",
        ],
        "certainty": "UNCONFIRMED",
        "confidence": "C",
        "review_state": "REQUIRES_HUMAN_INTERPRETATION",
        "publication_state": "BLOCKED",
    }


class IntelligenceDossierStore:
    def __init__(self, path: str | Path, *, integrity_key: bytes,
                 clock: Callable[[], int], max_dossiers: int = _MAX_DOSSIERS) -> None:
        self.path = Path(path)
        if (not self.path.name or not isinstance(integrity_key, bytes) or len(integrity_key) < 32
                or not isinstance(max_dossiers, int) or isinstance(max_dossiers, bool)
                or not 1 <= max_dossiers <= _MAX_DOSSIERS):
            raise IntelligenceDossierViolation("dossier store configuration is invalid")
        self._key, self._clock, self._capacity = bytes(integrity_key), clock, max_dossiers
        self._lock = Lock()
        self.failure_injector: Callable[[str], None] | None = None

    def _mac(self, value: str) -> str:
        return hmac.new(self._key, value.encode("utf-8"), sha256).hexdigest()

    def _config(self) -> str:
        return self._mac(f"intelligence-dossier-v{_VERSION}:{self._capacity}")

    def _record_hash(self, record: Mapping[str, Any]) -> str:
        return self._mac("dossier-record-v1:" + _encoded({
            key: record[key] for key in _RECORD_FIELDS - {"record_hash"}
        }))

    def _load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise IntelligenceDossierViolation("dossier store cannot be read") from error
        if (not isinstance(document, Mapping) or set(document) != {"version", "capacity", "config", "records"}
                or document["version"] != _VERSION or document["capacity"] != self._capacity
                or not isinstance(document["config"], str)
                or not hmac.compare_digest(document["config"], self._config())
                or not isinstance(document["records"], list) or len(document["records"]) > self._capacity):
            raise IntelligenceDossierViolation("dossier store schema or configuration is invalid")
        verified, previous_hash, previous_time, identities = [], "GENESIS", -1, set()
        for record in document["records"]:
            if not isinstance(record, Mapping) or frozenset(record) != _RECORD_FIELDS:
                raise IntelligenceDossierViolation("dossier record shape is invalid")
            dossier = build_intelligence_dossier(record["input"])
            if (record["dossier"] != dossier or record["dossier_id"] != dossier["dossier_id"]
                    or record["dossier_id"] in identities
                    or not isinstance(record["recorded_at"], int) or isinstance(record["recorded_at"], bool)
                    or record["recorded_at"] < 0 or record["recorded_at"] < previous_time
                    or record["previous_hash"] != previous_hash
                    or not isinstance(record["record_hash"], str)
                    or not hmac.compare_digest(record["record_hash"], self._record_hash(record))):
                raise IntelligenceDossierViolation("dossier history integrity failed")
            verified.append(dict(record)); identities.add(record["dossier_id"])
            previous_hash, previous_time = record["record_hash"], record["recorded_at"]
        return verified

    def _save(self, records: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_name = None
        try:
            with NamedTemporaryFile("w", encoding="utf-8", dir=self.path.parent, delete=False) as temporary:
                temporary_name = temporary.name
                json.dump({"version": _VERSION, "capacity": self._capacity, "config": self._config(), "records": records},
                          temporary, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
                temporary.flush(); os.fsync(temporary.fileno())
            if self.failure_injector:
                self.failure_injector("BEFORE_ATOMIC_REPLACE")
            os.replace(temporary_name, self.path)
        except OSError as error:
            if temporary_name:
                Path(temporary_name).unlink(missing_ok=True)
            raise IntelligenceDossierViolation("dossier store cannot be written") from error

    def persist(self, value: object) -> dict[str, Any]:
        source, dossier = _validated_input(value), build_intelligence_dossier(value)
        now = self._clock()
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise IntelligenceDossierViolation("dossier store clock is invalid")
        with self._lock:
            records = self._load()
            for record in records:
                if record["dossier_id"] == dossier["dossier_id"]:
                    return {"dossier_id": dossier["dossier_id"], "record_hash": record["record_hash"], "replay": True,
                            "review_state": dossier["review_state"], "publication_state": dossier["publication_state"]}
            if len(records) >= self._capacity or (records and now < records[-1]["recorded_at"]):
                raise IntelligenceDossierViolation("dossier capacity exhausted or time regressed")
            record = {"dossier_id": dossier["dossier_id"], "recorded_at": now,
                      "previous_hash": "GENESIS" if not records else records[-1]["record_hash"],
                      "record_hash": "", "input": source, "dossier": dossier}
            record["record_hash"] = self._record_hash(record)
            records.append(record); self._save(records)
            return {"dossier_id": dossier["dossier_id"], "record_hash": record["record_hash"], "replay": False,
                    "review_state": dossier["review_state"], "publication_state": dossier["publication_state"]}

    def list_dossiers(self) -> list[dict[str, Any]]:
        with self._lock:
            return [deepcopy(record["dossier"]) for record in self._load()]
