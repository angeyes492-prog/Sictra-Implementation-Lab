import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from sictra_block2_design.checkpoint import checkpoint_from_run, persist_checkpoint, plan_resume, request_hash
from sictra_block2_design.document_evolution import DocumentEditProposal, ElementEdit, persist_document_evolution
from sictra_block2_design.export_service import ExportRequest, persist_export
from sictra_block2_design.engine_registry import default_engine_registry, persist_engine_registry
from sictra_block2_design.orchestrator import execute_resumed_block2, persist_orchestrated_resume
from sictra_block2_design.project_graph import ProjectGraphStore
from sictra_block2_design.traceable_runtime import execute_traceable_block2
from sictra_block2_design.design_context import compile_design_context, persist_create_assessment
from sictra_block2_design.reference_fixture import reference_create_request, reference_run_input
from tests.test_block2_e05_e08_runtime import NOW


class DesignIntelligenceOsEndToEndTests(unittest.TestCase):
    def test_trace_checkpoint_edit_invalidate_and_export_boundaries(self):
        event_time = datetime(2026, 8, 31, 15, tzinfo=timezone.utc)
        create = compile_design_context(replace(
            reference_create_request(NOW), project_id="PROJECT-E2E",
        ))
        request = reference_run_input(NOW, create.envelope)
        registry = default_engine_registry()
        registry_hash, policy_hash, rights_hash = registry.content_hash, "b" * 64, "c" * 64
        with tempfile.TemporaryDirectory() as folder:
            with ProjectGraphStore(Path(folder) / "design-os.sqlite3") as graph:
                self.assertEqual("APPENDED", persist_create_assessment(
                    graph, create, created_at=event_time,
                ))
                self.assertEqual("APPENDED", persist_engine_registry(
                    graph, registry, project_id="PROJECT-E2E", created_at=event_time,
                ))
                trace = execute_traceable_block2(
                    request, graph=graph, project_id="PROJECT-E2E", document_id="DOCUMENT-E2E",
                    actor_id="ACTOR-E2E", run_id="RUN-E2E", now=NOW,
                    design_context=create.envelope,
                )
                self.assertTrue(trace.run.completed)
                self.assertEqual(trace.run.production.candidate.artifact.sha256, trace.run.gateway_receipt.output_hash)

                checkpoint = checkpoint_from_run(
                    request, trace.run, checkpoint_id="CHECKPOINT-E2E", project_id="PROJECT-E2E",
                    run_id="RUN-E2E", document_version_id=trace.document.version_id,
                    engine_registry_hash=registry_hash, policy_hash=policy_hash,
                    rights_hash=rights_hash, created_at=event_time,
                )
                self.assertEqual("APPENDED", persist_checkpoint(graph, checkpoint))
                current = dict(
                    current_envelope_fingerprint=request.envelope.fingerprint,
                    current_request_hash=request_hash(request),
                    current_engine_registry_hash=registry_hash,
                    current_policy_hash=policy_hash,
                    current_rights_hash=rights_hash,
                )
                self.assertEqual("RESUMED_COMPLETE", plan_resume(checkpoint, **current).disposition)

                edit = DocumentEditProposal(
                    "EDIT-E2E", "0.1.0", trace.document.project_id, trace.document.document_id,
                    trace.document.version_id, trace.document.content_hash, "CDD-EDIT-E2E", "EDITOR-E2E",
                    event_time, (ElementEdit("OP-E2E", trace.document.elements[0].element_id, "content", "Edited E2E candidate"),),
                )
                evolution = persist_document_evolution(graph, edit)
                resume = plan_resume(checkpoint, invalidation=evolution.invalidation, **current)
                self.assertEqual("REEXECUTE_FROM_E04", resume.disposition)
                resumed = execute_resumed_block2(
                    request, checkpoint=checkpoint, previous_result=trace.run,
                    current_policy_hash=policy_hash, current_rights_hash=rights_hash,
                    invalidation=evolution.invalidation, now=event_time,
                    engine_registry=registry,
                )
                self.assertTrue(resumed.run.completed)
                self.assertEqual(("E01", "E02", "E03"), resumed.run.reused_engines)
                self.assertEqual(("E04", "E05", "E06", "E07", "E08"), resumed.run.executed_engines)
                self.assertEqual("APPENDED", persist_orchestrated_resume(
                    graph, resumed, project_id="PROJECT-E2E", resume_id="RESUME-E2E",
                    checkpoint_id=checkpoint.checkpoint_id, created_at=event_time,
                ))

                edited_export = persist_export(graph, ExportRequest(
                    "EXPORT-EDITED-E2E", "0.1.0", "PROJECT-E2E", evolution.document.version_id,
                    "HTML", "EXPORTER-E2E", event_time,
                ))
                self.assertEqual("REVALIDATION_REQUIRED", edited_export.disposition)
                original_export = persist_export(graph, ExportRequest(
                    "EXPORT-ORIGINAL-E2E", "0.1.0", "PROJECT-E2E", trace.document.version_id,
                    "HTML", "EXPORTER-E2E", event_time,
                ))
                self.assertTrue(original_export.ready)
                self.assertEqual("NOT_PUBLISHED", original_export.package.publication_state)
                self.assertEqual("NOT_ACCEPTED", original_export.package.acceptance_state)

                snapshot = graph.snapshot("PROJECT-E2E")
                node_types = {node["node_type"] for node in snapshot["nodes"]}
                self.assertTrue({
                    "MODEL_GATEWAY_RECEIPT", "DESIGN_DOCUMENT_VERSION", "RUN_CHECKPOINT",
                    "DOCUMENT_DIFF", "INVALIDATION_PLAN", "EXPORT_PACKAGE",
                    "ENGINE_REGISTRY", "ENGINE_MANIFEST", "ORCHESTRATOR_RESUME",
                    "ENGINE_STAGE_RESUME",
                    "CREATE_ASSESSMENT", "DESIGN_CONTEXT_ENVELOPE",
                }.issubset(node_types))
                self.assertIn(
                    ("RUN-E2E-E01", "DERIVED_FROM", "DESIGN-CONTEXT-MESSAGE-DEMO"),
                    graph.edges("PROJECT-E2E"),
                )


if __name__ == "__main__":
    unittest.main()
