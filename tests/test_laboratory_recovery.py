from hashlib import sha256
from pathlib import Path
import tempfile
import unittest

from sictra_block4_orchestrator.operations import initialize, OperationsService
from sictra_block4_orchestrator.laboratory_recovery import backup, restore
from sictra_block4_orchestrator.operations_store import OperationsError, process_lock
from test_block1_eurostat_maritime_mapper import workbook


class LaboratoryRecoveryTests(unittest.TestCase):
    def test_empty_initialized_laboratory_preserves_uncreated_evidence_stores(self):
        empty=self.parent/'empty';initialize(empty)
        archive=self.parent/'empty-backup';backup(empty,archive)
        retired=self.parent/'empty-retired';empty.rename(retired)
        restore(archive,empty,retired)
        self.assertEqual([],OperationsService(empty).snapshot()['outputs'])
        self.assertFalse((empty/'pipeline'/'evidence.json').exists())

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.parent = Path(self.temp.name)
        self.root = self.parent / 'state'
        self.service = initialize(self.root, now=1789300800)
        self.service.clock = lambda: 1789300800
        for raw in (workbook(), workbook(last_updated='07/09/2026 06:14', rows=(('BE','Belgium','14',None,'15'),))):
            path = self.parent / 'source.xlsx'; path.write_bytes(raw)
            self.service.register_file(path, expected_sha256=sha256(raw).hexdigest()); self.service.tick()
        self.archive = self.parent / 'archive'

    def tearDown(self):
        self.service.stop();self.temp.cleanup()

    def test_full_restore_retains_sources_dossiers_and_outputs_but_stays_paused(self):
        launch_config = b'{"schema":"TELECARE_LOCAL_PATHS_V1","intake_store":"legacy","design_trace":"legacy"}'
        (self.root / 'launch-paths.json').write_bytes(launch_config)
        before = self.service.store.latest('OUTPUT')
        result = backup(self.root, self.archive)
        self.assertFalse(result['keys_included'])
        self.assertFalse(list(self.archive.rglob('*.key')))
        retired = self.parent / 'retired'
        self.root.rename(retired)
        self.assertEqual('RESTORED_PAUSED', restore(self.archive, self.root, retired)['status'])
        recovered = OperationsService(self.root, clock=lambda:1789300800)
        self.assertTrue(recovered.is_paused())
        self.assertEqual(launch_config, (self.root / 'launch-paths.json').read_bytes())
        self.assertEqual(before, recovered.store.latest('OUTPUT'))
        output = next(iter(before.values()))
        self.assertIn('12.5', recovered.output(output['id'])['plain_text'])
        self.assertIn('14 miles de toneladas', recovered.output(output['id'])['plain_text'])
        self.assertEqual(2,len(list((self.root/'inbox').glob('*.xlsx'))))
        self.assertEqual('PAUSED', recovered.tick()['state'])
        recovered.set_paused(False); recovered.tick()
        self.assertEqual(1,len(recovered.store.latest('OUTPUT')))

    def test_tampered_archive_and_existing_target_are_rejected_before_writes(self):
        backup(self.root, self.archive)
        with self.assertRaisesRegex(OperationsError,'TARGET_EXISTS'):restore(self.archive,self.root,self.root)
        retired=self.parent/'retired';self.root.rename(retired)
        (self.archive/'data'/'operations.sqlite').write_bytes(b'altered')
        with self.assertRaisesRegex(OperationsError,'DATA_CHANGED'):restore(self.archive,self.root,retired)
        self.assertFalse(self.root.exists())

    def test_wrong_keys_path_relocation_and_live_service_cannot_be_silently_accepted(self):
        with process_lock(self.root/'service.lock'):
            with self.assertRaises((OSError,OperationsError)):backup(self.root,self.archive)
        self.assertFalse(self.archive.exists())
        backup(self.root,self.archive)
        retired=self.parent/'retired';self.root.rename(retired)
        with self.assertRaisesRegex(OperationsError,'IDENTITY_MISMATCH'):restore(self.archive,self.parent/'different',retired)
        (retired/'keys'/'operations.key').write_bytes(b'x'*32)
        with self.assertRaisesRegex(OperationsError,'SIGNATURE_INVALID'):restore(self.archive,self.root,retired)
        self.assertFalse(self.root.exists())
