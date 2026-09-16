from hashlib import sha256
from pathlib import Path
import shutil
import tempfile
import unittest

from hn_customs_fixture import workbook
from sictra_block1.hn_customs_pipeline import (
    HNCustomsPipelineViolation, initialize_hn_customs_pipeline,
    load_hn_customs_pipeline, parse_hn_customs_workbook,
)
from sictra_block1.dossier_editorial_bridge import DossierEditorialBridge
from sictra_block1.operator_pipeline import load_operator_pipeline
from sictra_block1.lab_web import CompositeDossierStore
from sictra_block2_design.design_artifact import compose_content_design
from sictra_block4_orchestrator.operations import initialize
from sictra_block4_orchestrator.laboratory_recovery import backup, restore


NOW = 1_789_300_800


class HNCustomsPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "hn"
        self.key = b"h" * 32
        initialize_hn_customs_pipeline(self.root, key=self.key, clock=lambda: NOW)

    def tearDown(self):
        self.temp.cleanup()

    def test_retains_exact_periods_and_emits_blocked_unit_aware_dossier(self):
        pipeline = load_hn_customs_pipeline(self.root, key=self.key, clock=lambda: NOW)
        first = pipeline.ingest("2024.xlsx", workbook(2024))
        second = pipeline.ingest("2025.xlsx", workbook(2025), observed_at=NOW + 1)
        self.assertEqual("BASELINE_ESTABLISHED_NOT_EVIDENCE", first["status"])
        self.assertEqual("DELTA_DETECTED_NOT_EVIDENCE", second["status"])
        self.assertEqual(2, len(list((self.root / "sources").glob("*.xlsx"))))
        dossier = pipeline.list_dossiers()[0]
        self.assertEqual("HN_SARAH", dossier["source"]["root_source_identity"])
        self.assertEqual("BLOCKED", dossier["publication_state"])
        self.assertEqual([], dossier["interpretations"])
        package = pipeline.export_package(dossier["dossier_id"], package_key=b"p" * 32, now=NOW + 1)
        design = compose_content_design(dossier, package)
        self.assertIn("Honduras", design["title"])
        self.assertIn("millones de US$ CIF", design["claims"][0]["text"])

    def test_rejects_wrong_root_bad_reconciliation_and_same_content_new_bytes(self):
        with self.assertRaisesRegex(HNCustomsPipelineViolation, "CHECK_IDENTITY_INVALID"):
            parse_hn_customs_workbook("bad.xlsx", workbook(2024, root="OTHER"))
        with self.assertRaisesRegex(HNCustomsPipelineViolation, "RECONCILIATION_FAILED"):
            parse_hn_customs_workbook("bad.xlsx", workbook(2024, total=5000))
        pipeline = load_hn_customs_pipeline(self.root, key=self.key, clock=lambda: NOW)
        pipeline.ingest("2024.xlsx", workbook(2024))
        with self.assertRaisesRegex(HNCustomsPipelineViolation, "NORMALIZED_CONTENT_REPLAY_DIFFERENT_BYTES"):
            pipeline.ingest("2024-copy.xlsx", workbook(2024, suffix=" "))

    def test_retained_source_tamper_is_detected_on_every_read(self):
        pipeline = load_hn_customs_pipeline(self.root, key=self.key, clock=lambda: NOW)
        pipeline.ingest("2024.xlsx", workbook(2024))
        retained = next((self.root / "sources").glob("*.xlsx"))
        retained.write_bytes(retained.read_bytes() + b"tamper")
        with self.assertRaisesRegex(HNCustomsPipelineViolation, "JOURNAL_INTEGRITY_FAILED"):
            load_hn_customs_pipeline(self.root, key=self.key, clock=lambda: NOW)


class HNCustomsOperationsIntegrationTests(unittest.TestCase):
    def test_two_periods_reach_review_output_without_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "operations"
            service = initialize(root, now=NOW)
            service.clock = lambda: NOW
            try:
                catalog = workbook(2024)
                catalog_path = Path(directory) / "registry.xlsx"
                catalog_path.write_bytes(catalog)
                retained = service.retain_context_catalog(
                    catalog_path, expected_sha256=sha256(catalog).hexdigest(),
                    catalog_id="TELECARE_TRADE_SOURCE_REGISTRY",
                )
                self.assertEqual("NONE", retained["runtime_effect"])
                for year in (2024, 2025):
                    data = workbook(year)
                    path = Path(directory) / f"{year}.xlsx"
                    path.write_bytes(data)
                    service.register_file(
                        path, expected_sha256=sha256(data).hexdigest(),
                        source_type="HN_CUSTOMS_Q1_V1", geo_level="CUSTOMS_POINT",
                    )
                    cycle = service.tick()
                    if year == 2024:
                        self.assertEqual("COMPLETED", cycle["intake"])
                    else:
                        self.assertEqual("REVIEW_REQUIRED", cycle["intake"])
                output = next(iter(service.store.latest("OUTPUT").values()))
                self.assertTrue(output["dossier_id"].startswith("hn-customs:"))
                self.assertIn("Honduras", output["design_artifact"]["title"])
                self.assertEqual("BLOCKED", output["publication"])
                self.assertEqual("NONE", output["delivery"])
                composite = CompositeDossierStore((
                    load_operator_pipeline(root / "pipeline").dossiers,
                    load_hn_customs_pipeline(root / "hn-customs", key=service.hn_key, clock=lambda: NOW),
                ))
                editorial = DossierEditorialBridge(composite).candidate(output["dossier_id"])
                self.assertEqual("CUSTOMS", editorial["candidate"]["dimensions"]["mode"])
                self.assertEqual("BLOCKED", editorial["publication_state"])

                archive = Path(directory) / "archive"
                backup(root, archive)
                retired = Path(directory) / "retired"
                root.rename(retired)
                restore(archive, root, retired)
                recovered = load_hn_customs_pipeline(
                    root / "hn-customs", key=(root / "keys" / "hn-customs.key").read_bytes(),
                    clock=lambda: NOW,
                )
                self.assertEqual(2, recovered.snapshot()["retained_versions"])
                self.assertEqual(1, len(list((root / "catalog").glob("*.xlsx"))))
            finally:
                service.stop()

    def test_existing_install_can_add_new_source_identity_but_not_replace_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "operations"
            service = initialize(root, now=NOW)
            service.stop()
            shutil.rmtree(root / "hn-customs")
            (root / "keys" / "hn-customs.key").unlink()
            initialize(root, now=NOW).stop()
            self.assertTrue((root / "keys" / "hn-customs.key").is_file())
            (root / "keys" / "hn-customs.key").unlink()
            with self.assertRaisesRegex(Exception, "EXISTING_HN_CUSTOMS_KEY_MISSING"):
                initialize(root, now=NOW)
