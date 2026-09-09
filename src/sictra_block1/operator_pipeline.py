"""Reproducible local Eurostat intake for the bounded Block 1 laboratory.

This module deliberately has no network client.  An operator supplies an XLSX
file already obtained through an approved path.  The module retains only the
governed selection and its cryptographic lineage, then passes it through the
same stores and E01--E08 adapter used by the reference runtime.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import secrets
import time
from typing import Any, Callable

from .attested_evidence_store import AttestedEvidenceStore, AttestedEvidenceStoreViolation
from .attested_runtime_bridge import AttestedRuntimeBridge, AttestedRuntimeBridgeViolation
from .attested_watchlist_bridge import AttestedWatchlistBridge, AttestedWatchlistBridgeViolation
from .common import AuthorityIssuer, ContractViolation
from .evidence import EvidenceIssuer
from .eurostat_manual_bundle import build_eurostat_manual_bundle
from .intelligence_dossier import IntelligenceDossierStore, IntelligenceDossierViolation
from .manual_source_preflight import ManualSourcePreflightViolation, preflight_manual_source_file
from .manual_watchlist_cycle import ManualWatchlistCycle, ManualWatchlistCycleViolation
from .runtime import IntelligenceRuntime
from .source_control_store import SourceControlStore, SourceControlStoreViolation
from .source_gateway import SourceApprovalRecord, SourceBindingIssuer, SourceRegistration


_VERSION = 1
_SCOPE = "BLOCK1_LOCAL_EUROSTAT_OPERATOR_PIPELINE"
_MANIFEST = "pipeline-state.json"
_KEYS = {
    "source-control-integrity": "keys/source-control-integrity.key",
    "source-binding": "keys/source-binding.key",
    "gateway-evidence": "keys/gateway-evidence.key",
    "evidence-integrity": "keys/evidence-integrity.key",
    "watchlist-integrity": "keys/watchlist-integrity.key",
    "watchlist-bridge": "keys/watchlist-bridge.key",
    "dossier-integrity": "keys/dossier-integrity.key",
    "runtime-authority": "keys/runtime-authority.key",
    "runtime-execution": "keys/runtime-execution.key",
    "runtime-decision": "keys/runtime-decision.key",
    "runtime-integrity": "keys/runtime-integrity.key",
}
_FILES = {
    "source_control": "source-control.json",
    "evidence_store": "evidence.json",
    "watchlist": "watchlist.json",
    "dossier_store": "dossiers.json",
    "runtime_store": "runtime.sqlite3",
}
_BACKUP_MANIFEST = "pipeline-backup-manifest.json"
_BACKUP_SCOPE = "BLOCK1_LOCAL_EUROSTAT_PIPELINE_DATA_BACKUP"
_SOURCE_ID = "eurostat"
_SOURCE_URL = "https://ec.europa.eu/eurostat/databrowser/view/tran_r_mago_nm/default/table"
_SOURCE_SCOPE = "BLOCK1_EUROPE_MARITIME_INTELLIGENCE"
_CLAIM = "maritime_freight_weight_thousand_tonnes"
_EVIDENCE_MAX_AGE = 86_400
_BINDING_TTL = 15_552_000
# The owner approved this narrow data path and its manual-use boundary during
# the Block 1 source-governance review on 2026-09-06.  The reference is kept in
# the repository; the local binding itself is separately signed and expires.
_APPROVED_AT = 1_788_652_800


class OperatorPipelineViolation(ContractViolation):
    """The local governed intake cannot safely continue."""


def _path(root: Path, relative: str) -> Path:
    return root.joinpath(*relative.split("/"))


def _manifest() -> dict[str, Any]:
    return {
        "version": _VERSION,
        "scope": _SCOPE,
        "keys": dict(_KEYS),
        "files": dict(_FILES),
        "source": {
            "source_id": _SOURCE_ID,
            "source_url": _SOURCE_URL,
            "geo_levels": ["COUNTRY", "NUTS1", "NUTS2"],
            "network_acquisition": "DISABLED",
            "evidence_max_age_seconds": _EVIDENCE_MAX_AGE,
        },
    }


def _exclusive_write(path: Path, content: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise


def _clock_value(clock: Callable[[], int]) -> int:
    value = clock()
    if not isinstance(value, int) or isinstance(value, bool) or value < _APPROVED_AT:
        raise OperatorPipelineViolation("trusted clock predates approved source review")
    return value


def _read_manifest(root: Path) -> dict[str, Any]:
    path = root / _MANIFEST
    if path.is_symlink():
        raise OperatorPipelineViolation("pipeline manifest may not be a symbolic link")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OperatorPipelineViolation("pipeline manifest is unreadable") from error
    if not isinstance(value, dict) or value != _manifest():
        raise OperatorPipelineViolation("pipeline manifest is incompatible")
    return value


def _registration() -> SourceRegistration:
    return SourceRegistration(
        _SOURCE_ID, "Eurostat / European Commission", _SOURCE_SCOPE,
        ("ec.europa.eu",), frozenset((_CLAIM,)), "MANUAL_SOURCE_BUNDLE", 131_072, "BOUND",
    )


def _approval(registration: SourceRegistration) -> SourceApprovalRecord:
    return SourceApprovalRecord(
        _SOURCE_ID, "PROJECT_OWNER", _APPROVED_AT,
        "evidence/block1_eurostat_maritime_registration_draft_v0.1.md",
        registration.allowed_hosts, registration.claim_keys, registration.access_method,
        registration.max_content_bytes, "APPROVED",
    )


@dataclass(slots=True)
class OperatorPipeline:
    """Validated handles for one local, single-source laboratory pipeline."""

    root: Path
    clock: Callable[[], int]
    keys: dict[str, bytes]
    source_control: SourceControlStore
    evidence_store: AttestedEvidenceStore
    watchlist: ManualWatchlistCycle
    dossiers: IntelligenceDossierStore

    def gateway(self, *, now: int):
        return self.source_control.build_gateway(
            _SOURCE_ID, evidence_issuer=EvidenceIssuer("gateway", self.keys["gateway-evidence"]), now=now,
        )

    def runtime(self) -> IntelligenceRuntime:
        return IntelligenceRuntime.operational(
            store_path=self.root / _FILES["runtime_store"],
            authority_keys={"local-operator": self.keys["runtime-authority"]},
            authority_audience="block1-local-operator", authority_epoch=1,
            evidence_keys={"gateway": self.keys["gateway-evidence"]},
            evidence_scope=_SOURCE_SCOPE, evidence_max_age=_EVIDENCE_MAX_AGE,
            evidence_claims=frozenset((_CLAIM,)), execution_key=self.keys["runtime-execution"],
            decision_key=self.keys["runtime-decision"], storage_integrity_key=self.keys["runtime-integrity"],
            clock=self.clock,
        )


def initialize_operator_pipeline(root: str | Path, *, clock: Callable[[], int] | None = None) -> dict[str, Any]:
    """Create one exact local layout, binding the already-approved source once."""

    trusted_clock = clock or (lambda: int(time.time()))
    now = _clock_value(trusted_clock)
    target = Path(root)
    if not target.name or target.is_symlink():
        raise OperatorPipelineViolation("pipeline workspace path is invalid")
    manifest_path = target / _MANIFEST
    created_root = not target.exists()
    if target.exists():
        if not target.is_dir():
            raise OperatorPipelineViolation("pipeline workspace must be a directory")
        if manifest_path.exists():
            pipeline = load_operator_pipeline(target, clock=trusted_clock)
            active = pipeline.source_control.active_record(_SOURCE_ID, now=now)
            return {
                "scope": _SCOPE,
                "status": "READY" if active is not None else "BINDING_RENEWAL_REQUIRED",
                "root": str(target), "reused": True,
            }
        if any(target.iterdir()):
            raise OperatorPipelineViolation("pipeline workspace is non-empty and uninitialized")
    target.mkdir(parents=True, exist_ok=True)
    keys_dir = target / "keys"
    keys_dir.mkdir(exist_ok=True)
    if keys_dir.is_symlink() or any(keys_dir.iterdir()):
        raise OperatorPipelineViolation("pipeline key directory is not empty")
    created: list[Path] = []
    try:
        for relative in _KEYS.values():
            path = _path(target, relative)
            _exclusive_write(path, secrets.token_bytes(32))
            created.append(path)
        _exclusive_write(
            manifest_path,
            json.dumps(_manifest(), ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8"),
        )
        created.append(manifest_path)
        pipeline = load_operator_pipeline(target, clock=trusted_clock)
        registration = _registration()
        approval = _approval(registration)
        binding = SourceBindingIssuer("local-source-control", pipeline.keys["source-binding"]).issue(
            registration, approval, now=now, ttl=_BINDING_TTL,
        )
        pipeline.source_control.persist(registration, approval, binding)
        if pipeline.source_control.active_record(_SOURCE_ID, now=now) is None:
            raise OperatorPipelineViolation("approved source binding did not become active")
    except (OSError, ContractViolation) as error:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        try:
            keys_dir.rmdir()
            if created_root:
                target.rmdir()
        except OSError:
            pass
        raise OperatorPipelineViolation("pipeline initialization failed") from error
    return {"scope": _SCOPE, "status": "READY", "root": str(target), "reused": False}


def load_operator_pipeline(root: str | Path, *, clock: Callable[[], int] | None = None) -> OperatorPipeline:
    """Load the exact local layout and verify every durable component on read."""

    trusted_clock = clock or (lambda: int(time.time()))
    _clock_value(trusted_clock)
    target = Path(root)
    if not target.is_dir() or target.is_symlink():
        raise OperatorPipelineViolation("pipeline workspace is unavailable")
    manifest = _read_manifest(target)
    key_paths = {name: _path(target, relative) for name, relative in manifest["keys"].items()}
    if any(path.is_symlink() or not path.is_file() for path in key_paths.values()):
        raise OperatorPipelineViolation("pipeline key file is missing or unsafe")
    try:
        keys = {name: path.read_bytes() for name, path in key_paths.items()}
    except OSError as error:
        raise OperatorPipelineViolation("pipeline key file is unreadable") from error
    if any(len(value) != 32 for value in keys.values()):
        raise OperatorPipelineViolation("pipeline key length is invalid")
    paths = {name: _path(target, relative) for name, relative in manifest["files"].items()}
    if any(path.is_symlink() for path in paths.values()):
        raise OperatorPipelineViolation("pipeline data file may not be a symbolic link")
    try:
        source_control = SourceControlStore(
            paths["source_control"], binding_keys={"local-source-control": keys["source-binding"]},
            integrity_key=keys["source-control-integrity"], clock=trusted_clock,
        )
        source_control.list_records(now=_clock_value(trusted_clock))
        evidence_store = AttestedEvidenceStore(
            paths["evidence_store"], evidence_keys={"gateway": keys["gateway-evidence"]},
            evidence_scope=_SOURCE_SCOPE, evidence_max_age=_EVIDENCE_MAX_AGE,
            evidence_claims=frozenset((_CLAIM,)), integrity_key=keys["evidence-integrity"], clock=trusted_clock,
        )
        evidence_store.list_receipts(now=_clock_value(trusted_clock))
        watchlist = ManualWatchlistCycle(paths["watchlist"], integrity_key=keys["watchlist-integrity"], clock=trusted_clock)
        watchlist.list_cycles()
        dossiers = IntelligenceDossierStore(
            paths["dossier_store"], integrity_key=keys["dossier-integrity"],
            bridge_keys={"watchlist-bridge": keys["watchlist-bridge"]}, clock=trusted_clock,
        )
        dossiers.list_dossiers()
    except (SourceControlStoreViolation, AttestedEvidenceStoreViolation, ManualWatchlistCycleViolation,
            IntelligenceDossierViolation) as error:
        raise OperatorPipelineViolation("pipeline durable state failed integrity verification") from error
    return OperatorPipeline(target, trusted_clock, keys, source_control, evidence_store, watchlist, dossiers)


def pipeline_snapshot(root: str | Path, *, clock: Callable[[], int] | None = None) -> dict[str, Any]:
    """Return verified operational state without returning source contents or keys."""

    pipeline = load_operator_pipeline(root, clock=clock)
    now = _clock_value(pipeline.clock)
    source = pipeline.source_control.active_record(_SOURCE_ID, now=now)
    evidence = pipeline.evidence_store.list_receipts(now=now)
    current_evidence_count = sum(item["status"] == "CURRENT" for item in evidence)
    source_review_required = any(
        item["verification_reason"] == "SOURCE_SUPERSEDED_OR_AMBIGUOUS" for item in evidence
    )
    cycles = pipeline.watchlist.list_cycles()
    dossiers = pipeline.dossiers.list_dossiers()
    latest = pipeline.watchlist.latest_delta()
    return {
        "scope": _SCOPE,
        "status": (
            "BINDING_RENEWAL_REQUIRED" if source is None
            else "SOURCE_REVIEW_REQUIRED" if source_review_required
            else "READY"
        ),
        "network_acquisition": "DISABLED",
        "source": {"source_id": _SOURCE_ID, "binding_active": source is not None},
        "evidence": {"retained_count": len(evidence), "current_count": current_evidence_count},
        "watchlist": {
            "cycle_count": len(cycles),
            "latest_status": None if latest is None else latest["status"],
            "next_state": None if latest is None else latest["next_state"],
        },
        "dossiers": {"count": len(dossiers), "publication_authority": "NONE"},
    }


def _safe_backup_destination(root: Path, destination: Path) -> None:
    if not destination.name or destination.exists() or destination.is_symlink():
        raise OperatorPipelineViolation("backup destination must be a new directory")
    try:
        if destination.resolve().is_relative_to(root.resolve()):
            raise OperatorPipelineViolation("backup destination must be outside pipeline state")
    except OSError as error:
        raise OperatorPipelineViolation("backup destination cannot be resolved") from error


def create_pipeline_data_backup(
    root: str | Path, destination: str | Path, *, clock: Callable[[], int] | None = None,
) -> dict[str, Any]:
    """Copy verified source/evidence/watchlist/dossier ledgers, never any key."""

    pipeline = load_operator_pipeline(root, clock=clock)
    target = Path(destination)
    _safe_backup_destination(pipeline.root, target)
    data: dict[str, bytes | None] = {}
    for name, relative in _FILES.items():
        if name == "runtime_store":
            continue
        path = pipeline.root / relative
        if path.is_symlink():
            raise OperatorPipelineViolation("pipeline ledger may not be a symbolic link")
        try:
            data[name] = path.read_bytes() if path.exists() else None
        except OSError as error:
            raise OperatorPipelineViolation("pipeline ledger cannot be read for backup") from error
    # Verify again after the read; a concurrent mutation cannot be presented as
    # a coherent backup merely because every individual file was readable.
    load_operator_pipeline(pipeline.root, clock=pipeline.clock)
    for name, relative in _FILES.items():
        if name == "runtime_store":
            continue
        path = pipeline.root / relative
        try:
            confirmed = path.read_bytes() if path.exists() else None
        except OSError as error:
            raise OperatorPipelineViolation("pipeline ledger cannot be confirmed for backup") from error
        if confirmed != data[name]:
            raise OperatorPipelineViolation("pipeline ledger changed during backup")
    manifest = {
        "version": _VERSION,
        "scope": _BACKUP_SCOPE,
        "created_at": _clock_value(pipeline.clock),
        "keys_included": False,
        "runtime_store_included": False,
        "ledgers": {
            name: {
                "file": _FILES[name], "present": value is not None,
                "sha256": None if value is None else sha256(value).hexdigest(),
            }
            for name, value in data.items()
        },
    }
    created: list[Path] = []
    try:
        target.mkdir(parents=True)
        for name, value in data.items():
            if value is not None:
                path = target / _FILES[name]
                _exclusive_write(path, value)
                created.append(path)
        manifest_path = target / _BACKUP_MANIFEST
        _exclusive_write(
            manifest_path,
            json.dumps(manifest, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8"),
        )
        created.append(manifest_path)
    except OSError as error:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        try:
            target.rmdir()
        except OSError:
            pass
        raise OperatorPipelineViolation("pipeline data backup failed") from error
    return {"scope": _BACKUP_SCOPE, "status": "BACKUP_CREATED", "keys_included": False,
            "runtime_store_included": False, "destination": str(target)}


def restore_pipeline_data_backup(root: str | Path, backup: str | Path, *, clock: Callable[[], int] | None = None) -> dict[str, Any]:
    """Restore a complete absent ledger set only under its original retained keys."""

    pipeline = load_operator_pipeline(root, clock=clock)
    source = Path(backup)
    if not source.is_dir() or source.is_symlink():
        raise OperatorPipelineViolation("backup directory is unavailable or unsafe")
    try:
        if source.resolve().is_relative_to(pipeline.root.resolve()):
            raise OperatorPipelineViolation("backup directory must be outside pipeline state")
    except OSError as error:
        raise OperatorPipelineViolation("backup directory cannot be resolved") from error
    manifest_path = source / _BACKUP_MANIFEST
    if manifest_path.is_symlink():
        raise OperatorPipelineViolation("backup manifest may not be a symbolic link")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OperatorPipelineViolation("backup manifest is unreadable") from error
    expected_ledgers = {name: {"file", "present", "sha256"} for name in _FILES if name != "runtime_store"}
    if (
        not isinstance(manifest, dict)
        or set(manifest) != {"version", "scope", "created_at", "keys_included", "runtime_store_included", "ledgers"}
        or manifest["version"] != _VERSION or manifest["scope"] != _BACKUP_SCOPE
        or not isinstance(manifest["created_at"], int) or isinstance(manifest["created_at"], bool)
        or manifest["created_at"] < 0 or manifest["keys_included"] is not False
        or manifest["runtime_store_included"] is not False or not isinstance(manifest["ledgers"], dict)
        or set(manifest["ledgers"]) != set(expected_ledgers)
        or any(not isinstance(value, dict) or set(value) != fields for value, fields in
               ((manifest["ledgers"][name], expected_ledgers[name]) for name in expected_ledgers))
    ):
        raise OperatorPipelineViolation("backup manifest is incompatible")
    expected_entries = {_BACKUP_MANIFEST}
    contents: dict[str, bytes | None] = {}
    for name in expected_ledgers:
        descriptor = manifest["ledgers"][name]
        if descriptor["file"] != _FILES[name] or not isinstance(descriptor["present"], bool):
            raise OperatorPipelineViolation("backup ledger declaration is invalid")
        path = source / _FILES[name]
        if descriptor["present"]:
            expected_entries.add(_FILES[name])
            if path.is_symlink() or not path.is_file():
                raise OperatorPipelineViolation("backup ledger is missing or unsafe")
            try:
                content = path.read_bytes()
            except OSError as error:
                raise OperatorPipelineViolation("backup ledger is unreadable") from error
            if not isinstance(descriptor["sha256"], str) or sha256(content).hexdigest() != descriptor["sha256"]:
                raise OperatorPipelineViolation("backup ledger digest mismatch")
            contents[name] = content
        elif descriptor["sha256"] is not None or path.exists():
            raise OperatorPipelineViolation("backup ledger declaration is contradictory")
        else:
            contents[name] = None
    try:
        if {item.name for item in source.iterdir()} != expected_entries:
            raise OperatorPipelineViolation("backup directory contains unexpected content")
    except OSError as error:
        raise OperatorPipelineViolation("backup directory cannot be enumerated") from error
    target_paths = {name: pipeline.root / _FILES[name] for name in expected_ledgers}
    if any(path.exists() or path.is_symlink() for path in target_paths.values()):
        raise OperatorPipelineViolation("restore refuses to overwrite any current pipeline ledger")
    written: list[Path] = []
    try:
        for name, content in contents.items():
            if content is not None:
                _exclusive_write(target_paths[name], content)
                written.append(target_paths[name])
        load_operator_pipeline(pipeline.root, clock=pipeline.clock)
    except (OSError, OperatorPipelineViolation) as error:
        for path in reversed(written):
            path.unlink(missing_ok=True)
        raise OperatorPipelineViolation("restored pipeline data failed local key verification") from error
    return {"scope": _BACKUP_SCOPE, "status": "RESTORED", "keys_restored": False,
            "runtime_store_restored": False}


def ingest_eurostat_workbook(
    root: str | Path, workbook_path: str | Path, *, geo_level: str = "COUNTRY",
    clock: Callable[[], int] | None = None,
) -> dict[str, Any]:
    """Process an explicit local workbook through the full governed chain.

    A first release returns a non-evidentiary baseline.  A changed release can
    produce a literal-fact dossier, but cannot publish or create interpretation.
    """

    trusted_clock = clock or (lambda: int(time.time()))
    now = _clock_value(trusted_clock)
    source_path = Path(workbook_path)
    if source_path.is_symlink() or not source_path.is_file():
        raise OperatorPipelineViolation("operator workbook must be a regular local file")
    try:
        payload = source_path.read_bytes()
    except OSError as error:
        raise OperatorPipelineViolation("operator workbook cannot be read") from error
    try:
        preflight = preflight_manual_source_file(source_path.name, payload)
    except ManualSourcePreflightViolation as error:
        raise OperatorPipelineViolation("operator workbook failed controlled preflight") from error
    if preflight["status"] != "READY_FOR_SCHEMA_REVIEW":
        raise OperatorPipelineViolation(f"operator workbook rejected: {preflight['reason']}")
    # Every component in this ingestion must assess freshness against the same
    # verified instant.  Calling a wall clock again at a second boundary could
    # otherwise make the runtime reject evidence just admitted by this call.
    pipeline = load_operator_pipeline(root, clock=lambda: now)
    gateway = pipeline.gateway(now=now)
    correlation = f"eurostat:{sha256(payload).hexdigest()}"
    try:
        bundle = build_eurostat_manual_bundle(
            source_path.name, payload, geo_level, source_url=_SOURCE_URL,
            observed_at=now, correlation_id=correlation,
        )
        evidence = gateway.attest_manual_bundle(bundle, now=now)
        evidence_receipt = pipeline.evidence_store.persist(evidence)
        runtime = pipeline.runtime()
        try:
            authority = AuthorityIssuer(
                "local-operator", pipeline.keys["runtime-authority"], "block1-local-operator", 1,
            ).issue(
                task_id="eurostat-manual-intake", run_id=f"runtime:{sha256(bundle['content'].encode()).hexdigest()}",
                actions=("store_candidate",), now=now, ttl=300, nonce=correlation,
            )
            runtime_result = AttestedRuntimeBridge(pipeline.evidence_store, runtime).run(
                task_id="eurostat-manual-intake", run_id=f"runtime:{sha256(bundle['content'].encode()).hexdigest()}",
                objective="retain a governed Eurostat maritime selection without interpretation",
                authority=authority, now=now,
            )
        finally:
            runtime.close()
        bridge_result = AttestedWatchlistBridge(
            pipeline.evidence_store, pipeline.watchlist, receipt_issuer="watchlist-bridge",
            receipt_key=pipeline.keys["watchlist-bridge"],
        ).ingest(_SOURCE_ID, now=now)
        dossier_receipt = None
        if bridge_result["next_state"] == "REQUIRES_REVIEW":
            dossier_receipt = pipeline.dossiers.persist(bridge_result)
    except (ContractViolation, OSError) as error:
        raise OperatorPipelineViolation("governed pipeline rejected the workbook") from error
    return {
        "scope": _SCOPE,
        "status": bridge_result["watchlist_receipt"]["status"],
        "preflight": {"status": preflight["status"], "content_sha256": preflight["content_sha256"]},
        "source_control": {"status": "ACTIVE", "network_acquisition": "DISABLED"},
        "evidence": evidence_receipt,
        "runtime": {
            "enforcement": runtime_result.envelope.payload["enforcement"]["status"],
            "evidence_count": runtime_result.envelope.payload["outcome"]["evidence_count"],
        },
        "watchlist": {
            "status": bridge_result["watchlist_receipt"]["status"],
            "change_count": bridge_result["watchlist_receipt"]["change_count"],
            "next_state": bridge_result["next_state"],
        },
        "dossier": dossier_receipt,
        "publication_authority": "NONE",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "status", "ingest", "backup", "restore"))
    parser.add_argument("root", type=Path)
    parser.add_argument("workbook", type=Path, nargs="?")
    parser.add_argument("--geo-level", choices=("COUNTRY", "NUTS1", "NUTS2"), default="COUNTRY")
    args = parser.parse_args()
    if args.command == "init":
        result = initialize_operator_pipeline(args.root)
    elif args.command == "status":
        result = pipeline_snapshot(args.root)
    elif args.command == "ingest":
        if args.workbook is None:
            parser.error("ingest requires an explicitly supplied workbook")
        result = ingest_eurostat_workbook(args.root, args.workbook, geo_level=args.geo_level)
    elif args.command == "backup":
        if args.workbook is None:
            parser.error("backup requires a new destination directory")
        result = create_pipeline_data_backup(args.root, args.workbook)
    else:
        if args.workbook is None:
            parser.error("restore requires a backup directory")
        result = restore_pipeline_data_backup(args.root, args.workbook)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
