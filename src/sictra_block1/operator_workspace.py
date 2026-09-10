"""Local operator-state initialization without placing integrity keys in Git."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import secrets
import time
from typing import Any, Callable

from .common import ContractViolation
from .intelligence_dossier import IntelligenceDossierStore, IntelligenceDossierViolation


_VERSION = 1
_SCOPE = "BLOCK1_LOCAL_OPERATOR_WORKSPACE"
_MANIFEST = "operator-state.json"
_DOSSIERS = "dossiers.json"
_DOSSIER_KEY = "keys/dossier-integrity.key"
_BRIDGE_KEY = "keys/watchlist-bridge.key"
_BACKUP_VERSION = 1
_BACKUP_MANIFEST = "backup-manifest.json"
_BACKUP_SCOPE = "BLOCK1_LOCAL_OPERATOR_DATA_BACKUP"
_MANIFEST_FIELDS = frozenset((
    "version", "scope", "dossier_store", "dossier_integrity_key", "bridge_keys",
))


class OperatorWorkspaceViolation(ContractViolation):
    """Local operator state is incomplete, unsafe, or incompatible."""


def _path(root: Path, relative: str) -> Path:
    return root.joinpath(*relative.split("/"))


def _manifest() -> dict[str, Any]:
    return {
        "version": _VERSION,
        "scope": _SCOPE,
        "dossier_store": _DOSSIERS,
        "dossier_integrity_key": _DOSSIER_KEY,
        "bridge_keys": {"watchlist-bridge": _BRIDGE_KEY},
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


def _read_manifest(root: Path) -> dict[str, Any]:
    manifest_path = root / _MANIFEST
    if manifest_path.is_symlink():
        raise OperatorWorkspaceViolation("operator manifest may not be a symbolic link")
    try:
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OperatorWorkspaceViolation("operator manifest is unreadable") from error
    if (not isinstance(value, dict) or frozenset(value) != _MANIFEST_FIELDS
            or value != _manifest()):
        raise OperatorWorkspaceViolation("operator manifest is incompatible")
    return value


def initialize_operator_workspace(root: str | Path) -> dict[str, Any]:
    """Create or validate the bounded local operator-state directory."""

    target = Path(root)
    if not target.name or target.is_symlink():
        raise OperatorWorkspaceViolation("operator workspace path is invalid")
    manifest_path = target / _MANIFEST
    created_root = not target.exists()
    if target.exists():
        if not target.is_dir():
            raise OperatorWorkspaceViolation("operator workspace must be a directory")
        if manifest_path.exists():
            load_operator_dossier_store(target, clock=lambda: int(time.time()))
            return {"scope": _SCOPE, "status": "READY", "root": str(target), "reused": True}
        if any(target.iterdir()):
            raise OperatorWorkspaceViolation("operator workspace is non-empty and uninitialized")
    target.mkdir(parents=True, exist_ok=True)
    keys = target / "keys"
    keys.mkdir(exist_ok=True)
    if keys.is_symlink() or any(keys.iterdir()):
        raise OperatorWorkspaceViolation("operator key directory is not empty")
    created: list[Path] = []
    try:
        for relative in (_DOSSIER_KEY, _BRIDGE_KEY):
            path = _path(target, relative)
            _exclusive_write(path, secrets.token_bytes(32))
            created.append(path)
        _exclusive_write(
            manifest_path,
            json.dumps(_manifest(), ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8"),
        )
        created.append(manifest_path)
        load_operator_dossier_store(target, clock=lambda: int(time.time()))
    except (OSError, OperatorWorkspaceViolation, IntelligenceDossierViolation) as error:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        try:
            keys.rmdir()
            if created_root:
                target.rmdir()
        except OSError:
            pass
        raise OperatorWorkspaceViolation("operator workspace initialization failed") from error
    return {"scope": _SCOPE, "status": "READY", "root": str(target), "reused": False}


def load_operator_dossier_store(
    root: str | Path, *, clock: Callable[[], int] | None = None,
) -> IntelligenceDossierStore:
    """Load a dossier store only from the exact validated local layout."""

    target = Path(root)
    if not target.is_dir() or target.is_symlink():
        raise OperatorWorkspaceViolation("operator workspace is unavailable")
    manifest = _read_manifest(target)
    key_paths = {
        "integrity": _path(target, manifest["dossier_integrity_key"]),
        **{issuer: _path(target, relative) for issuer, relative in manifest["bridge_keys"].items()},
    }
    if any(path.is_symlink() or not path.is_file() for path in key_paths.values()):
        raise OperatorWorkspaceViolation("operator key file is missing or unsafe")
    try:
        keys = {name: path.read_bytes() for name, path in key_paths.items()}
    except OSError as error:
        raise OperatorWorkspaceViolation("operator key file is unreadable") from error
    if any(len(value) != 32 for value in keys.values()):
        raise OperatorWorkspaceViolation("operator key length is invalid")
    store_path = _path(target, manifest["dossier_store"])
    if store_path.is_symlink():
        raise OperatorWorkspaceViolation("dossier store may not be a symbolic link")
    try:
        store = IntelligenceDossierStore(
            store_path,
            integrity_key=keys["integrity"],
            bridge_keys={issuer: keys[issuer] for issuer in manifest["bridge_keys"]},
            clock=clock or (lambda: int(time.time())),
        )
        store.list_dossiers()
    except IntelligenceDossierViolation as error:
        raise OperatorWorkspaceViolation("dossier store failed integrity verification") from error
    return store


def _safe_backup_destination(root: Path, destination: Path) -> None:
    if not destination.name or destination.exists() or destination.is_symlink():
        raise OperatorWorkspaceViolation("backup destination must be a new directory")
    try:
        root_resolved = root.resolve()
        destination_resolved = destination.resolve()
    except OSError as error:
        raise OperatorWorkspaceViolation("backup destination cannot be resolved") from error
    if destination_resolved == root_resolved or destination_resolved.is_relative_to(root_resolved):
        raise OperatorWorkspaceViolation("backup destination must be outside operator state")


def create_operator_data_backup(
    root: str | Path, destination: str | Path, *, clock: Callable[[], int] | None = None,
) -> dict[str, Any]:
    """Copy a verified dossier ledger without copying integrity keys."""

    source_root, target = Path(root), Path(destination)
    store = load_operator_dossier_store(source_root, clock=clock)
    store.list_dossiers()
    _safe_backup_destination(source_root, target)
    now = (clock or (lambda: int(time.time())))()
    if not isinstance(now, int) or isinstance(now, bool) or now < 0:
        raise OperatorWorkspaceViolation("backup clock is invalid")
    dossier_path = source_root / _DOSSIERS
    try:
        dossier_bytes = dossier_path.read_bytes() if dossier_path.exists() else None
    except OSError as error:
        raise OperatorWorkspaceViolation("dossier ledger cannot be read for backup") from error
    store.list_dossiers()
    try:
        confirmed_bytes = dossier_path.read_bytes() if dossier_path.exists() else None
    except OSError as error:
        raise OperatorWorkspaceViolation("dossier ledger cannot be confirmed for backup") from error
    if confirmed_bytes != dossier_bytes:
        raise OperatorWorkspaceViolation("dossier ledger changed during backup")
    manifest = {
        "version": _BACKUP_VERSION,
        "scope": _BACKUP_SCOPE,
        "created_at": now,
        "dossier_present": dossier_bytes is not None,
        "dossier_sha256": sha256(dossier_bytes).hexdigest() if dossier_bytes is not None else None,
        "keys_included": False,
    }
    created: list[Path] = []
    try:
        target.mkdir(parents=True)
        if dossier_bytes is not None:
            backup_dossier = target / _DOSSIERS
            _exclusive_write(backup_dossier, dossier_bytes)
            created.append(backup_dossier)
        backup_manifest = target / _BACKUP_MANIFEST
        _exclusive_write(
            backup_manifest,
            json.dumps(manifest, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8"),
        )
        created.append(backup_manifest)
    except OSError as error:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        try:
            target.rmdir()
        except OSError:
            pass
        raise OperatorWorkspaceViolation("operator data backup failed") from error
    return {
        "scope": _BACKUP_SCOPE,
        "status": "BACKUP_CREATED",
        "destination": str(target),
        "dossier_present": dossier_bytes is not None,
        "keys_included": False,
    }


def restore_operator_data_backup(root: str | Path, backup: str | Path) -> dict[str, Any]:
    """Restore a verified data-only backup without overwriting current data."""

    target_root, source = Path(root), Path(backup)
    load_operator_dossier_store(target_root)
    target_dossier = target_root / _DOSSIERS
    if target_dossier.exists() or target_dossier.is_symlink():
        raise OperatorWorkspaceViolation("restore refuses to overwrite current dossier data")
    if not source.is_dir() or source.is_symlink():
        raise OperatorWorkspaceViolation("backup directory is unavailable or unsafe")
    try:
        if source.resolve() == target_root.resolve() or source.resolve().is_relative_to(target_root.resolve()):
            raise OperatorWorkspaceViolation("backup directory must be outside operator state")
    except OSError as error:
        raise OperatorWorkspaceViolation("backup directory cannot be resolved") from error
    manifest_path = source / _BACKUP_MANIFEST
    if manifest_path.is_symlink():
        raise OperatorWorkspaceViolation("backup manifest may not be a symbolic link")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OperatorWorkspaceViolation("backup manifest is unreadable") from error
    expected_fields = {
        "version", "scope", "created_at", "dossier_present", "dossier_sha256", "keys_included",
    }
    if (
        not isinstance(manifest, dict)
        or set(manifest) != expected_fields
        or manifest["version"] != _BACKUP_VERSION
        or manifest["scope"] != _BACKUP_SCOPE
        or not isinstance(manifest["created_at"], int)
        or isinstance(manifest["created_at"], bool)
        or manifest["created_at"] < 0
        or not isinstance(manifest["dossier_present"], bool)
        or manifest["keys_included"] is not False
    ):
        raise OperatorWorkspaceViolation("backup manifest is incompatible")
    expected_entries = {_BACKUP_MANIFEST}
    if manifest["dossier_present"]:
        expected_entries.add(_DOSSIERS)
    try:
        actual_entries = {item.name for item in source.iterdir()}
    except OSError as error:
        raise OperatorWorkspaceViolation("backup directory cannot be enumerated") from error
    if actual_entries != expected_entries:
        raise OperatorWorkspaceViolation("backup directory contains unexpected content")
    if not manifest["dossier_present"]:
        if manifest["dossier_sha256"] is not None or (source / _DOSSIERS).exists():
            raise OperatorWorkspaceViolation("empty backup has contradictory dossier state")
        return {"scope": _BACKUP_SCOPE, "status": "NO_DATA_TO_RESTORE", "keys_restored": False}
    backup_dossier = source / _DOSSIERS
    if backup_dossier.is_symlink() or not backup_dossier.is_file():
        raise OperatorWorkspaceViolation("backup dossier is missing or unsafe")
    try:
        dossier_bytes = backup_dossier.read_bytes()
    except OSError as error:
        raise OperatorWorkspaceViolation("backup dossier is unreadable") from error
    if (not isinstance(manifest["dossier_sha256"], str)
            or sha256(dossier_bytes).hexdigest() != manifest["dossier_sha256"]):
        raise OperatorWorkspaceViolation("backup dossier digest mismatch")
    try:
        _exclusive_write(target_dossier, dossier_bytes)
        load_operator_dossier_store(target_root)
    except (OSError, OperatorWorkspaceViolation) as error:
        target_dossier.unlink(missing_ok=True)
        raise OperatorWorkspaceViolation("restored dossier failed local key verification") from error
    return {"scope": _BACKUP_SCOPE, "status": "RESTORED", "keys_restored": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "check", "backup", "restore"))
    parser.add_argument("root", type=Path)
    parser.add_argument("destination", type=Path, nargs="?")
    args = parser.parse_args()
    if args.command == "init":
        result = initialize_operator_workspace(args.root)
    elif args.command == "check":
        store = load_operator_dossier_store(args.root)
        result = {"scope": _SCOPE, "status": "READY", "dossier_count": len(store.list_dossiers())}
    elif args.command == "backup":
        if args.destination is None:
            parser.error("backup requires a destination directory")
        result = create_operator_data_backup(args.root, args.destination)
    else:
        if args.destination is None:
            parser.error("restore requires a backup directory")
        result = restore_operator_data_backup(args.root, args.destination)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
