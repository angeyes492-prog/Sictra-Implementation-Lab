"""Candidate statistical retention over the existing evidence-history primitive."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re

from .attested_evidence_store import AttestedEvidenceStore
from .common import ContractViolation
from .research_acquisition import ResearchQuarantine, canonical, STATISTICS_RECIPE
from .research_admission import SCOPE, CLAIM, verify_statistics_candidate, _time
from .source_control_store import SourceControlStore


class StatisticalRetentionViolation(ContractViolation):
    pass


def _require(condition, reason):
    if not condition:
        raise StatisticalRetentionViolation(reason)


def _identities(source):
    try:
        body = json.loads(source["content"])
        provenance = body["provenance"]
        identities = provenance["data_candidate_id"], provenance["methodology_candidate_id"]
    except (KeyError, TypeError, ValueError, RecursionError) as error:
        raise StatisticalRetentionViolation("STATISTICAL_PACKET_INVALID") from error
    _require(all(isinstance(i, str) for i in identities), "STATISTICAL_IDENTITIES_INVALID")
    return identities


class _StatisticalHistory(AttestedEvidenceStore):
    """Reuse chain/config/atomic writes; never expose generic runtime retrieval."""
    def __init__(self, path, *, quarantine, control, control_checkpoint, history_checkpoint, **kwargs):
        self.quarantine, self.control = quarantine, control
        self.control_checkpoint, self.history_checkpoint = control_checkpoint, history_checkpoint
        super().__init__(path, evidence_scope=SCOPE, evidence_claims=frozenset((CLAIM,)), **kwargs)
        self._verified_history = {}

    def guard_authority(self):
        rows = self.control.list_records(now=_time(self._clock))
        _require(any(r["record_hash"] == self.control_checkpoint for r in rows),
                 "STATISTICAL_AUTHORITY_CHECKPOINT_MISSING")
        self.control_checkpoint = rows[-1]["record_hash"]
        return rows

    def _load_unlocked(self):
        self.guard_authority()
        records = super()._load_unlocked()
        if self.history_checkpoint is not None:
            _require(any(r["record_hash"] == self.history_checkpoint for r in records),
                     "STATISTICAL_HISTORY_CHECKPOINT_MISSING")
        if records:
            self.history_checkpoint = records[-1]["record_hash"]
        return records

    def _validate_evidence(self, value, *, now):
        _require(isinstance(value, dict), "STATISTICAL_PACKET_INVALID")
        source = deepcopy(value)
        data_id, metadata_id = _identities(source)
        # Rehash live bytes/lineage on every load. Only reuse full parsing and
        # historical signature reconstruction for the identical verified inputs.
        data, _ = self.quarantine.read(data_id, now=now, expected_recipe=STATISTICS_RECIPE)
        metadata, _ = self.quarantine.read(metadata_id, now=now, expected_recipe="EUROSTAT_MAR_METADATA")
        terms, _ = self.quarantine.read(data["terms_candidate_id"], now=now, expected_recipe="EUROSTAT_REUSE_NOTICE")
        key = sha256(canonical([source, now, data, metadata, terms, self.control.list_records(now=now)])).hexdigest()
        if key not in self._verified_history:
            self.verify(source, clock=lambda: now)
            if len(self._verified_history) >= self._capacity:
                self._verified_history.pop(next(iter(self._verified_history)))
            self._verified_history[key] = True
        return source

    def verify(self, source, *, clock):
        self.guard_authority()
        data_id, metadata_id = _identities(source)
        return verify_statistics_candidate(source, self.quarantine, data_id, metadata_id,
                                           self.control, self._verifier, clock=clock)

    def _receipt(self, record, *, now, replay=False):
        return {"evidence_id": record["evidence_id"], "admitted_at": record["admitted_at"],
                "record_hash": record["record_hash"], "replay": replay, "status": "RETAINED_HISTORY"}

    def runtime_records(self, **kwargs):
        raise StatisticalRetentionViolation("STATISTICAL_EXPLICIT_SELECTION_REQUIRED")


class StatisticalEvidenceStore:
    """Historical receipts and explicit, current-only candidate source selection."""
    def __init__(self, path, *, quarantine, control, evidence_keys, integrity_key,
                 clock, control_checkpoint, history_checkpoint=None,
                 evidence_max_age=86400, max_records=1000):
        _require(isinstance(quarantine, ResearchQuarantine) and isinstance(control, SourceControlStore)
                 and callable(clock), "STATISTICAL_DEPENDENCIES_INVALID")
        _require(type(evidence_max_age) is int and 0 <= evidence_max_age <= 86400,
                 "STATISTICAL_FRESHNESS_INVALID")
        target, research = Path(path).resolve(), quarantine.root.resolve()
        _require(target != control.path.resolve() and target != research and research not in target.parents,
                 "STATISTICAL_PATH_COLLISION")
        _require(isinstance(evidence_keys, dict) and integrity_key not in evidence_keys.values(),
                 "STATISTICAL_SEPARATE_KEYS_REQUIRED")
        _require(isinstance(control_checkpoint, str) and re.fullmatch(r"[0-9a-f]{64}", control_checkpoint)
                 and (history_checkpoint is None or
                      (isinstance(history_checkpoint, str) and re.fullmatch(r"[0-9a-f]{64}", history_checkpoint))),
                 "STATISTICAL_CHECKPOINT_INVALID")
        _require(not target.exists() or history_checkpoint is not None,
                 "STATISTICAL_HISTORY_CHECKPOINT_REQUIRED")
        self.path, self._clock = target, clock
        self._history = _StatisticalHistory(target, quarantine=quarantine, control=control,
            control_checkpoint=control_checkpoint, history_checkpoint=history_checkpoint,
            evidence_keys=evidence_keys, integrity_key=integrity_key, clock=clock,
            evidence_max_age=evidence_max_age, max_records=max_records)

    def checkpoint(self):
        """Last observed public heads for custody outside a data-only backup."""
        return {"control_checkpoint": self._history.control_checkpoint,
                "history_checkpoint": self._history.history_checkpoint}

    @property
    def failure_injector(self):
        return self._history.failure_injector

    @failure_injector.setter
    def failure_injector(self, value):
        self._history.failure_injector = value

    @staticmethod
    def _head(records):
        if not records:
            return None, "NO_RETAINED_EVIDENCE"
        releases = []
        for record in records:
            provenance = json.loads(record["evidence"]["content"])["provenance"]
            try:
                released = datetime.fromisoformat(provenance["publisher_updated_raw"].replace("Z", "+00:00"))
                if released.tzinfo is None:
                    return None, "PUBLISHER_TIME_UNORDERED"
                released = released.astimezone(timezone.utc)
            except (ValueError, OverflowError):
                return None, "PUBLISHER_TIME_UNORDERED"
            releases.append((released, provenance["source_file_sha256"], record))
        latest = max(item[0] for item in releases)
        head = [item for item in releases if item[0] == latest]
        if len({item[1] for item in head}) != 1:
            return None, "LATEST_RELEASE_AMBIGUOUS"
        return max((item[2] for item in head), key=lambda r: (
            r["evidence"]["observed_at"], r["admitted_at"], r["evidence_id"])), "SOURCE_SUPERSEDED"

    def _view(self, records, now):
        head, other_reason = self._head(records)
        receipts = []
        for record in records:
            source = record["evidence"]
            body = json.loads(source["content"])
            reason, status = other_reason, "NOT_CURRENT"
            if record is head:
                # Tentative projection only. _snapshot enforces the complete
                # independent current verifier before returning any CURRENT.
                valid, reason = self._history._verifier.verify(source, now=now)
                bindings = [r for r in self._history.control.list_records(now=now)
                            if r["source_id"] == "eurostat" and r["issued_at"] <= now]
                if valid and now >= body["expires_at"]:
                    valid, reason = False, "STATISTICAL_DEPENDENCIES_EXPIRED"
                if valid and (not bindings or bindings[-1]["binding_id"] != body["provenance"]["binding_id"]):
                    valid, reason = False, "ADMISSION_APPROVAL_SUPERSEDED"
                if valid and (bindings[-1]["status"] != "ACTIVE" or now >= bindings[-1]["expires_at"]):
                    valid, reason = False, "ADMISSION_NOT_CURRENT"
                if valid:
                    status = "CURRENT"
            receipts.append({"scope": SCOPE, "evidence_id": record["evidence_id"],
                "admitted_at": record["admitted_at"], "observed_at": source["observed_at"],
                "record_hash": record["record_hash"], "status": status, "verification_reason": reason,
                "data_candidate_id": body["provenance"]["data_candidate_id"],
                "binding_id": body["provenance"]["binding_id"], "expires_at": body["expires_at"],
                "publisher_updated_raw": body["provenance"]["publisher_updated_raw"],
                "runtime_effect": "NONE", "publication": "BLOCKED", "resolution": "NOT_RESOLVED"})
        return receipts

    def _snapshot(self):
        start = _time(self._clock)
        with self._history._lock:
            def authority(now):
                return [{k: v for k, v in r.items() if k != "status"}
                        for r in self._history.control.list_records(now=now)]
            control = authority(start)
            records = self._history._load_unlocked()
            _require(not records or records[-1]["admitted_at"] <= start, "STATISTICAL_CLOCK_REGRESSED")
            view = self._view(records, start)
            finish = _time(self._clock)
            _require(finish >= start, "STATISTICAL_CLOCK_REGRESSED")
            _require(records == self._history._load_unlocked(), "STATISTICAL_HISTORY_CHANGED")
            _require(view == self._view(records, finish), "STATISTICAL_READ_CHANGED")
            for record, receipt in zip(records, view):
                if receipt["status"] == "CURRENT":
                    self._history.verify(record["evidence"], clock=self._clock)
            _require(records == self._history._load_unlocked(), "STATISTICAL_HISTORY_CHANGED")
            _require(control == authority(finish), "STATISTICAL_AUTHORITY_CHANGED")
            end = _time(self._clock)
            _require(end >= finish, "STATISTICAL_CLOCK_REGRESSED")
            _require(all(r["status"] != "CURRENT" or
                         (end < r["expires_at"] and end - r["observed_at"] <= self._history._max_age)
                         for r in view), "STATISTICAL_READ_EXPIRED")
            return deepcopy(records), deepcopy(view)

    def retain(self, source):
        packet = deepcopy(source)
        self._history.verify(packet, clock=self._clock)
        retained = self._history.persist(packet)
        _, receipts = self._snapshot()
        receipt = next(r for r in receipts if r["evidence_id"] == retained["evidence_id"])
        return {**receipt, "replay": retained["replay"]}

    def history(self):
        return self._snapshot()[1]

    def select(self, evidence_id):
        _require(isinstance(evidence_id, str) and evidence_id.startswith("eurostat:"),
                 "STATISTICAL_SELECTION_INVALID")
        records, receipts = self._snapshot()
        for record, receipt in zip(records, receipts):
            if receipt["evidence_id"] == evidence_id:
                _require(receipt["status"] == "CURRENT", "STATISTICAL_SELECTION_NOT_CURRENT:" + receipt["verification_reason"])
                return deepcopy(record["evidence"])
        raise StatisticalRetentionViolation("STATISTICAL_SELECTION_NOT_RETAINED")
