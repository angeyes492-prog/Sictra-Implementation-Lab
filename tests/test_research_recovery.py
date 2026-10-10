from contextlib import contextmanager
from contextlib import redirect_stdout, redirect_stderr
from hashlib import sha256
import json
import io
import os
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch

from sictra_block1.research_acquisition import (
    ResearchAcquirer, ResearchQuarantine, ResearchAcquisitionError, canonical,
)
from sictra_block1.research_recovery import backup, restore, ResearchRecoveryError
from test_agent_research_acquisition import Response, dns, NOW


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        @contextmanager
        def transport(*args):
            yield Response(b"<html>official fixture bytes</html>")
        acquirer = ResearchAcquirer(self.base / "source", resolver=dns,
            transport=transport, clock=lambda: NOW)
        self.q = acquirer.quarantine
        self.terms = acquirer.acquire("EUROSTAT_REUSE_NOTICE")["candidate_id"]
        self.meta = acquirer.acquire("EUROSTAT_MAR_METADATA",
            terms_candidate_id=self.terms)["candidate_id"]
        self.archive = self.base / "archive"
        self.target = self.base / "restored"

    def tearDown(self):
        self.temp.cleanup()

    def make_backup(self):
        return backup(self.q, [self.meta], self.archive, clock=lambda: NOW + 86400)

    def test_exact_history_and_terms_restore_without_authority_or_expiry_renewal(self):
        receipt = self.make_backup()
        restore(self.archive, self.target,
            expected_manifest_sha256=receipt["manifest_sha256"])
        q = ResearchQuarantine(self.target)
        for candidate in (self.meta, self.terms):
            for name in ("manifest.json", "content.bin"):
                self.assertEqual((self.q.root / candidate / name).read_bytes(),
                    (q.root / candidate / name).read_bytes())
        descriptor, content = q.read(self.meta, now=NOW)
        self.assertEqual(b"<html>official fixture bytes</html>", content)
        self.assertEqual(self.terms, descriptor["terms_candidate_id"])
        self.assertEqual(NOW + 86400, descriptor["expires_at"])
        self.assertEqual("NOT_ADMITTED", descriptor["admission"])
        self.assertEqual("NONE", descriptor["runtime_effect"])
        self.assertEqual(sorted([self.meta, self.terms]), sorted(p.name for p in q.root.iterdir()))
        with self.assertRaisesRegex(ResearchAcquisitionError, "NOT_CURRENT"):
            q.read(self.meta, now=NOW + 86400)

    def test_wrong_external_digest_or_altered_body_never_exposes_destination(self):
        receipt = self.make_backup()
        with self.assertRaises(ResearchRecoveryError):
            restore(self.archive, self.target, expected_manifest_sha256="0" * 64)
        (self.archive / "data" / self.meta / "content.bin").write_bytes(b"tampered")
        with self.assertRaises(ResearchRecoveryError):
            restore(self.archive, self.target, expected_manifest_sha256=receipt["manifest_sha256"])
        self.assertFalse(self.target.exists())

    def test_resealed_archive_does_not_replace_the_external_identity(self):
        receipt = self.make_backup()
        path = self.archive / "archive-manifest.json"
        manifest = json.loads(path.read_bytes())
        manifest["created_at"] += 1
        path.write_bytes(canonical(manifest))
        with self.assertRaises(ResearchRecoveryError):
            restore(self.archive, self.target, expected_manifest_sha256=receipt["manifest_sha256"])
        self.assertFalse(self.target.exists())

    def test_extra_and_missing_dependency_files_fail_closed(self):
        receipt = self.make_backup()
        extra = self.archive / "operator.key"
        extra.write_bytes(b"not allowed")
        with self.assertRaises(ResearchRecoveryError):
            restore(self.archive, self.target, expected_manifest_sha256=receipt["manifest_sha256"])
        extra.unlink()
        (self.archive / "data" / self.terms / "manifest.json").unlink()
        with self.assertRaises(ResearchRecoveryError):
            restore(self.archive, self.target, expected_manifest_sha256=receipt["manifest_sha256"])
        self.assertFalse(self.target.exists())

    def test_existing_destination_and_source_overlap_are_not_overwritten(self):
        self.target.mkdir()
        marker = self.target / "keep"
        marker.write_bytes(b"owner data")
        receipt = self.make_backup()
        with self.assertRaises(ResearchRecoveryError):
            restore(self.archive, self.target, expected_manifest_sha256=receipt["manifest_sha256"])
        self.assertEqual(b"owner data", marker.read_bytes())
        with self.assertRaises(ResearchRecoveryError):
            backup(self.q, [self.meta], self.q.root / "nested")

    def test_bad_duplicate_and_oversized_selections_do_not_create_archive(self):
        for selected in ([], [self.meta, self.meta], ["../escape"], [self.meta] * 101):
            with self.subTest(selected=selected[:2]), self.assertRaises(ResearchRecoveryError):
                backup(self.q, selected, self.archive)
        self.assertFalse(self.archive.exists())

    def test_atomic_publish_failure_leaves_no_partial_restore(self):
        receipt = self.make_backup()
        with patch("sictra_block1.research_recovery._publish", side_effect=OSError("disk failure")):
            with self.assertRaises(ResearchRecoveryError):
                restore(self.archive, self.target, expected_manifest_sha256=receipt["manifest_sha256"])
        self.assertFalse(self.target.exists())
        self.assertFalse(list(self.base.glob(".research-recovery-*")))

    def test_source_mutation_before_publication_cannot_publish_a_backup(self):
        from sictra_block1 import research_recovery as recovery
        real = recovery._snapshot
        count = 0
        def changing(*args):
            nonlocal count
            count += 1
            if count == 2:
                (self.q.root / self.meta / "content.bin").write_bytes(b"changed")
            return real(*args)
        with patch.object(recovery, "_snapshot", side_effect=changing):
            with self.assertRaises(ResearchRecoveryError):
                self.make_backup()
        self.assertFalse(self.archive.exists())

    def test_concurrent_destination_creation_is_not_overwritten(self):
        from sictra_block1 import research_recovery as recovery
        receipt = self.make_backup()
        publish = recovery._publish
        def competing(stage, destination):
            destination.mkdir()
            # An empty competing target is already owner data: no POSIX replacement.
            publish(stage, destination)
        with patch.object(recovery, "_publish", side_effect=competing):
            with self.assertRaises(ResearchRecoveryError):
                restore(self.archive, self.target, expected_manifest_sha256=receipt["manifest_sha256"])
        self.assertEqual([], list(self.target.iterdir()))

    def test_bounded_body_and_total_bytes_reject_before_publication(self):
        from sictra_block1 import research_recovery as recovery
        for limit in ("MAX_FILE", "MAX_SESSION"):
            with self.subTest(limit=limit), patch.object(recovery, limit, 8):
                with self.assertRaises(ResearchRecoveryError):
                    self.make_backup()
        self.assertFalse(self.archive.exists())

    def test_missing_terms_or_forged_authority_cannot_be_archived(self):
        path = self.q.root / self.meta / "manifest.json"
        original = path.read_bytes()
        forged = json.loads(original)
        forged["admission"] = "APPROVED"
        path.write_bytes(canonical(forged))
        with self.assertRaises(ResearchRecoveryError):
            self.make_backup()
        path.write_bytes(original)
        (self.q.root / self.terms / "content.bin").unlink()
        with self.assertRaises(ResearchRecoveryError):
            self.make_backup()
        self.assertFalse(self.archive.exists())

    def test_duplicate_archive_json_fields_cannot_be_authenticated_as_valid(self):
        receipt = self.make_backup()
        path = self.archive / "archive-manifest.json"
        data = path.read_bytes()[:-1] + b',"version":"0.1.0"}'
        path.write_bytes(data)
        with self.assertRaises(ResearchRecoveryError):
            restore(self.archive, self.target, expected_manifest_sha256=sha256(data).hexdigest())
        self.assertFalse(self.target.exists())

    def test_file_symlink_is_rejected_without_following_it(self):
        receipt = self.make_backup()
        path = self.archive / "data" / self.meta / "content.bin"
        original = path.read_bytes()
        path.unlink()
        try:
            path.symlink_to(self.q.root / self.meta / "content.bin")
        except OSError:
            path.write_bytes(original)
            self.skipTest("host does not authorize creating symlinks")
        with self.assertRaises(ResearchRecoveryError):
            restore(self.archive, self.target, expected_manifest_sha256=receipt["manifest_sha256"])
        self.assertFalse(self.target.exists())

    def test_real_cli_roundtrip_and_invalid_source_do_not_create_missing_roots(self):
        from sictra_block1.research_recovery import main
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(0, main(["backup", "--root", str(self.q.root),
                "--candidate-id", self.meta, "--destination", str(self.archive)]))
        receipt = json.loads(output.getvalue())
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, main(["restore", "--archive", str(self.archive),
                "--destination", str(self.target), "--manifest-sha256", receipt["manifest_sha256"]]))
        self.assertEqual(b"<html>official fixture bytes</html>",
            (self.target / self.meta / "content.bin").read_bytes())
        missing = self.base / "missing"
        with self.assertRaises(SystemExit) as caught:
            main(["backup", "--root", str(missing), "--candidate-id", self.meta,
                "--destination", str(self.base / "other")])
        self.assertEqual(2, caught.exception.code)
        self.assertFalse(missing.exists())

    def test_nested_untrusted_json_is_a_controlled_rejection_not_a_traceback(self):
        self.make_backup()
        raw = b"[" * 10000 + b"0" + b"]" * 10000
        (self.archive / "archive-manifest.json").write_bytes(raw)
        with self.assertRaises(ResearchRecoveryError):
            restore(self.archive, self.target, expected_manifest_sha256=sha256(raw).hexdigest())
        from sictra_block1.research_recovery import main
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            main(["restore", "--archive", str(self.archive), "--destination", str(self.target),
                "--manifest-sha256", sha256(raw).hexdigest()])
        self.assertEqual(2, caught.exception.code)
        self.assertFalse(self.target.exists())

    def test_cleanup_failure_is_a_controlled_error_with_no_final_selection(self):
        receipt = self.make_backup()
        with patch("sictra_block1.research_recovery._write", side_effect=OSError("disk fault")), \
                patch("sictra_block1.research_recovery.shutil.rmtree", side_effect=OSError("cleanup denied")):
            with self.assertRaisesRegex(ResearchRecoveryError, "CLEANUP_FAILED.*unpublished stage") as caught:
                restore(self.archive, self.target, expected_manifest_sha256=receipt["manifest_sha256"])
        self.assertIsInstance(caught.exception.__cause__, ResearchRecoveryError)
        self.assertIn("RESTORE_FAILED", str(caught.exception.__cause__))
        self.assertFalse(self.target.exists())

    @unittest.skipUnless(os.name == "nt", "junctions are Windows-only")
    def test_windows_junction_archive_cannot_follow_another_quarantine(self):
        receipt = self.make_backup()
        target = self.base / "archive-junction"
        result = subprocess.run(["cmd.exe", "/c", "mklink", "/J", str(target), str(self.archive)],
            capture_output=True, text=True, timeout=10)
        if result.returncode:
            self.skipTest("host denies junction creation")
        try:
            with self.assertRaisesRegex(ResearchRecoveryError, "LINK_REJECTED"):
                restore(target, self.target, expected_manifest_sha256=receipt["manifest_sha256"])
            self.assertFalse(self.target.exists())
        finally:
            # Remove only the junction entry, never traverse/delete its target.
            target.rmdir()


if __name__ == "__main__":
    unittest.main()
