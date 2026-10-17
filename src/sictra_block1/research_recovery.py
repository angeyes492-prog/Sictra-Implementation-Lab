"""Offline known-byte recovery of Eurostat candidates; never source admission."""
import argparse
import ctypes
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time

from .research_acquisition import (
    BOUNDARY, MAX_FILE, MAX_SESSION, ResearchAcquisitionError, ResearchQuarantine, canonical,
)


class ResearchRecoveryError(ResearchAcquisitionError):
    pass


def _identity(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ResearchRecoveryError("RECOVERY_ID_INVALID")
    return value


def _path(value):
    path = Path(os.path.abspath(value))
    for part in (path, *path.parents):
        try:
            # Covers Windows junctions on supported Python 3.11 as well as symlinks.
            reparse = getattr(part.lstat(), "st_file_attributes", 0) & 0x400
        except FileNotFoundError:
            reparse = False
        if part.is_symlink() or reparse:
            raise ResearchRecoveryError("RECOVERY_LINK_REJECTED")
    return path


def _bytes(path, limit):
    path = _path(path)
    if not path.is_file():
        raise ResearchRecoveryError("RECOVERY_FILE_MISSING")
    with path.open("rb") as stream:
        value = stream.read(limit + 1)
    if len(value) > limit:
        raise ResearchRecoveryError("RECOVERY_SIZE_EXCEEDED")
    return value


def _json(value):
    def unique(pairs):
        result = {}
        for k, v in pairs:
            if k in result:
                raise ResearchRecoveryError("RECOVERY_DUPLICATE_FIELD")
            result[k] = v
        return result
    try:
        return json.loads(value, object_pairs_hook=unique)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ResearchRecoveryError("RECOVERY_JSON_INVALID") from error


def _selection(values):
    if (not isinstance(values, list) or not 1 <= len(values) <= 100
            or any(not isinstance(v, str) for v in values) or len(set(values)) != len(values)):
        raise ResearchRecoveryError("RECOVERY_SELECTION_INVALID")
    return sorted(_identity(v) for v in values)


class _MemoryQuarantine(ResearchQuarantine):
    """Validate bounded immutable snapshots using the existing admission boundary."""
    def __init__(self, records):
        self.records = records

    def read(self, candidate_id, *, now, expected_recipe=None):
        _identity(candidate_id)
        if type(now) is not int or now < 0 or candidate_id not in self.records:
            raise ResearchRecoveryError("RECOVERY_DEPENDENCY_INVALID")
        descriptor, content = self.records[candidate_id]
        # Terms cannot link to another candidate, avoiding cyclic malicious records.
        if expected_recipe is not None and descriptor.get("recipe") != expected_recipe:
            raise ResearchRecoveryError("RECOVERY_DEPENDENCY_INVALID")
        self._validate(candidate_id, descriptor, content, now=now, expected_recipe=expected_recipe)
        return descriptor, content


def _snapshot(root, selected):
    root = _path(root)
    if not root.is_dir():
        raise ResearchRecoveryError("RECOVERY_SOURCE_MISSING")
    pending, records, files, total = list(selected), {}, {}, 0
    while pending:
        identity = _identity(pending.pop())
        if identity in records:
            continue
        if len(records) >= 100:
            raise ResearchRecoveryError("RECOVERY_CANDIDATE_BUDGET")
        directory = _path(root / identity)
        if not directory.is_dir() or {p.name for p in directory.iterdir()} != {"manifest.json", "content.bin"}:
            raise ResearchRecoveryError("RECOVERY_INVENTORY_INVALID")
        raw = _bytes(directory / "manifest.json", 16000)
        body = _bytes(directory / "content.bin", MAX_FILE)
        total += len(raw) + len(body)
        if total > MAX_SESSION:
            raise ResearchRecoveryError("RECOVERY_BYTE_BUDGET")
        descriptor = _json(raw)
        if not isinstance(descriptor, dict):
            raise ResearchRecoveryError("RECOVERY_DESCRIPTOR_INVALID")
        records[identity] = (descriptor, body)
        files[f"{identity}/manifest.json"] = raw
        files[f"{identity}/content.bin"] = body
        if descriptor.get("terms_candidate_id") is not None:
            pending.append(_identity(descriptor["terms_candidate_id"]))
    reader = _MemoryQuarantine(records)
    for identity, (descriptor, _) in records.items():
        reader.read(identity, now=descriptor.get("acquired_at"))
    return files


def _clock(clock):
    value = int(clock())
    if value < 0:
        raise ResearchRecoveryError("RECOVERY_CLOCK_INVALID")
    return value


def _destination(source, value):
    source, target = _path(source), _path(value)
    if target.exists() or not target.parent.is_dir():
        raise ResearchRecoveryError("RECOVERY_DESTINATION_NOT_NEW")
    if source == target or source in target.parents or target in source.parents:
        raise ResearchRecoveryError("RECOVERY_PATH_OVERLAP")
    return target


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _publish(stage, destination):
    _path(stage)
    _path(destination)
    if os.name == "nt":
        # Windows rename refuses an existing directory (including a concurrent one).
        os.rename(stage, destination)
    elif sys.platform.startswith("linux"):
        # POSIX rename alone may overwrite an empty target; use no-replace semantics.
        library = ctypes.CDLL(None, use_errno=True)
        rename = library.renameat2
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        if rename(-100, os.fsencode(stage), -100, os.fsencode(destination), 1):
            raise OSError(ctypes.get_errno(), "recovery publication failed")
    else:
        raise ResearchRecoveryError("RECOVERY_PLATFORM_UNSUPPORTED")


def _cleanup(stage):
    original = sys.exception()
    try:
        shutil.rmtree(_path(stage))
    except (OSError, ResearchAcquisitionError) as error:
        # Preserve the primary failure as cause and identify unpublished residual data.
        raise ResearchRecoveryError(f"RECOVERY_CLEANUP_FAILED: unpublished stage {stage}") from (original or error)


def _archive(archive, digest):
    archive = _path(archive)
    _identity(digest)
    raw = _bytes(archive / "archive-manifest.json", 128 * 1024)
    if sha256(raw).hexdigest() != digest:
        raise ResearchRecoveryError("RECOVERY_MANIFEST_DIGEST_MISMATCH")
    manifest = _json(raw)
    if (not isinstance(manifest, dict)
            or set(manifest) != {"version", "scope", "created_at", "selected_ids", "candidate_ids", "files", "boundary"}
            or manifest["version"] != "0.1.0" or manifest["scope"] != "RESEARCH_QUARANTINE_DATA_ONLY"
            or manifest["boundary"] != BOUNDARY or type(manifest["created_at"]) is not int
            or manifest["created_at"] < 0 or canonical(manifest) != raw):
        raise ResearchRecoveryError("RECOVERY_MANIFEST_INVALID")
    selected = _selection(manifest["selected_ids"])
    candidates = _selection(manifest["candidate_ids"])
    if selected != manifest["selected_ids"] or candidates != manifest["candidate_ids"]:
        raise ResearchRecoveryError("RECOVERY_ORDER_INVALID")
    if {p.name for p in archive.iterdir()} != {"archive-manifest.json", "data"}:
        raise ResearchRecoveryError("RECOVERY_INVENTORY_INVALID")
    data = _path(archive / "data")
    if not data.is_dir() or sorted(p.name for p in data.iterdir()) != candidates:
        raise ResearchRecoveryError("RECOVERY_INVENTORY_INVALID")
    files = _snapshot(data, selected)
    if (sorted({p.split("/")[0] for p in files}) != candidates
            or manifest["files"] != {p: sha256(b).hexdigest() for p, b in files.items()}
            or sum(map(len, files.values())) + len(raw) > MAX_SESSION
            or any(_json(b)["acquired_at"] > manifest["created_at"]
                   for p, b in files.items() if p.endswith("manifest.json"))):
        raise ResearchRecoveryError("RECOVERY_ARCHIVE_INTEGRITY_INVALID")
    return raw, files


def backup(quarantine, candidate_ids, destination, *, clock=time.time):
    stage = None
    try:
        selected = _selection(candidate_ids)
        target = _destination(quarantine.root, destination)
        files = _snapshot(quarantine.root, selected)
        raw = canonical({"version": "0.1.0", "scope": "RESEARCH_QUARANTINE_DATA_ONLY",
            "created_at": _clock(clock), "selected_ids": selected,
            "candidate_ids": sorted({p.split("/")[0] for p in files}),
            "files": {p: sha256(b).hexdigest() for p, b in files.items()}, "boundary": BOUNDARY})
        digest = sha256(raw).hexdigest()
        stage = Path(tempfile.mkdtemp(prefix=".research-recovery-", dir=target.parent))
        _write(stage / "archive-manifest.json", raw)
        for path, value in files.items():
            _write(stage / "data" / path, value)
        _archive(stage, digest)
        if _snapshot(quarantine.root, selected) != files:
            raise ResearchRecoveryError("RECOVERY_SOURCE_CHANGED")
        _publish(stage, target)
        stage = None
        return {"archive": str(target), "manifest_sha256": digest,
            "candidate_count": len(files) // 2, "retained_bytes": sum(map(len, files.values())),
            "scope": "RESEARCH_QUARANTINE_DATA_ONLY", **BOUNDARY}
    except ResearchAcquisitionError as error:
        raise ResearchRecoveryError(str(error)) from error
    except (OSError, ValueError, TypeError, AttributeError) as error:
        raise ResearchRecoveryError("RECOVERY_BACKUP_FAILED") from error
    finally:
        if stage is not None:
            _cleanup(stage)


def restore(archive, destination, *, expected_manifest_sha256, clock=time.time):
    stage = None
    try:
        target = _destination(archive, destination)
        raw, files = _archive(archive, expected_manifest_sha256)
        if _json(raw)["created_at"] > _clock(clock):
            raise ResearchRecoveryError("RECOVERY_ARCHIVE_FUTURE")
        stage = Path(tempfile.mkdtemp(prefix=".research-recovery-", dir=target.parent))
        for path, value in files.items():
            _write(stage / path, value)
        selected = _json(raw)["selected_ids"]
        if _snapshot(stage, selected) != files or _archive(archive, expected_manifest_sha256) != (raw, files):
            raise ResearchRecoveryError("RECOVERY_SOURCE_CHANGED")
        _publish(stage, target)
        stage = None
        return {"destination": str(target), "manifest_sha256": expected_manifest_sha256,
            "candidate_count": len(files) // 2, "scope": "RESEARCH_QUARANTINE_DATA_ONLY", **BOUNDARY}
    except ResearchAcquisitionError as error:
        raise ResearchRecoveryError(str(error)) from error
    except (OSError, ValueError, TypeError, AttributeError) as error:
        raise ResearchRecoveryError("RECOVERY_RESTORE_FAILED") from error
    finally:
        if stage is not None:
            _cleanup(stage)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("backup")
    create.add_argument("--root", type=Path, required=True)
    create.add_argument("--candidate-id", action="append", required=True)
    create.add_argument("--destination", type=Path, required=True)
    recover = commands.add_parser("restore")
    recover.add_argument("--archive", type=Path, required=True)
    recover.add_argument("--destination", type=Path, required=True)
    recover.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "backup":
            if not _path(args.root).is_dir():
                raise ResearchRecoveryError("RECOVERY_SOURCE_MISSING")
            result = backup(ResearchQuarantine(args.root), args.candidate_id, args.destination)
        else:
            result = restore(args.archive, args.destination, expected_manifest_sha256=args.manifest_sha256)
    except ResearchRecoveryError as error:
        parser.exit(2, f"{error}\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
