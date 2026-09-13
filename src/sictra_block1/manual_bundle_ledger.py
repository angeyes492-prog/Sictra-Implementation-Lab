"""Atomic, tamper-detecting local records for un-attested manual bundles."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import hmac
import json
import math
import os
from pathlib import Path
import re
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
_SHA256 = re.compile(r"[0-9a-f]{64}$")
_CORRELATION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_OBSERVATION_FIELDS = frozenset((
    "geo_code", "geo_label", "geo_level", "time_period",
    "value_thousand_tonnes", "status_flag",
))
_COVERAGE_FIELDS = frozenset((
    "declared_geography_count", "observed_geography_count",
    "all_missing_geography_count", "expected_geo_time_cells",
    "observation_count", "missing_value_count",
))


class ManualBundleLedgerViolation(ContractViolation):
    """The local un-attested bundle ledger is malformed, altered, or unsafe."""


def _encoded(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _nonempty_text(name: str, value: object, maximum: int = 512) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ManualBundleLedgerViolation(f"{name} is invalid")
    return value


def validate_unattested_manual_bundle(value: object) -> dict[str, Any]:
    """Return a defensive copy only when the complete bundle is self-consistent."""

    if not isinstance(value, Mapping) or frozenset(value) != _BUNDLE_FIELDS:
        raise ManualBundleLedgerViolation("bundle fields do not match the gateway contract")
    bundle = dict(value)
    if bundle["source_id"] != "eurostat":
        raise ManualBundleLedgerViolation("bundle source is unsupported")
    for name in ("source_url", "content", "correlation_id"):
        _nonempty_text(name, bundle[name], 131_072 if name == "content" else 512)
    if _CORRELATION.fullmatch(bundle["correlation_id"]) is None:
        raise ManualBundleLedgerViolation("bundle correlation identifier is invalid")
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
    provenance = content["provenance"]
    if (
        set(provenance) != {
            "source_file_sha256", "dataset_code", "dataset_title",
            "dataset_last_updated", "mapping_scope", "mapping_status",
            "mapping_evidence_state",
        }
        or _SHA256.fullmatch(str(provenance.get("source_file_sha256"))) is None
        or provenance.get("dataset_code") != "tran_r_mago_nm"
        or not isinstance(provenance.get("dataset_title"), str)
        or not provenance["dataset_title"].strip()
        or provenance.get("mapping_scope") != "BLOCK1_EUROSTAT_MARITIME_SCHEMA_MAPPING"
    ):
        raise ManualBundleLedgerViolation("bundle provenance is invalid")
    try:
        datetime_value = provenance["dataset_last_updated"]
        if not isinstance(datetime_value, str):
            raise ValueError
        from datetime import datetime
        datetime.fromisoformat(datetime_value)
    except (TypeError, ValueError):
        raise ManualBundleLedgerViolation("bundle source update time is invalid") from None
    if content["filters"] != {
        "frequency": "A", "transport_measure": "FR_LD_NLD", "unit": "THS_T",
    }:
        raise ManualBundleLedgerViolation("bundle filters are outside the bounded asset")
    selection = content["selection"]
    if (
        set(selection) != {
            "geo_level", "grain", "years", "coverage", "selection_scope",
            "selection_status", "selection_evidence_state",
        }
        or selection.get("geo_level") not in {"COUNTRY", "NUTS1", "NUTS2"}
        or selection.get("grain") != ["geo_code", "time_period"]
        or selection.get("selection_scope") != "BLOCK1_EUROSTAT_MARITIME_GEO_LEVEL_SELECTION"
        or not isinstance(selection.get("years"), list)
    ):
        raise ManualBundleLedgerViolation("bundle selection is invalid")
    years = selection["years"]
    if (
        not years or any(not isinstance(year, int) or isinstance(year, bool) or not 1900 <= year <= 2100 for year in years)
        or years != sorted(set(years))
    ):
        raise ManualBundleLedgerViolation("bundle years are invalid")
    coverage = selection["coverage"]
    if not isinstance(coverage, Mapping) or frozenset(coverage) != _COVERAGE_FIELDS:
        raise ManualBundleLedgerViolation("bundle coverage shape is invalid")
    if any(not isinstance(coverage[field], int) or isinstance(coverage[field], bool) or coverage[field] < 0 for field in _COVERAGE_FIELDS):
        raise ManualBundleLedgerViolation("bundle coverage values are invalid")
    observations = content["observations"]
    seen: set[tuple[str, int]] = set()
    observed_codes: set[str] = set()
    for observation in observations:
        if not isinstance(observation, Mapping) or frozenset(observation) != _OBSERVATION_FIELDS:
            raise ManualBundleLedgerViolation("bundle observation shape is invalid")
        key = (observation["geo_code"], observation["time_period"])
        value = observation["value_thousand_tonnes"]
        flag = observation["status_flag"]
        if (
            not isinstance(key[0], str) or not key[0]
            or not isinstance(observation["geo_label"], str) or not observation["geo_label"].strip()
            or observation["geo_level"] != selection["geo_level"]
            or key[1] not in years or key in seen
            or not isinstance(value, (int, float)) or isinstance(value, bool)
            or not math.isfinite(value) or value < 0
            or (flag is not None and (not isinstance(flag, str) or not flag.strip()))
        ):
            raise ManualBundleLedgerViolation("bundle observation is invalid")
        seen.add(key)
        observed_codes.add(key[0])
    declared = coverage["declared_geography_count"]
    expected_cells = declared * len(years)
    if (
        coverage["observed_geography_count"] != len(observed_codes)
        or coverage["all_missing_geography_count"] != declared - len(observed_codes)
        or coverage["expected_geo_time_cells"] != expected_cells
        or coverage["observation_count"] != len(observations)
        or coverage["missing_value_count"] != expected_cells - len(observations)
        or declared < len(observed_codes) or len(observations) > expected_cells
    ):
        raise ManualBundleLedgerViolation("bundle coverage is inconsistent with observations")
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
            bundle = validate_unattested_manual_bundle(entry["bundle"])
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

    def latest_bundle(self) -> dict[str, Any] | None:
        """Return a defensive, revalidated checkpoint without changing its state."""

        with self._lock:
            entries = self._load_unlocked()
            return None if not entries else deepcopy(entries[-1]["bundle"])

    def record(self, bundle: Mapping[str, Any]) -> dict[str, Any]:
        normalized = validate_unattested_manual_bundle(bundle)
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
