import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from sictra_block2_design.project_graph import GraphNode, ProjectGraphStore


NOW = datetime(2026, 8, 31, 23, tzinfo=timezone.utc)


def node(index):
    identity = f"NODE-{index}"
    return GraphNode(
        "PROJECT-DURABLE", identity, "DURABILITY_FIXTURE",
        sha256(identity.encode("utf-8")).hexdigest(), {"index": index}, NOW,
    )


class ProjectGraphDurabilityTests(unittest.TestCase):
    def test_committed_state_survives_close_and_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "restart.sqlite3"
            with ProjectGraphStore(path) as graph:
                graph.append_node(node(1))
                graph.commit()
            with ProjectGraphStore(path) as reopened:
                snapshot = reopened.snapshot("PROJECT-DURABLE")
                self.assertEqual(("NODE-1",), reopened.node_ids("PROJECT-DURABLE"))
                self.assertEqual(1, snapshot["nodes"][0]["payload"]["index"])

    def test_uncommitted_append_is_not_promoted_by_close(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "rollback.sqlite3"
            graph = ProjectGraphStore(path)
            graph.append_node(node(2))
            graph.close()
            with ProjectGraphStore(path) as reopened:
                self.assertEqual((), reopened.node_ids("PROJECT-DURABLE"))

    def test_independent_writers_complete_under_bounded_contention(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "contention.sqlite3"
            with ProjectGraphStore(path):
                pass
            workers = 6
            barrier = threading.Barrier(workers)

            def write(index):
                with ProjectGraphStore(path) as graph:
                    barrier.wait(timeout=3)
                    graph.append_node(node(index))
                    graph.commit()
                    return index

            with ThreadPoolExecutor(max_workers=workers) as executor:
                completed = tuple(executor.map(write, range(workers)))
            self.assertEqual(tuple(range(workers)), completed)
            with ProjectGraphStore(path) as graph:
                self.assertEqual(workers, len(graph.node_ids("PROJECT-DURABLE")))


if __name__ == "__main__":
    unittest.main()
