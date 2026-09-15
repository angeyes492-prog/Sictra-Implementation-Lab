from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import hmac
import json
import tempfile
import unittest

from sictra_block3_precision.context import ContextSignal
from sictra_block3_precision.contracts import EvidenceRef
from sictra_block3_precision.decision import DecisionSignal
from sictra_block3_precision.person import ProfessionalFact
from sictra_block3_precision.pipeline import PrecisionInput
from sictra_block3_precision.relationship import RelationshipPolicy
from sictra_block3_precision.adaptive import AdaptiveEvidence, AdaptivePolicy, HardConstraints
from sictra_block3_precision.delivery import ChannelHistory, ChannelPolicy
from sictra_block3_precision.message import AuthorizedAsset, MessagePolicy
from sictra_block3_precision.precision_context import CeilingPolicy, PersonaStatePolicy
from sictra_block3_precision.relevance import RelevancePolicy
from sictra_block1.operator_pipeline import ingest_eurostat_workbook, initialize_operator_pipeline
from test_block1_eurostat_maritime_mapper import workbook
from sictra_block4_orchestrator.execution_receipt import sign_receipt
from sictra_block4_orchestrator.producer_adapters import (
    AdaptivePlanningPolicyBundle, Block1DossierPackageAdapter, Block2RuntimeAdapter, Block3RuntimeAdapter,
    SupervisedFederatedRunner,
)
from sictra_block4_orchestrator.runtime import FederatedContractError, FederatedOrchestratorStore, build_controlled_block1_package

NOW_DT = datetime(2026, 9, 13, 12, tzinfo=timezone.utc)
NOW = int(NOW_DT.timestamp())
PACKAGE_KEY = b"package-integrity-key-for-adapters"
B2_KEY = b"block2-execution-receipt-key-0001"
B3_KEY = b"block3-execution-receipt-key-0001"


def evidence(identity):
    root = "root:" + identity
    return EvidenceRef("evidence:" + identity, "LOCAL_TEST:" + identity, root, NOW,
                       "CURRENT", "VERIFIED", "B", (root,))


def precision_request(case_id, *, facts=True):
    signals = tuple(ContextSignal("context:" + scope.lower(), case_id, "account:1", scope,
        "claim:" + scope.lower(), scope + " supplied context", "FACT", 1, (scope.lower(),),
        NOW, NOW + 300, evidence("context:" + scope.lower()))
        for scope in ("GLOBAL", "INDUSTRY", "ACCOUNT", "ROLE", "MOMENT"))
    professional = (ProfessionalFact("fact:title", "person:1", "title", "Operations Director",
        "FACT", evidence("person")),) if facts else ()
    return PrecisionInput("person:1", case_id, "account:1", professional, (), (), signals,
        (DecisionSignal("decision:driver", "person:1", case_id, "DRIVER", "Control", 1,
                        "HYPOTHESIS", "GOVERNED_RULE", "rule:control", evidence("decision")),),
        RelationshipPolicy("relationship:1", "authority:relationship", 300))


def adaptive_bundle(parent_fingerprint):
    asset_evidence = EvidenceRef("evidence:block2-asset", "BLOCK2_ASSET_REGISTRY",
        parent_fingerprint, NOW, "CURRENT", "VERIFIED", "A", (parent_fingerprint,))
    return AdaptivePlanningPolicyBundle(
        "policy-bundle-v1", PersonaStatePolicy("persona:1", "authority:persona"),
        CeilingPolicy("ceiling:1", "authority:ceiling"),
        RelevancePolicy("relevance:1", "authority:relevance"),
        AdaptivePolicy("adaptive:1", "authority:adaptive"),
        AdaptiveEvidence("adaptive-evidence:1", 3, 10, 2, True, True),
        HardConstraints(True, True, True, True, True, True),
        MessagePolicy("message:1", "authority:message"),
        (AuthorizedAsset("asset:1", "BLOCK2", "v1", "NEWSLETTER", ("claim:global",),
            5, "authority:block2-assets", asset_evidence),),
        ChannelPolicy("channel:1", "authority:channel", ("EMAIL",), 3600, 86400, 3, 2),
        ChannelHistory("history:1", "person:1", "EMAIL", None, 0, NOW - 10, evidence("history")),
        "EMAIL",
    )


def resign_package(package, **changes):
    result = {**package, **changes}
    result.pop("signature", None)
    body = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    result["signature"] = hmac.new(PACKAGE_KEY, body, "sha256").hexdigest()
    return result


class ProducerAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = FederatedOrchestratorStore(Path(self.temp.name) / "journal.sqlite", integrity_key=PACKAGE_KEY,
            producer_keys={"BLOCK2": B2_KEY, "BLOCK3": B3_KEY})
        self.package = build_controlled_block1_package(integrity_key=PACKAGE_KEY, now=NOW_DT,
            certainty="VERIFIED", expires_at=NOW_DT + timedelta(hours=1))
        self.store.ingest(self.package, now=NOW_DT)
        self.block2 = Block2RuntimeAdapter(package_key=PACKAGE_KEY, receipt_key=B2_KEY)
        self.block3 = Block3RuntimeAdapter(receipt_key=B3_KEY)
        self.runner = SupervisedFederatedRunner(store=self.store, block2=self.block2, block3=self.block3)

    def tearDown(self): self.temp.cleanup()

    def test_real_block2_and_block3_runtimes_reach_only_human_gate(self):
        b2 = self.block2.execute(self.package, now=NOW_DT)
        self.assertEqual("COMPLETED", b2.disposition)
        self.assertEqual(tuple(f"E0{number}" for number in range(1, 9)), b2.executed_components)
        self.assertEqual("BLOCK2_CANDIDATE", self.store.record_execution(b2, now=NOW_DT).state)
        b3 = self.block3.execute(case_id=self.package["case_id"], run_id=self.package["run_id"],
            parent_fingerprint=b2.fingerprint, request=precision_request(self.package["case_id"]), now=NOW)
        self.assertIn(b3.disposition, {"ACCEPTED", "PARTIAL"})
        self.assertIn("M02", b3.executed_components)
        self.assertEqual("BLOCK3_GOVERNED", self.store.record_execution(b3, now=NOW_DT).state)
        final = self.runner.execute(self.package,
            precision_request=precision_request(self.package["case_id"]),
            adaptive_planning=adaptive_bundle(b2.fingerprint), now=NOW_DT)
        self.assertEqual("HUMAN_REVIEW_REQUIRED", final.state)
        events = [event["event_type"] for event in self.store.audit_events(final.case_id)]
        self.assertEqual(["INGESTED", "BLOCK2_RUNTIME_EXECUTED", "BLOCK3_RUNTIME_EXECUTED", "HUMAN_GATE_REACHED"], events)

    def test_supervised_runner_executes_end_to_end_and_recovers_from_block2_checkpoint(self):
        second_package = build_controlled_block1_package(integrity_key=PACKAGE_KEY, case_id="CASE-RUNNER-002",
            run_id="RUN-RUNNER-002", now=NOW_DT, certainty="VERIFIED", expires_at=NOW_DT + timedelta(hours=1))
        second_b2 = self.block2.execute(second_package, now=NOW_DT)
        final = self.runner.execute(second_package,
            precision_request=precision_request(second_package["case_id"]),
            adaptive_planning=adaptive_bundle(second_b2.fingerprint), now=NOW_DT)
        self.assertEqual("HUMAN_REVIEW_REQUIRED", final.state)
        b3 = self.store.execution_receipts(second_package["case_id"])[-1]
        self.assertEqual("SEND_CANDIDATE", b3.disposition)
        self.assertTrue({"M06", "M07"}.issubset(b3.executed_components))
        self.assertNotIn("M08", b3.executed_components)

        checkpoint_package = build_controlled_block1_package(integrity_key=PACKAGE_KEY, case_id="CASE-RECOVER-003",
            run_id="RUN-RECOVER-003", now=NOW_DT, certainty="VERIFIED", expires_at=NOW_DT + timedelta(hours=1))
        self.store.ingest(checkpoint_package, now=NOW_DT)
        b2 = self.block2.execute(checkpoint_package, now=NOW_DT)
        self.assertEqual("BLOCK2_CANDIDATE", self.store.record_execution(b2, now=NOW_DT).state)
        reopened = FederatedOrchestratorStore(Path(self.temp.name) / "journal.sqlite", integrity_key=PACKAGE_KEY,
            producer_keys={"BLOCK2": B2_KEY, "BLOCK3": B3_KEY})
        resumed = SupervisedFederatedRunner(store=reopened, block2=self.block2, block3=self.block3).execute(
            checkpoint_package, precision_request=precision_request(checkpoint_package["case_id"]),
            adaptive_planning=adaptive_bundle(b2.fingerprint), now=NOW_DT)
        self.assertEqual("HUMAN_REVIEW_REQUIRED", resumed.state)
        self.assertEqual(4, len(reopened.audit_events(checkpoint_package["case_id"])))

    def test_blocked_precision_runtime_returns_upstream_and_stops(self):
        b2 = self.block2.execute(self.package, now=NOW_DT)
        self.store.record_execution(b2, now=NOW_DT)
        b3 = self.block3.execute(case_id=self.package["case_id"], run_id=self.package["run_id"],
            parent_fingerprint=b2.fingerprint, request=precision_request(self.package["case_id"], facts=False), now=NOW)
        self.assertEqual("RETURN_UPSTREAM", b3.disposition)
        self.assertEqual("RETURN_UPSTREAM", self.store.record_execution(b3, now=NOW_DT).state)
        self.assertNotIn("HUMAN_GATE_REACHED", [e["event_type"] for e in self.store.audit_events(self.package["case_id"])])

    def test_tamper_wrong_parent_cross_case_and_replay_are_bounded(self):
        b2 = self.block2.execute(self.package, now=NOW_DT)
        with self.assertRaisesRegex(FederatedContractError, "SIGNATURE"):
            self.store.record_execution(replace(b2, output_fingerprint="0"*64), now=NOW_DT)
        forged_parent = sign_receipt(replace(b2, signature="", parent_fingerprint="f"*64,
            execution_id="B2-FORGED-PARENT"), B2_KEY)
        with self.assertRaisesRegex(FederatedContractError, "PARENT_MISMATCH"):
            self.store.record_execution(forged_parent, now=NOW_DT)
        first = self.store.record_execution(b2, now=NOW_DT)
        self.assertEqual(first, self.store.record_execution(b2, now=NOW_DT))
        with self.assertRaisesRegex(FederatedContractError, "PRECISION_CASE_IDENTITY_MISMATCH"):
            self.block3.execute(case_id=self.package["case_id"], run_id=self.package["run_id"],
                parent_fingerprint=b2.fingerprint, request=precision_request("OTHER"), now=NOW)

    def test_key_registry_time_and_component_boundaries_are_enforced(self):
        unconfigured = FederatedOrchestratorStore(Path(self.temp.name) / "unconfigured.sqlite",
            integrity_key=PACKAGE_KEY)
        unconfigured.ingest(self.package, now=NOW_DT)
        b2 = self.block2.execute(self.package, now=NOW_DT)
        with self.assertRaisesRegex(FederatedContractError, "KEYS_NOT_CONFIGURED"):
            unconfigured.record_execution(b2, now=NOW_DT)

        wrong_registry = FederatedOrchestratorStore(Path(self.temp.name) / "wrong.sqlite",
            integrity_key=PACKAGE_KEY,
            producer_keys={"BLOCK2": b"wrong-block2-execution-key-000000", "BLOCK3": B3_KEY})
        wrong_registry.ingest(self.package, now=NOW_DT)
        with self.assertRaisesRegex(FederatedContractError, "SIGNATURE"):
            wrong_registry.record_execution(b2, now=NOW_DT)

        old = sign_receipt(replace(b2, signature="", created_at=(NOW_DT - timedelta(seconds=1)).isoformat(),
            execution_id="B2-PREDATED"), B2_KEY)
        with self.assertRaisesRegex(FederatedContractError, "PREDATES_PACKAGE"):
            self.store.record_execution(old, now=NOW_DT)

        incomplete = sign_receipt(replace(b2, signature="", executed_components=("E01",),
            execution_id="B2-INCOMPLETE"), B2_KEY)
        self.assertEqual("RETURN_UPSTREAM", self.store.record_execution(incomplete, now=NOW_DT).state)

    def test_block3_without_decision_cannot_claim_governed_state(self):
        b2 = self.block2.execute(self.package, now=NOW_DT)
        self.store.record_execution(b2, now=NOW_DT)
        b3 = self.block3.execute(case_id=self.package["case_id"], run_id=self.package["run_id"],
            parent_fingerprint=b2.fingerprint, request=precision_request(self.package["case_id"]), now=NOW)
        no_decision = sign_receipt(replace(b3, signature="", execution_id="B3-NO-DECISION",
            executed_components=("M01", "M03", "M04", "M05"),
            payload={**b3.payload, "decision_present": False}), B3_KEY)
        self.assertEqual("RETURN_UPSTREAM", self.store.record_execution(no_decision, now=NOW_DT).state)

    def test_adaptive_path_rejects_asset_not_bound_to_block2_receipt(self):
        b2 = self.block2.execute(self.package, now=NOW_DT)
        self.store.record_execution(b2, now=NOW_DT)
        with self.assertRaisesRegex(FederatedContractError, "ASSET_RECEIPT_BINDING_MISSING"):
            self.block3.execute(case_id=self.package["case_id"], run_id=self.package["run_id"],
                parent_fingerprint=b2.fingerprint, request=precision_request(self.package["case_id"]),
                planning=adaptive_bundle("f" * 64), now=NOW)

    def test_real_block1_dossier_exports_as_current_signed_package_and_tamper_fails(self):
        pipeline = Path(self.temp.name) / "block1-pipeline"
        initialize_operator_pipeline(pipeline, clock=lambda: NOW)
        baseline = Path(self.temp.name) / "baseline.xlsx"
        baseline.write_bytes(workbook())
        changed = Path(self.temp.name) / "changed.xlsx"
        changed.write_bytes(workbook(last_updated="07/09/2026 06:14",
            rows=(("BE", "Belgium", "14", None, "15"),)))
        ingest_eurostat_workbook(pipeline, baseline, clock=lambda: NOW)
        result = ingest_eurostat_workbook(pipeline, changed, clock=lambda: NOW)
        dossier_id = result["dossier"]["dossier_id"]
        adapter = Block1DossierPackageAdapter(pipeline=pipeline, package_key=PACKAGE_KEY)
        package = adapter.export(dossier_id, now=NOW_DT)
        self.assertEqual(package, adapter.export(dossier_id, now=NOW_DT))
        self.assertEqual("UNCONFIRMED", package["certainty"])
        self.assertEqual("REVIEW_REQUIRED", package["disposition"])
        self.assertIn("NO_INTERPRETATION_ADDED", package["payload"]["limitations"])
        self.assertEqual("BLOCK1_ATTESTED", self.store.ingest(package, now=NOW_DT).state)
        with self.assertRaisesRegex(FederatedContractError, "EVIDENCE_NOT_CURRENT"):
            adapter.export(dossier_id, now=NOW_DT + timedelta(seconds=86_401))

        dossier_store = pipeline / "dossiers.json"
        dossier_store.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(FederatedContractError, "PIPELINE_INTEGRITY_ERROR"):
            adapter.export(dossier_id, now=NOW_DT)

    def test_stale_contradicted_or_expired_package_never_invokes_block2(self):
        for name, changes in (("stale", {"currentness": "STALE"}), ("contradicted", {"certainty": "CONTRADICTED"})):
            package = resign_package(build_controlled_block1_package(integrity_key=PACKAGE_KEY,
                case_id=name, now=NOW_DT, expires_at=NOW_DT + timedelta(hours=1)), **changes)
            with self.assertRaisesRegex(FederatedContractError, "NOT_EXECUTABLE"):
                self.block2.execute(package, now=NOW_DT)
        expired = build_controlled_block1_package(integrity_key=PACKAGE_KEY, case_id="expired",
            now=NOW_DT, expires_at=NOW_DT + timedelta(seconds=1), certainty="VERIFIED")
        with self.assertRaisesRegex(FederatedContractError, "NOT_EXECUTABLE"):
            self.block2.execute(expired, now=NOW_DT + timedelta(seconds=2))


if __name__ == "__main__": unittest.main()
