import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from sictra_block2_design.checkpoint import (
    CheckpointViolation, checkpoint_from_run, persist_checkpoint, plan_resume,
    request_hash,
)
from sictra_block2_design.document_evolution import DocumentEditProposal, ElementEdit, apply_document_edit
from sictra_block2_design.project_graph import ProjectGraphStore
from sictra_block2_design.runtime import execute_block2
from sictra_block2_design.canonical_document import document_from_completed_run
from tests.test_block2_e05_e08_runtime import NOW, complete_run_input


CURRENT = "a" * 64
POLICY = "b" * 64
RIGHTS = "c" * 64
CHECKPOINT_TIME = datetime(2026, 8, 31, 10, tzinfo=timezone.utc)


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.request = complete_run_input()
        self.result = execute_block2(self.request, now=NOW)
        self.document = document_from_completed_run(
            self.request, self.result, project_id="PROJECT-CHECKPOINT",
            document_id="DOCUMENT-CHECKPOINT", actor_id="ACTOR", created_at=NOW,
        )
        self.checkpoint = checkpoint_from_run(
            self.request, self.result, checkpoint_id="CHECKPOINT-001",
            project_id="PROJECT-CHECKPOINT", run_id="RUN-CHECKPOINT",
            document_version_id=self.document.version_id,
            engine_registry_hash=CURRENT, policy_hash=POLICY, rights_hash=RIGHTS,
            created_at=CHECKPOINT_TIME,
        )

    def current_args(self):
        return dict(
            current_envelope_fingerprint=self.request.envelope.fingerprint,
            current_request_hash=request_hash(self.request),
            current_engine_registry_hash=CURRENT,
            current_policy_hash=POLICY,
            current_rights_hash=RIGHTS,
        )

    def test_complete_current_checkpoint_rehydrates_without_execution(self):
        decision = plan_resume(self.checkpoint, **self.current_args())
        self.assertEqual("RESUMED_COMPLETE", decision.disposition)
        self.assertEqual(tuple(f"E0{i}" for i in range(1, 9)), decision.reused_engines)
        self.assertEqual((), decision.reexecute_engines)
        self.assertEqual((), decision.executed_engines)

    def test_changed_policy_rights_or_request_rejects_resume(self):
        for field, value, reason in (
            ("current_policy_hash", "x" * 64, "POLICY_HASH_MISMATCH"),
            ("current_rights_hash", "y" * 64, "RIGHTS_HASH_MISMATCH"),
            ("current_request_hash", "z" * 64, "REQUEST_HASH_MISMATCH"),
        ):
            arguments = self.current_args()
            arguments[field] = value
            decision = plan_resume(self.checkpoint, **arguments)
            self.assertEqual("RESUME_REJECTED", decision.disposition)
            self.assertIn(reason, decision.reasons)
            self.assertEqual((), decision.reused_engines)

    def test_content_edit_preserves_e01_e03_and_reexecutes_from_e04(self):
        proposal = DocumentEditProposal(
            "EDIT", "0.1.0", self.document.project_id, self.document.document_id,
            self.document.version_id, self.document.content_hash, "CDD-EDIT",
            "EDITOR", CHECKPOINT_TIME,
            (ElementEdit("OP", self.document.elements[0].element_id, "content", "Edited copy"),),
        )
        invalidation = apply_document_edit(self.document, proposal).invalidation
        decision = plan_resume(self.checkpoint, invalidation=invalidation, **self.current_args())
        self.assertEqual("REEXECUTE_FROM_E04", decision.disposition)
        self.assertEqual(("E01", "E02", "E03"), decision.reused_engines)
        self.assertEqual(("E04", "E05", "E06", "E07", "E08"), decision.reexecute_engines)

    def test_partial_checkpoint_resumes_at_next_contiguous_stage(self):
        partial = replace(self.checkpoint, completed_engines=("E01", "E02", "E03"))
        decision = plan_resume(partial, **self.current_args())
        self.assertEqual("REEXECUTE_FROM_E04", decision.disposition)
        self.assertEqual("E04", decision.next_engine)

    def test_non_contiguous_or_unknown_stage_is_rejected_at_construction(self):
        with self.assertRaises(CheckpointViolation):
            replace(self.checkpoint, completed_engines=("E01", "E03"))
        with self.assertRaises(CheckpointViolation):
            replace(self.checkpoint, completed_engines=("E01", "E99"))

    def test_checkpoint_persistence_is_idempotent_and_collision_safe(self):
        with tempfile.TemporaryDirectory() as folder:
            with ProjectGraphStore(Path(folder) / "checkpoint.sqlite3") as graph:
                self.assertEqual("APPENDED", persist_checkpoint(graph, self.checkpoint))
                self.assertEqual("IDEMPOTENT", persist_checkpoint(graph, self.checkpoint))
                with self.assertRaises(Exception):
                    persist_checkpoint(graph, replace(self.checkpoint, policy_hash="d" * 64))

    def test_failed_stage_is_not_misclassified_as_completed(self):
        bad_research = replace(
            self.request.research,
            references=(replace(self.request.research.references[0], rights_decision="QUARANTINE"),)
            + self.request.research.references[1:],
        )
        failed_request = replace(self.request, research=bad_research)
        failed = execute_block2(failed_request, now=NOW)
        checkpoint = checkpoint_from_run(
            failed_request, failed, checkpoint_id="CHECKPOINT-FAILED",
            project_id="PROJECT-CHECKPOINT", run_id="RUN-FAILED",
            document_version_id=None, engine_registry_hash=CURRENT,
            policy_hash=POLICY, rights_hash=RIGHTS, created_at=CHECKPOINT_TIME,
        )
        self.assertEqual("E05", failed.stopped_at)
        self.assertEqual(("E01", "E02", "E03", "E04"), checkpoint.completed_engines)


if __name__ == "__main__":
    unittest.main()
