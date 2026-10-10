from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

import test_agent_research_acquisition as acquisition
import test_research_review as review_fixture
from sictra_block1.research_acquisition import ResearchAcquisitionError
from sictra_block4_orchestrator import operations, operations_web


class ResearchStartupTests(unittest.TestCase):
    def setUp(self):
        now = int(time.time())
        self.fixture = review_fixture.ResearchReviewTests()
        with patch.object(acquisition, "NOW", now), patch.object(review_fixture, "NOW", now):
            self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.state = Path(self.fixture.fixture.temp.name) / "operations"
        self.service = operations.initialize(self.state, now=now)
        self.addCleanup(self.service.stop)

    def args(self, regional=None):
        f = self.fixture
        return ["operations", "--state", str(self.state), "serve", "--port", "0",
            "--research-root", str(f.fixture.root), "--research-data-id", f.data,
            "--research-metadata-id", f.metadata, "--research-regional-id", regional or f.regional]

    def test_cli_regional_selection_reaches_real_review_without_source_writes(self):
        f = self.fixture
        before = f.files()
        reports = []
        real_server = operations_web.create_operations_server
        def bounded_server(service, **kwargs):
            reports.append(kwargs["research_review"].read())
            server = real_server(service, **kwargs)
            def stop_after_start():
                raise KeyboardInterrupt
            server.serve_forever = stop_after_start
            return server
        with patch.object(sys, "argv", self.args()), redirect_stdout(io.StringIO()), \
                patch.object(operations_web, "create_operations_server", side_effect=bounded_server):
            self.assertEqual(0, operations.main())
        self.assertEqual("EXPLICIT_MAIN_PORTS_ONLY", reports[0]["regional_methodology"]["regional_scope_label"])
        self.assertEqual("NOT_ADMITTED", reports[0]["admission"])
        self.assertEqual("NONE", reports[0]["runtime_effect"])
        self.assertEqual(before, f.files())

    def test_wrong_regional_recipe_rejects_before_worker_or_server_start(self):
        with patch.object(sys, "argv", self.args(self.fixture.national)), \
                patch.object(operations.OperationsService, "start", side_effect=AssertionError("worker must not start")), \
                patch.object(operations_web, "create_operations_server", side_effect=AssertionError("server must not start")):
            with self.assertRaises(ResearchAcquisitionError):
                operations.main()

    def test_regional_only_configuration_cannot_silently_start_without_data(self):
        args = ["operations", "--state", str(self.state), "serve", "--research-regional-id", self.fixture.regional]
        with patch.object(sys, "argv", args), \
                patch.object(operations.OperationsService, "start", side_effect=AssertionError("worker must not start")):
            with self.assertRaises(SystemExit) as caught:
                operations.main()
        self.assertEqual(2, caught.exception.code)


if __name__ == "__main__":
    unittest.main()
