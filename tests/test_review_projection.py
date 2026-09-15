from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
import json
from http.client import HTTPConnection
from contextlib import closing
import threading
import time

from sictra_block4_orchestrator.operations import initialize, OperationsService
from sictra_block4_orchestrator.operations_store import OperationsError
from sictra_block4_orchestrator.review_projection import review_projection
from test_block1_eurostat_maritime_mapper import workbook


class ReviewProjectionTests(unittest.TestCase):
    def test_each_console_serves_own_projection_and_rejects_hostile_origin(self):
        from sictra_block2_design.design_console_web import create_server as design_server
        from sictra_block3_precision.precision_console_web import create_server as precision_server
        self.now=int(time.time());self.ready()
        servers=[design_server(self.root/'design.sqlite','TEST',port=0),precision_server(port=0)]
        for block,server in zip((2,3),servers):
            server.operations_state=self.root
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                with closing(HTTPConnection('127.0.0.1',server.server_port)) as client:
                    client.request('GET','/api/review-artifacts');response=client.getresponse();data=json.loads(response.read())
                    self.assertEqual(200,response.status);self.assertEqual(block,data['block']);self.assertEqual(1,len(data['artifacts']))
                    self.assertEqual('NOT_ACCEPTED',data['acceptance'])
                with closing(HTTPConnection('127.0.0.1',server.server_port)) as client:
                    client.request('GET','/api/review-artifacts',headers={'Origin':'https://evil.example'})
                    response=client.getresponse();response.read();self.assertEqual(403,response.status)
            finally:server.shutdown();server.server_close();thread.join(timeout=2)

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)/'state'
        self.now=1789300800;self.service=initialize(self.root,now=self.now);self.service.clock=lambda:self.now

    def tearDown(self):
        self.service.stop();self.temp.cleanup()

    def register(self,raw):
        source=Path(self.temp.name)/'input.xlsx';source.write_bytes(raw)
        return self.service.register_file(source,expected_sha256=sha256(raw).hexdigest())

    def ready(self):
        self.register(workbook());self.service.tick()
        self.register(workbook(last_updated='07/09/2026 06:14',rows=(('BE','Belgium','14',None,'15'),)));self.service.tick()

    def test_both_consoles_expose_same_verified_artifact_with_separate_owned_content(self):
        self.ready();before=self.service.store.records()
        design=review_projection(self.root,2,clock=lambda:self.now)['artifacts'][0]
        precision=review_projection(self.root,3,clock=lambda:self.now)['artifacts'][0]
        self.assertEqual(design['id'],precision['id']);self.assertEqual(design['dossier_id'],precision['dossier_id'])
        self.assertEqual(design['artifact_fingerprint'],precision['content']['artifact_fingerprint'])
        self.assertEqual('CONTENT_DESIGN_CANDIDATE',design['content']['artifact_type'])
        self.assertIn('14 miles de toneladas',str(precision['content']['content_blocks']))
        self.assertNotIn('control_token',design);self.assertNotIn('keys',precision)
        self.assertEqual(before,self.service.store.records())

    def test_expired_outputs_and_missing_store_never_fall_back_to_demo(self):
        self.ready();self.now+=86402
        for block in (2,3):
            result=review_projection(self.root,block,clock=lambda:self.now)
            self.assertEqual([],result['artifacts']);self.assertEqual(1,len(result['unavailable']))
            self.assertEqual('BLOCKED',result['publication'])
        missing=Path(self.temp.name)/'missing'
        with self.assertRaises(OperationsError):review_projection(missing,2)
        self.assertFalse(missing.exists())
        self.assertEqual('NOT_CONFIGURED',review_projection(None,3)['status'])

    def test_owner_deferred_review_policy_continues_without_approving_or_replaying(self):
        self.service.defer_evidence_reviews(True);self.ready()
        self.assertEqual([],self.service.snapshot()['intake_waiting'])
        record=self.service.snapshot()['deferred_reviews'][0]
        self.assertEqual('CLOSED_BY_ABSTENTION_EVIDENCE_DEFERRED',record['state'])
        self.assertEqual('NOT_ACCEPTED',record['acceptance']);self.assertEqual('BLOCKED',record['publication'])
        self.assertTrue(record['uncertainty'])
        self.register(workbook(last_updated='08/09/2026 06:14',rows=(('BE','Belgium','16',None,'17'),)));self.service.tick()
        self.assertEqual(2,len(self.service.store.latest('OUTPUT')))
        self.assertEqual(2,len(self.service.store.latest('DEFERRED_REVIEW')))
        self.service.tick();self.assertEqual(2,len(self.service.store.latest('OUTPUT')))
        reopened=OperationsService(self.root,clock=lambda:self.now)
        self.assertTrue(reopened.snapshot()['evidence_review_deferred'])
        self.assertTrue(all(x['publication']=='BLOCKED' for x in reopened.store.latest('OUTPUT').values()))

    def test_defer_does_not_close_ingestion_failure_or_override_pause(self):
        self.service.defer_evidence_reviews(True)
        job=self.register(workbook());next((self.root/'inbox').glob('*.xlsx')).write_bytes(b'tampered')
        self.service.tick()
        self.assertEqual(job,self.service.snapshot()['intake_waiting'][0]['job_id'])
        self.assertEqual([],self.service.snapshot()['deferred_reviews'])
        self.service.set_paused(True);self.assertEqual('PAUSED',self.service.tick()['state'])
