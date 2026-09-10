import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from sictra_block1.operator_workspace import (
    OperatorWorkspaceViolation,
    create_operator_data_backup,
    initialize_operator_workspace,
    load_operator_dossier_store,
    restore_operator_data_backup,
)
from test_block1_intelligence_dossier import BRIDGE_KEY, KEY, reviewable_delta


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
        backup_launcher = Path("backup_intelligence.cmd").read_text(encoding="utf-8")
        restore_launcher = Path("restore_intelligence.cmd").read_text(encoding="utf-8")
        self.assertIn("operator_workspace backup", backup_launcher)
        self.assertIn("Las claves NO fueron copiadas", backup_launcher)
        self.assertIn("operator_workspace restore", restore_launcher)
        self.assertIn("nunca reemplaza", restore_launcher)

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

    def test_data_only_backup_restores_with_original_keys_and_never_overwrites(self):
        initialize_operator_workspace(self.root)
        (self.root / "keys" / "dossier-integrity.key").write_bytes(KEY)
        (self.root / "keys" / "watchlist-bridge.key").write_bytes(BRIDGE_KEY)
        store = load_operator_dossier_store(self.root, clock=lambda: 10_001)
        receipt = store.persist(reviewable_delta())
        backup = Path(self.temp.name) / "backup-001"
        result = create_operator_data_backup(self.root, backup, clock=lambda: 10_002)
        self.assertEqual(result["status"], "BACKUP_CREATED")
        self.assertFalse(result["keys_included"])
        self.assertEqual({item.name for item in backup.iterdir()}, {
            "backup-manifest.json", "dossiers.json",
        })
        manifest = json.loads((backup / "backup-manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["keys_included"])

        with self.assertRaises(OperatorWorkspaceViolation):
            restore_operator_data_backup(self.root, backup)
        (self.root / "dossiers.json").unlink()
        restored = restore_operator_data_backup(self.root, backup)
        self.assertEqual(restored["status"], "RESTORED")
        dossiers = load_operator_dossier_store(self.root).list_dossiers()
        self.assertEqual([item["dossier_id"] for item in dossiers], [receipt["dossier_id"]])

    def test_backup_tamper_wrong_location_and_empty_state_fail_closed(self):
        initialize_operator_workspace(self.root)
        inside = self.root / "backup"
        with self.assertRaises(OperatorWorkspaceViolation):
            create_operator_data_backup(self.root, inside)

        empty_backup = Path(self.temp.name) / "empty-backup"
        created = create_operator_data_backup(self.root, empty_backup, clock=lambda: 10_002)
        self.assertFalse(created["dossier_present"])
        self.assertEqual(
            restore_operator_data_backup(self.root, empty_backup)["status"],
            "NO_DATA_TO_RESTORE",
        )

        (self.root / "keys" / "dossier-integrity.key").write_bytes(KEY)
        (self.root / "keys" / "watchlist-bridge.key").write_bytes(BRIDGE_KEY)
        store = load_operator_dossier_store(self.root, clock=lambda: 10_001)
        store.persist(reviewable_delta())
        backup = Path(self.temp.name) / "tampered-backup"
        create_operator_data_backup(self.root, backup, clock=lambda: 10_002)
        (self.root / "dossiers.json").unlink()
        (backup / "dossiers.json").write_bytes(b"tampered")
        with self.assertRaises(OperatorWorkspaceViolation):
            restore_operator_data_backup(self.root, backup)
        self.assertFalse((self.root / "dossiers.json").exists())


if __name__ == "__main__":
    unittest.main()
