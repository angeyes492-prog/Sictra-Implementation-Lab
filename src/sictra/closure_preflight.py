"""Finite twelve-arista mechanism checks; never a product acceptance authority."""
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
import re


@dataclass(frozen=True)
class Objective:
    arista: int
    objective: str
    owner: str
    outstanding: str
    positive: str
    rejection: str


OBJECTIVES = (
    Objective(1, "Retain only approved, hash-bound, current evidence with recoverable lineage", "B1/source authority",
              "Approval and rights for additional comparable sources",
              "test_block1_source_control_store.SourceControlStoreTests.test_persists_replays_and_builds_gateway_without_storing_secrets",
              "test_block1_source_control_store.SourceControlStoreTests.test_expired_binding_remains_history_but_cannot_build_gateway"),
    Objective(2, "Consume stable authorized files periodically without altered or duplicate effects", "B4/B1",
              "Accepted network acquisition contract per source; network acquisition remains disabled",
              "test_block4_local_worker.LocalWorkerTests.test_queued_files_execute_real_pipeline_and_stop_at_literal_dossier_review",
              "test_block4_local_worker.LocalWorkerTests.test_changed_file_does_not_execute_and_blocks_later_jobs"),
    Objective(3, "Distinguish literal value, period, coverage and flag changes without invented cause", "B1",
              "Source metadata needed to explain statistical revision versus real-world change",
              "test_block1_change_context.ChangeContextTests.test_distinct_customs_periods_not_same_period_revision",
              "test_block1_change_context.ChangeContextTests.test_bad_measurement_null_flag_or_scope_never_gets_a_context"),
    Objective(4, "Compare exact metric/unit/geography/period and retain disagreement and two-sided gaps", "B1",
              "Current approved independent source measuring the same phenomenon",
              "test_block1_evidence_comparison.EvidenceComparisonTests.test_exact_matching_measurement_is_only_a_review_candidate",
              "test_block1_evidence_comparison.EvidenceComparisonTests.test_metric_geography_and_period_mismatch_cannot_corroborate"),
    Objective(5, "Evaluate each typed need with evidence, reason and a governed resolution boundary", "B1/architecture authority",
              "Accepted per-need resolution semantics and independent reference cases",
              "test_block1_need_assessment.NeedAssessmentTests.test_agreement_still_needs_review_and_disagreement_is_not_causality",
              "test_block1_need_assessment.NeedAssessmentTests.test_forged_resolution_and_impossible_status_reject"),
    Objective(6, "Persist epistemically separated dossiers and execute E01-E08 only with current authority", "B1",
              "Evidence-backed interpretations and refutable hypotheses validated on real cases",
              "test_block1_runtime.Block1OperationalTests.test_e01_to_e08_authorize_before_durable_effect",
              "test_block1_runtime.Block1OperationalTests.test_unattested_tampered_stale_future_foreign_and_synthetic_sources_do_not_write"),
    Objective(7, "Produce traceable bounded editorial candidates, selection or abstention without publication", "B1/editorial authority",
              "Accepted relevance/quality reference cases; operational dossiers still need research",
              "test_block1_dossier_editorial_bridge.DossierEditorialBridgeTests.test_unreviewed_dossier_is_traceable_and_editorially_blocked",
              "test_block1_dossier_editorial_bridge.DossierEditorialBridgeTests.test_unknown_identity_and_tampered_store_fail_closed"),
    Objective(8, "Render source-bound design preserving facts, uncertainty and accessibility", "B2/product authority",
              "Accessibility and comprehension validation with authorized users",
              "test_telecare_operations.OperationsTests.test_complete_content_design_preserves_numbers_and_has_evidence_first_structure",
              "test_telecare_operations.OperationsTests.test_read_rejects_self_consistent_but_source_unbound_editorial_copy"),
    Objective(9, "Adapt current design only to authorized current audience/profile context", "B3/data authority",
              "Authorized account exposure/person context and consent where applicable",
              "test_telecare_operations.OperationsTests.test_profile_configuration_changes_presentation_without_changing_claims",
              "test_telecare_operations.OperationsTests.test_expired_or_superseded_profiles_and_sources_cannot_be_served"),
    Objective(10, "Run bounded evidence search, assessment and reevaluation with pause/STOP and replay safety", "B4/B1",
              "Accepted complete resolution-to-new-dossier-to-new-decision loop, not triage alone",
              "test_local_research_cycle.ResearchSchedulerTests.test_budget_progresses_beyond_first_batch_and_restart_replays_without_duplicates",
              "test_local_research_cycle.ResearchSchedulerTests.test_partial_persistence_rolls_back_result_and_head_then_retry_recovers"),
    Objective(11, "Learn only from an authorized observed delivery receipt and linked outcome", "B3/channel authority",
              "External channel activation, actual receipt and observed outcome; no external delivery enabled",
              "test_block3_precision_adaptive_frontier.LearningEngineTests.test_complete_chain_creates_candidate_not_rule",
              "test_block3_precision_adaptive_frontier.LearningEngineTests.test_no_receipt_means_no_learning"),
    Objective(12, "Reproduce local setup, integrated operation, paused full restore and exact-SHA CI", "B4/operator/architecture authority",
              "MAR activation, sustained installed pilot, operator identity/key custody and independent final review",
              "test_laboratory_recovery.LaboratoryRecoveryTests.test_full_restore_retains_sources_dossiers_and_outputs_but_stays_paused",
              "test_laboratory_recovery.LaboratoryRecoveryTests.test_tampered_archive_and_existing_target_are_rejected_before_writes"),
)


class RecordedResult(unittest.TextTestResult):
    """Record execution, including subtest and expected-failure non-passes."""
    def __init__(self, *args):
        super().__init__(*args)
        self.outcomes = {}

    def addSuccess(self, test):
        super().addSuccess(test)
        self.outcomes[test.id()] = "PASS"

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.outcomes[test.id()] = "FAIL"

    def addError(self, test, err):
        super().addError(test, err)
        self.outcomes[test.id()] = "ERROR"

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.outcomes[test.id()] = "SKIPPED"

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.outcomes[test.id()] = "EXPECTED_FAILURE"

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.outcomes[test.id()] = "UNEXPECTED_SUCCESS"

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            self.outcomes[test.id()] = "SUBTEST_FAILURE"


def run_checks(suite):
    """Execute once; callers cannot supply a precomputed list of passes."""
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=1, resultclass=RecordedResult).run(suite)
    return result, stream.getvalue()


def summarize(result, before, after, *, objectives=OBJECTIVES):
    expected = {test for item in objectives for test in (item.positive, item.rejection)}
    inventory_valid = (tuple(item.arista for item in objectives) == tuple(range(1, 13)) and
                       len(expected) == 24 and all(item.objective and item.owner and item.outstanding for item in objectives))
    executed_exactly = (result.testsRun == len(expected) and set(result.outcomes) == expected)
    stable = before == after
    identity_valid = (isinstance(before, dict) and set(before) == {"sha", "source_tree_sha256", "dirty"}
                      and isinstance(before["sha"], str) and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", before["sha"]) is not None
                      and isinstance(before["source_tree_sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", before["source_tree_sha256"]) is not None
                      and type(before["dirty"]) is bool)
    ok = (inventory_valid and identity_valid and executed_exactly and stable and result.wasSuccessful()
          and all(result.outcomes.get(test) == "PASS" for test in expected))
    return {"version": "0.1.0", "scope": "TWELVE_ARISTA_LOCAL_MECHANISM_PREFLIGHT",
            "checked_at": datetime.now(timezone.utc).isoformat(), "checkout": before,
            "checkout_unchanged": stable, "checkout_valid": identity_valid, "inventory_valid": inventory_valid,
            "exact_test_inventory_executed": executed_exactly,
            "all_mechanism_checks_passed": ok, "tests_run": result.testsRun,
            "outcomes": result.outcomes,
            "aristas": [{"arista": item.arista, "objective": item.objective, "owner": item.owner,
                         "positive_test": item.positive, "rejection_test": item.rejection,
                         "mechanism_check": "PASS" if stable and identity_valid and inventory_valid and executed_exactly and
                             all(result.outcomes.get(t) == "PASS" for t in (item.positive, item.rejection)) else "NOT_VERIFIED",
                         "product_closure": "INSUFFICIENT EVIDENCE", "outstanding": item.outstanding}
                        for item in objectives],
            "product_completion": "NOT_DEMONSTRATED", "acceptance": "NOT_ACCEPTED",
            "publication": "BLOCKED", "ci": "SEPARATE_EXACT_SHA_EVIDENCE_REQUIRED",
            "limitations": ["Selected mechanism fixtures are not full regression or independent product validation",
                            "This diagnostic cannot accept architecture, approve sources or promote gates"]}


def checkout_identity(root):
    """Bind tests to SHA plus tracked/untracked checkout bytes, including fixtures."""
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], timeout=30)
    if Path(git("rev-parse", "--show-toplevel").decode().strip()).resolve() != root.resolve():
        raise ValueError("PREFLIGHT_REPOSITORY_ROOT_MISMATCH")
    names = git("ls-files", "--cached", "--others", "--exclude-standard", "-z").decode().split("\0")
    material = []
    for name in sorted(set(names) - {""}):
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("PREFLIGHT_SOURCE_PATH_INVALID")
        material.append([name, sha256(path.read_bytes()).hexdigest() if path.is_file() else "DELETED"])
    return {"sha": git("rev-parse", "HEAD").decode().strip(),
            "source_tree_sha256": sha256(json.dumps(material, separators=(",", ":")).encode()).hexdigest(),
            "dirty": bool(git("status", "--porcelain"))}


def main():
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "tests"))
    before = checkout_identity(root)
    names = [test for item in OBJECTIVES for test in (item.positive, item.rejection)]
    suite = unittest.defaultTestLoader.loadTestsFromNames(names)
    result, diagnostic = run_checks(suite)
    report = summarize(result, before, checkout_identity(root))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["all_mechanism_checks_passed"]:
        print(diagnostic, file=sys.stderr)
        return 1
    return 0  # This is mechanism success only; product_completion stays NOT_DEMONSTRATED.


if __name__ == "__main__":
    raise SystemExit(main())
