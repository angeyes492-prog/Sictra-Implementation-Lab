"""Read-only fixed Statbel metadata inspection; no admission or runtime effect."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
import time

from .research_acquisition import ResearchAcquisitionError, canonical, _safe_path
from .research_statbel import StatbelResearchQuarantine, TERMS_RECIPE


PDF_URL = 'https://statbel.fgov.be/sites/default/files/files/metadata/T38.STAT_DTST_743.CTAC_ORG_1.DIFF_LVL_1.EN.pdf'
BOUNDARY = {'scope': 'LABORATORY_INTERNAL_SUPERVISED', 'admission': 'NOT_ADMITTED',
            'resolution': 'NOT_RESOLVED', 'acceptance': 'NOT_ACCEPTED',
            'runtime_effect': 'NONE', 'publication': 'BLOCKED'}
FIELDS = {'version', 'original_url', 'final_url', 'publisher', 'source_id',
          'root_identity', 'acquired_at', 'acquired_utc', 'expires_at', 'media_type',
          'byte_length', 'content_sha256', 'budget', 'rights_evidence', 'need',
          'publisher_version', *BOUNDARY}


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ResearchAcquisitionError('PDF_RECEIPT_DUPLICATE_FIELD')
        result[key] = value
    return result


def _field(text, start, end, *, optional=False):
    starts = list(re.finditer(start, text))
    if len(starts) != 1:
        raise ResearchAcquisitionError('PDF_METADATA_SECTION_AMBIGUOUS')
    ends = list(re.finditer(end, text))
    if len(ends) != 1 or ends[0].start() < starts[0].end():
        raise ResearchAcquisitionError('PDF_METADATA_SECTION_AMBIGUOUS')
    tail = text[starts[0].end():]
    finish = re.search(end, tail)
    if finish is None:
        raise ResearchAcquisitionError('PDF_METADATA_SECTION_MISSING')
    literal = tail[:finish.start()].strip()
    if optional and literal in ('', '-'):
        return None
    if not literal or len(literal) > 2000:
        raise ResearchAcquisitionError('PDF_METADATA_VALUE_INVALID')
    return literal


def _observations(pages):
    texts = [' '.join(page.split()) for page in pages]
    if any('Algemene Directie Statistiek - Statistics Belgium' not in text for text in texts):
        raise ResearchAcquisitionError('PDF_PUBLISHER_IDENTITY_INVALID')
    product = _field(texts[0], r'Statistical product ', r' Metadata update')
    if product.rstrip(' -') != 'Sea transport':
        raise ResearchAcquisitionError('PDF_PRODUCT_IDENTITY_INVALID')
    specs = {
        'document_update': (1, r'Document update ', r' Presentation'),
        'geographic_coverage': (1, r'Geographical coverage ', r' Time coverage'),
        'temporal_coverage': (1, r'Time coverage ', r' Sectors'),
        'periodicity': (2, r'Periodicity ', r' Dissemination format'),
        'online_database': (2, r'Online database ', r' Open data'),
        'timeliness': (2, r'Timeliness (?=Results)', r'$'),
        'revision_policy': (3, r'Data revision - policy ', r' Data revision - practice'),
        'revision_practice': (3, r'Data revision - practice ', r' Statistical processing'),
        'administrative_origin': (3, r'Source data - Administrative data ', r' Source data . Statistical products'),
        'collection_frequency': (3, r'Frequency of data collection ', r' Data collection'),
        'collection_method': (3, r'(?<!Frequency of )Data collection ', r' Data composition'),
    }
    result = {key: {'literal': _field(texts[page - 1], start, end), 'page': page}
              for key, (page, start, end) in specs.items()}
    def entity(name, next_field):
        title = _field(texts[0], name + r' - Title', ' ' + name + r' - Description', optional=True)
        description = _field(texts[0], name + r' - Description', next_field, optional=True)
        return None if title is None and description is None else {
            'title': title, 'description': description, 'page': 1}
    unit = entity('Statistical unit', r' Statistical population - Title')
    population = entity('Statistical population', r' Geographical coverage')
    return result, unit, population


class StatbelMetadataReview:
    def __init__(self, pdf_root, candidate_id, terms_root, *, clock=time.time, parser_timeout=15):
        if (not isinstance(candidate_id, str) or re.fullmatch('[0-9a-f]{64}', candidate_id) is None
                or not callable(clock) or type(parser_timeout) not in (int, float)
                or not 0 < parser_timeout <= 15):
            raise ResearchAcquisitionError('PDF_REVIEW_CONFIGURATION_INVALID')
        self.root, self.terms_root = _safe_path(pdf_root), _safe_path(terms_root)
        if not self.root.is_dir() or not self.terms_root.is_dir():
            raise ResearchAcquisitionError('PDF_REVIEW_ROOT_MISSING')
        self.candidate_id, self.clock, self.parser_timeout = candidate_id, clock, parser_timeout

    def _now(self):
        value = self.clock()
        if type(value) not in (int, float) or not 0 <= value < 253402300800:
            raise ResearchAcquisitionError('CLOCK_INVALID')
        return int(value)

    def _read_originals(self, now):
        folder = _safe_path(self.root / self.candidate_id)
        receipt_path, original_path = _safe_path(folder / 'descriptor.json'), _safe_path(folder / 'original.pdf')
        try:
            with receipt_path.open('rb') as receipt_file, original_path.open('rb') as pdf_file:
                receipt_bytes = receipt_file.read(16001)
                raw = pdf_file.read(256 * 1024 + 1)
            if len(receipt_bytes) > 16000 or not 0 < len(raw) <= 256 * 1024:
                raise ResearchAcquisitionError('PDF_CANDIDATE_SIZE_INVALID')
            descriptor = json.loads(receipt_bytes, object_pairs_hook=_unique)
        except (OSError, ValueError) as error:
            raise ResearchAcquisitionError('PDF_CANDIDATE_READ_INVALID') from error
        if (not isinstance(descriptor, dict) or set(descriptor) != FIELDS
                or sha256(canonical(descriptor)).hexdigest() != self.candidate_id
                or any(descriptor.get(key) != value for key, value in BOUNDARY.items())
                or descriptor['version'] != 'AGENT_RESEARCH_PDF_CANDIDATE_V1'
                or descriptor['original_url'] != PDF_URL or descriptor['final_url'] != PDF_URL
                or descriptor['publisher'] != 'Statistics Belgium / Statbel'
                or descriptor['source_id'] != 'statbel'
                or descriptor['root_identity'] != 'UNCONFIRMED_SAME_PORT_ORIGIN_CHAIN'
                or descriptor['publisher_version'] != 'TO_INSPECT_FROM_ORIGINAL'
                or descriptor['need'] != 'Specific Statbel maritime coverage and revision policy; no causal-gap conclusion'
                or descriptor['media_type'] != 'application/pdf'
                or type(descriptor['byte_length']) is not int or descriptor['byte_length'] != len(raw)
                or descriptor['content_sha256'] != sha256(raw).hexdigest()):
            raise ResearchAcquisitionError('PDF_CANDIDATE_INTEGRITY_INVALID')
        acquired, expiry = descriptor['acquired_at'], descriptor['expires_at']
        if (type(acquired) is not int or type(expiry) is not int
                or not 0 <= acquired <= now < expiry <= acquired + 86400
                or descriptor['acquired_utc'] != datetime.fromtimestamp(acquired, timezone.utc).isoformat()):
            raise ResearchAcquisitionError('PDF_CANDIDATE_NOT_CURRENT')
        budget = descriptor['budget']
        expected_budget = {'source_requests': 1, 'received_bytes': len(raw), 'request_limit': 1,
                           'file_limit_bytes': 8388608, 'timeout_seconds': 30, 'retry_limit': 0}
        if canonical(budget) != canonical(expected_budget):
            raise ResearchAcquisitionError('PDF_CANDIDATE_BUDGET_INVALID')
        rights = descriptor['rights_evidence']
        if (not isinstance(rights, dict) or set(rights) != {'candidate_id', 'content_sha256', 'pdf_applicability'}
                or rights['pdf_applicability'] != 'UNCONFIRMED'):
            raise ResearchAcquisitionError('PDF_RIGHTS_LINEAGE_INVALID')
        terms, _ = StatbelResearchQuarantine(self.terms_root).read(rights['candidate_id'], now=now, expected_recipe=TERMS_RECIPE)
        if rights['content_sha256'] != terms['content_sha256']:
            raise ResearchAcquisitionError('PDF_RIGHTS_LINEAGE_INVALID')
        return descriptor, raw, terms

    def _parse(self, raw):
        worker = Path(__file__).with_name('_research_pdf_worker.py')
        try:
            process = subprocess.run([sys.executable, '-I', str(worker)], input=raw,
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=self.parser_timeout, check=False)
        except subprocess.TimeoutExpired as error:
            raise ResearchAcquisitionError('PDF_PARSE_TIMEOUT') from error
        except OSError as error:
            raise ResearchAcquisitionError('PDF_PARSER_UNAVAILABLE') from error
        if process.returncode != 0 or len(process.stdout) > 256 * 1024:
            raise ResearchAcquisitionError('PDF_PARSE_REJECTED')
        try:
            pages = json.loads(process.stdout)
        except ValueError as error:
            raise ResearchAcquisitionError('PDF_PARSE_REJECTED') from error
        if not isinstance(pages, list) or len(pages) != 4 or any(not isinstance(p, str) for p in pages):
            raise ResearchAcquisitionError('PDF_PARSE_REJECTED')
        return pages

    def read(self):
        started = self._now()
        descriptor, raw, terms = self._read_originals(started)
        observations, unit, population = _observations(self._parse(raw))
        finished = self._now()
        if finished < started:
            raise ResearchAcquisitionError('PDF_REVIEW_CLOCK_ROLLBACK')
        # Fence bytes AND both expirations after processing, not just before it.
        current, _, current_terms = self._read_originals(finished)
        if canonical(current) != canonical(descriptor) or canonical(current_terms) != canonical(terms):
            raise ResearchAcquisitionError('PDF_REVIEW_CHANGED_DURING_READ')
        limitations = ['PDF_RIGHTS_APPLICABILITY_UNCONFIRMED', 'RELEASE_SPECIFIC_APPLICABILITY_UNCONFIRMED',
                       'PORT_UNIVERSE_EQUIVALENCE_UNCONFIRMED', 'INDEPENDENCE_NOT_ESTABLISHED',
                       'REVISION_STATEMENT_NOT_PROOF_OF_NO_REVISIONS', 'NUMERIC_GAP_CAUSE_UNCONFIRMED']
        if 'inland-water' in observations['online_database']['literal']:
            limitations.append('ONLINE_DATABASE_SCOPE_CONFLICT')
        report = {'version': 'STATBEL_PDF_METADATA_REVIEW_V1', 'candidate_id': self.candidate_id,
            'original_url': PDF_URL, 'content_sha256': descriptor['content_sha256'],
            'terms_candidate_id': descriptor['rights_evidence']['candidate_id'],
            'terms_content_sha256': terms['content_sha256'], 'checked_at': finished,
            'acquired_at': descriptor['acquired_at'], 'terms_acquired_at': terms['acquired_at'],
            'expires_at': min(descriptor['expires_at'], terms['expires_at']),
            'observations': observations, 'statistical_unit': unit, 'statistical_population': population,
            'limitations': limitations, 'independent_root': 'NOT_ESTABLISHED', **BOUNDARY}
        report['fingerprint'] = sha256(canonical(report)).hexdigest()
        return report

    def verify_current(self, report):
        if not isinstance(report, dict) or type(report.get('checked_at')) is not int:
            raise ResearchAcquisitionError('PDF_REPORT_INVALID')
        current = self.read()
        if not max(current['acquired_at'], current['terms_acquired_at']) <= report['checked_at'] <= current['checked_at'] < current['expires_at']:
            raise ResearchAcquisitionError('PDF_REPORT_NOT_CURRENT')
        expected = {**current, 'checked_at': report['checked_at']}
        expected.pop('fingerprint')
        expected['fingerprint'] = sha256(canonical(expected)).hexdigest()
        if canonical(report) != canonical(expected):
            raise ResearchAcquisitionError('PDF_REPORT_PROJECTION_INVALID')


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf-root', required=True, type=Path)
    parser.add_argument('--candidate-id', required=True)
    parser.add_argument('--terms-root', required=True, type=Path)
    args = parser.parse_args()
    review = StatbelMetadataReview(args.pdf_root, args.candidate_id, args.terms_root)
    try:
        report = review.read()
        serialized = json.dumps(report, ensure_ascii=True, indent=2)
        review.verify_current(report)
    except ResearchAcquisitionError as error:
        print(str(error), file=sys.stderr)
        return 2
    print(serialized)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
