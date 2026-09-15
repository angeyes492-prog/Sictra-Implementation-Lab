from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from sictra_block1.operator_pipeline import ingest_eurostat_workbook, initialize_operator_pipeline
from sictra_block3_precision.adaptive import AdaptiveEvidence, AdaptivePolicy, HardConstraints
from sictra_block3_precision.context import ContextSignal
from sictra_block3_precision.contracts import EvidenceRef
from sictra_block3_precision.decision import DecisionSignal
from sictra_block3_precision.delivery import ChannelHistory, ChannelPolicy
from sictra_block3_precision.message import AuthorizedAsset, MessagePolicy
from sictra_block3_precision.person import ProfessionalFact
from sictra_block3_precision.pipeline import PrecisionInput
from sictra_block3_precision.precision_context import CeilingPolicy, PersonaStatePolicy
from sictra_block3_precision.relationship import RelationshipPolicy
from sictra_block3_precision.relevance import RelevancePolicy
from sictra_block4_orchestrator.autonomy import AutonomousCasePlan, SupervisedAutonomyWorker
from sictra_block4_orchestrator.producer_adapters import (
    AdaptivePlanningPolicyBundle, Block1DossierPackageAdapter, Block2RuntimeAdapter,
    Block3RuntimeAdapter, SupervisedFederatedRunner,
)
from sictra_block4_orchestrator.runtime import FederatedOrchestratorStore
from test_block1_eurostat_maritime_mapper import workbook


NOW_DT = datetime(2026, 9, 13, 12, tzinfo=timezone.utc)
NOW = int(NOW_DT.timestamp())
PACKAGE_KEY = b"autonomy-package-integrity-key-0001"
B2_KEY = b"autonomy-block2-receipt-key-0001"
B3_KEY = b"autonomy-block3-receipt-key-0001"


def evidence(identity, root):
    return EvidenceRef("evidence:" + identity, "LOCAL_PLAN:" + identity, root, NOW,
                       "CURRENT", "VERIFIED", "B", (root,))


class AutonomyWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.pipeline = self.root / "pipeline"
        initialize_operator_pipeline(self.pipeline, clock=lambda: NOW)
        baseline = self.root / "baseline.xlsx"; baseline.write_bytes(workbook())
        changed = self.root / "changed.xlsx"
        changed.write_bytes(workbook(last_updated="07/09/2026 06:14",
                                     rows=(("BE", "Belgium", "14", None, "15"),)))
        ingest_eurostat_workbook(self.pipeline, baseline, clock=lambda: NOW)
        self.dossier_id = ingest_eurostat_workbook(self.pipeline, changed, clock=lambda: NOW)["dossier"]["dossier_id"]
        self.store = FederatedOrchestratorStore(self.root / "journal.sqlite", integrity_key=PACKAGE_KEY,
                                                producer_keys={"BLOCK2": B2_KEY, "BLOCK3": B3_KEY})
        self.adapter = Block1DossierPackageAdapter(pipeline=self.pipeline, package_key=PACKAGE_KEY)
        self.block2 = Block2RuntimeAdapter(package_key=PACKAGE_KEY, receipt_key=B2_KEY)
        self.block3 = Block3RuntimeAdapter(receipt_key=B3_KEY)
        self.runner = SupervisedFederatedRunner(store=self.store, block2=self.block2, block3=self.block3)

    def tearDown(self):
        self.temp.cleanup()

    def _configured_plan(self, package, now):
        case_id = package["case_id"]
        root = "profile:controlled-local-target"
        signals = tuple(ContextSignal(
            "signal:" + scope.lower(), case_id, "account:controlled", scope,
            "claim:" + scope.lower(), scope + " context supplied by the configured local plan",
            "FACT", 1, (scope.lower(),), now, now + 300, evidence(scope.lower(), root),
        ) for scope in ("GLOBAL", "INDUSTRY", "ACCOUNT", "ROLE", "MOMENT"))
        request = PrecisionInput(
            "person:controlled", case_id, "account:controlled",
            (ProfessionalFact("fact:title", "person:controlled", "title", "Operations Director",
                              "FACT", evidence("title", root)),),
            (), (), signals,
            (DecisionSignal("decision:control", "person:controlled", case_id, "DRIVER", "Control", 1,
                            "HYPOTHESIS", "GOVERNED_RULE", "rule:control", evidence("decision", root)),),
            RelationshipPolicy("relationship:controlled", "authority:relationship", 300),
        )
        def planning(parent_fingerprint):
            asset_evidence = EvidenceRef("evidence:block2-asset", "BLOCK2_ASSET_REGISTRY", parent_fingerprint,
                NOW, "CURRENT", "VERIFIED", "A", (parent_fingerprint,))
            return AdaptivePlanningPolicyBundle(
                "policy-bundle-v1", PersonaStatePolicy("persona:1", "authority:persona"),
                CeilingPolicy("ceiling:1", "authority:ceiling"), RelevancePolicy("relevance:1", "authority:relevance"),
                AdaptivePolicy("adaptive:1", "authority:adaptive"), AdaptiveEvidence("adaptive-evidence:1", 3, 10, 2, True, True),
                HardConstraints(True, True, True, True, True, True), MessagePolicy("message:1", "authority:message"),
                (AuthorizedAsset("asset:1", "BLOCK2", "v1", "NEWSLETTER", ("claim:global",), 5,
                                 "authority:block2-assets", asset_evidence),),
                ChannelPolicy("channel:1", "authority:channel", ("EMAIL",), 3600, 86400, 3, 2),
                ChannelHistory("history:1", "person:controlled", "EMAIL", None, 0, NOW - 10, evidence("history", root)),
                "EMAIL",
            )
        return AutonomousCasePlan(request, planning)

    def test_durable_dossier_advances_without_manual_block_handoffs_and_replays_safely(self):
        worker = SupervisedAutonomyWorker(pipeline=self.pipeline, dossier_adapter=self.adapter,
            runner=self.runner, resolve_plan=self._configured_plan, clock=lambda: NOW_DT)
        first = worker.run_once()
        self.assertEqual(1, len(first))
        self.assertEqual("HUMAN_REVIEW_REQUIRED", first[0].state)
        events = self.store.audit_events(first[0].case_id)
        self.assertEqual(["INGESTED", "BLOCK2_RUNTIME_EXECUTED", "BLOCK3_RUNTIME_EXECUTED", "HUMAN_GATE_REACHED"],
                         [event["event_type"] for event in events])
        replay = worker.watch(cycles=2, interval_seconds=1, sleep=lambda _: None)
        self.assertEqual(["HUMAN_REVIEW_REQUIRED", "HUMAN_REVIEW_REQUIRED"], [item.state for item in replay])
        self.assertEqual(4, len(self.store.audit_events(first[0].case_id)))

    def test_missing_mapping_records_return_upstream_without_invoking_downstream_blocks(self):
        worker = SupervisedAutonomyWorker(pipeline=self.pipeline, dossier_adapter=self.adapter,
            runner=self.runner, resolve_plan=lambda _package, _now: None, clock=lambda: NOW_DT)
        outcome = worker.run_once()[0]
        self.assertEqual("WAITING_FOR_PLAN", outcome.state)
        self.assertEqual("PRECISION_PLAN_NOT_CONFIGURED", outcome.reason)
        self.assertEqual(["INGESTED"],
                         [event["event_type"] for event in self.store.audit_events(outcome.case_id)])
        worker.resolve_plan = self._configured_plan
        resumed = worker.run_once()[0]
        self.assertEqual("HUMAN_REVIEW_REQUIRED", resumed.state)
        self.assertEqual(4, len(self.store.audit_events(outcome.case_id)))


if __name__ == "__main__":
    unittest.main()
