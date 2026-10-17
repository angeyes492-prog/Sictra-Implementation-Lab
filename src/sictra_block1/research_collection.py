"""Finite agent-operated collection; not an installed autonomous source adapter."""
import argparse
from hashlib import sha256
from http.client import HTTPException
import json
import socket
import tempfile
import time

from .research_acquisition import (
    MAX_SESSION, ResearchAcquirer, ResearchQuarantine, ResearchAcquisitionError,
    SessionBudget, canonical, pinned_response,
)
from .research_statbel import StatbelResearchAcquirer, StatbelResearchQuarantine
from .research_review import ResearchReview
from .research_same_chain import SameChainReview
from .research_recovery import _path, _identity, _bytes, _json, _write, _publish, _cleanup

EURO_RECIPES = ('EUROSTAT_REUSE_NOTICE', 'EUROSTAT_MAR_METADATA',
    'EUROSTAT_BE_MAR_METADATA', 'EUROSTAT_REGIONAL_MAR_METADATA', 'EUROSTAT_MAR_BE_2023_2024')
STATBEL_RECIPES = ('STATBEL_CC_BY_4_0', 'STATBEL_BE_SEA_TRANSPORT_HTML')
RECIPES = EURO_RECIPES + STATBEL_RECIPES
BOUNDARY = {'admission': 'NOT_ADMITTED', 'resolution': 'NOT_RESOLVED',
    'acceptance': 'NOT_ACCEPTED', 'runtime_effect': 'NONE', 'publication': 'BLOCKED'}
SCOPE = 'LABORATORY_INTERNAL_SUPERVISED'


def _time(clock):
    value = clock()
    if type(value) is not int or value < 0:
        raise ResearchAcquisitionError('COLLECTION_CLOCK_INVALID')
    return value


def _budget(budget):
    return {'attempts': budget.attempts, 'received_bytes': budget.received_bytes}


def _validate_manifest(value):
    if (not isinstance(value, dict) or set(value) != {'version', 'scope', 'started_at',
            'created_at', 'expires_at', 'candidates', 'budget', 'boundary'}
            or value['version'] != '0.1.0' or value['scope'] != SCOPE
            or value['boundary'] != BOUNDARY
            or any(type(value[k]) is not int for k in ('started_at', 'created_at', 'expires_at'))
            or not 0 <= value['started_at'] <= value['created_at'] < value['expires_at']
            or not isinstance(value['candidates'], dict) or set(value['candidates']) != set(RECIPES)
            or not isinstance(value['budget'], dict)
            or set(value['budget']) != {'attempts', 'received_bytes'}
            or any(type(v) is not int for v in value['budget'].values())
            or not 7 <= value['budget']['attempts'] <= 100
            or not 0 < value['budget']['received_bytes'] <= MAX_SESSION):
        raise ResearchAcquisitionError('COLLECTION_SELECTION_INVALID')
    for candidate in value['candidates'].values():
        if not isinstance(candidate, dict) or set(candidate) != {'candidate_id', 'content_sha256'}:
            raise ResearchAcquisitionError('COLLECTION_SELECTION_INVALID')
        _identity(candidate['candidate_id'])
        _identity(candidate['content_sha256'])


def _reviews(root, manifest, clock):
    now = _time(clock)
    if not manifest['created_at'] <= now < manifest['expires_at']:
        raise ResearchAcquisitionError('COLLECTION_NOT_CURRENT')
    roots = {recipe: _path(root / ('eurostat' if recipe in EURO_RECIPES else 'statbel'))
             for recipe in RECIPES}
    if any(not path.is_dir() for path in roots.values()):
        raise ResearchAcquisitionError('COLLECTION_QUARANTINE_MISSING')
    # Fence every selected path before inherited readers traverse its rights links.
    for recipe, candidate in manifest['candidates'].items():
        slot = _path(roots[recipe] / candidate['candidate_id'])
        _path(slot / 'manifest.json')
        _path(slot / 'content.bin')
    euro, statbel = ResearchQuarantine(root / 'eurostat'), StatbelResearchQuarantine(root / 'statbel')
    records = {}
    for recipe, selected in manifest['candidates'].items():
        quarantine = euro if recipe in EURO_RECIPES else statbel
        expected_terms = (None if recipe in (EURO_RECIPES[0], STATBEL_RECIPES[0]) else
            manifest['candidates'][EURO_RECIPES[0] if recipe in EURO_RECIPES else
                                   STATBEL_RECIPES[0]]['candidate_id'])
        retained_descriptor = _json(_bytes(roots[recipe] / selected['candidate_id'] / 'manifest.json', 32768))
        if not isinstance(retained_descriptor, dict) or retained_descriptor.get('terms_candidate_id') != expected_terms:
            raise ResearchAcquisitionError('COLLECTION_RIGHTS_MISMATCH')
        descriptor, _ = quarantine.read(selected['candidate_id'], now=now, expected_recipe=recipe)
        if descriptor['content_sha256'] != selected['content_sha256']:
            raise ResearchAcquisitionError('COLLECTION_HASH_MISMATCH')
        if descriptor['terms_candidate_id'] != expected_terms:
            raise ResearchAcquisitionError('COLLECTION_RIGHTS_MISMATCH')
        records[recipe] = descriptor
    if manifest['expires_at'] != min(record['expires_at'] for record in records.values()):
        raise ResearchAcquisitionError('COLLECTION_EXPIRY_MISMATCH')
    ids = {recipe: entry['candidate_id'] for recipe, entry in manifest['candidates'].items()}
    research = ResearchReview(euro, ids[EURO_RECIPES[4]], ids[EURO_RECIPES[1]],
        national_id=ids[EURO_RECIPES[2]], regional_id=ids[EURO_RECIPES[3]], clock=clock)
    comparison = SameChainReview(euro, ids[EURO_RECIPES[4]], statbel,
                                ids[STATBEL_RECIPES[1]], clock=clock)
    review, compared = research.read(), comparison.read()
    research.verify_current(review)
    comparison.verify_current(compared)
    final = _time(clock)
    if not now <= review['checked_at'] <= final < manifest['expires_at'] or not now <= compared['checked_at'] <= final:
        raise ResearchAcquisitionError('COLLECTION_CLOCK_REGRESSED_OR_EXPIRED')
    report = {'version': '0.1.0', 'scope': SCOPE, 'selection': manifest,
        'selection_id': sha256(canonical(manifest)).hexdigest(), 'checked_at': final,
        'expires_at': manifest['expires_at'], 'budget': manifest['budget'],
        'research': review, 'comparison': compared, **BOUNDARY}
    report['fingerprint'] = sha256(canonical(report)).hexdigest()
    return report


def _read_selection(root, selection_id, clock):
    root, identity = _path(root), _identity(selection_id)
    if not root.is_dir():
        raise ResearchAcquisitionError('COLLECTION_ROOT_MISSING')
    slot = _path(root / 'selections' / identity)
    if not slot.is_dir() or {p.name for p in slot.iterdir()} != {'selection.json'}:
        raise ResearchAcquisitionError('COLLECTION_SELECTION_MISSING_OR_EXTRA_FILES')
    raw = _bytes(slot / 'selection.json', 32 * 1024)
    if sha256(raw).hexdigest() != identity:
        raise ResearchAcquisitionError('COLLECTION_SELECTION_HASH_MISMATCH')
    manifest = _json(raw)
    _validate_manifest(manifest)
    if canonical(manifest) != raw:
        raise ResearchAcquisitionError('COLLECTION_SELECTION_NONCANONICAL')
    try:
        report = _reviews(root, manifest, clock)
    except (AssertionError, HTTPException) as error:
        raise ResearchAcquisitionError('COLLECTION_SOURCE_PARSE_FAILED') from error
    if _bytes(slot / 'selection.json', 32 * 1024) != raw:
        raise ResearchAcquisitionError('COLLECTION_SELECTION_CHANGED')
    final = _time(clock)
    if not report['checked_at'] <= final < report['expires_at']:
        raise ResearchAcquisitionError('COLLECTION_NOT_CURRENT')
    return report


def _committed(root, report):
    expected = {'state': 'COLLECTED', 'selection_id': report['selection_id'],
                'budget': report['budget'], 'boundary': BOUNDARY}
    try:
        raw = _bytes(_path(root) / 'cycle-outcome.json', 16 * 1024)
        if canonical(expected) != raw:
            raise ResearchAcquisitionError('COLLECTION_COMMIT_MISMATCH')
    except (OSError, ResearchAcquisitionError) as error:
        raise ResearchAcquisitionError('COLLECTION_COMMIT_MISSING_OR_INVALID') from error


def read_collection(root, selection_id, *, clock=lambda: int(time.time())):
    report = _read_selection(root, selection_id, clock)
    _committed(root, report)
    final = _time(clock)
    if not report['checked_at'] <= final < report['expires_at']:
        raise ResearchAcquisitionError('COLLECTION_NOT_CURRENT')
    return report


def _stable(report):
    value = {key: item for key, item in report.items() if key not in ('checked_at', 'fingerprint')}
    for name in ('research', 'comparison'):
        value[name] = {key: item for key, item in value[name].items()
                       if key not in ('checked_at', 'fingerprint')}
    regional = value['research']['regional_methodology']
    value['research']['regional_methodology'] = {key: item for key, item in regional.items()
                                               if key not in ('checked_at', 'fingerprint')}
    return canonical(value)


def verify_collection_current(root, report, *, clock=lambda: int(time.time())):
    try:
        if not isinstance(report, dict) or report.get('fingerprint') != sha256(canonical(
                {key: value for key, value in report.items() if key != 'fingerprint'})).hexdigest():
            raise ResearchAcquisitionError('COLLECTION_REPORT_INVALID')
        now = _time(clock)
        if type(report['checked_at']) is not int or not report['checked_at'] <= now < report['expires_at']:
            raise ResearchAcquisitionError('COLLECTION_NOT_CURRENT')
        fresh = read_collection(root, report['selection_id'], clock=clock)
        if _stable(fresh) != _stable(report):
            raise ResearchAcquisitionError('COLLECTION_REPORT_CHANGED')
        final = _time(clock)
        if not now <= fresh['checked_at'] <= final < report['expires_at']:
            raise ResearchAcquisitionError('COLLECTION_NOT_CURRENT')
    except (KeyError, TypeError, ValueError, RecursionError) as error:
        raise ResearchAcquisitionError('COLLECTION_REPORT_INVALID') from error


class ResearchCollection:
    def __init__(self, root, *, clock=lambda: int(time.time()), resolver=socket.getaddrinfo,
                 transport=None):
        if not all(callable(value) for value in (clock, resolver)) or (transport is not None and not callable(transport)):
            raise ResearchAcquisitionError('COLLECTION_CONFIGURATION_INVALID')
        self.root, self.clock = _path(root), clock
        self.resolver, self.transport = resolver, transport or pinned_response
        self.budget = SessionBudget()

    def collect(self):
        started = _time(self.clock)
        marker = _path(self.root / 'cycle-start.json')
        try:
            _write(marker, canonical({'version': '0.1.0', 'started_at': started,
                'scope': SCOPE, 'budget_before': _budget(self.budget), 'boundary': BOUNDARY}))
        except FileExistsError as error:
            raise ResearchAcquisitionError('COLLECTION_ALREADY_STARTED') from error
        except OSError as error:
            raise ResearchAcquisitionError('COLLECTION_START_FAILED') from error
        stage = published = failed_recipe = None
        receipts = {}
        try:
            euro_root, statbel_root = _path(self.root / 'eurostat'), _path(self.root / 'statbel')
            euro = ResearchAcquirer(euro_root, clock=lambda: _time(self.clock),
                resolver=self.resolver, transport=self.transport)
            statbel = StatbelResearchAcquirer(statbel_root, clock=lambda: _time(self.clock),
                resolver=self.resolver, transport=self.transport)
            euro.budget = statbel.budget = self.budget
            previous = started
            for recipes, collector in ((EURO_RECIPES, euro), (STATBEL_RECIPES, statbel)):
                terms = None
                for recipe in recipes:
                    failed_recipe = recipe
                    now = _time(self.clock)
                    if now < previous:
                        raise ResearchAcquisitionError('COLLECTION_CLOCK_REGRESSED')
                    receipt = collector.acquire(recipe, terms_candidate_id=terms)
                    ended = _time(self.clock)
                    if not now <= receipt['acquired_at'] <= ended:
                        raise ResearchAcquisitionError('COLLECTION_CLOCK_REGRESSED')
                    receipts[recipe] = receipt
                    if terms is None:
                        terms = receipt['candidate_id']
                    previous = ended
            created = _time(self.clock)
            if created < previous:
                raise ResearchAcquisitionError('COLLECTION_CLOCK_REGRESSED')
            manifest = {'version': '0.1.0', 'scope': SCOPE, 'started_at': started,
                'created_at': created, 'expires_at': min(r['expires_at'] for r in receipts.values()),
                'candidates': {recipe: {key: receipts[recipe][key] for key in
                    ('candidate_id', 'content_sha256')} for recipe in RECIPES},
                'budget': _budget(self.budget), 'boundary': BOUNDARY}
            _validate_manifest(manifest)
            failed_recipe = None
            report = _reviews(self.root, manifest, self.clock)
            raw = canonical(manifest)
            selection_root = _path(self.root / 'selections')
            selection_root.mkdir(exist_ok=True)
            stage = _path(tempfile.mkdtemp(prefix='.selection-', dir=selection_root))
            _write(stage / 'selection.json', raw)
            # Final byte and freshness fence before no-replace publication.
            if _stable(_reviews(self.root, manifest, self.clock)) != _stable(report):
                raise ResearchAcquisitionError('COLLECTION_INPUT_CHANGED')
            destination = selection_root / report['selection_id']
            _publish(stage, destination)
            published = destination
            stage = None
            result = _read_selection(self.root, report['selection_id'], self.clock)
            _write(_path(self.root / 'cycle-outcome.json'), canonical({'state': 'COLLECTED',
                'selection_id': report['selection_id'], 'budget': _budget(self.budget), 'boundary': BOUNDARY}))
            published = None
            return result
        except (OSError, ResearchAcquisitionError, ValueError, TypeError, RecursionError,
                AssertionError, HTTPException) as error:
            failure = error if isinstance(error, ResearchAcquisitionError) else ResearchAcquisitionError('COLLECTION_FAILED')
            try:
                _write(_path(self.root / 'cycle-outcome.json'), canonical({'state': 'FAILED',
                    'error': str(failure), 'failed_recipe': failed_recipe,
                    'error_type': type(error).__name__,
                    'error_errno': getattr(error, 'errno', None),
                    'error_winerror': getattr(error, 'winerror', None),
                    'retained': {recipe: {key: receipt[key] for key in ('candidate_id', 'content_sha256')}
                                 for recipe, receipt in receipts.items()},
                    'budget': _budget(self.budget), 'boundary': BOUNDARY}))
            except (OSError, ResearchAcquisitionError):
                raise ResearchAcquisitionError('COLLECTION_OUTCOME_RECORD_FAILED') from error
            raise failure from error
        finally:
            if stage is not None:
                _cleanup(stage)
            if published is not None:
                _cleanup(published)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    collect = sub.add_parser('collect')
    collect.add_argument('--root', required=True)
    read = sub.add_parser('read')
    read.add_argument('--root', required=True)
    read.add_argument('--selection-id', required=True)
    args = parser.parse_args(argv)
    cycle = None
    try:
        if args.command == 'collect':
            cycle = ResearchCollection(args.root)
            report = cycle.collect()
        else:
            report = read_collection(args.root, args.selection_id)
        # ASCII JSON escapes are lossless and also work on legacy Windows pipes.
        body = json.dumps(report, ensure_ascii=True, indent=2)
        verify_collection_current(args.root, report)
        print(body)
        return 0
    except (ResearchAcquisitionError, OSError) as error:
        print(json.dumps({'state': 'FAILED', 'error': str(error),
            'budget': _budget(cycle.budget) if cycle else None, **BOUNDARY}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
