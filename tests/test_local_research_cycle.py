"""Scheduling fixtures plus actual admitted Eurostat/HN pipeline integration."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sictra_block4_orchestrator.operations import initialize, OperationsService
from sictra_block4_orchestrator.operations_store import OperationsError, OperationsStore
from sictra_block4_orchestrator.research_cycle import LocalResearchCycle
from test_block1_eurostat_maritime_mapper import workbook
from hn_customs_fixture import workbook as hn_workbook


class ResearchSchedulerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = OperationsStore(Path(self.temp.name) / "ops.sqlite", b"x" * 32)
        self.now, self.stopped = 100, False
        self.tasks = [{"task_id": f"TASK-{i}", "dossier_id": "a", "source_id": "source-a",
                       "source_root": "root-a", "requirement": f"need-{i}"} for i in range(5)]
        self.dossiers = [{"dossier_id": name, "source": {"source_id": f"source-{name}",
                         "root_source_identity": f"root-{name}", "content_sha256": name * 64}}
                         for name in ("a", "b")]
        self.cycle = LocalResearchCycle(store=self.store, source_check=self.source,
            candidate_check=self.candidate, clock=lambda: self.now, stopped=lambda: self.stopped)

    def tearDown(self):
        self.temp.cleanup()

    def source(self, identity):
        return {"dossier_id": identity, "status": "CURRENT", "checked_at": self.now,
                "evidence_id": identity, "source_hash": identity * 64, "expires_at": "2999-01-01T00:00:00+00:00"}

    def candidate(self, task, identity):
        return {"dossier_id": identity, "evidence_id": identity, "source_hash": identity * 64,
                "expires_at": "2999-01-01T00:00:00+00:00",
                "assessment": {"verdict": "INSUFFICIENT", "reason_code": "NO_SHARED_MEASUREMENT",
                               "next_action": "REQUEST_COMPARABLE_APPROVED_SOURCE"}}

    def test_budget_progresses_beyond_first_batch_and_restart_replays_without_duplicates(self):
        observed = set()
        for _ in range(3):
            observed.update(r["task_id"] for r in self.cycle.run(self.tasks, self.dossiers, budget=2))
            self.now += 1
        self.assertEqual({t["task_id"] for t in self.tasks}, observed)
        self.assertEqual(5, len(self.store.latest("RESEARCH_EVALUATION")))
        reopened = LocalResearchCycle(store=OperationsStore(self.store.path, b"x" * 32),
            source_check=self.source, candidate_check=self.candidate,
            clock=lambda: self.now, stopped=lambda: False)
        reopened.run(self.tasks, self.dossiers, budget=32)
        self.assertEqual(5, len(self.store.latest("RESEARCH_EVALUATION")))
        self.assertEqual("CURRENT_INPUTS", reopened.view(self.tasks[0])["availability"])
        self.assertEqual("NOT_RESOLVED", reopened.view(self.tasks[0])["resolution"])

    def test_no_distinct_root_is_visible_wait_and_reads_do_not_write(self):
        same_root = deepcopy(self.dossiers)
        same_root[1]["source"]["root_source_identity"] = "root-a"
        self.cycle.run(self.tasks[:1], same_root)
        before = self.store.records()
        view = self.cycle.view(self.tasks[0])
        self.assertEqual("WAITING_LOCAL_EVIDENCE", view["verdict"])
        self.assertIsNone(view["candidate"])
        self.assertEqual("OBSERVED_CYCLE_SNAPSHOT", view["inventory_boundary"])
        self.assertEqual(before, self.store.records())

    def test_legacy_wait_is_withdrawn_then_reassessed_without_rewriting_history(self):
        task = self.tasks[0]
        self.cycle.run([task], self.dossiers)
        original = self.store.latest("RESEARCH_EVALUATION")
        routed = {**task, "evidence_route": "OFFICIAL_SOURCE_METHODOLOGY",
                  "next_action": "REQUEST_SOURCE_SPECIFIC_METHODOLOGY"}
        before = self.store.records()
        with patch.object(self.cycle, "candidate_check", side_effect=OperationsError("AUTONOMY_TASK_EVIDENCE_ROUTE_NOT_LINKABLE")):
            self.assertEqual("STALE_OR_REVOKED", self.cycle.view(routed)["availability"])
            self.assertEqual(before, self.store.records())
            self.cycle.run([routed], self.dossiers)
            result = self.cycle.view(routed)
        self.assertEqual("WAITING_TASK_SPECIFIC_EVIDENCE", result["verdict"])
        self.assertEqual("REQUEST_SOURCE_SPECIFIC_METHODOLOGY", result["next_action"])
        self.assertIsNone(result["candidate"])
        for identity, value in original.items():
            self.assertEqual(value, self.store.latest("RESEARCH_EVALUATION")[identity])
        records = self.store.records()
        self.cycle.run([routed], self.dossiers)
        self.assertEqual(2, len(self.store.latest("RESEARCH_EVALUATION")))
        self.assertEqual(records, self.store.records())

    def test_unavailable_candidate_does_not_starve_later_task(self):
        def reject_first(task, identity):
            if task["task_id"] == "TASK-0":
                raise OperationsError("AUTONOMY_TASK_EVIDENCE_NOT_CURRENT")
            return self.candidate(task, identity)
        with patch.object(self.cycle, "candidate_check", side_effect=reject_first):
            self.assertEqual([], self.cycle.run(self.tasks[:2], self.dossiers, budget=1))
            result = self.cycle.run(self.tasks[:2], self.dossiers, budget=1)
        self.assertEqual(["TASK-1"], [r["task_id"] for r in result])
        self.assertNotIn("TASK-0", self.store.latest("RESEARCH_HEAD"))

    def test_immutable_collision_rolls_back_other_entries_and_invalid_batch_is_rejected(self):
        self.store.put("RESEARCH_EVALUATION", "retained", {"value": 1}, immutable=True)
        before = self.store.records()
        with self.assertRaisesRegex(OperationsError, "IMMUTABLE_IDENTITY_COLLISION"):
            self.store.put_batch([("RESEARCH_HEAD", "new", {"evaluation_id": "new"}, False),
                                  ("RESEARCH_EVALUATION", "retained", {"value": 2}, True)])
        self.assertEqual(before, self.store.records())
        for invalid in ([], [None] * 4, "not a batch"):
            with self.assertRaisesRegex(OperationsError, "OPERATIONS_BATCH_INVALID"):
                self.store.put_batch(invalid)
        self.assertEqual(before, self.store.records())

    def test_stopped_stale_changed_and_invalid_budget_cannot_commit_evaluation(self):
        self.stopped = True
        self.assertEqual([], self.cycle.run(self.tasks, self.dossiers))
        self.stopped = False
        with patch.object(self.cycle, "source_check", return_value={"status": "UNAVAILABLE"}):
            self.cycle.run(self.tasks, self.dossiers)
        self.assertFalse(self.store.latest("RESEARCH_EVALUATION"))
        calls = [0]
        def changing(task, identity):
            calls[0] += 1
            value = self.candidate(task, identity)
            value["evidence_id"] = str(calls[0])
            return value
        with patch.object(self.cycle, "candidate_check", side_effect=changing):
            self.cycle.run(self.tasks, self.dossiers)
        self.assertFalse(self.store.latest("RESEARCH_EVALUATION"))
        for invalid in (0, 33, True, 1.5):
            with self.assertRaisesRegex(OperationsError, "RESEARCH_BUDGET_INVALID"):
                self.cycle.run(self.tasks, self.dossiers, budget=invalid)

    def test_stop_during_candidate_check_leaves_no_result_or_head(self):
        def stop_during_check(task, identity):
            self.stopped = True
            return self.candidate(task, identity)
        before = self.store.records()
        with patch.object(self.cycle, "candidate_check", side_effect=stop_during_check):
            self.cycle.run(self.tasks, self.dossiers)
        self.assertEqual(before, self.store.records())

    def test_expiry_during_final_candidate_check_cannot_commit_or_remain_current(self):
        calls = [0]
        def expiring_candidate(task, identity):
            calls[0] += 1
            if calls[0] == 2:
                self.now = 200
            return self.candidate(task, identity)
        def timed_source(identity):
            return {**self.source(identity), "status": "CURRENT" if self.now < 200 else "EXPIRED"}
        with patch.object(self.cycle, "source_check", side_effect=timed_source), \
             patch.object(self.cycle, "candidate_check", side_effect=expiring_candidate):
            self.cycle.run(self.tasks[:1], self.dossiers)
        self.assertFalse(self.store.latest("RESEARCH_EVALUATION"))
        self.now = 100
        self.cycle.run(self.tasks[:1], self.dossiers)
        before = self.store.records()
        def expire_on_read(task, identity):
            self.now = 200
            return self.candidate(task, identity)
        with patch.object(self.cycle, "source_check", side_effect=timed_source), \
             patch.object(self.cycle, "candidate_check", side_effect=expire_on_read):
            view = self.cycle.view(self.tasks[0])
        self.assertEqual("STALE_OR_REVOKED", view["availability"])
        self.assertNotIn("verdict", view)
        self.assertEqual(before, self.store.records())

    def test_partial_persistence_rolls_back_result_and_head_then_retry_recovers(self):
        append = self.store._append
        def failed_head(db, kind, identity, value):
            if kind == "RESEARCH_HEAD":
                raise OperationsError("INJECTED_HEAD_FAILURE")
            return append(db, kind, identity, value)
        before = self.store.records()
        with patch.object(self.store, "_append", side_effect=failed_head):
            with self.assertRaisesRegex(OperationsError, "INJECTED_HEAD_FAILURE"):
                self.cycle.run(self.tasks[:1], self.dossiers)
        self.assertEqual(before, self.store.records())
        self.cycle.run(self.tasks[:1], self.dossiers)
        self.assertEqual(1, len(self.store.latest("RESEARCH_EVALUATION")))
        self.assertEqual(1, len(self.store.latest("RESEARCH_HEAD")))

    def test_candidate_expiring_during_primary_recheck_is_rejected_at_commit_and_read(self):
        calls = [0]
        def primary_recheck(identity):
            calls[0] += 1
            if calls[0] == 3:
                self.now = 200
            return self.source(identity)
        def short_lived_candidate(task, identity):
            return {**self.candidate(task, identity), "expires_at": "1970-01-01T00:03:20+00:00"}
        with patch.object(self.cycle, "source_check", side_effect=primary_recheck), \
             patch.object(self.cycle, "candidate_check", side_effect=short_lived_candidate):
            self.cycle.run(self.tasks[:1], self.dossiers)
        self.assertFalse(self.store.latest("RESEARCH_EVALUATION"))
        self.now = 100
        with patch.object(self.cycle, "candidate_check", side_effect=short_lived_candidate):
            self.cycle.run(self.tasks[:1], self.dossiers)
            def advancing_clock():
                self.now = 200
                return self.now
            before = self.store.records()
            with patch.object(self.cycle, "clock", side_effect=advancing_clock):
                view = self.cycle.view(self.tasks[0])
        self.assertEqual("STALE_OR_REVOKED", view["availability"])
        self.assertNotIn("verdict", view)
        self.assertEqual(before, self.store.records())

    def test_forged_self_sealed_result_is_rejected_on_read(self):
        self.cycle.run(self.tasks[:1], self.dossiers)
        identity, value = next(iter(self.store.latest("RESEARCH_EVALUATION").items()))
        altered = deepcopy(value)
        altered["resolution"] = "RESOLVED"
        self.store.put("RESEARCH_EVALUATION", identity, altered)
        before = self.store.records()
        view = self.cycle.view(self.tasks[0])
        self.assertEqual("STALE_OR_REVOKED", view["availability"])
        self.assertNotIn("verdict", view)
        self.assertEqual(before, self.store.records())


class ResearchPipelineIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "state"
        self.now = 1789300800
        self.service = initialize(self.root, now=self.now)
        self.service.clock = lambda: self.now
        for data in (workbook(), workbook(last_updated="07/09/2026 06:14",
                     rows=(("BE", "Belgium", "14", None, "15"),))):
            self.ingest(data)

    def tearDown(self):
        self.service.stop()
        self.temp.cleanup()

    def ingest(self, data, hn=False):
        path = Path(self.temp.name) / "source.xlsx"
        path.write_bytes(data)
        options = {"source_type": "HN_CUSTOMS_Q1_V1", "geo_level": "CUSTOMS_POINT"} if hn else {}
        self.service.register_file(path, expected_sha256=sha256(data).hexdigest(), **options)
        self.service.tick()

    def add_hn(self):
        for job in self.service.snapshot()["intake_waiting"]:
            self.service.abstain_intake(job["job_id"], "Retain the prior dossier for research without accepting it")
        for year in (2024, 2025):
            self.ingest(hn_workbook(year), hn=True)

    def test_new_admitted_source_triggers_assessment_without_manual_evidence_link(self):
        initial = self.service.snapshot()["autonomy_tasks"]
        self.assertEqual(3, len(initial))
        self.assertEqual("WAITING_LOCAL_EVIDENCE", next(t for t in initial
                         if t["effective_kind"] == "INDEPENDENT_CORROBORATION")["research_evaluation"]["verdict"])
        self.assertTrue(all(t["research_evaluation"]["verdict"] == "WAITING_TASK_SPECIFIC_EVIDENCE"
                            for t in initial if t["effective_kind"] != "INDEPENDENT_CORROBORATION"))
        self.add_hn()
        view = self.service.snapshot()
        self.assertEqual(6, len(view["autonomy_tasks"]))
        self.assertTrue(all(t["state"] == "OPEN" and not t.get("evidence_link") for t in view["autonomy_tasks"]))
        corroboration = [t for t in view["autonomy_tasks"] if t["effective_kind"] == "INDEPENDENT_CORROBORATION"]
        self.assertTrue(all(t["research_evaluation"]["availability"] == "CURRENT_INPUTS" and
                            t["research_evaluation"]["verdict"] == "INSUFFICIENT" for t in corroboration))
        self.assertTrue(all(t["research_evaluation"]["candidate"]["comparison"]["status"] == "NO_SHARED_MEASUREMENT"
                            for t in corroboration))
        self.assertTrue(all(t["research_evaluation"]["verdict"] == "WAITING_TASK_SPECIFIC_EVIDENCE"
                            and t["research_evaluation"]["candidate"] is None
                            for t in view["autonomy_tasks"] if t["effective_kind"] != "INDEPENDENT_CORROBORATION"))
        self.assertEqual("BLOCKED", view["publication"])

    def test_restart_expiry_pause_and_stop_preserve_history_and_revalidate_inputs(self):
        self.add_hn()
        history = self.service.store.latest("RESEARCH_EVALUATION")
        reopened = OperationsService(self.root, clock=lambda: self.now)
        reopened.tick()
        self.assertEqual(history, reopened.store.latest("RESEARCH_EVALUATION"))
        reopened.set_paused(True)
        before = reopened.store.records()
        self.assertEqual("PAUSED", reopened.tick()["state"])
        self.assertEqual(before, reopened.store.records())
        self.now += 86402
        view = reopened.snapshot()
        euro = [t for t in view["autonomy_tasks"] if t["source_id"] == "eurostat"]
        self.assertTrue(all(t["research_evaluation"]["availability"] == "STALE_OR_REVOKED" for t in euro))
        self.assertEqual(before, reopened.store.records())
        reopened.set_paused(False)
        self.service = reopened
        for job in reopened.snapshot()["intake_waiting"]:
            reopened.abstain_intake(job["job_id"], "Retain expired source history without editorial acceptance")
        self.ingest(hn_workbook(2026), hn=True)
        current = [t for t in reopened.snapshot()["autonomy_tasks"]
                   if t["source_evidence_status"] == "CURRENT"]
        self.assertEqual(3, len(current))
        self.assertTrue(all(t["source_id"] == "HN_ADUANAS_BULLETINS" for t in current))
        self.assertEqual("WAITING_LOCAL_EVIDENCE", next(t for t in current
                         if t["effective_kind"] == "INDEPENDENT_CORROBORATION")["research_evaluation"]["verdict"])
        self.assertTrue(all(t["research_evaluation"]["verdict"] == "WAITING_TASK_SPECIFIC_EVIDENCE"
                            for t in current if t["effective_kind"] != "INDEPENDENT_CORROBORATION"))
        (self.root / "STOP").touch()
        before = reopened.store.records()
        self.assertEqual("STOPPED", reopened.tick()["state"])
        self.assertEqual(before, reopened.store.records())


if __name__ == "__main__":
    unittest.main()
