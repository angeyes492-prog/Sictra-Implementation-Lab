from copy import deepcopy
from contextlib import closing
from hashlib import sha256
from http.client import HTTPConnection
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from sictra_block2_design.design_artifact import DesignArtifactError, fingerprint, render_designed_review_artifact
from sictra_block3_precision.audience_draft import AudiencePolicyError, adapt_content_design
from sictra_block4_orchestrator.operations import initialize, OperationsService
from sictra_block4_orchestrator.operations_store import OperationsError, OperationsStore, process_lock
from sictra_block4_orchestrator.operations_web import create_operations_server
from sictra_block4_orchestrator.runtime import FederatedContractError
from test_block1_eurostat_maritime_mapper import workbook
from hn_customs_fixture import workbook as hn_workbook

NOW = 1789300800


class OperationsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "state"
        self.now = NOW
        self.service = initialize(self.root, now=self.now)
        self.service.clock = lambda: self.now

    def tearDown(self):
        self.service.stop()
        self.temp.cleanup()

    def register(self, data):
        path = Path(self.temp.name) / "supplied.xlsx"
        path.write_bytes(data)
        return self.service.register_file(path, expected_sha256=sha256(data).hexdigest())

    def ready(self):
        self.register(workbook())
        first = self.service.tick()
        self.assertEqual("COMPLETED", first["intake"])
        self.assertFalse(self.service.store.latest("OUTPUT"))
        self.register(workbook(last_updated="07/09/2026 06:14", rows=(("BE", "Belgium", "14", None, "15"),)))
        self.service.tick()
        return next(iter(self.service.store.latest("OUTPUT").values()))

    def hn_ready_after_eurostat(self):
        for waiting in self.service.snapshot()["intake_waiting"]:
            self.service.abstain_intake(waiting["job_id"], "Keep the prior dossier without editorial acceptance")
        for year in (2024, 2025):
            data = hn_workbook(year)
            path = Path(self.temp.name) / f"hn-{year}.xlsx"
            path.write_bytes(data)
            self.service.register_file(path, expected_sha256=sha256(data).hexdigest(),
                                       source_type="HN_CUSTOMS_Q1_V1", geo_level="CUSTOMS_POINT")
            self.service.tick()
        return next(value for value in self.service.store.latest("OUTPUT").values()
                    if value["dossier_id"].startswith("hn-customs:"))

    def test_complete_content_design_preserves_numbers_and_has_evidence_first_structure(self):
        output = self.ready()
        self.assertEqual(self.root.absolute(), self.service.root)
        self.assertIn("12.5", output["plain_text"])
        self.assertIn("14 miles de toneladas", output["plain_text"])
        self.assertIn("1.5 miles de toneladas", output["plain_text"])
        self.assertIn("No independent source corroboration", output["plain_text"])
        self.assertNotIn("Synthetic approved copy", output["plain_text"])
        self.assertEqual(["BLOCK1_DOSSIER_VERIFIED", "BLOCK2_CONTENT_DESIGN", "BLOCK3_AUDIENCE_ADAPTATION"], output["stages"])
        self.assertEqual("DESIGN_REVIEW_REQUIRED", output["state"])
        self.assertEqual("BLOCKED", output["publication"])
        self.assertEqual("NONE", output["delivery"])
        self.assertIn(output["design_artifact"]["evidence_id"], output["plain_text"])
        self.assertEqual("CONTENT_DESIGN_CANDIDATE", output["design_artifact"]["artifact_type"])
        self.assertEqual("REVIEW_NEWSLETTER", output["design_artifact"]["format"])
        self.assertEqual("EVIDENCE_FIRST", output["design_artifact"]["design_system"]["hierarchy"])
        self.assertIn("UNCERTAINTY", [block["kind"] for block in output["adaptation"]["content_blocks"]])
        self.assertEqual(output, self.service.output(output["id"]))

    def test_retained_expired_dossier_cannot_create_autonomy_work(self):
        self.register(workbook())
        self.service.intake.run()
        self.register(workbook(last_updated="07/09/2026 06:14", rows=(("BE", "Belgium", "14", None, "15"),)))
        self.service.intake.run()
        self.now += 86402
        self.service.tick()
        self.assertFalse(self.service.store.latest("AUTONOMY_TASK"))
        self.assertFalse(self.service.store.latest("OUTPUT"))
        states = self.service.snapshot()["dossier_evidence"]
        self.assertEqual(1, len(states))
        self.assertEqual("UNAVAILABLE", states[0]["status"])

    def test_task_source_expiry_is_observed_without_rewriting_history(self):
        output = self.ready()
        original = self.service.store.latest("AUTONOMY_TASK")
        self.assertTrue(original)
        self.assertEqual("CURRENT", self.service.snapshot()["dossier_evidence"][0]["status"])
        self.now += 86402
        before = self.service.store.records()
        view = self.service.snapshot()
        self.assertEqual(before, self.service.store.records())
        self.assertTrue(all(t["source_evidence_status"] == "UNAVAILABLE" for t in view["autonomy_tasks"]))
        task_id = next(iter(original))
        with self.assertRaisesRegex(OperationsError, "AUTONOMY_TASK_SOURCE_NOT_CURRENT"):
            self.service.acknowledge_autonomy_task(task_id, reviewer_id="local-operator",
                rationale="No new action should use the expired source dossier.")
        self.assertEqual(before, self.service.store.records())
        self.service.tick()
        transitions = [r for r in self.service.store.records() if r["kind"] == "DOSSIER_EVIDENCE_STATE"]
        self.assertEqual(["CURRENT", "UNAVAILABLE"], [r["value"]["status"] for r in transitions])
        reopened = OperationsService(self.root, clock=lambda: self.now)
        reopened.tick()
        self.assertEqual(transitions, [r for r in reopened.store.records() if r["kind"] == "DOSSIER_EVIDENCE_STATE"])
        self.assertEqual(original, reopened.store.latest("AUTONOMY_TASK"))
        self.assertEqual([output["id"]], list(reopened.store.latest("OUTPUT")))

    def test_expired_source_does_not_starve_current_other_source(self):
        original = self.ready()
        self.now += 86402
        independent = self.hn_ready_after_eurostat()
        self.assertIn("2025", independent["plain_text"])
        view = self.service.snapshot()
        by_id = {item["dossier_id"]: item["status"] for item in view["dossier_evidence"]}
        self.assertEqual("UNAVAILABLE", by_id[original["dossier_id"]])
        self.assertEqual("CURRENT", by_id[independent["dossier_id"]])
        self.assertTrue(any(t["dossier_id"] == independent["dossier_id"] for t in view["autonomy_tasks"]))
        self.assertEqual("BLOCKED", self.service.output(independent["id"])["publication"])

    def test_task_generation_rejects_substitution_invalid_attestation_and_midcycle_expiry(self):
        self.register(workbook())
        self.service.intake.run()
        self.register(workbook(last_updated="07/09/2026 06:14", rows=(("BE", "Belgium", "14", None, "15"),)))
        self.service.intake.run()
        dossiers = self.service.exporter.list_dossiers()
        # A real signed export for a different identity must not authorize this dossier.
        substitute = deepcopy(dossiers[0])
        substitute["dossier_id"] = "eurostat:substituted"
        real_export = self.service.exporter.export
        with patch.object(self.service.exporter, "export", side_effect=lambda identity, **kw:
                          real_export(dossiers[0]["dossier_id"], **kw)):
            self.assertEqual([], self.service._ensure_autonomy_tasks([substitute]))
        altered = deepcopy(dossiers[0])
        altered["source"]["content_sha256"] = "0" * 64
        self.assertEqual([], self.service._ensure_autonomy_tasks([altered]))
        def forged(identity, **kw):
            result = real_export(identity, **kw)
            result["signature"] = "0" * 64
            return result
        with patch.object(self.service.exporter, "export", side_effect=forged):
            self.assertEqual([], self.service._ensure_autonomy_tasks(dossiers))
        def expires_after_export(identity, **kw):
            result = real_export(identity, **kw)
            self.now += 86402
            return result
        with patch.object(self.service.exporter, "export", side_effect=expires_after_export):
            self.assertEqual([], self.service._ensure_autonomy_tasks(dossiers))
        self.assertFalse(self.service.store.latest("AUTONOMY_TASK"))
        self.assertFalse(self.service.store.latest("OUTPUT"))

    def test_lifecycle_polling_respects_pause_and_stop_without_hidden_transitions(self):
        self.ready()
        self.service.set_paused(True)
        self.now += 86402
        before = self.service.store.records()
        self.assertEqual("PAUSED", self.service.tick()["state"])
        self.assertEqual(before, self.service.store.records())
        self.service.set_paused(False)
        (self.root / "STOP").touch()
        before = self.service.store.records()
        self.assertEqual("STOPPED", self.service.tick()["state"])
        self.assertEqual(before, self.service.store.records())

    def test_restart_and_repeated_cycles_preserve_single_output(self):
        output = self.ready()
        reopened = OperationsService(self.root, clock=lambda: self.now)
        for _ in range(3):
            reopened.tick()
        self.assertEqual([output["id"]], list(reopened.store.latest("OUTPUT")))
        self.assertEqual(1, len([r for r in reopened.store.records() if r["kind"] == "OUTPUT"]))

    def test_profile_configuration_changes_presentation_without_changing_claims(self):
        output = self.ready()
        profile = {**output["profile"], "id": "executive", "label": "Dirección", "role": "Decisión logística",
                   "tone": "EXECUTIVE", "depth": "BRIEF"}
        self.service.add_profile(profile)
        self.service.tick()
        variants = list(self.service.store.latest("OUTPUT").values())
        self.assertEqual(2, len(variants))
        alternate = next(v for v in variants if v["profile"]["id"] == "executive")
        self.assertNotEqual(output["adaptation"]["heading"], alternate["adaptation"]["heading"])
        self.assertEqual(output["design_artifact"]["claims"], alternate["design_artifact"]["claims"])
        self.assertNotEqual(output["adaptation"]["framing"], alternate["adaptation"]["framing"])

    def test_design_is_evidence_first_and_precision_cannot_tamper_with_it(self):
        output = self.ready()
        design = output["design_artifact"]
        kinds = [block["kind"] for block in design["content_blocks"]]
        self.assertEqual("CONTEXT", kinds[0])
        self.assertLess(kinds.index("UNCERTAINTY"), kinds.index("PROVENANCE"))
        claim_ids = {claim["id"] for claim in design["claims"]}
        rendered_ids = {claim_id for block in output["adaptation"]["content_blocks"]
                        for claim_id in block["source_claim_ids"]}
        self.assertEqual(claim_ids, rendered_ids)
        altered = deepcopy(design)
        altered["content_blocks"][1]["body"] = "una conclusión comercial inventada"
        with self.assertRaisesRegex(AudiencePolicyError, "DESIGN_ARTIFACT_INVALID"):
            adapt_content_design(altered, output["profile"], now=self.now)
        altered_adaptation = deepcopy(output["adaptation"])
        altered_adaptation["artifact_fingerprint"] = "0" * 64
        with self.assertRaisesRegex(DesignArtifactError, "ADAPTATION_ARTIFACT_BINDING"):
            render_designed_review_artifact(design, altered_adaptation)
        unsupported = deepcopy(design)
        unsupported["version"] = 2
        unsupported["fingerprint"] = fingerprint({k: v for k, v in unsupported.items() if k != "fingerprint"})
        with self.assertRaisesRegex(AudiencePolicyError, "UNSUPPORTED_CONTENT_DESIGN_VERSION"):
            adapt_content_design(unsupported, output["profile"], now=self.now)
        missing_provenance = deepcopy(design)
        missing_provenance["content_blocks"] = [block for block in missing_provenance["content_blocks"]
                                                  if block["kind"] != "PROVENANCE"]
        missing_provenance["fingerprint"] = fingerprint({k: v for k, v in missing_provenance.items() if k != "fingerprint"})
        with self.assertRaisesRegex(AudiencePolicyError, "REQUIRED_BLOCK_MISSING"):
            adapt_content_design(missing_provenance, output["profile"], now=self.now)

    def test_read_rejects_self_consistent_but_source_unbound_editorial_copy(self):
        output = self.ready()
        self.assertIn("14 miles de toneladas", output["plain_text"])
        forged = deepcopy(output)
        design = forged["design_artifact"]
        design["claims"][0]["text"] = design["claims"][0]["text"].replace("14 miles de toneladas", "999 miles de toneladas")
        design["content_blocks"][1]["body"] = design["claims"][0]["text"]
        design["fingerprint"] = fingerprint({k: v for k, v in design.items() if k != "fingerprint"})
        forged["adaptation"] = adapt_content_design(design, forged["profile"], now=self.now)
        forged["html"], forged["plain_text"] = render_designed_review_artifact(design, forged["adaptation"])
        forged["html_sha256"] = sha256(forged["html"].encode()).hexdigest()
        self.assertIn("999 miles de toneladas", forged["plain_text"])
        self.service.store.put("OUTPUT", output["id"], forged)
        before = self.service.store.records()
        with self.assertRaisesRegex(OperationsError, "OUTPUT_DESIGN_MISMATCH"):
            self.service.output(output["id"])
        summary = self.service.snapshot()["outputs"][0]
        self.assertEqual("STALE_OR_REVOKED", summary["availability"])
        self.assertEqual("Resultado no verificable", summary["title"])
        self.assertNotIn("999 miles de toneladas", str(summary))
        self.assertEqual(before, self.service.store.records())
        server = create_operations_server(self.service, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        client = HTTPConnection("127.0.0.1", server.server_port)
        try:
            client.request("GET", "/api/operations/outputs/" + output["id"] + "/text")
            response = client.getresponse()
            self.assertEqual(409, response.status)
            self.assertNotIn(b"999 miles de toneladas", response.read())
        finally:
            client.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_read_rejects_rebound_adaptation_copy_and_authority_fields(self):
        output = self.ready()
        variants = []
        altered_adaptation = deepcopy(output)
        altered_adaptation["adaptation"]["framing"] = "Conclusión comercial inventada"
        altered_adaptation["adaptation"]["fingerprint"] = fingerprint({
            k: v for k, v in altered_adaptation["adaptation"].items() if k != "fingerprint"})
        altered_adaptation["html"], altered_adaptation["plain_text"] = render_designed_review_artifact(
            altered_adaptation["design_artifact"], altered_adaptation["adaptation"])
        altered_adaptation["html_sha256"] = sha256(altered_adaptation["html"].encode()).hexdigest()
        variants.append((altered_adaptation, "OUTPUT_ADAPTATION_MISMATCH"))
        altered_copy = deepcopy(output)
        altered_copy["plain_text"] += "\nConclusión inventada"
        variants.append((altered_copy, "OUTPUT_CONTENT_MISMATCH"))
        altered_authority = deepcopy(output)
        altered_authority["publication"] = "ALLOWED"
        variants.append((altered_authority, "OUTPUT_BOUNDARY_INVALID"))
        for forged, reason in variants:
            self.service.store.put("OUTPUT", output["id"], forged)
            before = self.service.store.records()
            with self.assertRaisesRegex(OperationsError, reason):
                self.service.output(output["id"])
            self.assertEqual(before, self.service.store.records())
        self.service.store.put("OUTPUT", output["id"], output)
        self.assertEqual(output, self.service.output(output["id"]))

    def test_legacy_source_draft_output_cannot_be_rendered_as_current_design(self):
        output = self.ready()
        legacy = deepcopy(output)
        legacy.pop("design_artifact")
        legacy["id"] = "legacy-source-draft"
        self.service.store.put("OUTPUT", legacy["id"], legacy, immutable=True)
        with self.assertRaisesRegex(OperationsError, "LEGACY_OUTPUT_REQUIRES_MIGRATION"):
            self.service.output(legacy["id"])

    def test_expired_or_superseded_profiles_and_sources_cannot_be_served(self):
        output = self.ready()
        self.service.add_profile({**output["profile"], "role": "Nuevo perfil"})
        with self.assertRaisesRegex(OperationsError, "PROFILE_SUPERSEDED"):
            self.service.output(output["id"])
        self.now += 86402
        self.assertEqual("STALE_OR_REVOKED", self.service.snapshot()["outputs"][0]["availability"])

    def test_budget_does_not_starve_seventeenth_profile(self):
        profile = self.service.store.latest("PROFILE")["logistics-general"]
        for number in range(17):
            self.service.add_profile({**profile, "id": "profile-" + str(number)})
        self.ready()
        self.service.tick(max_cases=16)
        self.assertEqual(18, len(self.service.store.latest("OUTPUT")))

    def test_pause_and_stop_prevent_processing_and_pause_survives_restart(self):
        self.register(workbook())
        self.service.set_paused(True)
        self.assertEqual("PAUSED", self.service.tick()["state"])
        reopened = OperationsService(self.root, clock=lambda: self.now)
        self.assertEqual("PAUSED", reopened.tick()["state"])
        reopened.set_paused(False)
        self.assertEqual("COMPLETED", reopened.tick()["intake"])
        (self.root / "STOP").touch()
        self.assertEqual("STOPPED", reopened.tick()["state"])

    def test_altered_input_and_unapproved_profile_fields_are_rejected(self):
        job = self.register(workbook())
        source = next((self.root / "inbox").iterdir())
        source.write_bytes(b"tampered")
        self.assertEqual("REVIEW_REQUIRED", self.service.tick()["intake"])
        self.assertFalse(self.service.store.latest("OUTPUT"))
        profile = self.service.store.latest("PROFILE")["logistics-general"]
        with self.assertRaisesRegex(AudiencePolicyError, "PROFILE_SCHEMA"):
            self.service.add_profile({**profile, "personality": "susceptible"})

    def test_output_tamper_detected_and_backup_restores_only_to_new_path(self):
        output = self.ready()
        backup = Path(self.temp.name) / "backup"
        self.service.store.backup(backup)
        restored = self.service.store.restore(backup, Path(self.temp.name) / "restored.sqlite")
        self.assertEqual(output, restored.latest("OUTPUT")[output["id"]])
        with self.assertRaisesRegex(OperationsError, "RESTORE_TARGET_EXISTS"):
            self.service.store.restore(backup, self.service.store.path)
        with closing(sqlite3.connect(self.service.store.path)) as db:
            db.execute("UPDATE records SET body='{}' WHERE kind='OUTPUT'")
            db.commit()
        with self.assertRaisesRegex(OperationsError, "INTEGRITY"):
            self.service.snapshot()

    def test_markup_is_escaped_and_unknown_geography_is_waiting(self):
        output = self.ready()
        design, adaptation = deepcopy(output["design_artifact"]), deepcopy(output["adaptation"])
        adaptation["heading"] = '<script>alert("x")</script>'
        adaptation["fingerprint"] = fingerprint({k: v for k, v in adaptation.items() if k != "fingerprint"})
        html, _ = render_designed_review_artifact(design, adaptation)
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)
        profile = {**output["profile"], "id": "unmatched", "geo_codes": ["ES"]}
        self.service.add_profile(profile)
        self.service.tick()
        self.assertTrue(any(w["reason"] == "NO_GEOGRAPHIC_MATCH" for w in self.service.snapshot()["waiting"]))

    def test_single_writer_lock_and_background_polling(self):
        with process_lock(self.root / "service.lock"):
            with self.assertRaisesRegex(OperationsError, "SERVICE_ALREADY_RUNNING"):
                with process_lock(self.root / "service.lock"):
                    self.fail("second process lock entered")
        self.register(workbook())
        self.service.start(interval=1)
        deadline = time.monotonic() + 5
        while self.service.last_cycle is None and time.monotonic() < deadline:
            time.sleep(.05)
        self.assertIsNotNone(self.service.last_cycle)
        self.assertEqual("RUNNING", self.service.snapshot()["status"])
        self.service.stop()
        self.assertFalse(self.service.thread.is_alive())

    def test_watch_requires_opt_in_stability_and_respects_pause(self):
        path = self.root / 'dropbox' / 'approved.xlsx'
        path.write_bytes(workbook())
        self.service.tick()
        self.assertFalse(self.service.intake.snapshot()['jobs'])
        self.service.enable_watch(True)
        self.service.tick()
        self.assertFalse(self.service.intake.snapshot()['jobs'])
        self.service.set_paused(True)
        self.service.tick()
        self.assertFalse(self.service.intake.snapshot()['jobs'])
        self.service.set_paused(False)
        self.assertEqual('COMPLETED', self.service.tick()['intake'])
        self.service.tick()
        self.assertEqual(1, len(self.service.intake.snapshot()['jobs']))

    def test_single_orchestrator_order_enables_local_collection_and_records_the_route(self):
        result = self.service.execute_orchestrated_run()
        self.assertEqual("ORCHESTRATION_EXECUTED", result["status"])
        self.assertEqual("APPROVED_LOCAL_DROPBOX", result["source_boundary"])
        self.assertEqual("BLOCKED", result["publication"])
        self.assertEqual("NONE", result["delivery"])
        self.assertTrue(self.service.snapshot()["watch_enabled"])
        self.assertEqual(result["run_id"], self.service.snapshot()["orchestration"]["last_run"]["run_id"])
        kinds = [record["kind"] for record in self.service.store.records()]
        self.assertIn("ORCHESTRATION_REQUEST", kinds)
        self.assertIn("ORCHESTRATION_RESULT", kinds)

    def test_orchestrator_order_preserves_human_pause_and_stop(self):
        self.service.set_paused(True)
        self.assertEqual("PAUSED", self.service.execute_orchestrated_run()["status"])
        self.assertFalse(self.service.snapshot()["watch_enabled"])
        self.service.set_paused(False)
        (self.root / "STOP").touch()
        self.assertEqual("STOPPED", self.service.execute_orchestrated_run()["status"])

    def test_watch_over_capacity_fails_explicitly_and_stop_cannot_be_restarted(self):
        for number in range(129):
            (self.root / 'dropbox' / str(number)).touch()
        self.service.enable_watch(True)
        with self.assertRaisesRegex(OperationsError, 'WATCH_DIRECTORY_CAPACITY_EXCEEDED'):
            self.service.tick()
        with self.assertRaisesRegex(OperationsError, 'INTERVAL_INVALID'):
            self.service.start(interval=0)
        self.service.stop()
        with self.assertRaisesRegex(OperationsError, 'EXPLICIT_RESET'):
            self.service.start()

    def test_explicit_abstention_releases_intake_without_accepting_output(self):
        output = self.ready()
        pending = self.service.snapshot()['intake_waiting']
        self.assertEqual(1, len(pending))
        self.service.abstain_intake(pending[0]['job_id'], 'Retain the dossier without editorial acceptance')
        self.assertFalse(self.service.snapshot()['intake_waiting'])
        self.assertEqual('DESIGN_REVIEW_REQUIRED', self.service.output(output['id'])['state'])
        self.assertEqual('BLOCKED', self.service.output(output['id'])['publication'])

    def test_dossier_gaps_become_durable_supervised_autonomy_tasks(self):
        output = self.ready()
        tasks = self.service.snapshot()["autonomy_tasks"]
        self.assertTrue(tasks)
        self.assertTrue(all(task["dossier_id"] == output["dossier_id"] for task in tasks))
        self.assertTrue(all(task["state"] == "OPEN" for task in tasks))
        self.assertTrue(all(task["completion_boundary"] == "BLOCK1_CONTRACTED_RESOLUTION_REQUIRED"
                            for task in tasks))
        self.assertTrue(all(task["boundary_status"] == "CURRENT" for task in tasks))
        self.assertEqual({"INDEPENDENT_CORROBORATION", "SOURCE_METHODOLOGY", "COMPANY_EXPOSURE"},
                         {task["effective_kind"] for task in tasks})
        acknowledged = self.service.acknowledge_autonomy_task(
            tasks[0]["task_id"], reviewer_id="operator-local",
            rationale="Se requiere una fuente aprobada de raíz independiente antes de interpretar el cambio.",
        )
        self.assertEqual("ACKNOWLEDGED_NOT_ACCEPTED", acknowledged["status"])
        current = {task["task_id"]: task for task in self.service.snapshot()["autonomy_tasks"]}
        self.assertEqual("HUMAN_ACKNOWLEDGED", current[tasks[0]["task_id"]]["state"])
        self.assertEqual("BLOCKED", self.service.output(output["id"])["publication"])
        with self.assertRaisesRegex(OperationsError, "AUTONOMY_TASK_REVIEW_INVALID"):
            self.service.acknowledge_autonomy_task(tasks[0]["task_id"], reviewer_id="", rationale="short")

    def test_legacy_task_boundary_is_preserved_but_never_projected_as_current_authority(self):
        self.ready()
        task = self.service.snapshot()["autonomy_tasks"][0]
        legacy = {key: value for key, value in task.items()
                  if key not in {"evidence_status", "effective_completion_boundary", "boundary_status"}}
        legacy["completion_boundary"] = "VERIFIED_EVIDENCE_LINK_AND_HUMAN_REASSESSMENT_REQUIRED"
        legacy["allowed_actions"] = ["REGISTER_APPROVED_LOCAL_SOURCE", "LINK_VERIFIED_EVIDENCE"]
        self.service.store.put("AUTONOMY_TASK", task["task_id"], legacy)
        count = len(self.service.store.records())
        view = next(item for item in self.service.snapshot()["autonomy_tasks"]
                    if item["task_id"] == task["task_id"])
        self.assertEqual("VERIFIED_EVIDENCE_LINK_AND_HUMAN_REASSESSMENT_REQUIRED", view["completion_boundary"])
        self.assertEqual("BLOCK1_CONTRACTED_RESOLUTION_REQUIRED", view["effective_completion_boundary"])
        self.assertEqual("LEGACY_SUPERSEDED", view["boundary_status"])
        self.assertEqual(count, len(self.service.store.records()))

    def test_independent_current_dossier_link_requests_block1_reassessment_without_closing_gap(self):
        original = self.ready()
        task = next(item for item in self.service.snapshot()["autonomy_tasks"]
                    if item["dossier_id"] == original["dossier_id"])
        independent = self.hn_ready_after_eurostat()
        linked = self.service.link_autonomy_task_evidence(task["task_id"], independent["dossier_id"])
        self.assertEqual("EVIDENCE_LINKED_REVIEW_REQUIRED", linked["status"])
        self.assertEqual("BLOCKED", linked["publication"])
        self.assertEqual("NOT_ACCEPTED", linked["acceptance"])
        self.assertEqual("HN_SARAH", linked["evidence_link"]["source_root"])
        self.assertEqual("NO_SHARED_MEASUREMENT", linked["evidence_link"]["comparison"]["status"])
        self.assertEqual("NOT_RESOLVED", linked["evidence_link"]["comparison"]["resolution"])
        count = len(self.service.store.records())
        self.assertEqual(linked, self.service.link_autonomy_task_evidence(task["task_id"], independent["dossier_id"]))
        self.assertEqual(count, len(self.service.store.records()))
        self.assertEqual("CURRENT", next(t for t in self.service.snapshot()["autonomy_tasks"]
                                         if t["task_id"] == task["task_id"])["evidence_status"])
        self.assertEqual("NO_SHARED_MEASUREMENT", next(t for t in self.service.snapshot()["autonomy_tasks"]
            if t["task_id"] == task["task_id"])["evidence_comparison"]["status"])
        self.assertEqual("INSUFFICIENT", next(t for t in self.service.snapshot()["autonomy_tasks"]
            if t["task_id"] == task["task_id"])["evidence_assessment"]["verdict"])
        legacy_task = deepcopy(self.service.store.latest("AUTONOMY_TASK")[task["task_id"]])
        legacy_task["evidence_link"].pop("comparison")
        legacy_task["evidence_link"].pop("assessment")
        self.service.store.put("AUTONOMY_TASK", task["task_id"], legacy_task)
        before_legacy_read = self.service.store.records()
        legacy_view = next(t for t in self.service.snapshot()["autonomy_tasks"]
                           if t["task_id"] == task["task_id"])
        self.assertEqual("CURRENT", legacy_view["evidence_status"])
        self.assertEqual("NO_SHARED_MEASUREMENT", legacy_view["evidence_comparison"]["status"])
        self.assertEqual("INSUFFICIENT", legacy_view["evidence_assessment"]["verdict"])
        self.assertEqual(before_legacy_read, self.service.store.records())
        reassessed = self.service.reassess_autonomy_task(
            task["task_id"], reviewer_id="local-reviewer",
            rationale="Solicito reevaluación de Intelligence; esto no valida causalidad ni aprueba el boletín.",
            decision="REQUEST_BLOCK1_REASSESSMENT")
        self.assertEqual("BLOCK1_REASSESSMENT_REQUIRED", reassessed["status"])
        self.assertEqual("NOT_ACCEPTED", reassessed["acceptance"])
        count = len(self.service.store.records())
        with self.assertRaisesRegex(OperationsError, "AUTONOMY_TASK_NOT_LINKABLE"):
            self.service.link_autonomy_task_evidence(task["task_id"], independent["dossier_id"])
        with self.assertRaisesRegex(OperationsError, "AUTONOMY_TASK_NOT_REASSESSABLE"):
            self.service.reassess_autonomy_task(
                task["task_id"], reviewer_id="local-reviewer",
                rationale="Un segundo acto local no puede fingir que Intelligence ya concluyó.",
                decision="REQUEST_BLOCK1_REASSESSMENT")
        self.assertEqual(count, len(self.service.store.records()))
        self.assertEqual("BLOCKED", self.service.output(original["id"])["publication"])
        self.assertEqual("NONE", self.service.output(independent["id"])["delivery"])
        reopened = OperationsService(self.root, clock=lambda: self.now)
        self.assertEqual("BLOCK1_REASSESSMENT_REQUIRED", next(t for t in reopened.snapshot()["autonomy_tasks"]
                                                           if t["task_id"] == task["task_id"])["state"])
        self.now += 86402
        historical = next(t for t in reopened.snapshot()["autonomy_tasks"]
                          if t["task_id"] == task["task_id"])
        self.assertEqual("STALE_OR_REVOKED", historical["evidence_status"])
        self.assertEqual("BLOCK1_REASSESSMENT_REQUIRED", historical["state"])

    def test_forged_need_assessment_cannot_be_replayed_as_resolution(self):
        original = self.ready()
        task = next(item for item in self.service.snapshot()["autonomy_tasks"]
                    if item["dossier_id"] == original["dossier_id"])
        independent = self.hn_ready_after_eurostat()
        self.service.link_autonomy_task_evidence(task["task_id"], independent["dossier_id"])
        altered = deepcopy(self.service.store.latest("AUTONOMY_TASK")[task["task_id"]])
        altered["evidence_link"]["assessment"]["resolution"] = "RESOLVED"
        self.service.store.put("AUTONOMY_TASK", task["task_id"], altered)
        before = self.service.store.records()
        with self.assertRaisesRegex(OperationsError, "AUTONOMY_TASK_EVIDENCE_LINK_CHANGED"):
            self.service.reassess_autonomy_task(
                task["task_id"], reviewer_id="local-reviewer",
                rationale="Un recibo de tarea alterado no puede fabricar resolución de Intelligence.",
                decision="REQUEST_BLOCK1_REASSESSMENT")
        view = next(item for item in self.service.snapshot()["autonomy_tasks"]
                    if item["task_id"] == task["task_id"])
        self.assertEqual("STALE_OR_REVOKED", view["evidence_status"])
        self.assertIsNone(view["evidence_assessment"])
        self.assertEqual(before, self.service.store.records())

    def test_task_link_rejects_same_root_replacement_and_stale_or_tampered_evidence(self):
        original = self.ready()
        task = next(item for item in self.service.snapshot()["autonomy_tasks"]
                    if item["dossier_id"] == original["dossier_id"])
        before = len(self.service.store.records())
        with self.assertRaisesRegex(OperationsError, "AUTONOMY_TASK_EVIDENCE_ID_INVALID"):
            self.service.link_autonomy_task_evidence(task["task_id"], original["dossier_id"])
        self.assertEqual(before, len(self.service.store.records()))
        independent = self.hn_ready_after_eurostat()
        real_export = self.service.exporter.export
        count = len(self.service.store.records())
        with patch.object(self.service.exporter, "export", side_effect=lambda identity, **kw:
                          real_export(independent["dossier_id"], **kw)
                          if identity == task["dossier_id"] else real_export(identity, **kw)):
            with self.assertRaisesRegex(OperationsError, "AUTONOMY_TASK_EVIDENCE_NOT_CURRENT"):
                self.service.link_autonomy_task_evidence(task["task_id"], independent["dossier_id"])
        self.assertEqual(count, len(self.service.store.records()))
        # Challenge the root check independently of the actual exporter.
        real_dossiers = self.service.exporter.list_dossiers()
        forged_metadata = [{**item, "source": {**item["source"], "root_source_identity": task["source_root"]}}
                           if item["dossier_id"] == independent["dossier_id"] else item for item in real_dossiers]
        count = len(self.service.store.records())
        with patch.object(self.service.exporter, "list_dossiers", return_value=forged_metadata):
            with self.assertRaisesRegex(OperationsError, "AUTONOMY_TASK_EVIDENCE_ROOT_NOT_INDEPENDENT"):
                self.service.link_autonomy_task_evidence(task["task_id"], independent["dossier_id"])
        self.assertEqual(count, len(self.service.store.records()))
        linked = self.service.link_autonomy_task_evidence(task["task_id"], independent["dossier_id"])
        with self.assertRaisesRegex(OperationsError, "AUTONOMY_TASK_LINK_REPLACEMENT_REQUIRES_REVIEW"):
            self.service.link_autonomy_task_evidence(task["task_id"], original["dossier_id"])
        with self.assertRaisesRegex(OperationsError, "AUTONOMY_TASK_REASSESSMENT_INVALID"):
            self.service.reassess_autonomy_task(task["task_id"], reviewer_id="x", rationale="too short", decision=[])
        self.assertEqual("EVIDENCE_LINKED_REVIEW_REQUIRED", linked["status"])
        retained = next((self.root / "hn-customs" / "sources").glob("*.xlsx"))
        retained.write_bytes(retained.read_bytes() + b"tamper")
        count = len(self.service.store.records())
        with self.assertRaisesRegex(OperationsError, "AUTONOMY_TASK_EVIDENCE_NOT_CURRENT"):
            self.service.reassess_autonomy_task(
                task["task_id"], reviewer_id="local-reviewer",
                rationale="No se puede aceptar una fuente retenida cuyo contenido cambió después del enlace.",
                decision="REQUEST_BLOCK1_REASSESSMENT")
        self.assertEqual(count, len(self.service.store.records()))
        view = next(t for t in self.service.snapshot()["autonomy_tasks"] if t["task_id"] == task["task_id"])
        self.assertEqual("STALE_OR_REVOKED", view["evidence_status"])

    def test_task_link_rejects_superseded_original_dossier_without_writes(self):
        original = self.ready()
        task = next(item for item in self.service.snapshot()["autonomy_tasks"]
                    if item["dossier_id"] == original["dossier_id"])
        self.service.abstain_intake(self.service.snapshot()["intake_waiting"][0]["job_id"],
                                    "Keep the prior dossier without editorial acceptance")
        self.register(workbook(last_updated="08/09/2026 06:14", rows=(("BE", "Belgium", "15", None, "17"),)))
        self.service.tick()
        independent = self.hn_ready_after_eurostat()
        count = len(self.service.store.records())
        with self.assertRaisesRegex(OperationsError, "AUTONOMY_TASK_EVIDENCE_NOT_CURRENT"):
            self.service.link_autonomy_task_evidence(task["task_id"], independent["dossier_id"])
        self.assertEqual(count, len(self.service.store.records()))

    def test_http_control_requires_same_origin_token_and_artifacts_are_current(self):
        output = self.ready()
        server = create_operations_server(self.service, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        def request(method, path, value=None, headers=None):
            connection = HTTPConnection('127.0.0.1', server.server_port, timeout=5)
            try:
                connection.request(method, path, body=json.dumps(value) if value is not None else None, headers=headers or {})
                response = connection.getresponse()
                return response.status, dict(response.getheaders()), response.read()
            finally:
                connection.close()
        try:
            status, _, body = request("GET", "/api/operations")
            token = json.loads(body)["control_token"]
            self.assertEqual(200, status)
            self.assertTrue(all(t["research_evaluation"]["verdict"] == "WAITING_LOCAL_EVIDENCE"
                                for t in json.loads(body)["autonomy_tasks"]))
            route = "/api/operations/outputs/" + output["id"] + "/html"
            status, headers, body = request("GET", route)
            self.assertEqual(200, status)
            self.assertIn("sandbox", headers["Content-Security-Policy"])
            self.assertIn(b"12.5", body)
            self.assertEqual(403, request("POST", "/api/operations/control", {"action": "pause"})[0])
            trusted = {"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{server.server_port}", "X-Telecare-Control": token}
            status, _, body = request("POST", "/api/operations/control", {"action": "execute"}, trusted)
            self.assertEqual(200, status)
            self.assertEqual("ORCHESTRATION_EXECUTED", json.loads(body)["status"])
            self.assertEqual(400, request("POST", "/api/operations/control", {"action": "execute", "extra": True}, trusted)[0])
            independent = self.hn_ready_after_eurostat()
            status, _, body = request("GET", "/api/operations")
            self.assertEqual(200, status)
            self.assertTrue(all(t["research_evaluation"]["verdict"] == "INSUFFICIENT"
                                for t in json.loads(body)["autonomy_tasks"]))
            task = next(t for t in self.service.snapshot()["autonomy_tasks"]
                        if t["dossier_id"] == output["dossier_id"])
            link_request = {"task_id": task["task_id"], "evidence_dossier_id": independent["dossier_id"]}
            self.assertEqual(403, request("POST", "/api/operations/tasks/link")[0])
            self.assertEqual(400, request("POST", "/api/operations/tasks/link", {**link_request, "approve": True}, trusted)[0])
            status, _, body = request("POST", "/api/operations/tasks/link", link_request, trusted)
            self.assertEqual(200, status)
            self.assertEqual("EVIDENCE_LINKED_REVIEW_REQUIRED", json.loads(body)["status"])
            review_request = {"task_id": task["task_id"], "reviewer_id": "local-reviewer",
                              "rationale": "La tarea se evalúa localmente; el dossier y el boletín siguen sin aceptación.",
                              "decision": "EVIDENCE_INSUFFICIENT"}
            self.assertEqual(403, request("POST", "/api/operations/tasks/reassess")[0])
            status, _, body = request("POST", "/api/operations/tasks/reassess", review_request, trusted)
            self.assertEqual(200, status)
            self.assertEqual("OPEN", json.loads(body)["status"])
            self.assertEqual(200, request("POST", "/api/operations/control", {"action": "pause"}, trusted)[0])
            self.assertTrue(self.service.is_paused())
            self.assertEqual(403, request("GET", "/api/operations", headers={"Host": "evil.example"})[0])
            self.now += 86402
            self.assertEqual(409, request("GET", route)[0])
            status, _, body = request("GET", "/api/operations")
            self.assertEqual(200, status)
            self.assertTrue(all(t["source_evidence_status"] == "UNAVAILABLE"
                                for t in json.loads(body)["autonomy_tasks"]))
            self.assertTrue(all(t["research_evaluation"]["availability"] == "STALE_OR_REVOKED"
                                and "verdict" not in t["research_evaluation"]
                                for t in json.loads(body)["autonomy_tasks"]))
            before = self.service.store.records()
            status, _, body = request("POST", "/api/operations/tasks/review", {
                "task_id": task["task_id"], "reviewer_id": "local-reviewer",
                "rationale": "Expired evidence must not allow a new workflow action."}, trusted)
            self.assertEqual(400, status)  # Existing POST contract: rejected commands are 400.
            self.assertEqual("OperationsError", json.loads(body)["reason"])
            self.assertEqual(before, self.service.store.records())
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
