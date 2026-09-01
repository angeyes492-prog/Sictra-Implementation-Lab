import unittest
from dataclasses import replace
from pathlib import Path
from datetime import datetime, timezone
import tempfile

from sictra_block2_design.engine_registry import (
    EngineRegistry, EngineRegistryViolation, default_engine_registry,
    persist_engine_registry,
)
from sictra_block2_design.project_graph import ProjectGraphStore


class EngineRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = default_engine_registry()

    def test_default_registry_pins_and_imports_all_eight_engines(self):
        self.assertEqual(tuple(f"E0{i}" for i in range(1, 9)), self.registry.verify_bindings())
        self.assertEqual(64, len(self.registry.content_hash))
        self.assertEqual("E06", self.registry.resolve("E06").engine_id)

    def test_manifest_change_changes_registry_identity(self):
        manifests = list(self.registry.manifests)
        manifests[5] = replace(manifests[5], authority_boundary="changed candidate boundary")
        changed = replace(self.registry, manifests=tuple(manifests))
        self.assertNotEqual(self.registry.content_hash, changed.content_hash)

    def test_missing_binding_fails_closed(self):
        manifests = list(self.registry.manifests)
        manifests[0] = replace(manifests[0], implementation_ref="sictra_block2_design.preflight:missing")
        changed = replace(self.registry, manifests=tuple(manifests))
        with self.assertRaises(EngineRegistryViolation):
            changed.verify_bindings()

    def test_dependency_shortcut_is_rejected(self):
        manifests = list(self.registry.manifests)
        manifests[4] = replace(manifests[4], dependencies=("E02",))
        with self.assertRaises(EngineRegistryViolation):
            EngineRegistry("BAD", "0.1.0", tuple(manifests))

    def test_unknown_engine_lookup_is_rejected(self):
        with self.assertRaises(EngineRegistryViolation):
            self.registry.resolve("E99")

    def test_registry_persistence_is_append_only_and_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            with ProjectGraphStore(Path(folder) / "registry.sqlite3") as graph:
                arguments = dict(
                    project_id="PROJECT-REGISTRY",
                    created_at=datetime(2026, 8, 31, tzinfo=timezone.utc),
                )
                self.assertEqual("APPENDED", persist_engine_registry(graph, self.registry, **arguments))
                self.assertEqual("IDEMPOTENT", persist_engine_registry(graph, self.registry, **arguments))
                snapshot = graph.snapshot("PROJECT-REGISTRY")
                self.assertEqual(1, len([n for n in snapshot["nodes"] if n["node_type"] == "ENGINE_REGISTRY"]))
                self.assertEqual(8, len([n for n in snapshot["nodes"] if n["node_type"] == "ENGINE_MANIFEST"]))


if __name__ == "__main__":
    unittest.main()
