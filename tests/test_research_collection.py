"""Real collectors/parsers composed; only external HTTP/DNS use fixtures."""
from contextlib import contextmanager
from hashlib import sha256
import importlib
import io
from http.client import BadStatusLine
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlsplit
from unittest.mock import patch

from sictra_block1.research_acquisition import RECIPES, canonical, ResearchAcquisitionError
from sictra_block1.research_statbel import STATBEL_RECIPES
import test_agent_research_acquisition as http
import test_research_statistics as stats
import test_research_methodology as method
import test_national_methodology as national
import test_regional_methodology as regional
import test_research_statbel as statbel


class CollectionTests(unittest.TestCase):
    def setUp(self):
        try:
            self.module = importlib.import_module('sictra_block1.research_collection')
        except ModuleNotFoundError:
            self.fail('Finite research collection capability is not implemented')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'cycle'
        self.now = http.NOW
        self.calls = []
        self.denied = None
        data = stats.dataset()
        data['dimension']['time']['category']['index'] = {'2023': 0, '2024': 1}
        data['value'], data['status'] = [272698.25, 274369.05], {}
        self.bodies = {
            'EUROSTAT_REUSE_NOTICE': http.BODY,
            'EUROSTAT_MAR_METADATA': method.html_sections(),
            'EUROSTAT_BE_MAR_METADATA': national.national_html(),
            'EUROSTAT_REGIONAL_MAR_METADATA': regional.page(),
            'EUROSTAT_MAR_BE_2023_2024': stats.raw(data),
            'STATBEL_CC_BY_4_0': statbel.TERMS,
            'STATBEL_BE_SEA_TRANSPORT_HTML': statbel.TABLE,
        }
        self.paths = {}
        for recipe, config in {**RECIPES, **STATBEL_RECIPES}.items():
            url = urlsplit(config)
            self.paths[(url.hostname, url.path + ('?' + url.query if url.query else ''))] = recipe
        @contextmanager
        def transport(host, _address, path):
            recipe = self.paths[(host, path)]
            self.calls.append(recipe)
            body = self.bodies[recipe]
            yield http.Response(body, status=403 if recipe == self.denied else 200,
                headers=[('Content-Type', 'application/json' if recipe ==
                         'EUROSTAT_MAR_BE_2023_2024' else 'text/html'),
                         ('Content-Length', str(len(body)))])
        self.transport = transport
        self.cycle = self.new_cycle()

    def new_cycle(self):
        return self.module.ResearchCollection(self.root, clock=lambda: self.now,
            resolver=http.dns, transport=self.transport)

    def collect(self):
        return self.cycle.collect()

    def test_one_cycle_exact_seven_originals_rights_budget_and_literal_gaps(self):
        report = self.collect()
        self.assertEqual(list(self.bodies), self.calls)
        self.assertEqual(7, report['budget']['attempts'])
        self.assertEqual(sum(map(len, self.bodies.values())), report['budget']['received_bytes'])
        self.assertEqual(['288.75', '524.95'], [row['numeric_gap_thousand_tonnes']
            for row in report['comparison']['rows']])
        self.assertEqual(7, len(report['selection']['candidates']))
        self.assertEqual('NOT_ESTABLISHED', report['comparison']['independent_root'])
        for key, value in {'admission': 'NOT_ADMITTED', 'resolution': 'NOT_RESOLVED',
                'acceptance': 'NOT_ACCEPTED', 'runtime_effect': 'NONE',
                'publication': 'BLOCKED'}.items():
            self.assertEqual(value, report[key])

    def test_offline_reopen_does_not_use_network(self):
        report = self.collect()
        self.now += 1
        with patch.object(self.module, 'pinned_response', side_effect=AssertionError('network')):
            reopened = self.module.read_collection(self.root, report['selection_id'],
                clock=lambda: self.now)
        self.assertEqual(report['comparison']['rows'], reopened['comparison']['rows'])
        self.assertEqual(7, len(self.calls))

    def test_denial_stops_and_persists_budget_without_complete_selection(self):
        self.denied = 'EUROSTAT_MAR_METADATA'
        with self.assertRaises(ResearchAcquisitionError):
            self.collect()
        self.assertEqual(['EUROSTAT_REUSE_NOTICE', 'EUROSTAT_MAR_METADATA'], self.calls)
        outcome = json.loads((self.root / 'cycle-outcome.json').read_bytes())
        self.assertEqual('FAILED', outcome['state'])
        self.assertEqual(2, outcome['budget']['attempts'])
        self.assertFalse((self.root / 'selections').exists())

    def test_failed_root_cannot_reset_budget_after_restart(self):
        self.denied = 'EUROSTAT_MAR_METADATA'
        with self.assertRaises(ResearchAcquisitionError):
            self.collect()
        before = list(self.calls)
        with self.assertRaisesRegex(ResearchAcquisitionError, 'ALREADY_STARTED'):
            self.new_cycle().collect()
        self.assertEqual(before, self.calls)

    def test_budget_shared_across_publishers(self):
        self.cycle.budget.attempts = 94
        with self.assertRaises(ResearchAcquisitionError):
            self.collect()
        self.assertEqual(100, self.cycle.budget.attempts)
        self.assertEqual('STATBEL_CC_BY_4_0', self.calls[-1])
        self.assertNotIn('STATBEL_BE_SEA_TRANSPORT_HTML', self.calls)
        self.assertFalse((self.root / 'selections').exists())

    def test_global_bytes_budget_not_reset(self):
        self.cycle.budget.received_bytes = self.module.MAX_SESSION - 1
        with self.assertRaises(ResearchAcquisitionError):
            self.collect()
        self.assertEqual(1, len(self.calls))
        self.assertFalse((self.root / 'selections').exists())

    def test_selection_manifest_tamper_rejected(self):
        report = self.collect()
        path = self.root / 'selections' / report['selection_id'] / 'selection.json'
        value = json.loads(path.read_bytes())
        value['budget']['attempts'] = 0
        path.write_bytes(canonical(value))
        with self.assertRaises(ResearchAcquisitionError):
            self.module.read_collection(self.root, report['selection_id'], clock=lambda: self.now)

    def test_original_body_tamper_rejected(self):
        report = self.collect()
        identity = report['selection']['candidates']['STATBEL_BE_SEA_TRANSPORT_HTML']['candidate_id']
        (self.root / 'statbel' / identity / 'content.bin').write_bytes(statbel.TABLE + b'changed')
        with self.assertRaises(ResearchAcquisitionError):
            self.module.read_collection(self.root, report['selection_id'], clock=lambda: self.now)

    def test_expired_originals_never_reopened_current(self):
        report = self.collect()
        self.now = report['expires_at']
        with self.assertRaises(ResearchAcquisitionError):
            self.module.read_collection(self.root, report['selection_id'], clock=lambda: self.now)

    def test_resealed_forged_conclusion_fails_final_fence(self):
        report = self.collect()
        report['comparison']['independent_root'] = 'VERIFIED'
        report['fingerprint'] = sha256(canonical({k: v for k, v in report.items()
                                               if k != 'fingerprint'})).hexdigest()
        with self.assertRaises(ResearchAcquisitionError):
            self.module.verify_collection_current(self.root, report, clock=lambda: self.now)

    def test_clock_regression_rejected(self):
        report = self.collect()
        self.now -= 1
        with self.assertRaises(ResearchAcquisitionError):
            self.module.read_collection(self.root, report['selection_id'], clock=lambda: self.now)

    def test_offline_missing_root_is_not_created(self):
        with self.assertRaises(ResearchAcquisitionError):
            self.module.read_collection(self.root, 'a' * 64, clock=lambda: self.now)
        self.assertFalse(self.root.exists())

    def test_invalid_clock_rejected_before_requests(self):
        self.now = True
        with self.assertRaises(ResearchAcquisitionError):
            self.collect()
        self.assertEqual([], self.calls)

    def test_publication_failure_keeps_originals_and_has_no_selection(self):
        with patch.object(self.module, '_publish', side_effect=OSError('disk failure')):
            with self.assertRaises(ResearchAcquisitionError):
                self.collect()
        self.assertEqual(7, len(self.calls))
        self.assertEqual(5, len(list((self.root / 'eurostat').iterdir())))
        self.assertEqual(2, len(list((self.root / 'statbel').iterdir())))
        self.assertEqual([], list((self.root / 'selections').iterdir()))

    def test_successful_cycle_cannot_run_again(self):
        self.collect()
        with self.assertRaisesRegex(ResearchAcquisitionError, 'ALREADY_STARTED'):
            self.new_cycle().collect()
        self.assertEqual(7, len(self.calls))

    def test_failed_postpublication_read_removes_only_uncommitted_selection(self):
        with patch.object(self.module, '_read_selection',
                          side_effect=ResearchAcquisitionError('postpublication expiry')):
            with self.assertRaisesRegex(ResearchAcquisitionError, 'postpublication expiry'):
                self.collect()
        self.assertEqual([], list((self.root / 'selections').iterdir()))
        self.assertEqual('FAILED', json.loads((self.root / 'cycle-outcome.json').read_bytes())['state'])
        self.assertEqual(5, len(list((self.root / 'eurostat').iterdir())))

    def test_clock_rollback_between_completed_acquisitions_rejected(self):
        original = self.module.ResearchAcquirer.acquire
        counter = [0]
        def delayed(collector, *args, **kwargs):
            result = original(collector, *args, **kwargs)
            counter[0] += 1
            if counter[0] == 1:
                self.now += 10
            elif counter[0] == 2:
                self.now -= 5
            return result
        with patch.object(self.module.ResearchAcquirer, 'acquire', delayed):
            with self.assertRaisesRegex(ResearchAcquisitionError, 'CLOCK'):
                self.collect()
        self.assertFalse((self.root / 'selections').exists())

    def test_parser_failure_retains_quarantined_bytes_but_not_selection(self):
        self.bodies['EUROSTAT_MAR_METADATA'] = b'<html>method absent</html>'
        with self.assertRaises(ResearchAcquisitionError):
            self.collect()
        self.assertEqual(7, len(self.calls))
        self.assertFalse((self.root / 'selections').exists())

    def test_extra_selection_file_rejected(self):
        report = self.collect()
        (self.root / 'selections' / report['selection_id'] / 'extra').write_bytes(b'not selected')
        with self.assertRaises(ResearchAcquisitionError):
            self.module.read_collection(self.root, report['selection_id'], clock=lambda: self.now)

    def test_cli_offline_read_current_report_and_no_new_requests(self):
        report = self.collect()
        output = io.StringIO()
        with patch.object(self.module.time, 'time', return_value=self.now), patch('sys.stdout', output):
            result = self.module.main(['read', '--root', str(self.root),
                                      '--selection-id', report['selection_id']])
        self.assertEqual(0, result)
        self.assertEqual('NOT_RESOLVED', json.loads(output.getvalue())['resolution'])
        self.assertEqual(7, len(self.calls))

    def test_cli_missing_root_failure_has_no_filesystem_or_network_effect(self):
        output = io.StringIO()
        with patch('sys.stdout', output):
            result = self.module.main(['read', '--root', str(self.root), '--selection-id', 'a' * 64])
        self.assertEqual(2, result)
        self.assertEqual('FAILED', json.loads(output.getvalue())['state'])
        self.assertFalse(self.root.exists())

    def test_transport_failure_records_failed_recipe_and_exception_kind(self):
        @contextmanager
        def broken_transport(*args):
            raise TimeoutError('external request timed out')
            yield
        self.cycle.transport = broken_transport
        with self.assertRaises(ResearchAcquisitionError):
            self.collect()
        outcome = json.loads((self.root / 'cycle-outcome.json').read_bytes())
        self.assertEqual('EUROSTAT_REUSE_NOTICE', outcome['failed_recipe'])
        self.assertEqual('TimeoutError', outcome['error_type'])
        self.assertEqual(1, outcome['budget']['attempts'])

    def test_expiry_during_final_handoff_rejected(self):
        report = self.collect()
        original = self.module.read_collection
        def expiring(*args, **kwargs):
            result = original(*args, **kwargs)
            self.now = report['expires_at']
            return result
        with patch.object(self.module, 'read_collection', expiring):
            with self.assertRaises(ResearchAcquisitionError):
                self.module.verify_collection_current(self.root, report, clock=lambda: self.now)

    def test_malformed_resealed_report_is_controlled_rejection(self):
        for body in ({}, {'selection_id': 'a' * 64, 'checked_at': 1, 'expires_at': 2},
                     {'selection_id': 'a' * 64, 'checked_at': True, 'expires_at': 3}):
            body['fingerprint'] = sha256(canonical(body)).hexdigest()
            with self.assertRaises(ResearchAcquisitionError):
                self.module.verify_collection_current(self.root, body, clock=lambda: self.now)

    def test_remote_html_parser_assertion_is_durable_controlled_failure(self):
        self.bodies['EUROSTAT_MAR_METADATA'] = b'<![bad]>'
        with self.assertRaises(ResearchAcquisitionError):
            self.collect()
        outcome = json.loads((self.root / 'cycle-outcome.json').read_bytes())
        self.assertEqual('FAILED', outcome['state'])
        self.assertEqual('AssertionError', outcome['error_type'])
        self.assertEqual(7, outcome['budget']['attempts'])
        self.assertEqual(7, len(outcome['retained']))
        self.assertFalse((self.root / 'selections').exists())

    def test_bad_http_status_line_is_durable_controlled_failure(self):
        @contextmanager
        def broken_transport(*args):
            raise BadStatusLine('bad remote status')
            yield
        self.cycle.transport = broken_transport
        with self.assertRaises(ResearchAcquisitionError):
            self.collect()
        outcome = json.loads((self.root / 'cycle-outcome.json').read_bytes())
        self.assertEqual('BadStatusLine', outcome['error_type'])
        self.assertEqual(1, outcome['budget']['attempts'])
        self.assertEqual({}, outcome['retained'])

    def test_selection_without_committed_cycle_is_rejected(self):
        report = self.collect()
        (self.root / 'cycle-outcome.json').unlink()
        with self.assertRaisesRegex(ResearchAcquisitionError, 'COMMIT'):
            self.module.read_collection(self.root, report['selection_id'], clock=lambda: self.now)

    def test_failed_cycle_residual_selection_is_unusable(self):
        report = self.collect()
        outcome = {'state': 'FAILED', 'budget': report['budget'], 'boundary': self.module.BOUNDARY}
        (self.root / 'cycle-outcome.json').write_bytes(canonical(outcome))
        with self.assertRaisesRegex(ResearchAcquisitionError, 'COMMIT'):
            self.module.read_collection(self.root, report['selection_id'], clock=lambda: self.now)

    def test_success_outcome_wrong_identity_is_rejected(self):
        report = self.collect()
        outcome = json.loads((self.root / 'cycle-outcome.json').read_bytes())
        outcome['selection_id'] = 'a' * 64
        (self.root / 'cycle-outcome.json').write_bytes(canonical(outcome))
        with self.assertRaisesRegex(ResearchAcquisitionError, 'COMMIT'):
            self.module.read_collection(self.root, report['selection_id'], clock=lambda: self.now)

    def test_cleanup_failure_residual_is_not_committed(self):
        with (patch.object(self.module, '_read_selection',
                          side_effect=ResearchAcquisitionError('postpublication validation')),
                patch.object(self.module, '_cleanup',
                             side_effect=ResearchAcquisitionError('cleanup failed'))):
            with self.assertRaises(ResearchAcquisitionError):
                self.collect()
        slots = list((self.root / 'selections').iterdir())
        self.assertEqual(1, len(slots))
        self.assertEqual('FAILED', json.loads((self.root / 'cycle-outcome.json').read_bytes())['state'])
        with self.assertRaisesRegex(ResearchAcquisitionError, 'COMMIT'):
            self.module.read_collection(self.root, slots[0].name, clock=lambda: self.now)

    def test_cli_nonascii_original_text_survives_legacy_windows_pipe(self):
        self.bodies['EUROSTAT_MAR_METADATA'] = method.html_sections(
            {**method.PARAGRAPHS, 'data_descr': 'Literal\u2011gross weight, not monetary imports.'})
        report = self.collect()
        output_bytes = io.BytesIO()
        output = io.TextIOWrapper(output_bytes, encoding='cp1252', write_through=True)
        with patch.object(self.module.time, 'time', return_value=self.now), patch('sys.stdout', output):
            result = self.module.main(['read', '--root', str(self.root),
                                      '--selection-id', report['selection_id']])
        self.assertEqual(0, result)
        reopened = json.loads(output_bytes.getvalue().decode('cp1252'))
        self.assertIn('Literal\u2011gross weight', str(reopened['research']['admission_review']))
        self.assertEqual('NOT_ADMITTED', reopened['admission'])

    def test_permission_failure_records_safe_codes_not_private_error_message(self):
        @contextmanager
        def denied_transport(*args):
            raise PermissionError(13, 'private credential context', 'C:/private/secret')
            yield
        self.cycle.transport = denied_transport
        with self.assertRaises(ResearchAcquisitionError):
            self.collect()
        raw = (self.root / 'cycle-outcome.json').read_bytes()
        outcome = json.loads(raw)
        self.assertEqual('PermissionError', outcome['error_type'])
        self.assertEqual(13, outcome['error_errno'])
        self.assertIsNone(outcome['error_winerror'])
        self.assertNotIn(b'private', raw)
