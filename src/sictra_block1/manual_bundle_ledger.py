"""Atomic, tamper-detecting local records for un-attested manual bundles."""

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
from urllib.parse import urlsplit
from uuid import uuid4

from .common import ContractViolation


_VERSION = 1
_MAX_BUNDLES = 100
_BUNDLE_FIELDS = frozenset((
    "source_id", "source_url", "content", "observed_at", "claim_key", "polarity", "correlation_id",
))
_ENTRY_FIELDS = frozenset((
    "entry_id", "recorded_at", "bundle_sha256", "previous_hash", "record_hash", "bundle",
))


class ManualBundleLedgerViolation(ContractViolation):
    """The local un-attested bundle ledger is malformed, altered, or unsafe."""


def _encoded(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _nonempty_text(name: str, value: object, maximum: int = 512) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ManualBundleLedgerViolation(f"{name} is invalid")
    return value


def _valid_bundle(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping) or frozenset(value) != _BUNDLE_FIELDS:
        raise ManualBundleLedgerViolation("bundle fields do not match the gateway contract")
    bundle = dict(value)
    if bundle["source_id"] != "eurostat":
        raise ManualBundleLedgerViolation("bundle source is unsupported")
    for name in ("source_url", "content", "correlation_id"):
        _nonempty_text(name, bundle[name], 131_072 if name == "content" else 512)
    if len(bundle["content"].encode("utf-8")) > 131_072:
        raise ManualBundleLedgerViolation("bundle content exceeds the governed byte limit")
    try:
        parsed_url = urlsplit(bundle["source_url"])
        port = parsed_url.port
    except ValueError as error:
        raise ManualBundleLedgerViolation("bundle source URL is invalid") from error
    if (
        parsed_url.scheme.lower() != "https" or parsed_url.hostname != "ec.europa.eu"
        or parsed_url.username or parsed_url.password or port is not None
        or parsed_url.fragment or "tran_r_mago_nm" not in parsed_url.path.lower()
    ):
        raise ManualBundleLedgerViolation("bundle source URL is outside the bounded asset")
    if (
        not isinstance(bundle["observed_at"], int) or isinstance(bundle["observed_at"], bool)
        or bundle["observed_at"] < 0 or bundle["claim_key"] != "maritime_freight_weight_thousand_tonnes"
        or bundle["polarity"] != 1 or isinstance(bundle["polarity"], bool)
    ):
        raise ManualBundleLedgerViolation("bundle gateway fields are invalid")
    try:
        content = json.loads(bundle["content"])
    except (TypeError, ValueError) as error:
        raise ManualBundleLedgerViolation("bundle content is not JSON") from error
    expected_content = {
        "schema_version", "content_type", "bundle_state", "provenance", "filters", "selection", "observations",
    }
    if (
        not isinstance(content, Mapping) or set(content) != expected_content
        or _encoded(content) != bundle["content"]
        or content["schema_version"] != "0.1.0"
        or content["content_type"] != "application/vnd.sictra.eurostat-maritime-selection+json"
        or content["bundle_state"] != "UNATTESTED_MANUAL_BUNDLE"
        or not isinstance(content["provenance"], Mapping)
        or content["provenance"].get("mapping_status") != "MAPPED_NOT_EVIDENCE"
        or content["provenance"].get("mapping_evidence_state") != "NOT_EVIDENCE"
        or not isinstance(content["selection"], Mapping)
        or content["selection"].get("selection_status") != "SELECTED_NOT_EVIDENCE"
        or content["selection"].get("selection_evidence_state") != "NOT_EVIDENCE"
        or not isinstance(content["observations"], list)
    ):
        raise ManualBundleLedgerViolation("bundle content is not an un-attested mapper selection")
    return deepcopy(bundle)


class ManualBundleLedger:
    """Bounded, local, HMAC-chained storage; no source admission authority."""

    def __init__(
        self, path: str | Path, *, integrity_key: bytes, clock: Callable[[], int],
        id_factory: Callable[[], str] | None = None, max_bundles: int = _MAX_BUNDLES,
    ) -> None:
        self.path = Path(path)
        if not self.path.name or not isinstance(integrity_key, bytes) or len(integrity_key) < 32:
            raise ManualBundleLedgerViolation("ledger path and 32-byte integrity key are required")
        if not isinstance(max_bundles, int) or isinstance(max_bundles, bool) or not 1 <= max_bundles <= _MAX_BUNDLES:
            raise ManualBundleLedgerViolation("ledger capacity is invalid")
        self._key, self._clock, self._capacity = bytes(integrity_key), clock, max_bundles
        self._id_factory = id_factory or (lambda: f"bundle-{uuid4().hex}")
        self._lock = Lock()

    def _mac(self, material: str) -> str:
        return hmac.new(self._key, material.encode("utf-8"), sha256).hexdigest()

    def _key_check(self) -> str:
        return self._mac(f"manual-bundle-ledger-v{_VERSION}:{self._capacity}")

    def _record_hash(self, entry: Mapping[str, Any]) -> str:
        material = {name: entry[name] for name in _ENTRY_FIELDS - {"record_hash"}}
        return self._mac("manual-bundle-record-v1:" + _encoded(material))

    def _receipt(self, entry: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "scope": "BLOCK1_LOCAL_UNATTESTED_BUNDLE_LEDGER",
            "entry_id": entry["entry_id"],
            "recorded_at": entry["recorded_at"],
            "bundle_sha256": entry["bundle_sha256"],
            "previous_hash": entry["previous_hash"],
            "record_hash": entry["record_hash"],
            "status": "RECORDED_UNATTESTED_NOT_EVIDENCE",
            "evidence_state": "NOT_EVIDENCE",
        }

    def _load_unlocked(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ManualBundleLedgerViolation("ledger cannot be read") from error
        if (
            not isinstance(document, Mapping) or set(document) != {"version", "capacity", "key_check", "entries"}
            or document["version"] != _VERSION or document["capacity"] != self._capacity
            or not isinstance(document["key_check"], str)
            or not hmac.compare_digest(document["key_check"], self._key_check())
            or not isinstance(document["entries"], list) or len(document["entries"]) > self._capacity
        ):
            raise ManualBundleLedgerViolation("ledger schema or key configuration is invalid")
        previous_hash = "GENESIS"
        previous_time = -1
        records: list[dict[str, Any]] = []
        for entry in document["entries"]:
            if not isinstance(entry, Mapping) or frozenset(entry) != _ENTRY_FIELDS:
                raise ManualBundleLedgerViolation("ledger entry shape is invalid")
            _nonempty_text("entry_id", entry["entry_id"], 100)
            if not isinstance(entry["recorded_at"], int) or isinstance(entry["recorded_at"], bool) or entry["recorded_at"] < 0:
                raise ManualBundleLedgerViolation("ledger record time is invalid")
            if entry["recorded_at"] < previous_time:
                raise ManualBundleLedgerViolation("ledger logical time regressed")
            bundle = _valid_bundle(entry["bundle"])
            bundle_sha = sha256(_encoded(bundle).encode("utf-8")).hexdigest()
            if (
                entry["bundle_sha256"] != bundle_sha or entry["previous_hash"] != previous_hash
                or not isinstance(entry["record_hash"], str)
                or not hmac.compare_digest(entry["record_hash"], self._record_hash(entry))
            ):
                raise ManualBundleLedgerViolation("ledger integrity verification failed")
            records.append(dict(entry))
            previous_hash = entry["record_hash"]
            previous_time = entry["recorded_at"]
        if len({entry["entry_id"] for entry in records}) != len(records):
            raise ManualBundleLedgerViolation("ledger contains duplicate entry identities")
        return records

    def _save_unlocked(self, entries: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_name: str | None = None
        try:
            with NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent, delete=False) as temporary:
                temporary_name = temporary.name
                json.dump(
                    {"version": _VERSION, "capacity": self._capacity, "key_check": self._key_check(), "entries": entries},
                    temporary, ensure_ascii=False, separators=(",", ":"), sort_keys=True,
                )
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_name, self.path)
        except OSError as error:
            if temporary_name:
                Path(temporary_name).unlink(missing_ok=True)
            raise ManualBundleLedgerViolation("ledger cannot be written") from error

    def list_receipts(self) -> list[dict[str, Any]]:
        with self._lock:
            return [self._receipt(entry) for entry in self._load_unlocked()]

    def record(self, bundle: Mapping[str, Any]) -> dict[str, Any]:
        normalized = _valid_bundle(bundle)
        fingerprint = sha256(_encoded(normalized).encode("utf-8")).hexdigest()
        with self._lock:
            entries = self._load_unlocked()
            for entry in entries:
                if entry["bundle_sha256"] == fingerprint:
                    return self._receipt(entry)
            if len(entries) >= self._capacity:
                raise ManualBundleLedgerViolation("ledger capacity exhausted")
            entry_id = self._id_factory()
            _nonempty_text("entry_id", entry_id, 100)
            if any(entry["entry_id"] == entry_id for entry in entries):
                raise ManualBundleLedgerViolation("ledger entry identity collision")
            recorded_at = self._clock()
            if not isinstance(recorded_at, int) or isinstance(recorded_at, bool) or recorded_at < 0:
                raise ManualBundleLedgerViolation("ledger clock is invalid")
            if entries and recorded_at < entries[-1]["recorded_at"]:
                raise ManualBundleLedgerViolation("ledger logical time regressed")
            entry = {
                "entry_id": entry_id,
                "recorded_at": recorded_at,
                "bundle_sha256": fingerprint,
                "previous_hash": "GENESIS" if not entries else entries[-1]["record_hash"],
                "record_hash": "",
                "bundle": normalized,
            }
            entry["record_hash"] = self._record_hash(entry)
            entries.append(entry)
            self._save_unlocked(entries)
            return self._receipt(entry)
