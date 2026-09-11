import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sictra_block2_design.__main__ import main


class TraceableCliTests(unittest.TestCase):
    def test_cli_exposes_persistent_trace_without_claiming_acceptance(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / "trace.sqlite3"
            arguments = [
                "sictra_block2_design", "--trace-db", str(database),
                "--run-at", "2026-08-30T00:00:00+00:00",
                "--run-id", "RUN-CLI-001",
            ]
            output = io.StringIO()
            with patch("sys.argv", arguments), patch("sys.stdout", output):
                self.assertEqual(0, main())
            payload = json.loads(output.getvalue())
            self.assertTrue(payload["completed"])
            self.assertEqual("APPENDED", payload["trace"]["graph_action"])
            self.assertEqual("RUN-CLI-001", payload["trace"]["run_id"])
            self.assertEqual("CANDIDATE_NOT_ACCEPTED", payload["trace"]["state"])
            self.assertEqual("NOT_ACCEPTED", payload["acceptance_state"])
            self.assertTrue(database.exists())

            replay = io.StringIO()
            with patch("sys.argv", arguments), patch("sys.stdout", replay):
                self.assertEqual(0, main())
            self.assertEqual("IDEMPOTENT", json.loads(replay.getvalue())["trace"]["graph_action"])


if __name__ == "__main__":
    unittest.main()
