"""Local operator-state initialization without placing integrity keys in Git."""

from __future__ import annotations

import argparse
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "check"))
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    if args.command == "init":
        result = initialize_operator_workspace(args.root)
    else:
        store = load_operator_dossier_store(args.root)
        result = {"scope": _SCOPE, "status": "READY", "dossier_count": len(store.list_dossiers())}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
