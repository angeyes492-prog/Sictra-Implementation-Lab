from dataclasses import replace
import unittest

from sictra_block3_precision.account_context import AccountContextAdmissionPolicy, AccountContextIngress
from sictra_block3_precision.account_knowledge import AccountKnowledgeDossier, WebObservation
from sictra_block3_precision.account_memory import AccountKnowledgeStore
from sictra_block3_precision.account_research import AccountResearchReceipt, ResearchReceiptLedger
from sictra_block3_precision.contracts import EvidenceRef, PrecisionContractViolation
from sictra_block3_precision.context import ContextSignal
from sictra_block3_precision.decision_catalog import DecisionSignalCatalogPolicy, DecisionSignalRule, GovernedDecisionSignalCatalog
from sictra_block3_precision.person import ProfessionalFact
from sictra_block3_precision.pipeline import PrecisionFoundationPipeline, PrecisionInput
from sictra_block3_precision.relationship import RelationshipPolicy


NOW = 2_000_000_000
KEY = b"account-context-ingress-test-key-32bytes"


def dossier(*, quarantined=False):
    evidence = EvidenceRef(
        evidence_id="official-observation:1", source_identity="OFFICIAL_WEBSITE:https://example.test/operations",
        root_provenance="official-page:example.test:operations", observed_at=NOW,
        temporal_state="CURRENT", epistemic_state="UNCONFIRMED", confidence="C",
        provenance_refs=("official-page:example.test:operations",),
    )
    observation = WebObservation(
        observation_id="web-observation:1", tenant_id="tenant-a", account_id="account-a",
        source_url="https://example.test/operations", page_kind="SERVICES", label="Operations",
        excerpt="The company describes its supply-chain operations.", tags=("operations", "supply-chain"),
        captured_at=NOW, expires_at=NOW + 100, source_content_hash="content-hash", evidence=evidence,
        quarantined=quarantined, restrictions=("OFFICIAL_SITE_DECLARATION", "NO_FACT_PROMOTION"),
    )
    return AccountKnowledgeDossier(
        dossier_id="dossier:account-a:1", tenant_id="tenant-a", account_id="account-a",
        official_url="https://example.test/", policy_id="website-policy:1", captured_at=NOW,
        expires_at=NOW + 100, observations=(observation,),
        quarantined_observation_ids=(observation.observation_id,) if quarantined else (), skipped_urls=(),
        restrictions=("SHADOW_ENRICHMENT_ONLY", "NO_FACT_PROMOTION"),
    )


def receipt_for(item):
    return AccountResearchReceipt(
        receipt_id="receipt:account-a:1", tenant_id="tenant-a", account_id="account-a",
        approval_id="approval:1", import_id="import:1", dossier_id=item.dossier_id,
        dossier_fingerprint=item.output_fingerprint, policy_id="research-policy:1", captured_at=NOW,
        persisted_at=NOW, expires_at=NOW + 100, status="SHADOW_COMPLETED",
        restrictions=("SHADOW_RESEARCH_ONLY", "NO_FACT_PROMOTION", "NO_DELIVERY"),
    )


class AccountContextIngressTests(unittest.TestCase):
    def setUp(self):
        self.memory = AccountKnowledgeStore(integrity_key=KEY)
        self.ledger = ResearchReceiptLedger(integrity_key=KEY)
        self.policy = AccountContextAdmissionPolicy("account-context-policy:1", "authority:account-context")
        self.ingress = AccountContextIngress(
            policy=self.policy, knowledge_store=self.memory, receipt_ledger=self.ledger, attestation_key=KEY,
        )
        self.dossier = dossier()
        self.receipt = receipt_for(self.dossier)

    def tearDown(self):
        self.memory.close()
        self.ledger.close()

    def _persist(self):
        self.memory.append_dossier(self.dossier)
        self.ledger.append(self.receipt)

    def test_durable_receipt_and_dossier_admit_only_account_hypotheses(self):
        self._persist()
        result = self.ingress.admit(receipt=self.receipt, dossier=self.dossier, insight_id="insight:1", now=NOW)
        self.assertEqual("PARTIAL", result.assessment.disposition)
        self.assertEqual("HYPOTHESIS", result.admission.context_signals[0].kind)
        self.assertEqual("ACCOUNT", result.admission.context_signals[0].scope)
        self.assertIn("NO_FACT_PROMOTION", result.admission.restrictions)

    def test_absent_or_substituted_durable_lineage_is_rejected(self):
        self.ledger.append(self.receipt)
        with self.assertRaises(PrecisionContractViolation):
            self.ingress.admit(receipt=self.receipt, dossier=self.dossier, insight_id="insight:1", now=NOW)
        self.memory.append_dossier(self.dossier)
        with self.assertRaises(PrecisionContractViolation):
            self.ingress.admit(receipt=replace(self.receipt, receipt_id="receipt:substituted"), dossier=self.dossier, insight_id="insight:1", now=NOW)

    def test_expiry_and_cross_account_substitution_cannot_enter_m05(self):
        self._persist()
        with self.assertRaises(PrecisionContractViolation):
            self.ingress.admit(receipt=replace(self.receipt, expires_at=NOW - 1), dossier=self.dossier, insight_id="insight:1", now=NOW)
        foreign = replace(
            self.dossier, account_id="account-b",
            observations=(replace(self.dossier.observations[0], account_id="account-b"),),
        )
        with self.assertRaises(PrecisionContractViolation):
            self.ingress.admit(receipt=self.receipt, dossier=foreign, insight_id="insight:1", now=NOW)

    def test_quarantined_observations_never_create_account_context(self):
        blocked_dossier = dossier(quarantined=True)
        blocked_receipt = receipt_for(blocked_dossier)
        self.memory.append_dossier(blocked_dossier)
        self.ledger.append(blocked_receipt)
        result = self.ingress.admit(receipt=blocked_receipt, dossier=blocked_dossier, insight_id="insight:1", now=NOW)
        self.assertEqual("RETURN_UPSTREAM", result.assessment.disposition)
        self.assertIsNone(result.admission)


class GovernedDecisionSignalCatalogTests(unittest.TestCase):
    def setUp(self):
        self.memory = AccountKnowledgeStore(integrity_key=KEY)
        self.ledger = ResearchReceiptLedger(integrity_key=KEY)
        item = dossier()
        record = receipt_for(item)
        self.memory.append_dossier(item)
        self.ledger.append(record)
        self.admission = AccountContextIngress(
            policy=AccountContextAdmissionPolicy("account-context-policy:1", "authority:account-context"),
            knowledge_store=self.memory, receipt_ledger=self.ledger, attestation_key=KEY,
        ).admit(receipt=record, dossier=item, insight_id="insight:1", now=NOW).admission

    def catalog(self, rule):
        return GovernedDecisionSignalCatalog(
            policy=DecisionSignalCatalogPolicy(
                "decision-catalog:1", "authority:decision-catalog", (rule,),
                accepted_admission_policy_ids=("account-context-policy:1",),
            ),
            admission_keys={"LOCAL_ACCOUNT_CONTEXT_INGRESS": KEY},
        )

    def tearDown(self):
        self.memory.close()
        self.ledger.close()

    def test_explicit_tag_rule_emits_a_hypothesis_not_personal_preference(self):
        catalog = self.catalog(DecisionSignalRule("operations-control", "DRIVER", "Control", ("operations",)))
        result = catalog.derive(person_id="functional-mailbox:customer-service", admission=self.admission, now=NOW)
        self.assertEqual("PARTIAL", result.assessment.disposition)
        self.assertEqual("GOVERNED_RULE", result.signals[0].source_engine)
        self.assertEqual("HYPOTHESIS", result.signals[0].basis_kind)
        self.assertIn("RULE_MATCH_IS_NOT_PERSONAL_PREFERENCE", result.restrictions)

    def test_no_matching_rule_returns_upstream_instead_of_inventing_a_driver(self):
        catalog = self.catalog(DecisionSignalRule("unmatched", "DRIVER", "Cost", ("finance",)))
        result = catalog.derive(person_id="person:1", admission=self.admission, now=NOW)
        self.assertEqual("RETURN_UPSTREAM", result.assessment.disposition)
        self.assertEqual((), result.signals)

    def test_catalog_rejects_ambiguous_rule_container_and_non_string_tags(self):
        with self.assertRaises(PrecisionContractViolation):
            DecisionSignalRule("bad-tags", "DRIVER", "Cost", "finance")
        valid = DecisionSignalRule("valid", "DRIVER", "Cost", ("finance",))
        with self.assertRaises(PrecisionContractViolation):
            DecisionSignalCatalogPolicy(
                "decision-catalog:bad", "authority:decision-catalog", [valid],
                accepted_admission_policy_ids=("account-context-policy:1",),
            )

    def test_forged_or_policy_substituted_admission_cannot_create_m02_signal(self):
        catalog = self.catalog(DecisionSignalRule("operations-control", "DRIVER", "Control", ("operations",)))
        for forged in (
            replace(self.admission, attestation="0" * 64),
            replace(self.admission, policy_id="other-policy"),
            replace(self.admission, issuer_id="untrusted-ingress"),
        ):
            with self.assertRaises(PrecisionContractViolation):
                catalog.derive(person_id="person:1", admission=forged, now=NOW)

    def test_admitted_account_context_and_catalog_reach_m05_then_m02_as_hypotheses(self):
        catalog = self.catalog(DecisionSignalRule("operations-control", "DRIVER", "Control", ("operations",)))
        derived = catalog.derive(person_id="person:1", admission=self.admission, now=NOW)
        supplementary = []
        for scope in ("GLOBAL", "INDUSTRY", "ROLE", "MOMENT"):
            root = f"independent:{scope.lower()}"
            supplementary.append(ContextSignal(
                signal_id=f"context:{scope.lower()}", insight_id="insight:1", target_id="account-a",
                scope=scope, claim_key=f"claim:{scope.lower()}", statement=f"{scope} supplied context",
                kind="FACT", polarity=1, tags=(scope.lower(),), valid_from=NOW, valid_until=NOW + 10,
                evidence=EvidenceRef(f"evidence:{scope.lower()}", f"TEST:{scope}", root, NOW, "CURRENT", "VERIFIED", "B", (root,)),
            ))
        person_root = "independent:person"
        request = PrecisionInput(
            person_id="person:1", insight_id="insight:1", target_id="account-a",
            professional_facts=(ProfessionalFact("fact:title", "person:1", "title", "Operations Director", "FACT", EvidenceRef(
                "evidence:person", "TEST:PERSON", person_root, NOW, "CURRENT", "VERIFIED", "B", (person_root,),
            )),),
            behavior_events=(), relationship_events=(),
            context_signals=tuple(supplementary) + self.admission.context_signals,
            decision_signals=derived.signals,
            relationship_policy=RelationshipPolicy("relationship:1", "authority:relationship", 100),
        )
        result = PrecisionFoundationPipeline().execute(request, now=NOW)
        self.assertEqual("Control", result.decision.hypothesis.primary_driver)
        account_stage = next(stage for stage in result.context.relevance_map.stages if stage.scope == "ACCOUNT")
        self.assertEqual((), account_stage.fact_statements)
        self.assertIn("NO_DELIVERY_AUTHORITY", result.decision.hypothesis.restrictions)


if __name__ == "__main__":
    unittest.main()
