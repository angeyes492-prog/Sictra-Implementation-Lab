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
        self.assertTrue(all(task["completion_boundary"] == "VERIFIED_EVIDENCE_LINK_AND_HUMAN_REASSESSMENT_REQUIRED"
                            for task in tasks))
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
            self.assertEqual(200, request("POST", "/api/operations/control", {"action": "pause"}, trusted)[0])
            self.assertTrue(self.service.is_paused())
            self.assertEqual(403, request("GET", "/api/operations", headers={"Host": "evil.example"})[0])
            self.now += 86402
            self.assertEqual(409, request("GET", route)[0])
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
