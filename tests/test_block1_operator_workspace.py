import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from sictra_block1.operator_workspace import (
    OperatorWorkspaceViolation,
    initialize_operator_workspace,
    load_operator_dossier_store,
)


class Block1OperatorWorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name) / "operator"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_initializes_reuses_and_never_places_keys_in_manifest(self):
        created = initialize_operator_workspace(self.root)
        self.assertFalse(created["reused"])
        self.assertEqual(created["status"], "READY")
        manifest_text = (self.root / "operator-state.json").read_text(encoding="utf-8")
        manifest = json.loads(manifest_text)
        self.assertEqual(set(manifest), {
            "version", "scope", "dossier_store", "dossier_integrity_key", "bridge_keys",
        })
        for relative in (
            manifest["dossier_integrity_key"],
            manifest["bridge_keys"]["watchlist-bridge"],
        ):
            key = self.root.joinpath(*relative.split("/")).read_bytes()
            self.assertEqual(len(key), 32)
            self.assertNotIn(key.hex(), manifest_text)
        self.assertEqual(load_operator_dossier_store(self.root).list_dossiers(), [])
        reused = initialize_operator_workspace(self.root)
        self.assertTrue(reused["reused"])

    def test_nonempty_uninitialized_and_modified_configuration_fail_closed(self):
        self.root.mkdir()
        (self.root / "unexpected.txt").write_text("do not overwrite", encoding="utf-8")
        with self.assertRaises(OperatorWorkspaceViolation):
            initialize_operator_workspace(self.root)
        self.assertEqual((self.root / "unexpected.txt").read_text(encoding="utf-8"), "do not overwrite")

        other = Path(self.temp.name) / "configured"
        initialize_operator_workspace(other)
        manifest_path = other / "operator-state.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["dossier_store"] = "substituted.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(OperatorWorkspaceViolation):
            load_operator_dossier_store(other)

    def test_truncated_key_and_partial_initialization_are_rejected(self):
        initialize_operator_workspace(self.root)
        key_path = self.root / "keys" / "dossier-integrity.key"
        key_path.write_bytes(b"short")
        with self.assertRaises(OperatorWorkspaceViolation):
            load_operator_dossier_store(self.root)
        with self.assertRaises(OperatorWorkspaceViolation):
            initialize_operator_workspace(self.root)

        other = Path(self.temp.name) / "tampered-store"
        initialize_operator_workspace(other)
        (other / "dossiers.json").write_text("not-json", encoding="utf-8")
        with self.assertRaises(OperatorWorkspaceViolation):
            load_operator_dossier_store(other)

        partial = Path(self.temp.name) / "partial"
        with patch(
            "sictra_block1.operator_workspace._exclusive_write",
            side_effect=OSError("injected"),
        ):
            with self.assertRaises(OperatorWorkspaceViolation):
                initialize_operator_workspace(partial)
        self.assertFalse(partial.exists())


if __name__ == "__main__":
    unittest.main()
