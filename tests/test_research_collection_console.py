"""Collection console contract: real readers/persistence; only HTTP fixture."""
from copy import deepcopy
from contextlib import redirect_stdout, redirect_stderr
from hashlib import sha256
from http.client import HTTPConnection
import importlib
import io
import json
from pathlib import Path
import threading
import time
import sys
import unittest
from unittest.mock import patch

import test_research_collection as fixtures
from sictra_block1.research_acquisition import ResearchAcquisitionError, canonical
from sictra_block4_orchestrator.operations import initialize
from sictra_block4_orchestrator import operations, operations_web
from sictra_block4_orchestrator.operations_web import create_operations_server
from sictra_block1.research_review import render_research_review


class CollectionConsoleTests(unittest.TestCase):
    def setUp(self):
        try:
            self.module = importlib.import_module('sictra_block1.research_collection_review')
        except ModuleNotFoundError:
            self.fail('Exact collection console selection is not implemented')
        self.fixture = fixtures.CollectionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.original = self.fixture.collect()
        self.selection = self.original['selection_id']
        self.review = self.module.CollectionResearchReview(self.fixture.root, self.selection,
                                                          clock=lambda: self.fixture.now)

    def files(self):
        return {str(p.relative_to(self.fixture.root)): p.read_bytes()
                for p in self.fixture.root.rglob('*') if p.is_file()}

    def corrupt_statbel(self):
        identity = self.original['selection']['candidates']['STATBEL_BE_SEA_TRANSPORT_HTML']['candidate_id']
        (self.fixture.root / 'statbel' / identity / 'content.bin').write_bytes(b'altered')

    def test_exact_selection_reopens_all_seven_originals_without_network_or_writes(self):
        before, requests = self.files(), len(self.fixture.calls)
        report = self.review.read()
        self.assertEqual(self.selection, report['collection']['selection_id'])
        self.assertEqual(7, len(report['collection']['selection']['candidates']))
        self.assertEqual([272698.25, 274369.05], [r['value_thousand_tonnes'] for r in
            report['admission_review']['data']['observations']])
        self.assertEqual('NOT_ESTABLISHED', report['collection']['comparison']['independent_root'])
        self.assertEqual('NOT_ADMITTED', report['admission'])
        self.assertEqual('NONE', report['runtime_effect'])
        self.assertEqual('BLOCKED', report['publication'])
        self.review.verify_current(report)
        reopened = self.module.CollectionResearchReview(self.fixture.root, self.selection,
                                                        clock=lambda: self.fixture.now)
        self.assertEqual(report, reopened.read())
        self.assertEqual(before, self.files())
        self.assertEqual(requests, len(self.fixture.calls))

    def test_report_self_reseal_cannot_forge_outer_authority_or_comparison(self):
        report = self.review.read()
        for mutate in (lambda r: r.update(admission='APPROVED'),
                       lambda r: r['collection']['comparison'].update(independent_root='ESTABLISHED'),
                       lambda r: r.update(expires_at=r['expires_at'] + 1),
                       lambda r: r['collection'].update(selection_id='a' * 64)):
            with self.subTest(mutate=mutate):
                forged = deepcopy(report)
                mutate(forged)
                embedded = forged['collection']
                embedded['fingerprint'] = sha256(canonical({k: v for k, v in embedded.items()
                                                            if k != 'fingerprint'})).hexdigest()
                forged['fingerprint'] = sha256(canonical({k: v for k, v in forged.items()
                                                          if k != 'fingerprint'})).hexdigest()
                with self.assertRaises(ResearchAcquisitionError):
                    self.review.verify_current(forged)

    def test_render_identifies_collection_and_unconfirmed_numeric_disagreement(self):
        body = render_research_review(self.review.read())
        self.assertIn(self.selection, body)
        self.assertIn('288.75', body)
        self.assertIn('524.95', body)
        self.assertIn('NOT_ESTABLISHED', body)
        self.assertIn('UNCONFIRMED', body)
        self.assertIn('No demuestra equivalencia', body)
        self.assertIn('NOT_ADMITTED', body)

    def test_numeric_gap_heading_defines_subtraction_direction(self):
        body = render_research_review(self.review.read())
        self.assertIn('Diferencia (Statbel - Eurostat)', body)

    def test_non_eurostat_original_tamper_withdraws_entire_collection(self):
        report = self.review.read()
        self.corrupt_statbel()
        for action in (self.review.read, lambda: self.review.verify_current(report)):
            with self.assertRaises(ResearchAcquisitionError):
                action()

    def test_missing_committed_outcome_withdraws_collection(self):
        report = self.review.read()
        (self.fixture.root / 'cycle-outcome.json').unlink()
        with self.assertRaises(ResearchAcquisitionError):
            self.review.verify_current(report)
        with self.assertRaises(ResearchAcquisitionError):
            self.review.read()

    def test_expiry_and_clock_rollback_reject_current_and_prepared_report(self):
        report = self.review.read()
        for now in (report['checked_at'] - 1, report['expires_at']):
            self.fixture.now = now
            for action in (self.review.read, lambda: self.review.verify_current(report)):
                with self.assertRaises(ResearchAcquisitionError):
                    action()

    def test_partial_malformed_or_wrong_selection_rejects_at_construction(self):
        for identity in ('../escape', True, 'A' * 64, 'a' * 64):
            with self.assertRaises(ResearchAcquisitionError):
                self.module.CollectionResearchReview(self.fixture.root, identity,
                                                      clock=lambda: self.fixture.now)
        with self.assertRaises(ResearchAcquisitionError):
            self.module.CollectionResearchReview(self.fixture.root / 'missing', self.selection,
                                                  clock=lambda: self.fixture.now)

    def server(self):
        service = initialize(Path(self.fixture.temp.name) / 'operations', now=self.fixture.now)
        self.addCleanup(service.stop)
        server = create_operations_server(service, port=0, research_review=self.review)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join, 3)
        self.addCleanup(server.shutdown)
        return server, service

    def request(self, server, path):
        connection = HTTPConnection('127.0.0.1', server.server_port, timeout=10)
        self.addCleanup(connection.close)
        connection.request('GET', path)
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()

    def test_real_http_json_contains_exact_selection_and_preserves_journal(self):
        server, service = self.server()
        before, originals = service.store.records(), self.files()
        status, headers, body = self.request(server, '/api/research')
        self.assertEqual(200, status)
        self.assertEqual(self.selection, json.loads(body)['collection']['selection_id'])
        self.assertIn('no-store', headers['Cache-Control'])
        status, _, body = self.request(server, '/research')
        self.assertEqual(200, status)
        self.assertIn(b'272698.25', body)
        self.assertEqual(before, service.store.records())
        self.assertEqual(originals, self.files())

    def test_statbel_tamper_during_html_render_withdraws_measurements_before_headers(self):
        server, service = self.server()
        before = service.store.records()
        def tampering(report):
            body = render_research_review(report)
            self.corrupt_statbel()
            return body
        with patch('sictra_block4_orchestrator.operations_web.render_research_review', side_effect=tampering):
            status, _, body = self.request(server, '/research')
        self.assertEqual(409, status)
        self.assertIn(b'UNAVAILABLE', body)
        self.assertNotIn(b'272698.25', body)
        self.assertEqual(409, self.request(server, '/api/research')[0])
        self.assertEqual(before, service.store.records())

    def test_expiry_during_render_withdraws_collection(self):
        server, _ = self.server()
        def expiring(report):
            body = render_research_review(report)
            self.fixture.now = report['expires_at']
            return body
        with patch('sictra_block4_orchestrator.operations_web.render_research_review', side_effect=expiring):
            status, _, body = self.request(server, '/research')
        self.assertEqual(409, status)
        self.assertIn(b'UNAVAILABLE', body)
        self.assertNotIn(b'272698.25', body)

    def serialization_attack(self, mutate):
        server, service = self.server()
        before = service.store.records()
        real_dumps = json.dumps
        def changing(payload, *args, **kwargs):
            body = real_dumps(payload, *args, **kwargs)
            # Attack response serialization only, never canonical input reads.
            if isinstance(payload, dict) and payload.get('version') == '0.3.0' and not kwargs.get('sort_keys'):
                mutate(payload)
            return body
        with patch('sictra_block4_orchestrator.operations_web.json.dumps', side_effect=changing):
            status, _, body = self.request(server, '/api/research')
        self.assertEqual(409, status)
        self.assertIn(b'UNAVAILABLE', body)
        self.assertNotIn(b'272698.25', body)
        self.assertEqual(before, service.store.records())

    def test_statbel_tamper_during_json_serialization_withdraws_before_success_headers(self):
        self.serialization_attack(lambda _report: self.corrupt_statbel())

    def test_expiry_during_json_serialization_withdraws_before_success_headers(self):
        def expire(report):
            self.fixture.now = report['expires_at']
        self.serialization_attack(expire)


class CollectionStartupTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.CollectionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.now = int(time.time())
        self.report = self.fixture.collect()
        self.state = Path(self.fixture.temp.name) / 'operations'
        self.service = initialize(self.state, now=self.fixture.now)
        self.addCleanup(self.service.stop)

    def args(self):
        return ['operations', '--state', str(self.state), 'serve', '--port', '0',
                '--research-collection-root', str(self.fixture.root),
                '--research-selection-id', self.report['selection_id']]

    def test_cli_collection_root_and_selection_reaches_real_read_only_server(self):
        reports = []
        before = {str(p): p.read_bytes() for p in self.fixture.root.rglob('*') if p.is_file()}
        real_server = operations_web.create_operations_server
        def bounded_server(service, **kwargs):
            reports.append(kwargs['research_review'].read())
            server = real_server(service, **kwargs)
            def finish():
                raise KeyboardInterrupt
            server.serve_forever = finish
            return server
        with patch.object(sys, 'argv', self.args()), redirect_stdout(io.StringIO()), \
                patch.object(operations_web, 'create_operations_server', side_effect=bounded_server):
            self.assertEqual(0, operations.main())
        self.assertEqual(self.report['selection_id'], reports[0]['collection']['selection_id'])
        self.assertEqual('NONE', reports[0]['runtime_effect'])
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.fixture.root.rglob('*') if p.is_file()})

    def test_partial_and_mixed_configuration_reject_before_start(self):
        base = self.args()[:6]
        cases = [base + ['--research-collection-root', str(self.fixture.root)],
                 base + ['--research-selection-id', self.report['selection_id']]]
        for flag, value in (('--research-root', str(self.fixture.root / 'eurostat')),
                            ('--research-data-id', 'a' * 64),
                            ('--research-metadata-id', 'a' * 64),
                            ('--research-national-id', 'a' * 64),
                            ('--research-regional-id', 'a' * 64)):
            cases.append(self.args() + [flag, value])
        for args in cases:
            with self.subTest(args=args), patch.object(sys, 'argv', args), redirect_stderr(io.StringIO()), \
                    patch.object(operations.OperationsService, 'start', side_effect=AssertionError('worker must not start')), \
                    patch.object(operations_web, 'create_operations_server', side_effect=AssertionError('server must not start')):
                with self.assertRaises(SystemExit) as caught:
                    operations.main()
                self.assertEqual(2, caught.exception.code)

    def test_tampered_collection_rejects_before_worker_or_server(self):
        identity = self.report['selection']['candidates']['STATBEL_CC_BY_4_0']['candidate_id']
        (self.fixture.root / 'statbel' / identity / 'content.bin').write_bytes(b'altered')
        with patch.object(sys, 'argv', self.args()), \
                patch.object(operations.OperationsService, 'start', side_effect=AssertionError('worker must not start')), \
                patch.object(operations_web, 'create_operations_server', side_effect=AssertionError('server must not start')):
            with self.assertRaises(ResearchAcquisitionError):
                operations.main()


if __name__ == '__main__':
    unittest.main()
