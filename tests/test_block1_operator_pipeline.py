from http.client import HTTPConnection
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
import unittest

from sictra_block1.operator_pipeline import (
    OperatorPipelineViolation,
    create_pipeline_data_backup,
    ingest_eurostat_workbook,
    initialize_operator_pipeline,
    load_operator_pipeline,
    pipeline_snapshot,
    restore_pipeline_data_backup,
)
from test_block1_eurostat_maritime_mapper import workbook


NOW = 1_788_700_000


class Block1OperatorPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name) / "pipeline"
        self.now = NOW

    def tearDown(self) -> None:
        self.temp.cleanup()

    def clock(self) -> int:
        return self.now

    def write_workbook(self, name: str, payload: bytes) -> Path:
        path = Path(self.temp.name) / name
        path.write_bytes(payload)
        return path

    def test_first_release_runs_full_chain_and_establishes_only_a_baseline(self):
        initialized = initialize_operator_pipeline(self.root, clock=self.clock)
        self.assertEqual(initialized["status"], "READY")
        first = self.write_workbook("eurostat-first.xlsx", workbook())

        result = ingest_eurostat_workbook(self.root, first, clock=self.clock)

        self.assertEqual(result["status"], "BASELINE_ESTABLISHED_NOT_EVIDENCE")
        self.assertEqual(result["runtime"], {"enforcement": "COMMITTED", "evidence_count": 1})
        self.assertEqual(result["watchlist"]["next_state"], "AWAIT_NEWER_SOURCE")
        self.assertIsNone(result["dossier"])
        self.assertEqual(result["publication_authority"], "NONE")
        snapshot = pipeline_snapshot(self.root, clock=self.clock)
        self.assertEqual(snapshot["evidence"], {"retained_count": 1, "current_count": 1})
        self.assertEqual(snapshot["watchlist"]["latest_status"], "BASELINE_ESTABLISHED_NOT_EVIDENCE")
        self.assertEqual(snapshot["dossiers"]["count"], 0)

    def test_new_release_immediately_supersedes_current_evidence_and_creates_literal_fact_dossier(self):
        initialize_operator_pipeline(self.root, clock=self.clock)
        first = self.write_workbook("eurostat-first.xlsx", workbook())
        ingest_eurostat_workbook(self.root, first, clock=self.clock)

        self.now += 1
        second = self.write_workbook(
            "eurostat-second.xlsx",
            workbook(last_updated="07/09/2026 06:14", rows=(("BE", "Belgium", "14", None, "15"),)),
        )
        result = ingest_eurostat_workbook(self.root, second, clock=self.clock)

        self.assertEqual(result["status"], "DELTA_DETECTED_NOT_EVIDENCE")
        self.assertGreater(result["watchlist"]["change_count"], 0)
        self.assertEqual(result["watchlist"]["next_state"], "REQUIRES_REVIEW")
        self.assertIsNotNone(result["dossier"])
        pipeline = load_operator_pipeline(self.root, clock=self.clock)
        dossier = pipeline.dossiers.list_dossiers()[0]
        self.assertTrue(dossier["facts"])
        self.assertEqual(dossier["interpretations"], [])
        self.assertEqual(dossier["publication_state"], "BLOCKED")
        self.assertEqual(pipeline_snapshot(self.root, clock=self.clock)["evidence"], {"retained_count": 2, "current_count": 1})

    def test_rejection_and_tamper_fail_before_state_or_runtime_effect(self):
        initialize_operator_pipeline(self.root, clock=self.clock)
        invalid = self.write_workbook("not-eurostat.xlsx", b"not a workbook")
        with self.assertRaises(OperatorPipelineViolation):
            ingest_eurostat_workbook(self.root, invalid, clock=self.clock)
        snapshot = pipeline_snapshot(self.root, clock=self.clock)
        self.assertEqual(snapshot["evidence"]["retained_count"], 0)
        self.assertEqual(snapshot["watchlist"]["cycle_count"], 0)

        valid = self.write_workbook("eurostat-valid.xlsx", workbook())
        ingest_eurostat_workbook(self.root, valid, clock=self.clock)
        key = self.root / "keys" / "evidence-integrity.key"
        key.write_bytes(b"x" * 32)
        with self.assertRaises(OperatorPipelineViolation):
            load_operator_pipeline(self.root, clock=self.clock)

    def test_ingest_uses_one_trusted_time_across_runtime_and_evidence(self):
        initialize_operator_pipeline(self.root, clock=self.clock)
        source = self.write_workbook("eurostat-one-clock.xlsx", workbook())
        result = ingest_eurostat_workbook(self.root, source, clock=self.clock)
        self.assertEqual(result["runtime"]["enforcement"], "COMMITTED")

    def test_data_backup_restores_only_missing_ledgers_under_original_keys(self):
        initialize_operator_pipeline(self.root, clock=self.clock)
        source = self.write_workbook("eurostat.xlsx", workbook())
        ingest_eurostat_workbook(self.root, source, clock=self.clock)
        backup = Path(self.temp.name) / "pipeline-backup"
        created = create_pipeline_data_backup(self.root, backup, clock=self.clock)
        self.assertEqual(created["status"], "BACKUP_CREATED")
        self.assertFalse(created["keys_included"])
        self.assertFalse(created["runtime_store_included"])
        self.assertFalse(any(item.name == "keys" for item in backup.iterdir()))
        launcher = Path("backup_eurostat_pipeline.cmd").read_text(encoding="utf-8")
        restore_launcher = Path("restore_eurostat_pipeline.cmd").read_text(encoding="utf-8")
        self.assertIn("operator_pipeline backup", launcher)
        self.assertIn("No incluye claves", launcher)
        self.assertIn("operator_pipeline restore", restore_launcher)
        self.assertIn("niega a reemplazar", restore_launcher)
        with self.assertRaises(OperatorPipelineViolation):
            restore_pipeline_data_backup(self.root, backup, clock=self.clock)
        for name in ("source-control.json", "evidence.json", "watchlist.json", "dossiers.json"):
            (self.root / name).unlink(missing_ok=True)
        restored = restore_pipeline_data_backup(self.root, backup, clock=self.clock)
        self.assertEqual(restored["status"], "RESTORED")
        snapshot = pipeline_snapshot(self.root, clock=self.clock)
        self.assertEqual(snapshot["evidence"]["retained_count"], 1)
        (backup / "watchlist.json").write_bytes(b"tampered")
        for name in ("source-control.json", "evidence.json", "watchlist.json", "dossiers.json"):
            (self.root / name).unlink(missing_ok=True)
        with self.assertRaises(OperatorPipelineViolation):
            restore_pipeline_data_backup(self.root, backup, clock=self.clock)

    def test_local_ui_exposes_sanitized_pipeline_state_without_source_content(self):
        initialize_operator_pipeline(self.root, clock=self.clock)
        source = self.write_workbook("eurostat.xlsx", workbook())
        ingest_eurostat_workbook(self.root, source, clock=self.clock)
        pipeline = load_operator_pipeline(self.root, clock=self.clock)
        from sictra_block1.lab_web import create_server
        server = create_server(port=0, dossier_store=pipeline.dossiers, pipeline_root=self.root)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            connection.request("GET", "/api/pipeline")
            response = connection.getresponse()
            payload = response.read().decode("utf-8")
            connection.close()
            self.assertEqual(response.status, 200)
            self.assertIn('"status":"READY"', payload)
            self.assertIn('"latest_status":"BASELINE_ESTABLISHED_NOT_EVIDENCE"', payload)
            self.assertNotIn("source-control-integrity", payload)
            self.assertNotIn("content_sha256", payload)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
