import json
import sqlite3
import tempfile
import threading
import unittest
from contextlib import closing
from hashlib import sha256
from http.client import HTTPConnection
from pathlib import Path

from sictra_block4_orchestrator.operations import initialize
from sictra_block4_orchestrator.operations_store import OperationsError
from sictra_block4_orchestrator.operations_web import create_operations_server
from sictra_block4_orchestrator.factsheet import build_factsheet, render_factsheet
from test_block1_eurostat_maritime_mapper import workbook


class FactsheetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.now = 1789300800
        self.root = Path(self.temp.name) / 'state'
        self.service = initialize(self.root, now=self.now)
        self.service.clock = lambda: self.now
        self.service.defer_evidence_reviews(True)
        self.raw = workbook(last_updated='07/09/2026 06:14', rows=(('BE','Belgium','14',None,'15'),))
        for raw in (workbook(), self.raw):
            source = Path(self.temp.name) / 'input.xlsx'; source.write_bytes(raw)
            self.service.register_file(source, expected_sha256=sha256(raw).hexdigest())
            self.service.tick()
        self.identity = next(iter(self.service.store.latest('OUTPUT')))

    def tearDown(self):
        self.service.stop(); self.temp.cleanup()

    def test_identity_source_checksum_and_deferred_review_are_read_only(self):
        self.service.store.put('DEFERRED_REVIEW', 'unrelated', {'dossier_id':'elsewhere'})
        before = self.service.store.records()
        value = build_factsheet(self.service, self.identity)
        self.assertEqual('TELECARE_FACTSHEET_V1', value['schema'])
        # Independently hash the last retained input, not the factsheet/design
        # projection. ZIP metadata legitimately differs across operating systems.
        evidence = json.loads((self.root/'pipeline'/'evidence.json').read_text(encoding='utf-8'))['records'][-1]
        retained = evidence['evidence']['content']
        self.assertEqual(sha256(self.raw).hexdigest(), json.loads(retained)['provenance']['source_file_sha256'])
        self.assertEqual(sha256(retained.encode()).hexdigest(), value['source']['source_hash'])
        self.assertEqual(evidence['evidence_id'], value['source']['evidence_id'])
        self.assertEqual(self.identity, value['id'])
        self.assertEqual(1, len(value['deferred_reviews']))
        self.assertEqual('NOT_ACCEPTED', value['deferred_reviews'][0]['acceptance'])
        self.assertEqual('BLOCKED', value['publication'])
        self.assertEqual('NOT_ATTACHED', value['validation']['independent_review'])
        checksum = value.pop('sha256')
        canonical = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()
        self.assertEqual(sha256(canonical).hexdigest(), checksum)
        self.assertEqual(before, self.service.store.records())
        self.assertNotIn('control_token', str(value)); self.assertNotIn('recovery_key', str(value))

    def test_expiry_unknown_identity_and_tamper_rejected(self):
        with self.assertRaises(OperationsError): build_factsheet(self.service, 'z' * 64)
        with self.assertRaises(OperationsError): build_factsheet(self.service, '0' * 64)
        self.now += 86402
        with self.assertRaises(ValueError): build_factsheet(self.service, self.identity)
        self.now -= 86402
        with closing(sqlite3.connect(self.root/'operations.sqlite')) as db:
            db.execute("UPDATE records SET body='{}' WHERE kind='OUTPUT'")
            db.commit()
        with self.assertRaisesRegex(OperationsError, 'INTEGRITY'):
            build_factsheet(self.service, self.identity)

    def test_misaligned_content_is_rejected_and_html_escapes_labels(self):
        value = build_factsheet(self.service, self.identity)
        value['title']='<script>alert(1)</script>'
        rendered = render_factsheet(value)
        self.assertNotIn('<script>', rendered)
        self.assertIn('&lt;script&gt;', rendered)
        output = self.service.output(self.identity)
        output['plain_text']='unbound claim'
        self.service.store.put('OUTPUT', self.identity, output)
        with self.assertRaisesRegex(OperationsError, 'CONTENT_MISMATCH'):
            build_factsheet(self.service, self.identity)

    def test_http_export_view_origin_and_stale_rejection(self):
        server=create_operations_server(self.service, port=0)
        thread=threading.Thread(target=server.serve_forever, daemon=True);thread.start()
        def read(suffix, headers=None):
            client=HTTPConnection('127.0.0.1',server.server_port)
            try:
                client.request('GET',f'/api/operations/outputs/{self.identity}/{suffix}',headers=headers or {})
                response=client.getresponse()
                return response.status,dict(response.getheaders()),response.read()
            finally: client.close()
        try:
            status,headers,body=read('factsheet.json')
            self.assertEqual(200,status);self.assertIn('attachment',headers['Content-Disposition'])
            self.assertEqual(self.identity,json.loads(body)['id'])
            status,headers,body=read('factsheet')
            self.assertEqual(200,status);self.assertIn(b'Ficha de trazabilidad',body)
            self.assertIn("default-src 'none'",headers['Content-Security-Policy'])
            self.assertEqual(403,read('factsheet',{'Origin':'https://evil.example'})[0])
            self.now+=86402;self.assertEqual(409,read('factsheet.json')[0])
        finally:server.shutdown();server.server_close();thread.join(timeout=2)
