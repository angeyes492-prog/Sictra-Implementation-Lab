import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from sictra_block2_design.document_evolution import DocumentEditProposal, ElementEdit, persist_document_evolution
from sictra_block2_design.export_service import ExportRequest, build_export_package, persist_export
from sictra_block2_design.project_graph import ProjectGraphStore
from sictra_block2_design.traceable_runtime import execute_traceable_block2
from tests.test_block2_e05_e08_runtime import NOW, complete_run_input


EXPORT_TIME = datetime(2026, 8, 31, 13, tzinfo=timezone.utc)


class ExportServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.graph = ProjectGraphStore(Path(self.temp.name) / "exports.sqlite3")
        run = execute_traceable_block2(
            complete_run_input(), graph=self.graph, project_id="PROJECT-EXPORT",
            document_id="DOCUMENT-EXPORT", actor_id="ACTOR", run_id="RUN-EXPORT", now=NOW,
        )
        self.document = run.document

    def tearDown(self):
        self.graph.close()
        self.temp.cleanup()

    def request(self, target="HTML", export_id="EXPORT-001", version_id=None):
        return ExportRequest(
            export_id, "0.1.0", self.document.project_id,
            version_id or self.document.version_id, target, "EXPORTER-LOCAL", EXPORT_TIME,
        )

    def test_html_and_svg_are_deterministic_accessible_and_not_published(self):
        for target, media_type in (("HTML", "text/html"), ("SVG", "image/svg+xml")):
            request = self.request(target, f"EXPORT-{target}")
            first = build_export_package(self.document, request)
            second = build_export_package(self.document, request)
            self.assertTrue(first.ready)
            self.assertEqual(media_type, first.package.media_type)
            self.assertEqual(first.package.content_hash, second.package.content_hash)
            self.assertTrue(first.package.accessibility_content)
            self.assertEqual("NOT_PUBLISHED", first.package.publication_state)
            self.assertEqual("NOT_ACCEPTED", first.package.acceptance_state)
            self.assertNotIn(b"<script", first.package.content.lower())
            self.assertNotIn(b'href="http', first.package.content.lower())
            self.assertNotIn(b'src="http', first.package.content.lower())

    def test_edited_document_without_revalidation_cannot_export(self):
        proposal = DocumentEditProposal(
            "EDIT-EXPORT", "0.1.0", self.document.project_id, self.document.document_id,
            self.document.version_id, self.document.content_hash, "CDD-EDIT-EXPORT", "EDITOR",
            EXPORT_TIME, (ElementEdit("OP", self.document.elements[0].element_id, "content", "Edited candidate"),),
        )
        edited = persist_document_evolution(self.graph, proposal).document
        assessment = build_export_package(edited, self.request(version_id=edited.version_id))
        self.assertFalse(assessment.ready)
        self.assertIn("REVALIDATION_REQUIRED", assessment.reasons)

    def test_persisted_export_has_lineage_and_exact_replay(self):
        request = self.request()
        first = persist_export(self.graph, request)
        replay = persist_export(self.graph, request)
        self.assertEqual("APPENDED", first.graph_action)
        self.assertEqual("IDEMPOTENT", replay.graph_action)
        self.assertIn(
            (f"DOCUMENT-{self.document.version_id}", "EXPORTED_AS", request.export_id),
            self.graph.edges(self.document.project_id),
        )

    def test_missing_document_is_not_interpreted_as_empty_export(self):
        assessment = persist_export(self.graph, self.request(version_id="MISSING"))
        self.assertEqual("RETURN_TO_DOCUMENT", assessment.disposition)
        self.assertIsNone(assessment.package)

    def test_svg_wraps_long_valid_copy_without_truncating_the_accessible_text(self):
        long_copy = " ".join(["evidencia-trazable"] * 120)
        first = replace(self.document.elements[0], content=long_copy)
        document = replace(self.document, elements=(first, *self.document.elements[1:]))
        assessment = build_export_package(document, self.request("SVG"))
        self.assertTrue(assessment.ready)
        svg = assessment.package.content.decode("utf-8")
        self.assertGreater(svg.count("<tspan"), 2)
        self.assertIn("evidencia-trazable", svg)
        self.assertIn(long_copy, assessment.package.accessibility_content.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
