from dataclasses import replace
from pathlib import Path
import subprocess
import tempfile
import unittest

from sictra.closure_preflight import OBJECTIVES, checkout_identity, run_checks, summarize

IDENTITY = {"sha": "1" * 40, "source_tree_sha256": "2" * 64, "dirty": True}

def cases(mode=None):
    def passes(self):
        self.assertEqual(4, 2 + 2)
    def fails(self):
        self.fail("Injected failure must not become closure evidence")
    def skip(self):
        self.skipTest("Execution absent")
    def subtest(self):
        with self.subTest(vector="tamper"):
            self.fail("Injected failed subtest")
    def expected_failure(self):
        self.fail("Known defect is not a pass")
    def unexpected(self):
        self.assertEqual(4, 2 + 2)
    methods = {f"test_{index:02d}": passes for index in range(24)}
    methods["test_00"] = {"fail": fails, "skip": skip, "subtest": subtest,
                          "expected": unittest.expectedFailure(expected_failure),
                          "unexpected": unittest.expectedFailure(unexpected)}.get(mode, passes)
    case_type = type("SentinelCases", (unittest.TestCase,), methods)
    suite = unittest.TestSuite(case_type(f"test_{index:02d}") for index in range(24))
    names = [case_type(f"test_{index:02d}").id() for index in range(24)]
    objectives = tuple(replace(item, positive=names[index * 2], rejection=names[index * 2 + 1])
                       for index, item in enumerate(OBJECTIVES))
    return suite, objectives


class ClosurePreflightTests(unittest.TestCase):
    def test_exact_executed_inventory_never_claims_product_completion(self):
        suite, objectives = cases()
        result, _ = run_checks(suite)
        report = summarize(result, IDENTITY, IDENTITY, objectives=objectives)
        self.assertTrue(report["all_mechanism_checks_passed"])
        self.assertEqual(24, report["tests_run"])
        self.assertEqual(list(range(1, 13)), [a["arista"] for a in report["aristas"]])
        self.assertTrue(all(a["product_closure"] == "INSUFFICIENT EVIDENCE" and a["outstanding"]
                            for a in report["aristas"]))
        self.assertEqual("NOT_DEMONSTRATED", report["product_completion"])
        self.assertEqual("NOT_ACCEPTED", report["acceptance"])
        self.assertEqual("BLOCKED", report["publication"])
        self.assertEqual("SEPARATE_EXACT_SHA_EVIDENCE_REQUIRED", report["ci"])

    def test_failure_skip_expected_failure_unexpected_success_and_subtest_fail_closed(self):
        for mode in ("fail", "skip", "expected", "unexpected", "subtest"):
            with self.subTest(mode=mode):
                suite, objectives = cases(mode)
                result, _ = run_checks(suite)
                report = summarize(result, IDENTITY, IDENTITY, objectives=objectives)
                self.assertFalse(report["all_mechanism_checks_passed"])
                self.assertEqual("NOT_VERIFIED", report["aristas"][0]["mechanism_check"])

    def test_missing_or_duplicate_execution_cannot_be_laundered_by_test_count(self):
        for duplicate in (False, True):
            suite, objectives = cases()
            tests = list(suite)
            modified = tests[:-1] + ([type(tests[0])("test_00")] if duplicate else [])
            result, _ = run_checks(unittest.TestSuite(modified))
            report = summarize(result, IDENTITY, IDENTITY, objectives=objectives)
            self.assertFalse(report["all_mechanism_checks_passed"])
            self.assertFalse(report["exact_test_inventory_executed"])

    def test_checkout_drift_and_incomplete_goal_inventory_reject(self):
        suite, objectives = cases()
        result, _ = run_checks(suite)
        report = summarize(result, {"source_tree_sha256": "old"}, {"source_tree_sha256": "new"}, objectives=objectives)
        self.assertFalse(report["all_mechanism_checks_passed"])
        self.assertTrue(all(a["mechanism_check"] == "NOT_VERIFIED" for a in report["aristas"]))
        for bad in (objectives[:-1], (replace(objectives[0], owner=""),) + objectives[1:]):
            report = summarize(result, IDENTITY, IDENTITY, objectives=bad)
            self.assertFalse(report["inventory_valid"])
            self.assertFalse(report["all_mechanism_checks_passed"])

    def test_missing_checkout_identity_cannot_claim_pass(self):
        suite, objectives = cases()
        result, _ = run_checks(suite)
        for bad in ({}, {**IDENTITY, "sha": "unknown"}, {**IDENTITY, "dirty": "no"}):
            report = summarize(result, bad, bad, objectives=objectives)
            self.assertFalse(report["checkout_valid"])
            self.assertFalse(report["all_mechanism_checks_passed"])

    def test_checkout_identity_binds_dirty_untracked_and_deleted_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            def git(*args):
                subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)
            git("init", "-q")
            source = root / "implementation.py"
            source.write_text("VERSION = 1\n", encoding="utf-8")
            git("add", "implementation.py")
            git("-c", "user.name=Local Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "Fixture baseline")
            initial = checkout_identity(root)
            self.assertFalse(initial["dirty"])
            source.write_text("VERSION = 2\n", encoding="utf-8")
            changed = checkout_identity(root)
            self.assertEqual(initial["sha"], changed["sha"])
            self.assertNotEqual(initial["source_tree_sha256"], changed["source_tree_sha256"])
            self.assertTrue(changed["dirty"])
            (root / "new_test.py").write_text("CHECK = True\n", encoding="utf-8")
            new = checkout_identity(root)
            self.assertNotEqual(changed["source_tree_sha256"], new["source_tree_sha256"])
            fixture = root / "fixture.json"
            fixture.write_text('{"measurement": 12}', encoding="utf-8")
            fixture_before = checkout_identity(root)
            fixture.write_text('{"measurement": 99}', encoding="utf-8")
            self.assertNotEqual(fixture_before["source_tree_sha256"], checkout_identity(root)["source_tree_sha256"])
            source.unlink()
            self.assertNotEqual(new["source_tree_sha256"], checkout_identity(root)["source_tree_sha256"])


if __name__ == "__main__":
    unittest.main()
