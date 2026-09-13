from hashlib import sha256
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from http.client import HTTPConnection
from threading import Thread
from unittest.mock import patch

from sictra_block1.operator_pipeline import initialize_operator_pipeline, pipeline_snapshot
from sictra_block4_orchestrator.local_worker import LocalIntakeWorker, WorkerViolation
from test_block1_eurostat_maritime_mapper import workbook


class LocalWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.inbox = self.root / "inbox"
        self.inbox.mkdir()
        self.pipeline = self.root / "pipeline"
        self.now = 1_788_700_000
        self.key = b"local-worker-testing-key-32-bytes!"
        initialize_operator_pipeline(self.pipeline, clock=lambda: self.now)
        self.worker = self.reopen()

    def tearDown(self):
        self.temp.cleanup()

    def reopen(self):
        return LocalIntakeWorker(self.root / "queue.sqlite", inbox=self.inbox,
            pipeline=self.pipeline, key=self.key, clock=lambda: self.now)

    def enqueue(self, filename="first.xlsx", content=None):
        content = workbook() if content is None else content
        (self.inbox / filename).write_bytes(content)
        return self.worker.enqueue(filename, expected_sha256=sha256(content).hexdigest())

    def test_queued_files_execute_real_pipeline_and_stop_at_literal_dossier_review(self):
        first = self.enqueue()
        self.enqueue("second.xlsx", workbook(last_updated="07/09/2026 06:14",
            rows=(("BE", "Belgium", "14", None, "15"),)))
        results = self.worker.run(max_jobs=4)
        self.assertEqual(["COMPLETED", "REVIEW_REQUIRED"], [result["state"] for result in results])
        self.assertEqual("COMMITTED", results[0]["result"]["runtime"]["enforcement"])
        self.assertEqual("DELTA_DETECTED_NOT_EVIDENCE", results[1]["result"]["status"])
        snapshot = pipeline_snapshot(self.pipeline, clock=lambda: self.now)
        self.assertEqual(2, snapshot["evidence"]["retained_count"])
        self.assertEqual(1, snapshot["dossiers"]["count"])
        self.assertEqual("NONE", results[1]["result"]["publication_authority"])
        self.assertEqual(first, self.enqueue())  # completed input is not resubmitted
        self.assertEqual(2, len(self.reopen().snapshot()["jobs"]))
        self.assertEqual("REVIEW_REQUIRED", self.reopen().run()[0]["state"])

    def test_pause_persists_and_resume_preserves_exact_job(self):
        self.enqueue()
        self.worker.set_paused(True)
        self.assertEqual([{"state": "PAUSED"}], self.reopen().run())
        self.assertEqual(0, pipeline_snapshot(self.pipeline, clock=lambda:self.now)["evidence"]["retained_count"])
        self.reopen().set_paused(False)
        self.assertEqual("COMPLETED", self.reopen().run()[0]["state"])
        self.assertEqual([{"state": "IDLE"}], self.reopen().run())

    def test_changed_file_does_not_execute_and_blocks_later_jobs(self):
        self.enqueue()
        (self.inbox / "first.xlsx").write_bytes(b"tampered")
        self.enqueue("later.xlsx", workbook(rows=(("BE","Belgium","99",None,"15"),)))
        result = self.worker.run(max_jobs=8)
        self.assertEqual(1, len(result))
        self.assertEqual("INPUT_HASH_MISMATCH", result[0]["result"]["reason"])
        self.assertEqual("QUEUED", self.worker.snapshot()["jobs"][1]["state"])
        self.assertEqual(0, pipeline_snapshot(self.pipeline, clock=lambda:self.now)["evidence"]["retained_count"])
        self.assertEqual("REVIEW_REQUIRED", self.worker.run()[0]["state"])

    def test_interrupted_claim_is_never_automatically_reexecuted(self):
        self.enqueue()
        with patch("sictra_block4_orchestrator.local_worker.ingest_eurostat_workbook",
                   side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.worker.run()
        self.assertEqual("RUNNING", self.reopen().snapshot()["jobs"][0]["state"])
        self.assertEqual("RECOVERY_REQUIRED", self.reopen().run()[0]["state"])

    def test_queue_tamper_and_deleted_state_fail_closed(self):
        self.enqueue()
        with closing(sqlite3.connect(self.worker.path)) as db:
            db.execute("UPDATE worker SET body='{}'")
            db.commit()
        with self.assertRaisesRegex(WorkerViolation, "QUEUE_INTEGRITY_ERROR"):
            self.worker.run()
        with closing(sqlite3.connect(self.worker.path)) as db:
            db.execute("DELETE FROM worker")
            db.commit()
        with self.assertRaisesRegex(WorkerViolation, "QUEUE_MISSING"):
            self.reopen()

    def test_path_budget_hash_and_scope_rejections(self):
        for filename in ("../outside.xlsx", "sub/file.xlsx", "C:private.xlsx"):
            with self.assertRaises(WorkerViolation):
                self.worker.enqueue(filename, expected_sha256="0"*64)
        (self.inbox / "first.xlsx").write_bytes(workbook())
        with self.assertRaisesRegex(WorkerViolation, "INPUT_HASH_MISMATCH"):
            self.worker.enqueue("first.xlsx", expected_sha256="0"*64)
        for budget in (0,33,True,1.5):
            with self.assertRaisesRegex(WorkerViolation, "RUN_BUDGET_INVALID"):
                self.worker.run(max_jobs=budget)
        other = self.root / "other"
        other.mkdir()
        with self.assertRaisesRegex(WorkerViolation, "QUEUE_SCOPE_MISMATCH"):
            LocalIntakeWorker(self.worker.path, inbox=other, pipeline=self.pipeline, key=self.key)
        self.assertEqual([], self.worker.snapshot()["jobs"])

    def test_polling_runs_new_explicit_job_and_obeys_pause_and_cycle_budget(self):
        sleeps = []
        def enqueue_during_wait(seconds):
            sleeps.append(seconds)
            self.enqueue()
        results = self.worker.watch(cycles=2, interval_seconds=1, sleep=enqueue_during_wait)
        self.assertEqual(["IDLE", "COMPLETED"], [item["state"] for item in results])
        self.assertEqual([1], sleeps)
        self.worker.set_paused(True)
        self.assertEqual([{"state": "PAUSED"}], self.worker.watch(cycles=120, sleep=lambda _:self.fail("paused worker slept")))
        for cycles in (0,121,True):
            with self.assertRaisesRegex(WorkerViolation, "CYCLE_BUDGET_INVALID"):
                self.worker.watch(cycles=cycles)
        with self.assertRaisesRegex(WorkerViolation, "INTERVAL_INVALID"):
            self.worker.watch(interval_seconds=0)

    def test_console_reports_real_queue_without_paths_and_rejects_tamper(self):
        import json
        from sictra_block4_orchestrator.runtime import FederatedOrchestratorStore
        from sictra_block4_orchestrator.web import create_server
        self.enqueue()
        store = FederatedOrchestratorStore(self.root / "cases.sqlite", integrity_key=self.key)
        server = create_server(store, port=0, worker=self.worker)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        def request(method):
            connection = HTTPConnection("127.0.0.1", server.server_port, timeout=2)
            try:
                connection.request(method, "/api/worker")
                response = connection.getresponse()
                return response.status, response.read().decode()
            finally:
                connection.close()
        try:
            status, body = request("GET")
            self.assertEqual(200, status)
            self.assertEqual("QUEUED", json.loads(body)["jobs"][0]["state"])
            self.assertNotIn(str(self.root), body)
            self.assertNotIn("first.xlsx", body)
            self.assertEqual(405, request("POST")[0])
            with closing(sqlite3.connect(self.worker.path)) as db:
                db.execute("UPDATE worker SET body='{}'")
                db.commit()
            self.assertEqual(409, request("GET")[0])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
