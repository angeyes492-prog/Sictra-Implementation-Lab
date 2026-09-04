import unittest
from dataclasses import replace

from sictra_block2_design.checkpoint import checkpoint_from_run, request_hash
from sictra_block2_design.document_evolution import InvalidationPlan
from sictra_block2_design.engine_registry import default_engine_registry
from sictra_block2_design.orchestrator import execute_resumed_block2
from sictra_block2_design.runtime import execute_block2
from tests.test_block2_e05_e08_runtime import NOW, complete_run_input, research, reference


POLICY = "b" * 64
RIGHTS = "c" * 64


class PartialOrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.request = complete_run_input()
        self.registry = default_engine_registry()
        self.previous = execute_block2(self.request, now=NOW, engine_registry=self.registry)
        self.checkpoint = checkpoint_from_run(
            self.request, self.previous, checkpoint_id="CHECKPOINT-ORCH",
            project_id="PROJECT-ORCH", run_id="RUN-ORCH", document_version_id="CDD-ORCH",
            engine_registry_hash=self.registry.content_hash, policy_hash=POLICY,
            rights_hash=RIGHTS, created_at=NOW,
        )

    @staticmethod
    def content_invalidation():
        return InvalidationPlan(
            "PLAN-CONTENT", "DIFF-CONTENT", ("E04",),
            ("E04", "E05", "E06", "E07", "E08"),
            ("E01", "E02", "E03"), ("CONTENT",),
        )

    def test_content_invalidation_actually_executes_e04_through_e08(self):
        resumed = execute_resumed_block2(
            self.request, checkpoint=self.checkpoint, previous_result=self.previous,
            current_policy_hash=POLICY, current_rights_hash=RIGHTS,
            invalidation=self.content_invalidation(), now=NOW, engine_registry=self.registry,
        )
        self.assertTrue(resumed.run.completed)
        self.assertEqual(("E01", "E02", "E03"), resumed.run.reused_engines)
        self.assertEqual(("E04", "E05", "E06", "E07", "E08"), resumed.run.executed_engines)
        self.assertEqual(resumed.run.executed_engines, resumed.decision.executed_engines)
        self.assertEqual(
            ("REUSED_CHECKPOINT",) * 3 + ("EXECUTED",) * 5,
            tuple(stage.execution_state for stage in resumed.run.stages),
        )

    def test_complete_resume_executes_no_engine(self):
        resumed = execute_resumed_block2(
            self.request, checkpoint=self.checkpoint, previous_result=self.previous,
            current_policy_hash=POLICY, current_rights_hash=RIGHTS,
            now=NOW, engine_registry=self.registry,
        )
        self.assertEqual("RESUMED_COMPLETE", resumed.decision.disposition)
        self.assertEqual((), resumed.run.executed_engines)
        self.assertEqual(tuple(f"E0{i}" for i in range(1, 9)), resumed.run.reused_engines)
        self.assertEqual("REUSED_CHECKPOINT", resumed.run.memory_store_action)

    def test_currentness_mismatch_rejects_without_runtime(self):
        resumed = execute_resumed_block2(
            self.request, checkpoint=self.checkpoint, previous_result=self.previous,
            current_policy_hash="x" * 64, current_rights_hash=RIGHTS,
            invalidation=self.content_invalidation(), now=NOW, engine_registry=self.registry,
        )
        self.assertEqual("RESUME_REJECTED", resumed.decision.disposition)
        self.assertIsNone(resumed.run)

    def test_registry_change_rejects_before_partial_execution(self):
        manifests = list(self.registry.manifests)
        manifests[0] = replace(manifests[0], authority_boundary="changed boundary")
        changed = replace(self.registry, manifests=tuple(manifests))
        resumed = execute_resumed_block2(
            self.request, checkpoint=self.checkpoint, previous_result=self.previous,
            current_policy_hash=POLICY, current_rights_hash=RIGHTS,
            invalidation=self.content_invalidation(), now=NOW, engine_registry=changed,
        )
        self.assertEqual("RESUME_REJECTED", resumed.decision.disposition)
        self.assertIn("ENGINE_REGISTRY_HASH_MISMATCH", resumed.decision.reasons)
        self.assertIsNone(resumed.run)

    def test_partial_execution_still_stops_fail_closed(self):
        bad_research = research(references=(reference(rights_decision="QUARANTINE"), reference("REF-2")))
        changed_request = replace(self.request, research=bad_research)
        changed_checkpoint = replace(self.checkpoint, request_hash=request_hash(changed_request))
        resumed = execute_resumed_block2(
            changed_request, checkpoint=changed_checkpoint, previous_result=self.previous,
            current_policy_hash=POLICY, current_rights_hash=RIGHTS,
            invalidation=self.content_invalidation(), now=NOW, engine_registry=self.registry,
        )
        self.assertFalse(resumed.run.completed)
        self.assertEqual("E05", resumed.run.stopped_at)
        self.assertEqual(("E04", "E05"), resumed.run.executed_engines)
        self.assertNotIn("E06", resumed.run.executed_engines)


if __name__ == "__main__":
    unittest.main()
