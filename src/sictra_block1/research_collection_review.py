"""Exact offline collection projection for the candidate read-only console."""
from copy import deepcopy
from hashlib import sha256
import time

from .research_acquisition import ResearchAcquisitionError, ResearchQuarantine, canonical
from .research_collection import EURO_RECIPES, read_collection, verify_collection_current
from .research_recovery import _identity, _path
from .research_review import ResearchReview


def _projection(collection):
    report = deepcopy(collection['research'])
    report.pop('fingerprint')
    report.update(version='0.3.0', checked_at=collection['checked_at'],
                  expires_at=collection['expires_at'], collection=deepcopy(collection))
    report['fingerprint'] = sha256(canonical(report)).hexdigest()
    return report


class CollectionResearchReview(ResearchReview):
    """Reuse the existing console interface, but fence every selected original."""
    def __init__(self, root, selection_id, *, clock=lambda: int(time.time())):
        if not callable(clock):
            raise ResearchAcquisitionError('COLLECTION_CONSOLE_CONFIGURATION_INVALID')
        self.collection_root, self.selection_id = _path(root), _identity(selection_id)
        collection = read_collection(self.collection_root, self.selection_id, clock=clock)
        ids = {recipe: value['candidate_id'] for recipe, value in
               collection['selection']['candidates'].items()}
        super().__init__(ResearchQuarantine(self.collection_root / 'eurostat'),
            ids[EURO_RECIPES[4]], ids[EURO_RECIPES[1]], national_id=ids[EURO_RECIPES[2]],
            regional_id=ids[EURO_RECIPES[3]], clock=clock)

    def read(self):
        return _projection(read_collection(self.collection_root, self.selection_id, clock=self.clock))

    def verify_current(self, report):
        try:
            collection = report['collection']
            if (collection['selection_id'] != self.selection_id or
                    canonical(report) != canonical(_projection(collection))):
                raise ResearchAcquisitionError('COLLECTION_CONSOLE_REPORT_INVALID')
            now = self._time()
            if not report['checked_at'] <= now < report['expires_at']:
                raise ResearchAcquisitionError('COLLECTION_CONSOLE_NOT_CURRENT')
            verify_collection_current(self.collection_root, collection, clock=self.clock)
            final = self._time()
            if not now <= final < report['expires_at']:
                raise ResearchAcquisitionError('COLLECTION_CONSOLE_NOT_CURRENT')
        except (KeyError, TypeError, ValueError, RecursionError) as error:
            raise ResearchAcquisitionError('COLLECTION_CONSOLE_REPORT_INVALID') from error
