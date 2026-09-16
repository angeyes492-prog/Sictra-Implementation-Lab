"""Offline whole-laboratory data recovery, to its original path, keys external.

Not an encrypted backup or a production anti-rollback anchor. Refuses a running
operations service, existing restore target, changed files and missing keys.
"""
import argparse
from hashlib import sha256
import hmac
import json
from pathlib import Path
import re
import sqlite3
import tempfile
from contextlib import closing

from .operations import OperationsService
from .operations_store import OperationsError, encoded, process_lock
from sictra_block1.operator_pipeline import pipeline_snapshot
from sictra_block1.hn_customs_pipeline import load_hn_customs_pipeline

FIXED = {'operations.sqlite', 'intake.sqlite', 'cases.sqlite',
         'pipeline/pipeline-state.json', 'pipeline/source-control.json',
         'hn-customs/manifest.json'}
OPTIONAL = {'STOP', 'research-intake.json', 'design-console.sqlite', 'launch-paths.json',
            'pipeline/evidence.json', 'pipeline/watchlist.json',
            'pipeline/dossiers.json', 'pipeline/runtime.sqlite3',
            'hn-customs/journal.json'}


def safe(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise OperationsError('RECOVERY_SYMLINK_REJECTED')
    return path


def permitted(name):
    return name in FIXED | OPTIONAL or bool(re.fullmatch(
        r'(?:inbox|dropbox)/[A-Za-z0-9_. -]{1,160}\.xlsx|(?:catalog|hn-customs/sources)/[0-9a-f]{64}\.xlsx', name,
    ))


def content(path):
    path = safe(path)
    with path.open('rb') as stream:
        value = stream.read(32_000_001)
    if len(value) > 32_000_000:
        raise OperationsError('RECOVERY_FILE_LIMIT')
    return value


def keys(root):
    found = {}
    for folder in ('keys', 'pipeline/keys'):
        for path in safe(root / folder).iterdir():
            if not path.is_file() or path.suffix != '.key':
                raise OperationsError('RECOVERY_KEY_INVENTORY_INVALID')
            found[path.relative_to(root).as_posix()] = content(path)
    if 'keys/operations.key' not in found:
        raise OperationsError('RECOVERY_KEYS_MISSING')
    return found


def database_bytes(path):
    # SQLite backup includes committed WAL data; copying the main file does not.
    with tempfile.TemporaryDirectory(prefix='telecare-db-snapshot-') as temp:
        target = Path(temp) / 'snapshot.sqlite'
        with closing(sqlite3.connect(path)) as source, closing(sqlite3.connect(target)) as destination:
            source.backup(destination)
        return content(target)


def backup(root, destination):
    root, destination = safe(root), safe(destination)
    if destination.exists() or destination.is_relative_to(root):
        raise OperationsError('RECOVERY_DESTINATION_REQUIRES_NEW_EXTERNAL_PATH')
    with process_lock(root / 'service.lock'):
        service = OperationsService(root)
        service.snapshot(); pipeline_snapshot(service.pipeline)
        load_hn_customs_pipeline(service.hn_pipeline, key=service.hn_key).snapshot()
        material = keys(root)
        names = set(FIXED) | {name for name in OPTIONAL if (root / name).is_file()}
        for folder in ('inbox', 'dropbox', 'catalog'):
            for path in safe(root / folder).iterdir():
                name = path.relative_to(root).as_posix()
                if not permitted(name) or not path.is_file():
                    raise OperationsError('RECOVERY_UNEXPECTED_INPUT')
                names.add(name)
        for path in safe(root / 'hn-customs' / 'sources').iterdir():
            name = path.relative_to(root).as_posix()
            if not permitted(name) or not path.is_file():
                raise OperationsError('RECOVERY_UNEXPECTED_INPUT')
            names.add(name)
        if len(names) > 1024:
            raise OperationsError('RECOVERY_FILE_COUNT_LIMIT')
        original = {name: content(root / name) for name in sorted(names)}
        payload = {name: database_bytes(root / name) if name.endswith(('.sqlite','.sqlite3')) else value
                   for name, value in original.items()}
        if sum(map(len, payload.values())) > 256_000_000:
            raise OperationsError('RECOVERY_TOTAL_LIMIT')
        manifest = {'version': 1, 'scope': 'OFFLINE_LABORATORY_DATA_ORIGINAL_PATH',
            'root': str(root), 'keys_included': False, 'publication': 'BLOCKED',
            'files': {n: sha256(v).hexdigest() for n, v in payload.items()},
            'keys': {n: sha256(v).hexdigest() for n, v in material.items()}}
        # All writers must be stopped; detect incidental concurrent edits too.
        if any(content(root / n) != v for n, v in original.items()):
            raise OperationsError('RECOVERY_SOURCE_CHANGED')
        manifest['signature'] = hmac.new(material['keys/operations.key'], encoded(manifest), 'sha256').hexdigest()
        destination.mkdir(parents=True, exist_ok=False)
        for name, value in payload.items():
            target = destination / 'data' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream: stream.write(value)
        with (destination / 'manifest.json').open('xb') as stream: stream.write(encoded(manifest))
        return {'scope': manifest['scope'], 'files': len(payload), 'keys_included': False}


def restore(archive, destination, key_source):
    archive, destination, key_source = safe(archive), safe(destination), safe(key_source)
    if destination.exists():
        raise OperationsError('RECOVERY_TARGET_EXISTS')
    manifest = json.loads(content(archive / 'manifest.json'))
    signature = manifest.pop('signature', None)
    material = keys(key_source)
    expected = hmac.new(material['keys/operations.key'], encoded(manifest), 'sha256').hexdigest()
    if not isinstance(signature, str) or not hmac.compare_digest(signature, expected):
        raise OperationsError('RECOVERY_SIGNATURE_INVALID')
    if (manifest.get('version') != 1 or manifest.get('scope') != 'OFFLINE_LABORATORY_DATA_ORIGINAL_PATH'
            or manifest.get('root') != str(destination) or manifest.get('keys_included') is not False
            or manifest.get('publication') != 'BLOCKED'
            or manifest.get('keys') != {n: sha256(v).hexdigest() for n, v in material.items()}):
        raise OperationsError('RECOVERY_IDENTITY_MISMATCH')
    declared = manifest.get('files')
    if not isinstance(declared, dict) or not FIXED <= declared.keys() or len(declared) > 1024 or not all(permitted(n) for n in declared):
        raise OperationsError('RECOVERY_INVENTORY_INVALID')
    payload = {name: content(archive / 'data' / name) for name in declared}
    if sum(map(len, payload.values())) > 256_000_000 or any(sha256(v).hexdigest() != declared[n] for n, v in payload.items()):
        raise OperationsError('RECOVERY_DATA_CHANGED')
    # No writes before signature, complete data and external keys are verified.
    destination.mkdir(parents=True, exist_ok=False)
    (destination / 'STOP').write_text('RECOVERY_PENDING', encoding='ascii')
    for name, value in {**payload, **material}.items():
        if name == 'STOP':
            continue  # Retain the fail-closed recovery marker.
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream: stream.write(value)
    for name in ('inbox', 'dropbox', 'backups', 'catalog'):
        (destination / name).mkdir(exist_ok=True)
    (destination / 'hn-customs' / 'sources').mkdir(parents=True, exist_ok=True)
    service = OperationsService(destination)
    service.snapshot(); pipeline_snapshot(service.pipeline)
    load_hn_customs_pipeline(service.hn_pipeline, key=service.hn_key).snapshot()
    service.set_paused(True)  # Recovery never implicitly resumes processing.
    service.store.put('RECOVERY', sha256(encoded(manifest)).hexdigest(),
                      {'scope': manifest['scope'], 'state': 'RESTORED_PAUSED', 'publication': 'BLOCKED'}, immutable=True)
    if 'STOP' not in payload:
        (destination / 'STOP').unlink()
    return {'scope': manifest['scope'], 'status': 'RESTORED_PAUSED', 'publication': 'BLOCKED'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('backup', 'restore'))
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--key-source', type=Path)
    args = parser.parse_args()
    if args.action == 'restore' and args.key_source is None:
        parser.error('restore requires --key-source retained separately')
    print(json.dumps(backup(args.state, args.archive) if args.action == 'backup'
        else restore(args.archive, args.state, args.key_source)))


if __name__ == '__main__': main()
