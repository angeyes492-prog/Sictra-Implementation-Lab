"""Atomic local watchlist checkpoints with recomputable Eurostat deltas."""

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
from uuid import uuid4

from .common import ContractViolation
from .eurostat_maritime_delta import (
    EurostatMaritimeDeltaViolation,
    compare_eurostat_manual_bundles,
)
from .manual_bundle_ledger import (
    ManualBundleLedgerViolation,
    validate_unattested_manual_bundle,
)


_VERSION = 1
_MAX_CYCLES = 100
_ENTRY_FIELDS = frozenset((
    "cycle_id", "recorded_at", "bundle_sha256", "delta_sha256",
    "previous_hash", "record_hash", "bundle", "delta",
))


class ManualWatchlistCycleViolation(ContractViolation):
    """The durable manual watchlist state is invalid or cannot advance safely."""


def _encoded(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _fingerprint(value: object) -> str:
    return sha256(_encoded(value).encode("utf-8")).hexdigest()


def _source_file_sha(bundle: Mapping[str, Any]) -> str:
    return json.loads(bundle["content"])["provenance"]["source_file_sha256"]


def _baseline(bundle: Mapping[str, Any]) -> dict[str, Any]:
    content = json.loads(bundle["content"])
    selection = content["selection"]
    return {
        "scope": "BLOCK1_LOCAL_MANUAL_WATCHLIST_CYCLE",
        "source_id": "eurostat",
        "dataset_code": "tran_r_mago_nm",
        "selected_geo_level": selection["geo_level"],
        "previous": None,
        "current": {
            "content_sha256": content["provenance"]["source_file_sha256"],
            "last_updated": content["provenance"]["dataset_last_updated"],
            "coverage": selection["coverage"],
        },
        "change_count": 0,
        "changes": [],
        "status": "BASELINE_ESTABLISHED_NOT_EVIDENCE",
        "evidence_state": "NOT_EVIDENCE",
        "next_state": "AWAIT_NEWER_MANUAL_RELEASE",
    }


class ManualWatchlistCycle:
    """Persist each checkpoint together with its independently recomputable delta."""

    def __init__(
        self, path: str | Path, *, integrity_key: bytes, clock: Callable[[], int],
        id_factory: Callable[[], str] | None = None, max_cycles: int = _MAX_CYCLES,
    ) -> None:
        self.path = Path(path)
        if not self.path.name or not isinstance(integrity_key, bytes) or len(integrity_key) < 32:
            raise ManualWatchlistCycleViolation("watchlist path and 32-byte integrity key are required")
        if not isinstance(max_cycles, int) or isinstance(max_cycles, bool) or not 1 <= max_cycles <= _MAX_CYCLES:
            raise ManualWatchlistCycleViolation("watchlist capacity is invalid")
        self._key = bytes(integrity_key)
        self._clock = clock
        self._id_factory = id_factory or (lambda: f"cycle-{uuid4().hex}")
        self._capacity = max_cycles
        self._lock = Lock()
        self.failure_injector: Callable[[str], None] | None = None

    def _mac(self, material: str) -> str:
        return hmac.new(self._key, material.encode("utf-8"), sha256).hexdigest()

    def _key_check(self) -> str:
        return self._mac(f"manual-watchlist-cycle-v{_VERSION}:{self._capacity}")

    def _record_hash(self, entry: Mapping[str, Any]) -> str:
        material = {field: entry[field] for field in _ENTRY_FIELDS - {"record_hash"}}
        return self._mac("manual-watchlist-record-v1:" + _encoded(material))

    @staticmethod
    def _receipt(entry: Mapping[str, Any], *, replay: bool = False) -> dict[str, Any]:
        delta = entry["delta"]
        return {
            "scope": "BLOCK1_LOCAL_MANUAL_WATCHLIST_CYCLE",
            "cycle_id": entry["cycle_id"],
            "recorded_at": entry["recorded_at"],
            "bundle_sha256": entry["bundle_sha256"],
            "delta_sha256": entry["delta_sha256"],
            "record_hash": entry["record_hash"],
            "status": delta["status"],
            "change_count": delta["change_count"],
            "evidence_state": "NOT_EVIDENCE",
            "replay": replay,
        }

    def _load_unlocked(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ManualWatchlistCycleViolation("watchlist ledger cannot be read") from error
        if (
            not isinstance(document, Mapping)
            or set(document) != {"version", "capacity", "key_check", "entries"}
            or document["version"] != _VERSION or document["capacity"] != self._capacity
            or not isinstance(document["key_check"], str)
            or not hmac.compare_digest(document["key_check"], self._key_check())
            or not isinstance(document["entries"], list)
            or len(document["entries"]) > self._capacity
        ):
            raise ManualWatchlistCycleViolation("watchlist schema or key configuration is invalid")
        verified: list[dict[str, Any]] = []
        previous_hash = "GENESIS"
        previous_time = -1
        source_hashes: set[str] = set()
        for entry in document["entries"]:
            if not isinstance(entry, Mapping) or frozenset(entry) != _ENTRY_FIELDS:
                raise ManualWatchlistCycleViolation("watchlist entry shape is invalid")
            try:
                bundle = validate_unattested_manual_bundle(entry["bundle"])
                expected_delta = _baseline(bundle) if not verified else compare_eurostat_manual_bundles(
                    verified[-1]["bundle"], bundle,
                )
            except (ManualBundleLedgerViolation, EurostatMaritimeDeltaViolation) as error:
                raise ManualWatchlistCycleViolation("watchlist checkpoint cannot be revalidated") from error
            if (
                not isinstance(entry["cycle_id"], str) or not entry["cycle_id"].strip()
                or len(entry["cycle_id"]) > 100
                or not isinstance(entry["recorded_at"], int) or isinstance(entry["recorded_at"], bool)
                or entry["recorded_at"] < 0 or entry["recorded_at"] < previous_time
                or entry["bundle_sha256"] != _fingerprint(bundle)
                or entry["delta"] != expected_delta
                or entry["delta_sha256"] != _fingerprint(expected_delta)
                or entry["previous_hash"] != previous_hash
                or not isinstance(entry["record_hash"], str)
                or not hmac.compare_digest(entry["record_hash"], self._record_hash(entry))
            ):
                raise ManualWatchlistCycleViolation("watchlist integrity verification failed")
            source_hash = _source_file_sha(bundle)
            if source_hash in source_hashes:
                raise ManualWatchlistCycleViolation("watchlist contains a duplicate source checkpoint")
            source_hashes.add(source_hash)
            verified.append(dict(entry))
            previous_hash = entry["record_hash"]
            previous_time = entry["recorded_at"]
        if len({entry["cycle_id"] for entry in verified}) != len(verified):
            raise ManualWatchlistCycleViolation("watchlist contains duplicate cycle identities")
        return verified

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
            if self.failure_injector:
                self.failure_injector("BEFORE_ATOMIC_REPLACE")
            os.replace(temporary_name, self.path)
        except OSError as error:
            if temporary_name:
                Path(temporary_name).unlink(missing_ok=True)
            raise ManualWatchlistCycleViolation("watchlist ledger cannot be written") from error

    def ingest(self, bundle: Mapping[str, Any]) -> dict[str, Any]:
        try:
            normalized = validate_unattested_manual_bundle(bundle)
        except ManualBundleLedgerViolation as error:
            raise ManualWatchlistCycleViolation("watchlist bundle is invalid") from error
        with self._lock:
            entries = self._load_unlocked()
            if entries and _source_file_sha(entries[-1]["bundle"]) == _source_file_sha(normalized):
                return self._receipt(entries[-1], replay=True)
            if len(entries) >= self._capacity:
                raise ManualWatchlistCycleViolation("watchlist capacity exhausted")
            try:
                delta = _baseline(normalized) if not entries else compare_eurostat_manual_bundles(
                    entries[-1]["bundle"], normalized,
                )
            except EurostatMaritimeDeltaViolation as error:
                raise ManualWatchlistCycleViolation("watchlist release cannot advance") from error
            cycle_id = self._id_factory()
            recorded_at = self._clock()
            if (
                not isinstance(cycle_id, str) or not cycle_id.strip() or len(cycle_id) > 100
                or any(entry["cycle_id"] == cycle_id for entry in entries)
            ):
                raise ManualWatchlistCycleViolation("watchlist cycle identity is invalid or duplicated")
            if (
                not isinstance(recorded_at, int) or isinstance(recorded_at, bool) or recorded_at < 0
                or (entries and recorded_at < entries[-1]["recorded_at"])
            ):
                raise ManualWatchlistCycleViolation("watchlist logical time is invalid")
            entry = {
                "cycle_id": cycle_id,
                "recorded_at": recorded_at,
                "bundle_sha256": _fingerprint(normalized),
                "delta_sha256": _fingerprint(delta),
                "previous_hash": "GENESIS" if not entries else entries[-1]["record_hash"],
                "record_hash": "",
                "bundle": normalized,
                "delta": delta,
            }
            entry["record_hash"] = self._record_hash(entry)
            entries.append(entry)
            self._save_unlocked(entries)
            return self._receipt(entry)

    def list_cycles(self) -> list[dict[str, Any]]:
        with self._lock:
            return [self._receipt(entry) for entry in self._load_unlocked()]

    def latest_delta(self) -> dict[str, Any] | None:
        with self._lock:
            entries = self._load_unlocked()
            return None if not entries else deepcopy(entries[-1]["delta"])
