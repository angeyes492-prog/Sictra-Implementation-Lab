from contextlib import redirect_stdout
import io
import json
from unittest.mock import patch
import unittest

from sictra_block1.__main__ import main, source_readiness


class SourceReadinessCliTests(unittest.TestCase):
    def test_readiness_snapshot_exposes_candidates_and_not_admissible_sources(self):
        payload = source_readiness(region="AMERICAS", domain="TRADE")
        self.assertEqual(payload["status"], "RESEARCH_BLOCKED_PENDING_SOURCE_BINDING")
        self.assertEqual(payload["admissible_source_count"], 0)
        self.assertIn("cepal", {candidate["source_id"] for candidate in payload["candidates"]})
        self.assertTrue(all(candidate["status"] == "PROPOSED" for candidate in payload["candidates"]))

    def test_cli_serializes_a_readiness_snapshot_without_fixture(self):
        output = io.StringIO()
        with patch("sys.argv", ["sictra_block1", "--source-readiness", "--region", "EUROPE", "--domain", "TRADE"]):
            with redirect_stdout(output):
                self.assertEqual(main(), 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["query"], {"region": "EUROPE", "domain": "TRADE"})
        self.assertEqual(payload["admissible_source_count"], 0)


if __name__ == "__main__":
    unittest.main()
