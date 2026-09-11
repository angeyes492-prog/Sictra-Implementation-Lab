import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from hashlib import sha256

from sictra_block2_design.canonical_document import (
    CanonicalDocumentViolation, DesignElement, document_from_completed_run,
)
from sictra_block2_design.project_graph import GraphEdge, GraphNode, ProjectGraphStore, ProjectGraphViolation
from sictra_block2_design.runtime import execute_block2
from sictra_block2_design.traceable_runtime import execute_traceable_block2
from tests.test_block2_e05_e08_runtime import NOW, complete_run_input, reference, research


PROJECT = "PROJECT-TRACE-001"
DOCUMENT = "DOCUMENT-TRACE-001"
ACTOR = "ACTOR-TRACE-001"


class TraceableRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.graph = ProjectGraphStore(Path(self.temp.name) / "project-graph.sqlite3")

    def tearDown(self):
        self.graph.close()
        self.temp.cleanup()

    def run_traceable(self, request=None):
        return execute_traceable_block2(
            request or complete_run_input(), graph=self.graph, project_id=PROJECT,
            document_id=DOCUMENT, actor_id=ACTOR, run_id="RUN-TRACE-001", now=NOW,
        )

    def test_completed_run_persists_cdd_and_full_engine_lineage(self):
        result = self.run_traceable()
        self.assertTrue(result.run.completed)
        self.assertEqual("APPENDED", result.graph_action)
        self.assertIsNotNone(result.document)
        self.assertEqual(result.document.content_hash, self.graph.document_hash(PROJECT, result.document.version_id))
        nodes = self.graph.node_ids(PROJECT)
        self.assertTrue(all(any(node.endswith(f"-E0{number}") for node in nodes) for number in range(1, 9)))
        self.assertIn(
            (f"ASSET-{result.run.production.candidate.artifact.sha256}", "VALIDATED_BY", "RUN-TRACE-001-E07"),
            self.graph.edges(PROJECT),
        )
        receipt_id = result.run.gateway_receipt.receipt_id
        self.assertIn((receipt_id, "DERIVED_FROM", "RUN-TRACE-001-E06"), self.graph.edges(PROJECT))
        self.assertIn(
            (f"ASSET-{result.run.production.candidate.artifact.sha256}", "GENERATED_BY", receipt_id),
            self.graph.edges(PROJECT),
        )

    def test_exact_replay_is_idempotent(self):
        first = self.run_traceable()
        second = self.run_traceable()
        self.assertEqual("IDEMPOTENT", second.graph_action)
        self.assertEqual(first.document.content_hash, second.document.content_hash)

    def test_blocked_e05_run_records_only_reached_stages_and_no_document(self):
        bad = research(references=(reference(rights_decision="QUARANTINE"), reference("REF-2")))
        result = self.run_traceable(complete_run_input(research=bad))
        self.assertEqual("E05", result.run.stopped_at)
        self.assertIsNone(result.document)
        nodes = self.graph.node_ids(PROJECT)
        self.assertTrue(any(node.endswith("-E05") for node in nodes))
        self.assertFalse(any(node.endswith("-E06") for node in nodes))

    def test_document_version_collision_cannot_overwrite_history(self):
        result = self.run_traceable()
        changed = replace(result.document, actor_id="DIFFERENT-ACTOR")
        with self.assertRaises(ProjectGraphViolation):
            self.graph.append_document(changed)

    def test_child_version_requires_existing_parent_and_preserves_parent(self):
        result = self.run_traceable()
        original = result.document
        edited_element = replace(original.elements[0], content="Edited approved candidate copy")
        child = original.next_version(
            version_id="CDD-EDIT-001", elements=(edited_element,) + original.elements[1:],
            actor_id="EDITOR-001", created_at=datetime(2026, 8, 30, 1, tzinfo=timezone.utc),
        )
        self.assertEqual("APPENDED", self.graph.append_document(child))
        self.graph.commit()
        self.assertEqual(original.version_id, child.parent_version_id)
        self.assertNotEqual(original.content_hash, child.content_hash)
        self.assertEqual(original.content_hash, self.graph.document_hash(PROJECT, original.version_id))

    def test_cdd_rejects_remote_and_executable_content(self):
        run = execute_block2(complete_run_input(), now=NOW)
        document = document_from_completed_run(
            complete_run_input(), run, project_id=PROJECT, document_id=DOCUMENT,
            actor_id=ACTOR, created_at=NOW,
        )
        with self.assertRaises(CanonicalDocumentViolation):
            replace(document.elements[0], content="https://untrusted.test/asset")
        with self.assertRaises(CanonicalDocumentViolation):
            replace(document.elements[0], content="<script>alert(1)</script>")

    def test_graph_rejects_unknown_relations_and_missing_nodes(self):
        node = GraphNode(PROJECT, "NODE-1", "TEST", sha256(b"node-1").hexdigest(), {}, NOW)
        self.graph.append_node(node)
        with self.assertRaises(ProjectGraphViolation):
            self.graph.append_edge(GraphEdge(PROJECT, "NODE-1", "ACCEPTED_BY", "NODE-2", "NONE", NOW))
        with self.assertRaises(ProjectGraphViolation):
            self.graph.append_edge(GraphEdge(PROJECT, "NODE-1", "DERIVED_FROM", "NODE-2", "NONE", NOW))

    def test_distinct_run_ids_allow_same_envelope_to_be_reassessed(self):
        first = self.run_traceable()
        second = execute_traceable_block2(
            complete_run_input(), graph=self.graph, project_id=PROJECT,
            document_id=DOCUMENT, actor_id=ACTOR, run_id="RUN-TRACE-002",
            now=datetime(2026, 8, 30, 2, tzinfo=timezone.utc),
        )
        self.assertEqual("APPENDED", second.graph_action)
        self.assertNotEqual(first.run_id, second.run_id)
        nodes = self.graph.node_ids(PROJECT)
        self.assertTrue(any(node == "RUN-TRACE-001-E01" for node in nodes))
        self.assertTrue(any(node == "RUN-TRACE-002-E01" for node in nodes))

    def test_mid_run_collision_rolls_back_every_partial_append(self):
        poison = GraphNode(
            PROJECT, "RUN-ATOMIC-E03", "ENGINE_STAGE", sha256(b"poison").hexdigest(),
            {"disposition": "CONTRADICTED"}, NOW,
        )
        self.graph.append_node(poison)
        self.graph.commit()
        with self.assertRaises(ProjectGraphViolation):
            execute_traceable_block2(
                complete_run_input(), graph=self.graph, project_id=PROJECT,
                document_id=DOCUMENT, actor_id=ACTOR, run_id="RUN-ATOMIC", now=NOW,
            )
        self.assertEqual(("RUN-ATOMIC-E03",), self.graph.node_ids(PROJECT))


if __name__ == "__main__":
    unittest.main()
