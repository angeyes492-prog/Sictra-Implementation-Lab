"""Independent literal PDF oracles; no downloaded file is needed by CI."""
from copy import deepcopy
from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import contextlib
from unittest.mock import patch

from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

from sictra_block1.research_acquisition import canonical, ResearchAcquisitionError
from sictra_block1.research_statbel import StatbelResearchQuarantine, TERMS_RECIPE
from sictra_block1.research_statbel import StatbelResearchAcquirer
from test_research_statbel import Response, dns


URL = "https://statbel.fgov.be/sites/default/files/files/metadata/T38.STAT_DTST_743.CTAC_ORG_1.DIFF_LVL_1.EN.pdf"
PAGES = [
    "Algemene Directie Statistiek - Statistics Belgium\nMetadata\nStatistical product\nSea transport\n-\nMetadata update\nDocument update 12/02/2025\nPresentation\nKeywords\nDomain 3.4. Transport\nStatistical unit - Title\nStatistical unit - Description\nStatistical population - Title\nStatistical population - Description\nGeographical coverage Belgian seaports\nTime coverage Quarter\nSectors\nOther coverage\nReference period",
    "Algemene Directie Statistiek - Statistics Belgium\nPublication policy\nRelease calendar The release calendar is available via the internet\nPeriodicity Quarterly\nDissemination format\nPress release\nPublications Publication on the Internet\nOnline database https://statbel.fgov.be/en/themes/mobility/inland-water-\ntransport-waterborne-transport\nOpen data\nTimeliness\nTimeliness Results available 5 months after the reference period",
    "Algemene Directie Statistiek - Statistics Belgium\nData revision\nData revision - policy Not applicable.\nData revision - practice Not applicable.\nStatistical processing\nSource data - surveys -\nSource data - Administrative data\nData from all Belgian seaports\nSource data - Statistical products\n-\nFrequency of data collection\nQuarterly\nData collection Re-use of administrative data\nData composition\nAdjustment",
    "Algemene Directie Statistiek - Statistics Belgium\nRelated documents\nInternet: Sea transport https://statbel.fgov.be/en/themes/mobility/transport/sea-transport\nExternal IDs\nStatistical variables\nTitle Definition Unit/Nomenclature\n-",
]
TERMS = b'<html>Statbel General terms of use CC BY 4.0</html>'


def retain_terms(root, now):
    @contextmanager
    def transport(_host, _address, _path):
        yield Response(TERMS)
    receipt = StatbelResearchAcquirer(root, clock=lambda: now, resolver=dns,
                                     transport=transport).acquire(TERMS_RECIPE)
    identity = receipt.pop('candidate_id')
    return identity, receipt


def pdf_bytes(pages=None, *, active=False, encrypted=False, compress=False, embedded_font=False):
    writer = PdfWriter()
    for text in pages or PAGES:
        page = writer.add_blank_page(width=612, height=792)
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
                                 NameObject('/Subtype'): NameObject('/Type1'),
                                 NameObject('/BaseFont'): NameObject('/Helvetica')})
        if embedded_font:
            font_data = DecodedStreamObject()
            font_data.set_data(b'font-padding' * 60000)
            font[NameObject('/FontDescriptor')] = DictionaryObject({NameObject('/FontFile2'):
                writer._add_object(font_data.flate_encode())})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'):
            DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
        lines = ['BT /F1 10 Tf 14 TL 30 750 Td']
        for line in text.splitlines():
            escaped = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
            lines.append(f'({escaped}) Tj T*')
        lines.append('ET')
        stream = DecodedStreamObject()
        stream.set_data('\n'.join(lines).encode('latin-1'))
        page[NameObject('/Contents')] = writer._add_object(stream.flate_encode() if compress else stream)
    if active:
        writer.add_js('app.alert("untrusted")')
    if encrypted:
        writer.encrypt('not-a-public-document')
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


class StatbelMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'pdf'
        self.root.mkdir()
        self.terms_root = Path(self.temp.name) / 'terms'
        self.now = 1700000100
        self.terms_id, self.terms_descriptor = retain_terms(self.terms_root, 1700000000)
        self.content = pdf_bytes()
        self.descriptor = {
            'version': 'AGENT_RESEARCH_PDF_CANDIDATE_V1', 'original_url': URL, 'final_url': URL,
            'publisher': 'Statistics Belgium / Statbel', 'source_id': 'statbel',
            'root_identity': 'UNCONFIRMED_SAME_PORT_ORIGIN_CHAIN',
            'acquired_at': 1700000050, 'acquired_utc': datetime.fromtimestamp(1700000050, timezone.utc).isoformat(),
            'expires_at': 1700086400, 'media_type': 'application/pdf', 'byte_length': len(self.content),
            'content_sha256': sha256(self.content).hexdigest(),
            'budget': {'source_requests': 1, 'received_bytes': len(self.content), 'request_limit': 1,
                       'file_limit_bytes': 8388608, 'timeout_seconds': 30, 'retry_limit': 0},
            'rights_evidence': {'candidate_id': self.terms_id,
                               'content_sha256': sha256(TERMS).hexdigest(), 'pdf_applicability': 'UNCONFIRMED'},
            'need': 'Specific Statbel maritime coverage and revision policy; no causal-gap conclusion',
            'publisher_version': 'TO_INSPECT_FROM_ORIGINAL', 'scope': 'LABORATORY_INTERNAL_SUPERVISED',
            'admission': 'NOT_ADMITTED', 'resolution': 'NOT_RESOLVED', 'acceptance': 'NOT_ACCEPTED',
            'runtime_effect': 'NONE', 'publication': 'BLOCKED',
        }
        self.save()

    def save(self):
        self.descriptor['byte_length'] = len(self.content)
        self.descriptor['content_sha256'] = sha256(self.content).hexdigest()
        self.descriptor['budget']['received_bytes'] = len(self.content)
        self.identity = sha256(canonical(self.descriptor)).hexdigest()
        self.folder = self.root / self.identity
        self.folder.mkdir(exist_ok=True)
        (self.folder / 'descriptor.json').write_bytes(canonical(self.descriptor))
        (self.folder / 'original.pdf').write_bytes(self.content)

    def reader(self, **kwargs):
        try:
            from sictra_block1.research_statbel_metadata import StatbelMetadataReview
        except ImportError:
            self.fail('Missing bounded Statbel original-PDF metadata reader')
        return StatbelMetadataReview(self.root, self.identity, self.terms_root,
                                    clock=lambda: self.now, **kwargs)

    def test_original_literals_reopen_no_writes_no_network_and_no_promotion(self):
        # Break: using copied receipt claims, inventing a unit or admitting metadata.
        files = {str(p): p.read_bytes() for p in Path(self.temp.name).rglob('*') if p.is_file()}
        with patch('socket.create_connection', side_effect=AssertionError('no network')):
            report = self.reader().read()
            self.reader().verify_current(report)
        self.assertEqual(report['observations']['geographic_coverage'], {'literal': 'Belgian seaports', 'page': 1})
        self.assertEqual(report['observations']['administrative_origin'], {'literal': 'Data from all Belgian seaports', 'page': 3})
        self.assertEqual(report['observations']['revision_policy'], {'literal': 'Not applicable.', 'page': 3})
        self.assertEqual(report['observations']['revision_practice'], {'literal': 'Not applicable.', 'page': 3})
        self.assertEqual(report['observations']['document_update'], {'literal': '12/02/2025', 'page': 1})
        self.assertIsNone(report['statistical_unit'])
        self.assertIsNone(report['statistical_population'])
        self.assertEqual(report['independent_root'], 'NOT_ESTABLISHED')
        self.assertEqual(report['admission'], 'NOT_ADMITTED')
        self.assertEqual(report['resolution'], 'NOT_RESOLVED')
        self.assertEqual(report['runtime_effect'], 'NONE')
        self.assertIn('ONLINE_DATABASE_SCOPE_CONFLICT', report['limitations'])
        self.assertIn('REVISION_STATEMENT_NOT_PROOF_OF_NO_REVISIONS', report['limitations'])
        self.assertEqual(report['expires_at'], 1700086400)
        self.assertEqual(files, {str(p): p.read_bytes() for p in Path(self.temp.name).rglob('*') if p.is_file()})

    def test_changed_original_is_withdrawn_even_if_projection_resealed(self):
        report = self.reader().read()
        (self.folder / 'original.pdf').write_bytes(pdf_bytes([p.replace('Belgian seaports', 'World ports') for p in PAGES]))
        with self.assertRaises(ResearchAcquisitionError):
            self.reader().verify_current(report)

    def test_changed_terms_or_wrong_terms_hash_is_rejected(self):
        (self.terms_root / self.terms_id / 'content.bin').write_bytes(TERMS + b'changed')
        with self.assertRaises(ResearchAcquisitionError):
            self.reader().read()

    def test_self_resealed_false_observation_or_authority_is_rejected(self):
        report = self.reader().read()
        for key in ('observations', 'admission', 'independent_root', 'expires_at'):
            forged = deepcopy(report)
            if key == 'observations':
                forged[key]['revision_policy']['literal'] = 'No revisions ever'
            elif key == 'expires_at':
                forged[key] += 100
            else:
                forged[key] = 'ACCEPTED'
            forged['fingerprint'] = sha256(canonical({k: v for k, v in forged.items() if k != 'fingerprint'})).hexdigest()
            with self.subTest(key=key), self.assertRaises(ResearchAcquisitionError):
                self.reader().verify_current(forged)

    def test_resealed_check_time_cannot_predate_retained_originals(self):
        report = self.reader().read()
        for checked in (-1, 1700000049):
            forged = deepcopy(report)
            forged['checked_at'] = checked
            forged['fingerprint'] = sha256(canonical({k: v for k, v in forged.items() if k != 'fingerprint'})).hexdigest()
            with self.subTest(checked=checked), self.assertRaises(ResearchAcquisitionError):
                self.reader().verify_current(forged)

    def test_duplicate_section_end_marker_cannot_hide_conflicting_scope(self):
        pages = [*PAGES[:2], PAGES[2] + '\nStatistical processing', PAGES[3]]
        self.content = pdf_bytes(pages)
        self.save()
        with self.assertRaises(ResearchAcquisitionError):
            self.reader().read()

    def test_expiry_and_future_receipt_reject(self):
        for instant in (1700000049, 1700086400):
            self.now = instant
            with self.subTest(now=instant), self.assertRaises(ResearchAcquisitionError):
                self.reader().read()

    def test_clock_rollback_after_read_rejects_replay(self):
        report = self.reader().read()
        self.now -= 1
        with self.assertRaises(ResearchAcquisitionError):
            self.reader().verify_current(report)

    def test_exact_known_receipt_identity_rejects_descriptor_mutation(self):
        self.descriptor['publisher_version'] = 'invented'
        (self.folder / 'descriptor.json').write_bytes(canonical(self.descriptor))
        with self.assertRaises(ResearchAcquisitionError):
            self.reader().read()

    def test_resealed_receipt_cannot_change_fixed_boundary_or_rights(self):
        for field, value in (('admission', 'APPROVED'), ('final_url', 'https://other.example/a.pdf'),
                             ('rights_evidence', {**self.descriptor['rights_evidence'], 'content_sha256': '0' * 64})):
            original = deepcopy(self.descriptor)
            self.descriptor[field] = value
            self.save()
            with self.subTest(field=field), self.assertRaises(ResearchAcquisitionError):
                self.reader().read()
            self.descriptor = original

    def test_duplicate_json_fields_are_not_silently_collapsed(self):
        data = canonical(self.descriptor)
        (self.folder / 'descriptor.json').write_bytes(b'{"admission":"APPROVED",' + data[1:])
        with self.assertRaises(ResearchAcquisitionError):
            self.reader().read()

    def test_non_pdf_encrypted_and_active_content_reject(self):
        for content in (b'%PDF-1.7\nmalformed', pdf_bytes(encrypted=True), pdf_bytes(active=True)):
            self.content = content
            self.save()
            with self.subTest(size=len(content)), self.assertRaises(ResearchAcquisitionError):
                self.reader().read()

    def test_missing_duplicate_and_wrong_product_sections_reject(self):
        mutations = [PAGES[0].replace('Sea transport', 'Inland water transport'),
                     PAGES[0].replace('Geographical coverage Belgian seaports', 'No geographical coverage'),
                     PAGES[0] + '\nGeographical coverage World ports\nTime coverage Annual\nSectors']
        for page in mutations:
            self.content = pdf_bytes([page, *PAGES[1:]])
            self.save()
            with self.subTest(page=page[-60:]), self.assertRaises(ResearchAcquisitionError):
                self.reader().read()

    def test_page_and_decoded_stream_limits_fail_closed(self):
        for content in (pdf_bytes([*PAGES, PAGES[3]]),
                        pdf_bytes([PAGES[0] + '\n' + 'A' * 530000, *PAGES[1:]], compress=True)):
            self.content = content
            self.save()
            with self.subTest(size=len(content)), self.assertRaises(ResearchAcquisitionError):
                self.reader().read()

    def test_oversized_original_and_invalid_id_fail_before_parsing(self):
        (self.folder / 'original.pdf').write_bytes(b'A' * 262145)
        with self.assertRaises(ResearchAcquisitionError):
            self.reader().read()
        self.identity = '../escape'
        with self.assertRaises(ResearchAcquisitionError):
            self.reader().read()

    def test_real_child_timeout_is_controlled_and_returns_no_partial_report(self):
        with self.assertRaisesRegex(ResearchAcquisitionError, 'PDF_PARSE_TIMEOUT'):
            self.reader(parser_timeout=0.001).read()

    def test_filled_unit_and_population_titles_are_not_discarded(self):
        page = PAGES[0].replace('Statistical unit - Title', 'Statistical unit - Title Vessel').replace(
            'Statistical unit - Description', 'Statistical unit - Description Statistical ship').replace(
            'Statistical population - Title', 'Statistical population - Title All arrivals').replace(
            'Statistical population - Description', 'Statistical population - Description Maritime arrivals')
        self.content = pdf_bytes([page, *PAGES[1:]])
        self.save()
        report = self.reader().read()
        self.assertEqual(report['statistical_unit'], {'title': 'Vessel', 'description': 'Statistical ship', 'page': 1})
        self.assertEqual(report['statistical_population'], {'title': 'All arrivals', 'description': 'Maritime arrivals', 'page': 1})

    def test_embedded_font_is_not_mistaken_for_oversized_page_content(self):
        # Real publisher embeds fonts larger than its four textual content streams.
        self.content = pdf_bytes(embedded_font=True)
        self.save()
        try:
            report = self.reader().read()
        except ResearchAcquisitionError as error:
            self.fail(f'Bounded embedded fonts should not reject valid metadata: {error}')
        self.assertEqual(report['observations']['geographic_coverage']['literal'], 'Belgian seaports')

    def test_non_ascii_literal_survives_child_pipe_encoding(self):
        self.content = pdf_bytes([PAGES[0].replace('Belgian seaports', 'Belgian séaports'), *PAGES[1:]])
        self.save()
        try:
            report = self.reader().read()
        except ResearchAcquisitionError as error:
            self.fail(f'Original Unicode text must survive the worker pipe: {error}')
        self.assertEqual(report['observations']['geographic_coverage']['literal'], 'Belgian séaports')

    def test_change_or_expiry_during_real_parsing_withdraws_report(self):
        reader = self.reader()
        original_parse = reader._parse
        def change(raw):
            pages = original_parse(raw)
            (self.folder / 'original.pdf').write_bytes(raw + b'changed')
            return pages
        with patch.object(reader, '_parse', side_effect=change), self.assertRaises(ResearchAcquisitionError):
            reader.read()
        self.save()
        def expire(raw):
            pages = original_parse(raw)
            self.now = 1700086400
            return pages
        with patch.object(reader, '_parse', side_effect=expire), self.assertRaises(ResearchAcquisitionError):
            reader.read()

    def test_cli_serialization_tamper_withdraws_before_stdout(self):
        from sictra_block1 import research_statbel_metadata as module
        argv = ['research', '--pdf-root', str(self.root), '--candidate-id', self.identity,
                '--terms-root', str(self.terms_root)]
        dumps = json.dumps
        def changed(value, **kwargs):
            result = dumps(value, **kwargs)
            if kwargs.get('indent') == 2:
                (self.folder / 'original.pdf').write_bytes(b'changed')
            return result
        import io
        output, errors = io.StringIO(), io.StringIO()
        # Constructor defaults bind time.time at definition; provide a real instance instead.
        reader = self.reader()
        with patch.object(sys, 'argv', argv), patch.object(module, 'StatbelMetadataReview', return_value=reader), \
                patch.object(module.json, 'dumps', side_effect=changed), contextlib.redirect_stdout(output), \
                contextlib.redirect_stderr(errors):
            self.assertEqual(module.main(), 2)
        self.assertEqual(output.getvalue(), '')
        self.assertIn('PDF_CANDIDATE_INTEGRITY_INVALID', errors.getvalue())

    def test_missing_root_never_creates_an_empty_quarantine(self):
        self.terms_root = Path(self.temp.name) / 'absent'
        with self.assertRaises(ResearchAcquisitionError):
            self.reader().read()
        self.assertFalse(self.terms_root.exists())

    def test_cli_recomputes_and_prints_only_current_report(self):
        command = [sys.executable, '-m', 'sictra_block1.research_statbel_metadata',
                   '--pdf-root', str(self.root), '--candidate-id', self.identity,
                   '--terms-root', str(self.terms_root)]
        # Real CLI clock: retain a fixture current at wall time, without changing literal PDF oracle.
        import time
        self.now = int(time.time())
        self.terms_id, self.terms_descriptor = retain_terms(self.terms_root, self.now - 10)
        self.descriptor.update(acquired_at=self.now - 5, acquired_utc=datetime.fromtimestamp(self.now - 5, timezone.utc).isoformat(), expires_at=self.now + 86390)
        self.descriptor['rights_evidence']['candidate_id'] = self.terms_id
        self.save()
        command[command.index('--candidate-id') + 1] = self.identity
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['observations']['periodicity']['literal'], 'Quarterly')
        (self.folder / 'original.pdf').write_bytes(b'changed')
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')


if __name__ == '__main__':
    unittest.main()
