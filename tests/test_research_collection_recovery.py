"""Complete collection recovery; existing collectors/readers are real fixtures."""
from contextlib import redirect_stdout, redirect_stderr
from hashlib import sha256
from http.client import HTTPException
import importlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from sictra_block1.research_acquisition import canonical, ResearchAcquisitionError
from sictra_block1.research_collection import read_collection, ResearchCollection
from sictra_block1.research_recovery import ResearchRecoveryError, restore as legacy_restore
import test_research_collection as collection_fixture


def files(root):
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in root.rglob('*') if p.is_file()}


class CollectionRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = collection_fixture.CollectionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.report = self.fixture.collect()
        self.root = self.fixture.root
        self.base = self.root.parent
        self.archive, self.target = self.base / 'archive', self.base / 'restored'
        self.now = self.fixture.now
        self.identity = self.report['selection_id']
        try:
            self.module = importlib.import_module('sictra_block1.research_collection_recovery')
        except ModuleNotFoundError:
            self.fail('Complete Eurostat+Statbel collection recovery is missing')

    def backup(self):
        return self.module.backup_collection(self.root, self.identity, self.archive, clock=lambda: self.now)

    def restore(self, receipt):
        return self.module.restore_collection(self.archive, self.target,
            expected_manifest_sha256=receipt['manifest_sha256'], clock=lambda: self.now)

    def test_exact_seventeen_files_restore_reopen_and_spent_marker_prevents_reacquisition(self):
        # Break: omit Statbel/selection/outcome/marker, renew TTL, or call acquisition.
        original = files(self.root)
        with patch('socket.create_connection', side_effect=AssertionError('no network')):
            receipt = self.backup()
            result = self.restore(receipt)
            report = read_collection(self.target, self.identity, clock=lambda: self.now)
            with self.assertRaisesRegex(ResearchAcquisitionError, 'ALREADY_STARTED'):
                ResearchCollection(self.target, clock=lambda: self.now).collect()
        self.assertEqual(17, len(original))
        self.assertEqual(original, files(self.target))
        self.assertEqual(original, files(self.root))
        self.assertEqual(receipt['file_count'], 17)
        self.assertEqual(result['candidate_count'], 7)
        self.assertEqual(result['runtime_effect'], 'NONE')
        self.assertEqual(result['admission'], 'NOT_ADMITTED')
        self.assertEqual(self.report['budget'], report['budget'])
        self.assertEqual(self.report['expires_at'], report['expires_at'])
        self.assertEqual(['288.75', '524.95'], [r['numeric_gap_thousand_tonnes'] for r in report['comparison']['rows']])

    def test_expired_history_is_recovered_but_not_made_current(self):
        original = files(self.root)
        self.now += 90000
        receipt = self.backup()
        self.restore(receipt)
        self.assertEqual(original, files(self.target))
        with self.assertRaisesRegex(ResearchAcquisitionError, 'NOT_CURRENT'):
            read_collection(self.target, self.identity, clock=lambda: self.now)

    def test_wrong_digest_or_tampered_statbel_never_publishes_restore(self):
        receipt = self.backup()
        with self.assertRaises(ResearchRecoveryError):
            self.module.restore_collection(self.archive, self.target,
                expected_manifest_sha256='0' * 64, clock=lambda: self.now)
        statbel_id = self.report['selection']['candidates']['STATBEL_BE_SEA_TRANSPORT_HTML']['candidate_id']
        (self.archive / 'data' / 'statbel' / statbel_id / 'content.bin').write_bytes(b'changed')
        with self.assertRaises(ResearchRecoveryError):
            self.restore(receipt)
        self.assertFalse(self.target.exists())

    def test_self_resealed_manifest_cannot_replace_external_digest(self):
        receipt = self.backup()
        path = self.archive / 'archive-manifest.json'
        value = json.loads(path.read_bytes())
        value['created_at'] += 1
        path.write_bytes(canonical(value))
        with self.assertRaises(ResearchRecoveryError):
            self.restore(receipt)
        self.assertFalse(self.target.exists())

    def test_attacker_supplied_new_digest_cannot_authorize_arbitrary_paths(self):
        receipt = self.backup()
        path = self.archive / 'archive-manifest.json'
        value = json.loads(path.read_bytes())
        value['files']['../../outside'] = '0' * 64
        data = canonical(value)
        path.write_bytes(data)
        receipt['manifest_sha256'] = sha256(data).hexdigest()
        with self.assertRaises(ResearchRecoveryError):
            self.restore(receipt)
        self.assertFalse(self.target.exists())
        self.assertFalse((self.base / 'outside').exists())

    def test_source_private_files_are_not_copied_and_archive_extras_reject(self):
        (self.root / 'operator.key').write_bytes(b'private local fixture')
        receipt = self.backup()
        self.assertNotIn('operator.key', files(self.archive / 'data'))
        (self.archive / 'operator.key').write_bytes(b'not permitted')
        with self.assertRaises(ResearchRecoveryError):
            self.restore(receipt)
        self.assertFalse(self.target.exists())

    def test_missing_original_or_commit_outcome_rejects_before_archive(self):
        path = self.root / 'cycle-outcome.json'
        original = path.read_bytes()
        path.unlink()
        with self.assertRaises(ResearchRecoveryError):
            self.backup()
        path.write_bytes(original)
        identity = self.report['selection']['candidates']['STATBEL_CC_BY_4_0']['candidate_id']
        (self.root / 'statbel' / identity / 'content.bin').unlink()
        with self.assertRaises(ResearchRecoveryError):
            self.backup()
        self.assertFalse(self.archive.exists())

    def test_spent_budget_marker_cannot_be_rewritten_before_backup(self):
        path = self.root / 'cycle-start.json'
        marker = json.loads(path.read_bytes())
        marker['budget_before']['attempts'] = 7
        path.write_bytes(canonical(marker))
        with self.assertRaises(ResearchRecoveryError):
            self.backup()
        self.assertFalse(self.archive.exists())

    def test_resealed_selection_with_foreign_rights_hash_rejects(self):
        path = self.root / 'selections' / self.identity / 'selection.json'
        manifest = json.loads(path.read_bytes())
        manifest['candidates']['STATBEL_CC_BY_4_0']['content_sha256'] = '0' * 64
        encoded = canonical(manifest)
        self.identity = sha256(encoded).hexdigest()
        new_slot = path.parent.parent / self.identity
        new_slot.mkdir()
        (new_slot / 'selection.json').write_bytes(encoded)
        outcome = json.loads((self.root / 'cycle-outcome.json').read_bytes())
        outcome['selection_id'] = self.identity
        (self.root / 'cycle-outcome.json').write_bytes(canonical(outcome))
        with self.assertRaises(ResearchRecoveryError):
            self.backup()
        self.assertFalse(self.archive.exists())

    def test_existing_destination_and_overlap_never_overwrite_operator_data(self):
        self.target.mkdir()
        marker = self.target / 'keep'
        marker.write_bytes(b'owner data')
        receipt = self.backup()
        with self.assertRaises(ResearchRecoveryError):
            self.restore(receipt)
        self.assertEqual(marker.read_bytes(), b'owner data')
        with self.assertRaises(ResearchRecoveryError):
            self.module.backup_collection(self.root, self.identity, self.root / 'nested', clock=lambda: self.now)

    def test_publication_failure_cleans_stage_and_never_exposes_final_root(self):
        receipt = self.backup()
        with patch.object(self.module, '_publish', side_effect=OSError('disk failure')):
            with self.assertRaises(ResearchRecoveryError):
                self.restore(receipt)
        self.assertFalse(self.target.exists())
        self.assertFalse(list(self.base.glob('.collection-recovery-*')))

    def test_source_change_during_archive_write_withdraws_publication(self):
        original_write = self.module._write
        def changed(path, data):
            original_write(path, data)
            if path.name == 'archive-manifest.json':
                with (self.root / 'cycle-start.json').open('ab') as output:
                    output.write(b'changed')
        with patch.object(self.module, '_write', side_effect=changed), self.assertRaises(ResearchRecoveryError):
            self.backup()
        self.assertFalse(self.archive.exists())
        self.assertFalse(list(self.base.glob('.collection-recovery-*')))

    def test_rollback_and_future_archive_creation_reject(self):
        receipt = self.backup()
        self.now -= 1
        with self.assertRaises(ResearchRecoveryError):
            self.restore(receipt)
        self.assertFalse(self.target.exists())

    def test_old_eurostat_reader_cannot_consume_collection_archive(self):
        receipt = self.backup()
        with self.assertRaises(ResearchRecoveryError):
            legacy_restore(self.archive, self.target, expected_manifest_sha256=receipt['manifest_sha256'])
        self.assertFalse(self.target.exists())

    def test_actual_resealed_malformed_metadata_fails_with_controlled_diagnostic(self):
        # Integrity identifiers cannot turn malformed retained HTML into evidence.
        selection_path = self.root / 'selections' / self.identity / 'selection.json'
        selection = json.loads(selection_path.read_bytes())
        selected = selection['candidates']['EUROSTAT_MAR_METADATA']
        slot = self.root / 'eurostat' / selected['candidate_id']
        descriptor = json.loads((slot / 'manifest.json').read_bytes())
        original_length = len((slot / 'content.bin').read_bytes())
        # CPython 3.11/3.12 can disagree about the internal exception. Both
        # must reject: these bytes contain no required methodology sections.
        content = b'<![bad]>'
        descriptor['content_sha256'] = sha256(content).hexdigest()
        descriptor['byte_length'] = len(content)
        encoded = canonical(descriptor)
        identity = sha256(encoded).hexdigest()
        new_slot = slot.parent / identity
        new_slot.mkdir()
        (new_slot / 'manifest.json').write_bytes(encoded)
        (new_slot / 'content.bin').write_bytes(content)
        selected['candidate_id'] = identity
        selected['content_sha256'] = descriptor['content_sha256']
        selection['budget']['received_bytes'] += len(content) - original_length
        encoded = canonical(selection)
        self.identity = sha256(encoded).hexdigest()
        new_selection = selection_path.parent.parent / self.identity
        new_selection.mkdir()
        (new_selection / 'selection.json').write_bytes(encoded)
        outcome_path = self.root / 'cycle-outcome.json'
        outcome = json.loads(outcome_path.read_bytes())
        outcome['selection_id'] = self.identity
        outcome['budget'] = selection['budget']
        outcome_path.write_bytes(canonical(outcome))
        with self.assertRaises(ResearchRecoveryError):
            self.backup()
        self.assertFalse(self.archive.exists())
        self.assertFalse(list(self.base.glob('.collection-recovery-*')))

    def test_expected_parser_exceptions_are_controlled_for_backup_and_restore(self):
        receipt = self.backup()
        for error_type in (AssertionError, HTTPException):
            for operation in ('backup', 'restore'):
                with self.subTest(error=error_type.__name__, operation=operation):
                    destination = self.base / f'{operation}-{error_type.__name__}'
                    with patch.object(self.module.ResearchReview, 'read', side_effect=error_type('bad retained HTML')):
                        with self.assertRaises(ResearchRecoveryError):
                            if operation == 'backup':
                                self.module.backup_collection(self.root, self.identity, destination, clock=lambda: self.now)
                            else:
                                self.module.restore_collection(self.archive, destination,
                                    expected_manifest_sha256=receipt['manifest_sha256'], clock=lambda: self.now)
                    self.assertFalse(destination.exists())
                    self.assertFalse(list(self.base.glob('.collection-recovery-*')))

    def test_cli_backup_restore_and_controlled_missing_source(self):
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            self.assertEqual(self.module.main(['backup', '--root', str(self.root),
                '--selection-id', self.identity, '--destination', str(self.archive)]), 0)
        receipt = json.loads(output.getvalue())
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            self.assertEqual(self.module.main(['restore', '--archive', str(self.archive),
                '--destination', str(self.target), '--manifest-sha256', receipt['manifest_sha256']]), 0)
        self.assertEqual(files(self.root), files(self.target))
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors), self.assertRaises(SystemExit) as failure:
            self.module.main(['backup', '--root', str(self.base / 'missing'),
                '--selection-id', self.identity, '--destination', str(self.base / 'unused')])
        self.assertEqual(failure.exception.code, 2)
        self.assertEqual(output.getvalue(), '')
        self.assertFalse((self.base / 'missing').exists())


if __name__ == '__main__':
    unittest.main()
