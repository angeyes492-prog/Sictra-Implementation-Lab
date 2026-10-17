"""Offline exact seven-recipe recovery; no authority or expiry renewal."""
import argparse
from hashlib import sha256
from http.client import HTTPException
import json
from pathlib import Path
import tempfile
import time

from .common import ContractViolation
from .research_acquisition import canonical, MAX_FILE, MAX_SESSION
from .research_collection import BOUNDARY, SCOPE as LAB_SCOPE, EURO_RECIPES, STATBEL_RECIPES, _validate_manifest
from .research_statbel import StatbelResearchQuarantine
from .research_review import ResearchReview
from .research_same_chain import SameChainReview
from .research_recovery import (
    ResearchRecoveryError, _MemoryQuarantine, _path, _identity, _bytes, _json,
    _destination, _write, _publish, _cleanup,
)

SCOPE = 'RESEARCH_COLLECTION_DATA_ONLY_V1'


class _MemoryStatbel(_MemoryQuarantine, StatbelResearchQuarantine):
    """Reuse Statbel validation, with inherited immutable-snapshot reads."""


def _clock(clock):
    value = clock()
    if type(value) is not int or value < 0:
        raise ResearchRecoveryError('COLLECTION_RECOVERY_CLOCK_INVALID')
    return value


def _snapshot(root, selection_id, *, exact=False):
    root, selection_id = _path(root), _identity(selection_id)
    if not root.is_dir():
        raise ResearchRecoveryError('COLLECTION_RECOVERY_SOURCE_MISSING')
    selection_path = f'selections/{selection_id}/selection.json'
    files = {selection_path: _bytes(root / selection_path, 32768),
             'cycle-start.json': _bytes(root / 'cycle-start.json', 16384),
             'cycle-outcome.json': _bytes(root / 'cycle-outcome.json', 16384)}
    manifest = _json(files[selection_path])
    _validate_manifest(manifest)
    if canonical(manifest) != files[selection_path] or sha256(files[selection_path]).hexdigest() != selection_id:
        raise ResearchRecoveryError('COLLECTION_RECOVERY_SELECTION_INVALID')
    marker, outcome = _json(files['cycle-start.json']), _json(files['cycle-outcome.json'])
    if (not isinstance(marker, dict) or set(marker) != {'version', 'started_at', 'scope', 'budget_before', 'boundary'}
            or marker['version'] != '0.1.0' or marker['scope'] != LAB_SCOPE
            or type(marker['started_at']) is not int or marker['started_at'] != manifest['started_at']
            or canonical(marker['boundary']) != canonical(BOUNDARY)
            or canonical(marker) != files['cycle-start.json']
            or canonical(outcome) != files['cycle-outcome.json']
            or canonical(outcome) != canonical({'state': 'COLLECTED', 'selection_id': selection_id,
                                                'budget': manifest['budget'], 'boundary': BOUNDARY})):
        raise ResearchRecoveryError('COLLECTION_RECOVERY_COMMIT_INVALID')
    before = marker['budget_before']
    if (not isinstance(before, dict) or set(before) != {'attempts', 'received_bytes'}
            or any(type(v) is not int or v < 0 for v in before.values())
            or manifest['budget']['attempts'] != before['attempts'] + 7):
        raise ResearchRecoveryError('COLLECTION_RECOVERY_BUDGET_INVALID')
    euro, statbel = {}, {}
    body_bytes = 0
    for recipe, selected in manifest['candidates'].items():
        owner = 'eurostat' if recipe in EURO_RECIPES else 'statbel'
        identity = selected['candidate_id']
        slot = _path(root / owner / identity)
        if not slot.is_dir() or {p.name for p in slot.iterdir()} != {'manifest.json', 'content.bin'}:
            raise ResearchRecoveryError('COLLECTION_RECOVERY_INVENTORY_INVALID')
        descriptor_raw = _bytes(slot / 'manifest.json', 16384)
        content = _bytes(slot / 'content.bin', MAX_FILE)
        descriptor = _json(descriptor_raw)
        if not isinstance(descriptor, dict) or canonical(descriptor) != descriptor_raw:
            raise ResearchRecoveryError('COLLECTION_RECOVERY_DESCRIPTOR_INVALID')
        files[f'{owner}/{identity}/manifest.json'] = descriptor_raw
        files[f'{owner}/{identity}/content.bin'] = content
        body_bytes += len(content)
        if sum(map(len, files.values())) > MAX_SESSION:
            raise ResearchRecoveryError('COLLECTION_RECOVERY_BYTE_BUDGET')
        records = euro if owner == 'eurostat' else statbel
        records[identity] = (descriptor, content)
    if len(files) != 17 or before['received_bytes'] + body_bytes != manifest['budget']['received_bytes']:
        raise ResearchRecoveryError('COLLECTION_RECOVERY_BUDGET_INVALID')
    readers = {'eurostat': _MemoryQuarantine(euro), 'statbel': _MemoryStatbel(statbel)}
    expires = []
    for recipe, selected in manifest['candidates'].items():
        recipes = EURO_RECIPES if recipe in EURO_RECIPES else STATBEL_RECIPES
        owner = 'eurostat' if recipe in EURO_RECIPES else 'statbel'
        descriptor, _ = readers[owner].read(selected['candidate_id'], now=manifest['created_at'], expected_recipe=recipe)
        terms_id = None if recipe == recipes[0] else manifest['candidates'][recipes[0]]['candidate_id']
        if descriptor['terms_candidate_id'] != terms_id or descriptor['content_sha256'] != selected['content_sha256']:
            raise ResearchRecoveryError('COLLECTION_RECOVERY_LINEAGE_INVALID')
        if not manifest['started_at'] <= descriptor['acquired_at'] <= manifest['created_at']:
            raise ResearchRecoveryError('COLLECTION_RECOVERY_CHRONOLOGY_INVALID')
        expires.append(descriptor['expires_at'])
    if manifest['expires_at'] != min(expires):
        raise ResearchRecoveryError('COLLECTION_RECOVERY_EXPIRY_INVALID')
    ids = {recipe: selected['candidate_id'] for recipe, selected in manifest['candidates'].items()}
    historical_clock = lambda: manifest['created_at']
    # Parse only immutable bounded copies, never reread a growing source file.
    ResearchReview(readers['eurostat'], ids[EURO_RECIPES[4]], ids[EURO_RECIPES[1]],
        national_id=ids[EURO_RECIPES[2]], regional_id=ids[EURO_RECIPES[3]], clock=historical_clock).read()
    SameChainReview(readers['eurostat'], ids[EURO_RECIPES[4]], readers['statbel'],
                    ids[STATBEL_RECIPES[1]], clock=historical_clock).read()
    if exact:
        # Bounded-depth inventory: no arbitrary recursive traversal of an archive.
        wanted = {'eurostat', 'statbel', 'selections', 'cycle-start.json', 'cycle-outcome.json'}
        if {p.name for p in root.iterdir()} != wanted:
            raise ResearchRecoveryError('COLLECTION_RECOVERY_INVENTORY_INVALID')
        for owner, records in (('eurostat', euro), ('statbel', statbel)):
            if {p.name for p in _path(root / owner).iterdir()} != set(records):
                raise ResearchRecoveryError('COLLECTION_RECOVERY_INVENTORY_INVALID')
        if ({p.name for p in _path(root / 'selections').iterdir()} != {selection_id}
                or {p.name for p in _path(root / 'selections' / selection_id).iterdir()} != {'selection.json'}):
            raise ResearchRecoveryError('COLLECTION_RECOVERY_INVENTORY_INVALID')
    return files, manifest


def _archive(root, digest):
    root, digest = _path(root), _identity(digest)
    raw = _bytes(root / 'archive-manifest.json', 128 * 1024)
    if sha256(raw).hexdigest() != digest:
        raise ResearchRecoveryError('COLLECTION_RECOVERY_DIGEST_MISMATCH')
    manifest = _json(raw)
    if (not isinstance(manifest, dict) or set(manifest) != {'version', 'scope', 'created_at', 'selection_id', 'files', 'boundary'}
            or manifest['version'] != '0.1.0' or manifest['scope'] != SCOPE
            or type(manifest['created_at']) is not int or manifest['created_at'] < 0
            or canonical(manifest['boundary']) != canonical(BOUNDARY) or canonical(manifest) != raw
            or {p.name for p in root.iterdir()} != {'archive-manifest.json', 'data'}):
        raise ResearchRecoveryError('COLLECTION_RECOVERY_ARCHIVE_INVALID')
    files, selection = _snapshot(root / 'data', manifest['selection_id'], exact=True)
    if (canonical(manifest['files']) != canonical({p: sha256(b).hexdigest() for p, b in files.items()})
            or selection['created_at'] > manifest['created_at']
            or sum(map(len, files.values())) + len(raw) > MAX_SESSION):
        raise ResearchRecoveryError('COLLECTION_RECOVERY_ARCHIVE_INVALID')
    return raw, files, selection


def _receipt(destination, digest, selection_id):
    return {'destination': str(destination), 'manifest_sha256': digest, 'selection_id': selection_id,
            'file_count': 17, 'candidate_count': 7, 'scope': SCOPE,
            'evidence_state': 'HISTORICAL_CONTEXT_ONLY', **BOUNDARY}


def backup_collection(root, selection_id, destination, *, clock=lambda: int(time.time())):
    stage = None
    try:
        started = _clock(clock)
        target = _destination(root, destination)
        files, selection = _snapshot(root, selection_id)
        if selection['created_at'] > started:
            raise ResearchRecoveryError('COLLECTION_RECOVERY_CLOCK_ROLLBACK')
        raw = canonical({'version': '0.1.0', 'scope': SCOPE, 'created_at': started,
            'selection_id': selection_id, 'files': {p: sha256(b).hexdigest() for p, b in files.items()}, 'boundary': BOUNDARY})
        digest = sha256(raw).hexdigest()
        stage = Path(tempfile.mkdtemp(prefix='.collection-recovery-', dir=target.parent))
        _write(stage / 'archive-manifest.json', raw)
        for path, data in files.items():
            _write(stage / 'data' / path, data)
        _archive(stage, digest)
        if _snapshot(root, selection_id) != (files, selection) or _clock(clock) < started:
            raise ResearchRecoveryError('COLLECTION_RECOVERY_INPUT_CHANGED')
        _publish(stage, target)
        stage = None
        return _receipt(target, digest, selection_id)
    except ResearchRecoveryError:
        raise
    except (ContractViolation, OSError, ValueError, TypeError, AttributeError, RecursionError,
            AssertionError, HTTPException) as error:
        raise ResearchRecoveryError('COLLECTION_RECOVERY_BACKUP_FAILED') from error
    finally:
        if stage is not None:
            _cleanup(stage)


def restore_collection(archive, destination, *, expected_manifest_sha256, clock=lambda: int(time.time())):
    stage = None
    try:
        started = _clock(clock)
        target = _destination(archive, destination)
        raw, files, selection = _archive(archive, expected_manifest_sha256)
        if _json(raw)['created_at'] > started:
            raise ResearchRecoveryError('COLLECTION_RECOVERY_ARCHIVE_FUTURE')
        stage = Path(tempfile.mkdtemp(prefix='.collection-recovery-', dir=target.parent))
        for path, data in files.items():
            _write(stage / path, data)
        if (_snapshot(stage, _json(raw)['selection_id'], exact=True) != (files, selection)
                or _archive(archive, expected_manifest_sha256) != (raw, files, selection)
                or _clock(clock) < started):
            raise ResearchRecoveryError('COLLECTION_RECOVERY_INPUT_CHANGED')
        _publish(stage, target)
        stage = None
        return _receipt(target, expected_manifest_sha256, _json(raw)['selection_id'])
    except ResearchRecoveryError:
        raise
    except (ContractViolation, OSError, ValueError, TypeError, AttributeError, RecursionError,
            AssertionError, HTTPException) as error:
        raise ResearchRecoveryError('COLLECTION_RECOVERY_RESTORE_FAILED') from error
    finally:
        if stage is not None:
            _cleanup(stage)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    create = commands.add_parser('backup')
    create.add_argument('--root', required=True)
    create.add_argument('--selection-id', required=True)
    create.add_argument('--destination', required=True)
    recover = commands.add_parser('restore')
    recover.add_argument('--archive', required=True)
    recover.add_argument('--destination', required=True)
    recover.add_argument('--manifest-sha256', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'backup':
            result = backup_collection(args.root, args.selection_id, args.destination)
        else:
            result = restore_collection(args.archive, args.destination, expected_manifest_sha256=args.manifest_sha256)
    except ResearchRecoveryError as error:
        parser.exit(2, f'{error}\n')
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
