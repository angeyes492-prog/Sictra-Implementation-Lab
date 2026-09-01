import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from sictra_block2_design.document_evolution import (
    DocumentEditProposal, DocumentEvolutionViolation, ElementEdit,
    apply_document_edit, persist_document_evolution,
)
from sictra_block2_design.project_graph import ProjectGraphStore
from sictra_block2_design.traceable_runtime import execute_traceable_block2
from tests.test_block2_e05_e08_runtime import NOW, complete_run_input


EDIT_TIME = datetime(2026, 8, 31, 9, tzinfo=timezone.utc)


class DocumentEvolutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.graph = ProjectGraphStore(Path(self.temp.name) / "evolution.sqlite3")
        run = execute_traceable_block2(
            complete_run_input(), graph=self.graph, project_id="PROJECT-EVOLUTION",
            document_id="DOCUMENT-EVOLUTION", actor_id="ACTOR-ORIGINAL",
            run_id="RUN-EVOLUTION", now=NOW,
        )
        self.base = run.document

    def tearDown(self):
        self.graph.close()
        self.temp.cleanup()

    def proposal(self, operations=None, **changes):
        value = DocumentEditProposal(
            "EDIT-001", "0.1.0", self.base.project_id, self.base.document_id,
            self.base.version_id, self.base.content_hash, "CDD-EDIT-001",
            "EDITOR-001", EDIT_TIME,
            operations or (ElementEdit("OP-001", self.base.elements[0].element_id, "content", "Revised approved candidate copy"),),
        )
        return replace(value, **changes)

    def test_content_edit_creates_child_diff_and_minimal_invalidation(self):
        result = apply_document_edit(self.base, self.proposal())
        self.assertEqual(self.base.version_id, result.document.parent_version_id)
        self.assertEqual("EDITED_CANDIDATE_NOT_VALIDATED", result.document.state)
        self.assertEqual((), result.document.validation_refs)
        self.assertEqual(("CONTENT",), result.invalidation.reason_domains)
        self.assertEqual(("E04",), result.invalidation.root_engines)
        self.assertEqual(("E01", "E02", "E03"), result.invalidation.preserved_engines)
        self.assertEqual(("E04", "E05", "E06", "E07", "E08"), result.invalidation.invalidated_engines)

    def test_style_and_rights_edits_choose_earliest_conservative_root(self):
        operations = (
            ElementEdit("OP-STYLE", self.base.elements[0].element_id, "token_refs", ("new-token",)),
            ElementEdit("OP-RIGHTS", self.base.elements[1].element_id, "rights_state", "REVIEW_REQUIRED"),
        )
        result = apply_document_edit(self.base, self.proposal(operations))
        self.assertEqual(("E03", "E05"), result.invalidation.root_engines)
        self.assertEqual(("E01", "E02"), result.invalidation.preserved_engines)
        self.assertEqual(tuple(f"E0{i}" for i in range(3, 9)), result.invalidation.invalidated_engines)

    def test_stale_hash_forbidden_field_noop_and_unknown_element_fail_closed(self):
        with self.assertRaisesRegex(DocumentEvolutionViolation, "BASE_CONTENT_HASH_MISMATCH"):
            apply_document_edit(self.base, self.proposal(base_content_hash="0" * 64))
        with self.assertRaises(DocumentEvolutionViolation):
            ElementEdit("OP", self.base.elements[0].element_id, "claim_refs", ("MUTATED",))
        with self.assertRaisesRegex(DocumentEvolutionViolation, "NO_OP"):
            apply_document_edit(self.base, self.proposal((ElementEdit("OP", self.base.elements[0].element_id, "content", self.base.elements[0].content),)))
        with self.assertRaisesRegex(DocumentEvolutionViolation, "NOT_FOUND"):
            apply_document_edit(self.base, self.proposal((ElementEdit("OP", "MISSING", "content", "copy"),)))

    def test_persistence_is_append_only_and_exact_replay_is_idempotent(self):
        proposal = self.proposal()
        first = persist_document_evolution(self.graph, proposal)
        replay = persist_document_evolution(self.graph, proposal)
        self.assertEqual("APPENDED", first.store_action)
        self.assertEqual("IDEMPOTENT", replay.store_action)
        self.assertEqual(first.document.content_hash, self.graph.document_hash(first.document.project_id, first.document.version_id))
        edges = self.graph.edges(first.document.project_id)
        self.assertIn((f"DOCUMENT-{first.document.version_id}", "SUPERSEDES", f"DOCUMENT-{self.base.version_id}"), edges)
        self.assertIn((first.invalidation.plan_id, "DERIVED_FROM", first.diff.diff_id), edges)

    def test_stale_base_cannot_branch_silently_after_new_version(self):
        persist_document_evolution(self.graph, self.proposal())
        with self.assertRaisesRegex(DocumentEvolutionViolation, "BASE_VERSION_STALE"):
            persist_document_evolution(self.graph, replace(self.proposal(), edit_id="EDIT-002", new_version_id="CDD-EDIT-002"))

    def test_invalid_child_value_rolls_back_without_new_version(self):
        invalid = self.proposal((ElementEdit("OP", self.base.elements[0].element_id, "asset_refs", ("not-a-hash",)),))
        with self.assertRaises(DocumentEvolutionViolation):
            persist_document_evolution(self.graph, invalid)
        self.assertIsNone(self.graph.document_hash(self.base.project_id, invalid.new_version_id))


if __name__ == "__main__":
    unittest.main()
