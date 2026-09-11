import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from sictra_block2_design.design_context import (
    CreateDesignRequest, assess_runtime_binding, compile_design_context,
    persist_create_assessment,
)
from sictra_block2_design.project_graph import ProjectGraphStore
from sictra_block2_design.reference_fixture import reference_create_request, reference_run_input


NOW = datetime(2026, 8, 31, 21, tzinfo=timezone.utc)


def request(**changes):
    value = CreateDesignRequest(
        "CREATE-001", "0.1.0", "PROJECT-CREATE", "MESSAGE-CREATE",
        "TASK-CREATE", "RUN-CREATE", "INTELLIGENCE-ADAPTER",
        "BLOCK2-E01", "HUMAN-CREATE", NOW, "INTEL-OBJECT-001",
        "INTELLIGENCE:OBJECT:001", ("FACT-001",), ("EVIDENCE-001",),
        "VERIFIED", ("CONTRADICTION-001",), "AUTHORITY-001", "CURRENT",
        ("PROVENANCE-001",), "operations leaders", "understand a bounded claim",
        "create an accessible executive brief", ("EMAIL",),
        "reader locates claim and limitation", ("WCAG-AA",), ("NO-DECEPTION",),
        ("EMAIL-600PX",), False, "BRAND-MANIFEST-001", None,
        ("sample size remains visible",), ("NO-CAUSAL-CLAIM",),
    )
    return replace(value, **changes)


class DesignContextCompilerTests(unittest.TestCase):
    def test_complete_request_compiles_without_accepting_or_publishing(self):
        result = compile_design_context(request())
        self.assertEqual("CONTINUE", result.disposition)
        self.assertEqual(64, len(result.envelope.fingerprint))
        self.assertEqual(("FACT-001",), result.envelope.fact_ids)
        self.assertEqual("NOT_PUBLISHED", result.publication_state)
        self.assertEqual("NOT_ACCEPTED", result.acceptance_state)

    def test_missing_upstream_fields_are_aggregated_in_one_return(self):
        result = compile_design_context(request(
            object_id="", authority_reference="", audience="", fact_ids=(),
            evidence_refs=(), provenance_refs=(), channel_set=(),
        ))
        self.assertEqual("RETURN_UPSTREAM", result.disposition)
        self.assertIsNone(result.envelope)
        self.assertTrue({
            "OBJECT_ID_MISSING", "AUTHORITY_REFERENCE_MISSING", "AUDIENCE_MISSING",
            "FACTS_MISSING", "EVIDENCE_MISSING", "PROVENANCE_MISSING",
            "CHANNELS_MISSING",
        }.issubset(result.reasons))

    def test_certainty_temporality_and_version_fail_closed(self):
        result = compile_design_context(request(
            certainty="probably", temporal_state="STALE", contract_version="0.2.0",
        ))
        self.assertEqual(
            ("UNSUPPORTED_VERSION", "CERTAINTY_UNGOVERNED", "UPSTREAM_NOT_CURRENT"),
            result.reasons,
        )

    def test_unsupported_channel_is_not_approximated(self):
        result = compile_design_context(request(channel_set=("HOLOGRAM",)))
        self.assertIn("UNSUPPORTED_CHANNEL_HOLOGRAM", result.reasons)
        self.assertIsNone(result.envelope)

    def test_declared_reference_requires_rights_manifest(self):
        result = compile_design_context(request(references_declared=True))
        self.assertEqual(("REFERENCE_RIGHTS_MANIFEST_MISSING",), result.reasons)
        accepted = compile_design_context(request(
            references_declared=True,
            reference_rights_manifest_ref="RIGHTS-MANIFEST-001",
        ))
        self.assertEqual("CONTINUE", accepted.disposition)

    def test_fingerprint_is_deterministic_and_content_sensitive(self):
        first = compile_design_context(request()).envelope.fingerprint
        self.assertEqual(first, compile_design_context(request()).envelope.fingerprint)
        changed = compile_design_context(request(success_criterion="different explicit criterion"))
        self.assertNotEqual(first, changed.envelope.fingerprint)

    def test_persistence_is_idempotent_and_identity_collision_is_rejected(self):
        assessment = compile_design_context(request())
        with tempfile.TemporaryDirectory() as folder:
            with ProjectGraphStore(Path(folder) / "create.sqlite3") as graph:
                self.assertEqual("APPENDED", persist_create_assessment(graph, assessment, created_at=NOW))
                self.assertEqual("IDEMPOTENT", persist_create_assessment(graph, assessment, created_at=NOW))
                snapshot = graph.snapshot("PROJECT-CREATE")
                self.assertEqual(1, len([n for n in snapshot["nodes"] if n["node_type"] == "DESIGN_CONTEXT_ENVELOPE"]))
                changed = compile_design_context(request(success_criterion="colliding content"))
                with self.assertRaises(Exception):
                    persist_create_assessment(graph, changed, created_at=NOW)

    def test_rejected_request_persists_assessment_without_envelope(self):
        assessment = compile_design_context(request(evidence_refs=()))
        with tempfile.TemporaryDirectory() as folder:
            with ProjectGraphStore(Path(folder) / "rejected.sqlite3") as graph:
                persist_create_assessment(graph, assessment, created_at=NOW)
                types = {node["node_type"] for node in graph.snapshot("PROJECT-CREATE")["nodes"]}
                self.assertEqual({"CREATE_ASSESSMENT"}, types)

    def test_runtime_binding_requires_exact_handoff_identity(self):
        envelope = compile_design_context(reference_create_request(NOW)).envelope
        run = reference_run_input(NOW, envelope)
        self.assertEqual("BOUND_FOR_E01", assess_runtime_binding(envelope, run).disposition)
        mutated = replace(run, envelope=replace(run.envelope, fingerprint="substituted"))
        result = assess_runtime_binding(envelope, mutated)
        self.assertEqual("RETURN_TO_CREATE", result.disposition)
        self.assertEqual(("CREATE_RUNTIME_FINGERPRINT_MISMATCH",), result.reasons)


if __name__ == "__main__":
    unittest.main()
