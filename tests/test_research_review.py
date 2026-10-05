from http.client import HTTPConnection
from pathlib import Path
import threading
import unittest
from unittest.mock import patch

import test_agent_research_acquisition as acquisition
from test_agent_research_acquisition import Response, NOW
from test_research_methodology import html_sections
from test_research_statistics import dataset, raw
from test_national_methodology import national_html
from sictra_block1.research_acquisition import ResearchQuarantine, ResearchAcquisitionError
from sictra_block1.research_review import ResearchReview, render_research_review
from sictra_block4_orchestrator.operations import initialize
from sictra_block4_orchestrator.operations_web import create_operations_server


class ResearchReviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture = acquisition.AcquisitionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.now = NOW
        self.terms = self.fixture.terms()
        self.metadata = self.acquire('EUROSTAT_MAR_METADATA', html_sections())
        self.data = self.acquire('EUROSTAT_MAR_BE_2023_2024', raw(dataset()), 'application/json')
        self.national = self.acquire('EUROSTAT_BE_MAR_METADATA', national_html())
        self.review = ResearchReview(self.fixture.session.quarantine, self.data, self.metadata,
                                    national_id=self.national, clock=lambda: self.now)

    def acquire(self, recipe, body, media='text/html', terms=None):
        self.fixture.response = Response(body=body, headers=[('Content-Type', media),
                                             ('Content-Length', str(len(body)))])
        return self.fixture.session.acquire(recipe, terms_candidate_id=terms or self.terms)['candidate_id']

    def files(self):
        return {str(p): p.read_bytes() for p in self.fixture.root.rglob('*') if p.is_file()}

    def test_exact_observations_pending_authority_replay_and_reopen_without_writes(self):
        before = self.files()
        report = self.review.read()
        self.assertEqual([(2023, 10.0), (2024, 12.5)], [(r['time_period'], r['value_thousand_tonnes'])
                            for r in report['admission_review']['data']['observations']])
        self.assertEqual(8, len(report['admission_review']['methodology']['sections']))
        self.assertEqual(16, len(report['national_methodology']['sections']))
        self.assertIsNone(report['admission_review']['required_approval']['reviewer_id'])
        self.assertEqual('PENDING', report['admission_review']['required_approval']['decision'])
        self.assertTrue(all(n['state'] == 'INSUFFICIENT EVIDENCE' for n in report['needs']))
        for key, expected in [('admission', 'NOT_ADMITTED'), ('resolution', 'NOT_RESOLVED'),
                              ('acceptance', 'NOT_ACCEPTED'), ('runtime_effect', 'NONE'),
                              ('publication', 'BLOCKED')]:
            self.assertEqual(expected, report[key])
        reopened = ResearchReview(ResearchQuarantine(self.fixture.root), self.data, self.metadata,
                                  national_id=self.national, clock=lambda: self.now)
        self.assertEqual(report, reopened.read())
        self.assertEqual(report, self.review.read())
        self.assertEqual(before, self.files())

    def test_optional_national_is_not_invented_and_invalid_identity_rejects(self):
        review = ResearchReview(self.fixture.session.quarantine, self.data, self.metadata,
                                clock=lambda: self.now)
        self.assertIsNone(review.read()['national_methodology'])
        for identity in ('../escape', 'A' * 64, None):
            with self.assertRaisesRegex(ResearchAcquisitionError, 'CONFIGURATION_INVALID'):
                ResearchReview(self.fixture.session.quarantine, identity, self.metadata)
        with self.assertRaises(Exception):
            ResearchReview(self.fixture.session.quarantine, self.data, self.national,
                          clock=lambda: self.now).read()

    def test_national_terms_substitution_cannot_join_separate_collection_lineages(self):
        self.fixture.now += 1
        other_terms = self.fixture.terms()
        other = self.acquire('EUROSTAT_BE_MAR_METADATA', national_html(), terms=other_terms)
        self.now += 1
        with self.assertRaisesRegex(ResearchAcquisitionError, 'TERMS_MISMATCH'):
            ResearchReview(self.fixture.session.quarantine, self.data, self.metadata,
                           national_id=other, clock=lambda: self.now).read()

    def test_expiry_future_clock_regression_and_final_expiry_fence(self):
        for at in (NOW - 1, NOW + 86400):
            self.now = at
            with self.assertRaises(Exception):
                self.review.read()
        for times in ([NOW, NOW - 1], [NOW, NOW, NOW + 86400], [NOW, NOW, NOW - 1]):
            self.review.clock = iter(times).__next__
            with self.assertRaises(ResearchAcquisitionError):
                self.review.read()
        for value in (True, 1.5, None, -1):
            self.review.clock = lambda: value
            with self.assertRaisesRegex(ResearchAcquisitionError, 'CLOCK_INVALID'):
                self.review.read()

    def test_tamper_between_reads_rejects_instead_of_serving_cached_values(self):
        original = self.review._inputs
        def tamper(now):
            result = original(now)
            (self.fixture.root / self.data / 'content.bin').write_bytes(b'altered')
            return result
        with patch.object(self.review, '_inputs', side_effect=tamper):
            with self.assertRaises(Exception):
                self.review.read()

    def test_renderer_escapes_remote_text_and_explains_non_admission(self):
        report = self.review.read()
        report['admission_review']['data']['dataset_title'] = '<script>alert(1)</script>'
        report['national_methodology']['sections'][0]['text'] = '<img src=x onerror=alert(2)>'
        html = render_research_review(report)
        self.assertNotIn('<script>', html)
        self.assertNotIn('<img', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('NOT_ADMITTED', html)
        self.assertIn('10.0', html)
        self.assertIn('12.5', html)

    def server(self, review):
        service = initialize(Path(self.fixture.temp.name) / 'operations', now=NOW)
        service.clock = lambda: self.now
        self.addCleanup(service.stop)
        server = create_operations_server(service, port=0, research_review=review)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join, 3)
        self.addCleanup(server.shutdown)
        return server, service

    def request(self, server, path, headers=None):
        conn = HTTPConnection('127.0.0.1', server.server_port, timeout=5)
        self.addCleanup(conn.close)
        conn.request('GET', path, headers=headers or {})
        response = conn.getresponse()
        return response.status, dict(response.getheaders()), response.read()

    def test_http_real_server_read_only_expiry_withdrawal_host_guard_and_no_runtime_mutation(self):
        server, service = self.server(self.review)
        before = service.store.records()
        status, headers, body = self.request(server, '/research')
        self.assertEqual(200, status)
        self.assertIn(b'12.5', body)
        self.assertIn("default-src 'none'", headers['Content-Security-Policy'])
        self.assertIn('no-store', headers['Cache-Control'])
        self.assertEqual(200, self.request(server, '/api/research')[0])
        self.assertEqual(403, self.request(server, '/api/research', {'Host': 'evil.example'})[0])
        self.now += 86400
        for path in ('/research', '/api/research'):
            status, _, body = self.request(server, path)
            self.assertEqual(409, status)
            self.assertIn(b'UNAVAILABLE', body)
            self.assertNotIn(b'12.5', body)
        self.assertEqual(before, service.store.records())

    def test_unconfigured_server_does_not_choose_or_admit_a_source(self):
        server, service = self.server(None)
        before = service.store.records()
        for path in ('/research', '/api/research'):
            status, _, body = self.request(server, path)
            self.assertEqual(404, status)
            self.assertIn(b'NOT_CONFIGURED', body)
        self.assertEqual(before, service.store.records())

    def test_http_expiry_during_render_withdraws_values_before_headers(self):
        server, _ = self.server(self.review)
        def expiring(report):
            body = render_research_review(report)
            self.now += 86400
            return body
        with patch('sictra_block4_orchestrator.operations_web.render_research_review', side_effect=expiring):
            status, _, body = self.request(server, '/research')
        self.assertEqual(409, status)
        self.assertIn(b'UNAVAILABLE', body)
        self.assertNotIn(b'12.5', body)

    def test_prepared_report_forgery_or_changed_original_cannot_pass_final_fence(self):
        report = self.review.read()
        report['admission'] = 'APPROVED'
        with self.assertRaises(ResearchAcquisitionError):
            self.review.verify_current(report)
        report = self.review.read()
        (self.fixture.root / self.data / 'content.bin').write_bytes(b'changed')
        with self.assertRaises(ResearchAcquisitionError):
            self.review.verify_current(report)
