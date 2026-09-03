import json
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

from sictra_block2_design.e08_creative_memory import E08ContractViolation, assess_memory_candidate
from sictra_block2_design.creative_memory_store import ProjectGraphCreativeMemoryStore
from sictra_block2_design.project_graph import GraphNode, ProjectGraphStore, ProjectGraphViolation
from sictra_block2_design.runtime import execute_block2
from sictra_block2_design.traceable_runtime import execute_traceable_block2
from tests.test_block2_e05_e08_runtime import NOW, complete_run_input, memory


PROJECT = "PROJECT-MEMORY-DURABLE"
RUN = "RUN-MEMORY-DURABLE"


class CreativeMemoryDurabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "project-graph.sqlite3"

    def tearDown(self):
        self.temp.cleanup()

    def execute(self, graph, *, run_id=RUN):
        return execute_traceable_block2(
            complete_run_input(), graph=graph, project_id=PROJECT,
            document_id="DOCUMENT-MEMORY-DURABLE", actor_id="ACTOR-MEMORY",
            run_id=run_id, now=NOW,
        )

    def test_default_trace_store_survives_restart_with_e08_lineage(self):
        with ProjectGraphStore(self.path) as graph:
            result = self.execute(graph)
            self.assertTrue(result.run.completed)
            self.assertEqual("STORED", result.run.memory_store_action)

        with ProjectGraphStore(self.path) as reopened:
            store = ProjectGraphCreativeMemoryStore(reopened, PROJECT, recorded_at=NOW)
            stored = store.get("MEMORY-001")
            self.assertIsNotNone(stored)
            self.assertEqual("ACTIVE_CANDIDATE", stored.state)
            self.assertEqual(memory().content_hash, stored.content_hash)
            self.assertIn(
                ("CREATIVE-MEMORY-MEMORY-001", "DERIVED_FROM", f"{RUN}-E08"),
                reopened.edges(PROJECT),
            )
            snapshot = reopened.snapshot(PROJECT)
            self.assertEqual(1, len(snapshot["creative_memories"]))
            self.assertEqual([], snapshot["creative_memory_events"])

    def test_deprecation_is_append_only_idempotent_and_restart_safe(self):
        deprecated_at = NOW + timedelta(hours=1)
        with ProjectGraphStore(self.path) as graph:
            self.execute(graph)
            store = ProjectGraphCreativeMemoryStore(graph, PROJECT, recorded_at=NOW)
            deprecated = store.deprecate(
                "MEMORY-001", "out-of-sample failure", at=deprecated_at,
            )
            replay = store.deprecate(
                "MEMORY-001", "out-of-sample failure", at=deprecated_at,
            )
            graph.commit()
            self.assertEqual("DEPRECATED", deprecated.state)
            self.assertEqual(deprecated, replay)
            self.assertEqual(1, len(graph.memory_events(PROJECT, "MEMORY-001")))

        with ProjectGraphStore(self.path) as reopened:
            store = ProjectGraphCreativeMemoryStore(reopened, PROJECT, recorded_at=NOW)
            stored = store.get("MEMORY-001")
            self.assertEqual("DEPRECATED", stored.state)
            self.assertEqual("out-of-sample failure", stored.deprecation_reason)
            self.assertEqual(memory().content_hash, stored.content_hash)
            self.assertEqual(1, len(reopened.memory_events(PROJECT, "MEMORY-001")))

    def test_identity_collision_never_overwrites_durable_memory(self):
        with ProjectGraphStore(self.path) as graph:
            result = self.execute(graph)
            changed = replace(memory(), observation="poisoned replacement")
            assessment = assess_memory_candidate(
                result.run.visual, complete_run_input().external_validation, changed, NOW,
            )
            store = ProjectGraphCreativeMemoryStore(graph, PROJECT, recorded_at=NOW)
            action, existing = store.write(assessment, changed)
            graph.commit()
            self.assertEqual("IDENTITY_COLLISION", action)
            self.assertEqual(memory().content_hash, existing.content_hash)
            self.assertEqual(memory().content_hash, store.get("MEMORY-001").content_hash)

    def test_mid_trace_failure_rolls_back_memory_and_graph_together(self):
        with ProjectGraphStore(self.path) as graph:
            graph.append_node(GraphNode(
                PROJECT, f"{RUN}-E03", "ENGINE_STAGE", "0" * 64,
                {"disposition": "POISON"}, NOW,
            ))
            graph.commit()
            with self.assertRaises(ProjectGraphViolation):
                self.execute(graph)
            self.assertIsNone(graph.load_memory_record(PROJECT, "MEMORY-001"))
            self.assertNotIn("CREATIVE-MEMORY-MEMORY-001", graph.node_ids(PROJECT))

    def test_persisted_governance_tamper_fails_integrity_check(self):
        with ProjectGraphStore(self.path) as graph:
            self.execute(graph)
        connection = sqlite3.connect(self.path)
        try:
            raw = connection.execute(
                "SELECT canonical_json FROM creative_memory_records WHERE project_id=? AND memory_id=?",
                (PROJECT, "MEMORY-001"),
            ).fetchone()[0]
            payload = json.loads(raw)
            payload["privacy_allowed"] = False
            connection.execute(
                "UPDATE creative_memory_records SET canonical_json=? WHERE project_id=? AND memory_id=?",
                (json.dumps(payload, sort_keys=True, separators=(",", ":")), PROJECT, "MEMORY-001"),
            )
            connection.commit()
        finally:
            connection.close()
        with ProjectGraphStore(self.path) as reopened:
            store = ProjectGraphCreativeMemoryStore(reopened, PROJECT, recorded_at=NOW)
            with self.assertRaises(E08ContractViolation):
                store.get("MEMORY-001")

    def test_memory_hash_authenticates_every_governance_field(self):
        original = memory()
        mutations = (
            replace(original, promotion_owner_id="OTHER-OWNER"),
            replace(original, rights_current=False),
            replace(original, privacy_allowed=False),
            replace(original, source_generation=0),
            replace(original, expires_at=original.expires_at + timedelta(days=1)),
        )
        self.assertTrue(all(item.content_hash != original.content_hash for item in mutations))

    def test_persisted_deprecation_tamper_fails_integrity_check(self):
        with ProjectGraphStore(self.path) as graph:
            self.execute(graph)
            store = ProjectGraphCreativeMemoryStore(graph, PROJECT, recorded_at=NOW)
            store.deprecate("MEMORY-001", "observed regression")
            graph.commit()
        connection = sqlite3.connect(self.path)
        try:
            connection.execute(
                "UPDATE creative_memory_events SET canonical_json=? WHERE project_id=? AND memory_id=?",
                ('{"reason":"laundered"}', PROJECT, "MEMORY-001"),
            )
            connection.commit()
        finally:
            connection.close()
        with ProjectGraphStore(self.path) as reopened:
            store = ProjectGraphCreativeMemoryStore(reopened, PROJECT, recorded_at=NOW)
            with self.assertRaises(E08ContractViolation):
                store.get("MEMORY-001")

    def test_concurrent_exact_writers_converge_without_duplicate_memory(self):
        proposal = memory()
        assessment = execute_block2(complete_run_input(), now=NOW).memory
        barrier = threading.Barrier(2)

        def bounded_write():
            with ProjectGraphStore(self.path) as graph:
                store = ProjectGraphCreativeMemoryStore(graph, PROJECT, recorded_at=NOW)
                # An initialization or locking regression must surface as a
                # bounded test failure, never leave its peer waiting forever.
                barrier.wait(timeout=5)
                action, _ = store.write(assessment, proposal)
                graph.commit()
                return action

        with ThreadPoolExecutor(max_workers=2) as pool:
            actions = tuple(pool.map(lambda _: bounded_write(), range(2)))
        self.assertEqual({"STORED", "IDEMPOTENT"}, set(actions))
        with ProjectGraphStore(self.path) as graph:
            snapshot = graph.snapshot(PROJECT)
            self.assertEqual(1, len(snapshot["creative_memories"]))


if __name__ == "__main__":
    unittest.main()
