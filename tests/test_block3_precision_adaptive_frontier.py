from dataclasses import replace
import itertools
import unittest

from sictra_block3_precision.adaptive import (
    AdaptiveEvidence, AdaptiveFrontierController, AdaptivePolicy, HardConstraints,
)
from sictra_block3_precision.adaptive_pipeline import (
    AdaptivePlanningInput, PrecisionAdaptivePipeline,
)
from sictra_block3_precision.behavioral import BehaviorEvent
from sictra_block3_precision.context import ContextSignal
from sictra_block3_precision.contracts import EvidenceRef, PrecisionContractViolation
from sictra_block3_precision.decision import DecisionSignal
from sictra_block3_precision.delivery import (
    ChannelHistory, ChannelPolicy, TimingChannelIntelligenceEngine,
)
from sictra_block3_precision.learning import (
    DeliveryReceipt, LearningEngine, LearningPolicy, ObservedOutcome,
)
from sictra_block3_precision.message import (
    AuthorizedAsset, MessageIntelligenceEngine, MessagePolicy,
)
from sictra_block3_precision.person import ProfessionalFact
from sictra_block3_precision.pipeline import PrecisionFoundationPipeline, PrecisionInput
from sictra_block3_precision.precision_context import (
    CeilingPolicy, PersonaStatePolicy, PrecisionContextPackComposer,
)
from sictra_block3_precision.relationship import RelationshipEvent, RelationshipPolicy
from sictra_block3_precision.relevance import RelevanceGate, RelevancePolicy


NOW = 2_000_000_000
RELATIONSHIP_POLICY = RelationshipPolicy("relationship-policy", "authority:relationship", 86_400)
PERSONA_POLICY = PersonaStatePolicy("persona-policy", "authority:persona")
CEILING_POLICY = CeilingPolicy("ceiling-policy", "authority:ceiling")
RELEVANCE_POLICY = RelevancePolicy("relevance-policy", "authority:relevance")
ADAPTIVE_POLICY = AdaptivePolicy("adaptive-policy", "authority:adaptive")
MESSAGE_POLICY = MessagePolicy("message-policy", "authority:message")
CHANNEL_POLICY = ChannelPolicy(
    "channel-policy", "authority:channel", ("EMAIL",), 3_600, 86_400, 3, 2,
)
LEARNING_POLICY = LearningPolicy("learning-policy", "authority:learning", 86_400)
ALL_CONSTRAINTS = HardConstraints(True, True, True, True, True, True)
ADAPTIVE_EVIDENCE = AdaptiveEvidence("adaptive-evidence", 3, 10, 2, True, True)
ASSET = AuthorizedAsset(
    "asset-1", "BLOCK2", "v1", "NEWSLETTER", ("claim:global",), 5,
    "authority:block2-assets",
    EvidenceRef(
        "evidence:asset", "BLOCK2_ASSET_REGISTRY", "root:block2:asset", NOW,
        "CURRENT", "VERIFIED", "A", ("root:block2:asset",),
    ),
)


def evidence(identity, *, at=NOW, source=None, root=None, temporal="CURRENT", confidence="A"):
    root = root or f"root:{identity}"
    return EvidenceRef(
        evidence_id=f"evidence:{identity}",
        source_identity=source or f"source:{identity}",
        root_provenance=root,
        observed_at=at,
        temporal_state=temporal,
        epistemic_state="VERIFIED",
        confidence=confidence,
        provenance_refs=(root,),
    )


def fact(identity, field, value, *, kind="FACT"):
    return ProfessionalFact(
        f"fact:{identity}", "person-1", field, value, kind, evidence(identity),
    )


def behavior(identity="reply", *, event_type="REPLY", topic="disruption"):
    return BehaviorEvent(
        f"behavior:{identity}", "person-1", event_type, NOW,
        evidence(f"behavior:{identity}"), topic=topic, channel="EMAIL",
    )


def relationship(identity="talk", *, kind="BILATERAL_EXCHANGE"):
    return RelationshipEvent(
        f"relationship:{identity}", "person-1", kind, NOW,
        evidence(f"relationship:{identity}"),
    )


def context_signal(scope, *, kind="FACT", polarity=1, claim=None, tags=()):
    key = claim or scope.casefold()
    return ContextSignal(
        f"context:{scope}:{kind}:{polarity}:{key}", "insight-1", "account-1",
        scope, key, f"{scope} {kind} statement", kind, polarity,
        tuple(tags) or (scope.casefold(),), NOW - 10, NOW + 100_000,
        evidence(f"context:{scope}:{kind}:{polarity}:{key}"),
    )


def decision_signal(identity, dimension, value):
    return DecisionSignal(
        f"decision:{identity}", "person-1", "insight-1", dimension, value, 1,
        "HYPOTHESIS", "M05", f"basis:{identity}", evidence(f"decision:{identity}"),
    )


def foundation(
    *, scopes=("GLOBAL", "INDUSTRY", "ACCOUNT", "ROLE", "MOMENT"),
    functional=False, no_behavior=False, unsubscribe=False, opportunity=False,
):
    professional = [fact("title", "title", "VP Supply Chain"), fact("company", "company", "Example Importer")]
    if functional:
        professional.extend((
            fact("mailbox", "contact_kind", "FUNCTIONAL_MAILBOX"),
            fact("function", "contact_function", "CUSTOMER_SERVICE"),
        ))
    relationship_events = []
    if opportunity:
        relationship_events.append(relationship("opportunity", kind="OPPORTUNITY_ACTIVE"))
    elif not functional:
        relationship_events.append(relationship())
    if unsubscribe:
        relationship_events.append(relationship("unsubscribe", kind="UNSUBSCRIBE"))
    request = PrecisionInput(
        person_id="person-1",
        insight_id="insight-1",
        target_id="account-1",
        professional_facts=tuple(professional),
        behavior_events=() if no_behavior else (behavior(),),
        relationship_events=tuple(relationship_events),
        context_signals=tuple(
            context_signal(
                scope,
                tags=("risk", "disruption") if scope == "MOMENT" else (scope.casefold(),),
            )
            for scope in scopes
        ),
        decision_signals=(
            decision_signal("driver", "DRIVER", "Control"),
            decision_signal("horizon", "HORIZON", "Quarter"),
            decision_signal("proof", "EVIDENCE_PREFERENCE", "Benchmark"),
            decision_signal("frame", "FRAMING", "Resilience"),
        ),
        relationship_policy=RELATIONSHIP_POLICY,
    )
    return PrecisionFoundationPipeline().execute(request, now=NOW)


def pack_for(**changes):
    return PrecisionContextPackComposer().compose(
        foundation=foundation(**changes),
        person_id="person-1", insight_id="insight-1", target_id="account-1",
        now=NOW, policy_version="policy-bundle-v1",
        persona_policy=PERSONA_POLICY, ceiling_policy=CEILING_POLICY,
    )


def decisions_for(pack):
    relevance = RelevanceGate().evaluate(pack=pack, policy=RELEVANCE_POLICY, now=NOW)
    adaptive = AdaptiveFrontierController().decide(
        relevance=relevance.decision, constraints=ALL_CONSTRAINTS,
        evidence=ADAPTIVE_EVIDENCE, policy=ADAPTIVE_POLICY,
    )
    return relevance, adaptive


def strategy_for(pack):
    relevance, adaptive = decisions_for(pack)
    message = MessageIntelligenceEngine().formulate(
        pack=pack, relevance=relevance.decision, adaptive=adaptive.decision,
        assets=(ASSET,), policy=MESSAGE_POLICY,
    )
    return relevance, adaptive, message


def proposal_for(pack=None):
    pack = pack or pack_for()
    relevance, adaptive, message = strategy_for(pack)
    history = ChannelHistory(
        "history-1", "person-1", "EMAIL", None, 0, NOW - 10_000,
        evidence("history-1"),
    )
    delivery = TimingChannelIntelligenceEngine().propose(
        strategy=message.strategy, pack=pack, relevance=relevance.decision,
        adaptive=adaptive.decision, history=history, requested_channel="EMAIL",
        policy=CHANNEL_POLICY, now=NOW,
    )
    return pack, relevance, adaptive, message, delivery


class ContextPackAndSharedStateTests(unittest.TestCase):
    def test_context_pack_is_current_deterministic_and_bound(self):
        first = pack_for()
        second = pack_for()
        self.assertEqual(first.output_fingerprint, second.output_fingerprint)
        self.assertTrue(first.current_at(NOW))
        self.assertEqual("person-1", first.persona_state.person_id)

    def test_blocked_foundation_cannot_be_packed(self):
        blocked = foundation(scopes=("ACCOUNT",))
        with self.assertRaises(PrecisionContractViolation):
            PrecisionContextPackComposer().compose(
                foundation=blocked, person_id="person-1", insight_id="insight-1",
                target_id="account-1", now=NOW, policy_version="v1",
                persona_policy=PERSONA_POLICY, ceiling_policy=CEILING_POLICY,
            )

    def test_persona_state_is_reversible_projection_not_personality(self):
        pack = pack_for(opportunity=True)
        self.assertEqual("DECISION", pack.persona_state.state)
        self.assertIn("NOT_PERSONALITY", pack.persona_state.restrictions)

    def test_missing_moment_produces_unknown_persona_state(self):
        pack = pack_for(scopes=("GLOBAL", "INDUSTRY", "ACCOUNT", "ROLE"))
        self.assertEqual("UNKNOWN", pack.persona_state.state)

    def test_unsubscribe_caps_personalization_at_zero(self):
        pack = pack_for(unsubscribe=True)
        self.assertEqual(0, pack.ceiling.effective_level)

    def test_stricter_policy_never_increases_ceiling(self):
        base = pack_for()
        strict = PrecisionContextPackComposer().compose(
            foundation=foundation(), person_id="person-1", insight_id="insight-1",
            target_id="account-1", now=NOW, policy_version="strict",
            persona_policy=PERSONA_POLICY,
            ceiling_policy=CeilingPolicy("strict", "authority:strict", maximum_level=1),
        )
        self.assertLessEqual(strict.ceiling.effective_level, base.ceiling.effective_level)


class RelevanceGateTests(unittest.TestCase):
    def test_complete_chain_is_high_even_without_observed_interest(self):
        pack = pack_for(no_behavior=True)
        result = RelevanceGate().evaluate(pack=pack, policy=RELEVANCE_POLICY, now=NOW)
        self.assertEqual("HIGH", result.decision.level)
        observed = next(item for item in result.decision.dimensions if item.dimension == "OBSERVED_INTEREST")
        self.assertEqual("ABSENT", observed.state)

    def test_two_supported_core_dimensions_are_medium(self):
        pack = pack_for(scopes=("GLOBAL", "INDUSTRY", "ACCOUNT"))
        result = RelevanceGate().evaluate(pack=pack, policy=RELEVANCE_POLICY, now=NOW)
        self.assertEqual("MEDIUM", result.decision.level)
        self.assertLessEqual(result.decision.ceiling_cap, 2)

    def test_global_only_is_low_not_fabricated_relevance(self):
        pack = pack_for(scopes=("GLOBAL",))
        result = RelevanceGate().evaluate(pack=pack, policy=RELEVANCE_POLICY, now=NOW)
        self.assertEqual("LOW", result.decision.level)

    def test_expired_context_pack_returns_upstream(self):
        pack = pack_for()
        result = RelevanceGate().evaluate(
            pack=pack, policy=RELEVANCE_POLICY, now=pack.valid_until + 1,
        )
        self.assertEqual("RETURN_UPSTREAM", result.decision.level)

    def test_independent_relevance_oracle_exhausts_all_core_scope_combinations(self):
        base = pack_for()
        global_stage = next(stage for stage in base.context.stages if stage.scope == "GLOBAL")
        other_stages = {stage.scope: stage for stage in base.context.stages if stage.scope != "GLOBAL"}
        names = ("INDUSTRY", "ACCOUNT", "ROLE", "MOMENT")
        for bits in itertools.product((False, True), repeat=4):
            selected_names = {name for name, present in zip(names, bits) if present}
            context = replace(
                base.context,
                stages=(global_stage,) + tuple(other_stages[name] for name in names if name in selected_names),
                missing_scopes=tuple(name for name in names if name not in selected_names),
            )
            test_pack = replace(base, context=context)
            result = RelevanceGate().evaluate(pack=test_pack, policy=RELEVANCE_POLICY, now=NOW)
            count = len(selected_names)
            expected = "HIGH" if count == 4 else "MEDIUM" if count >= 2 else "LOW"
            self.assertEqual(expected, result.decision.level, bits)

    def test_correlated_roots_are_visible_not_counted_as_independent(self):
        base = pack_for()
        context = replace(
            base.context,
            stages=tuple(
                replace(stage, root_provenance_ids=("root:shared",), independent_root_count=1)
                for stage in base.context.stages
            ),
        )
        result = RelevanceGate().evaluate(
            pack=replace(base, context=context), policy=RELEVANCE_POLICY, now=NOW,
        )
        self.assertIn("CORRELATED_RELEVANCE_ROOTS_PRESERVED", result.decision.reasons)


class AdaptiveFrontierTests(unittest.TestCase):
    def test_hard_constraint_failure_forces_l0(self):
        relevance, _ = decisions_for(pack_for())
        result = AdaptiveFrontierController().decide(
            relevance=relevance.decision,
            constraints=HardConstraints(True, True, True, False, True, True),
            evidence=ADAPTIVE_EVIDENCE, policy=ADAPTIVE_POLICY,
        )
        self.assertEqual(0, result.decision.level)
        self.assertIn("AUDITABILITY", result.decision.failed_constraints)

    def test_marginal_benefit_must_exceed_sacrifice(self):
        relevance, _ = decisions_for(pack_for())
        result = AdaptiveFrontierController().decide(
            relevance=relevance.decision, constraints=ALL_CONSTRAINTS,
            evidence=AdaptiveEvidence("weak", 3, 4, 4, True, True),
            policy=ADAPTIVE_POLICY,
        )
        self.assertEqual(0, result.decision.level)

    def test_medium_relevance_caps_adaptation_at_l1(self):
        relevance, _ = decisions_for(pack_for(scopes=("GLOBAL", "INDUSTRY", "ACCOUNT")))
        result = AdaptiveFrontierController().decide(
            relevance=relevance.decision, constraints=ALL_CONSTRAINTS,
            evidence=ADAPTIVE_EVIDENCE, policy=ADAPTIVE_POLICY,
        )
        self.assertEqual(1, result.decision.level)

    def test_baseline_regression_triggers_l0(self):
        relevance, _ = decisions_for(pack_for())
        result = AdaptiveFrontierController().decide(
            relevance=relevance.decision, constraints=ALL_CONSTRAINTS,
            evidence=AdaptiveEvidence("regression", 3, 100, 1, True, False),
            policy=ADAPTIVE_POLICY,
        )
        self.assertEqual(0, result.decision.level)

    def test_independent_constraint_oracle_exhausts_boolean_matrix(self):
        relevance, _ = decisions_for(pack_for())
        for flags in itertools.product((False, True), repeat=6):
            constraints = HardConstraints(*flags)
            result = AdaptiveFrontierController().decide(
                relevance=relevance.decision, constraints=constraints,
                evidence=ADAPTIVE_EVIDENCE, policy=ADAPTIVE_POLICY,
            )
            expected = 3 if all(flags) else 0
            self.assertEqual(expected, result.decision.level, flags)


class MessageIntelligenceTests(unittest.TestCase):
    def test_builds_strategy_without_copy_or_delivery_authority(self):
        pack = pack_for()
        relevance, adaptive, message = strategy_for(pack)
        self.assertIsNotNone(message.strategy)
        self.assertLessEqual(message.strategy.applied_level, message.strategy.maximum_ceiling)
        self.assertIn("STRATEGY_NOT_FINAL_COPY", message.strategy.restrictions)
        self.assertIn("NO_DELIVERY_AUTHORITY", message.strategy.restrictions)

    def test_functional_mailbox_gets_forwardable_low_friction_strategy(self):
        pack = pack_for(functional=True)
        _, _, message = strategy_for(pack)
        self.assertEqual("INSTITUTIONALLY_FORWARDABLE", message.strategy.audience_route)
        self.assertEqual("LOW_FRICTION_INFORMATION", message.strategy.cta)

    def test_foreign_asset_owner_is_rejected(self):
        with self.assertRaises(PrecisionContractViolation):
            AuthorizedAsset(
                "foreign", "BLOCK3", "v1", "NEWSLETTER", ("claim",), 1,
                "authority:foreign", evidence("foreign"),
            )

    def test_missing_asset_returns_upstream(self):
        pack = pack_for()
        relevance, adaptive = decisions_for(pack)
        result = MessageIntelligenceEngine().formulate(
            pack=pack, relevance=relevance.decision, adaptive=adaptive.decision,
            assets=(), policy=MESSAGE_POLICY,
        )
        self.assertIsNone(result.strategy)
        self.assertEqual("RETURN_UPSTREAM", result.assessment.disposition)

    def test_stale_asset_authorization_returns_upstream(self):
        pack = pack_for()
        relevance, adaptive = decisions_for(pack)
        stale = replace(
            ASSET,
            asset_id="stale-asset",
            evidence=replace(ASSET.evidence, evidence_id="evidence:stale-asset", temporal_state="STALE"),
        )
        result = MessageIntelligenceEngine().formulate(
            pack=pack, relevance=relevance.decision, adaptive=adaptive.decision,
            assets=(stale,), policy=MESSAGE_POLICY,
        )
        self.assertIsNone(result.strategy)
        self.assertEqual("RETURN_UPSTREAM", result.assessment.disposition)

    def test_low_relevance_never_builds_message(self):
        pack = pack_for(scopes=("GLOBAL",))
        relevance, adaptive = decisions_for(pack)
        result = MessageIntelligenceEngine().formulate(
            pack=pack, relevance=relevance.decision, adaptive=adaptive.decision,
            assets=(ASSET,), policy=MESSAGE_POLICY,
        )
        self.assertIsNone(result.strategy)


class TimingChannelTests(unittest.TestCase):
    def test_send_candidate_is_only_a_proposal_with_executor_checks(self):
        *_, delivery = proposal_for()
        self.assertEqual("SEND_CANDIDATE", delivery.proposal.disposition)
        self.assertIn("CONSENT_CURRENT", delivery.proposal.required_executor_checks)
        self.assertIn("PROPOSAL_NOT_EXECUTION", delivery.proposal.restrictions)

    def test_unsubscribe_produces_do_not_send(self):
        pack = pack_for(unsubscribe=True)
        relevance, adaptive, message = strategy_for(pack)
        history = ChannelHistory("h", "person-1", "EMAIL", None, 0, NOW - 1, evidence("h"))
        result = TimingChannelIntelligenceEngine().propose(
            strategy=message.strategy, pack=pack, relevance=relevance.decision,
            adaptive=adaptive.decision, history=history, requested_channel="EMAIL",
            policy=CHANNEL_POLICY, now=NOW,
        )
        self.assertEqual("DO_NOT_SEND", result.proposal.disposition)

    def test_frequency_limit_produces_wait(self):
        pack = pack_for()
        relevance, adaptive, message = strategy_for(pack)
        history = ChannelHistory(
            "h", "person-1", "EMAIL", NOW - 10, 3, NOW - 100, evidence("h"),
        )
        result = TimingChannelIntelligenceEngine().propose(
            strategy=message.strategy, pack=pack, relevance=relevance.decision,
            adaptive=adaptive.decision, history=history, requested_channel="EMAIL",
            policy=CHANNEL_POLICY, now=NOW,
        )
        self.assertEqual("WAIT", result.proposal.disposition)
        self.assertEqual(0, result.proposal.contact_pressure)

    def test_unauthorized_channel_returns_upstream(self):
        pack = pack_for()
        relevance, adaptive, message = strategy_for(pack)
        history = ChannelHistory(
            "h", "person-1", "LINKEDIN", None, 0, NOW - 1, evidence("h"),
        )
        result = TimingChannelIntelligenceEngine().propose(
            strategy=message.strategy, pack=pack, relevance=relevance.decision,
            adaptive=adaptive.decision, history=history, requested_channel="LINKEDIN",
            policy=CHANNEL_POLICY, now=NOW,
        )
        self.assertEqual("RETURN_UPSTREAM", result.proposal.disposition)

    def test_medium_relevance_never_increases_pressure(self):
        pack = pack_for(scopes=("GLOBAL", "INDUSTRY", "ACCOUNT"))
        relevance, adaptive, message = strategy_for(pack)
        history = ChannelHistory("h", "person-1", "EMAIL", None, 0, NOW - 1, evidence("h"))
        result = TimingChannelIntelligenceEngine().propose(
            strategy=message.strategy, pack=pack, relevance=relevance.decision,
            adaptive=adaptive.decision, history=history, requested_channel="EMAIL",
            policy=CHANNEL_POLICY, now=NOW,
        )
        self.assertLessEqual(result.proposal.contact_pressure, 1)

    def test_stale_channel_history_returns_upstream(self):
        pack = pack_for()
        relevance, adaptive, message = strategy_for(pack)
        history = ChannelHistory(
            "stale", "person-1", "EMAIL", None, 0, NOW - 1,
            evidence("stale-history", temporal="STALE"),
        )
        result = TimingChannelIntelligenceEngine().propose(
            strategy=message.strategy, pack=pack, relevance=relevance.decision,
            adaptive=adaptive.decision, history=history, requested_channel="EMAIL",
            policy=CHANNEL_POLICY, now=NOW,
        )
        self.assertEqual("RETURN_UPSTREAM", result.proposal.disposition)


class LearningEngineTests(unittest.TestCase):
    def fixtures(self, *, receipt_disposition="EXECUTED", outcome_kind="ESCALATED", source="executor"):
        *_, message, delivery = proposal_for()
        receipt = DeliveryReceipt(
            "receipt-1", delivery.proposal.proposal_id, receipt_disposition, NOW + 10,
            "authority:executor", evidence("receipt", at=NOW + 10, source=source, root=f"root:{source}:receipt"),
        )
        outcome = ObservedOutcome(
            "outcome-1", receipt.receipt_id, outcome_kind, NOW + 20,
            evidence("outcome", at=NOW + 20, source=source, root=f"root:{source}:outcome"),
        )
        return message.strategy, delivery.proposal, receipt, outcome

    def test_no_receipt_means_no_learning(self):
        strategy, proposal, _, _ = self.fixtures()
        result = LearningEngine().learn(
            strategy=strategy, proposal=proposal, receipt=None, outcome=None,
            policy=LEARNING_POLICY, now=NOW + 20,
        )
        self.assertIsNone(result.next_best_test)

    def test_executor_rejection_is_not_recipient_behavior(self):
        strategy, proposal, receipt, outcome = self.fixtures(receipt_disposition="REJECTED")
        result = LearningEngine().learn(
            strategy=strategy, proposal=proposal, receipt=receipt, outcome=outcome,
            policy=LEARNING_POLICY, now=NOW + 20,
        )
        self.assertIsNone(result.next_best_test)
        self.assertIn("EXECUTOR_REJECTION_NOT_RECIPIENT_BEHAVIOR", result.assessment.reasons)

    def test_complete_chain_creates_candidate_not_rule(self):
        strategy, proposal, receipt, outcome = self.fixtures()
        result = LearningEngine().learn(
            strategy=strategy, proposal=proposal, receipt=receipt, outcome=outcome,
            policy=LEARNING_POLICY, now=NOW + 20,
        )
        self.assertIsNotNone(result.next_best_test)
        self.assertIn("CANDIDATE_NOT_ACCEPTED_RULE", result.next_best_test.restrictions)
        self.assertIn("FUTURE_VERSION_ONLY", result.next_best_test.restrictions)

    def test_no_response_is_not_rejection(self):
        strategy, proposal, receipt, outcome = self.fixtures(outcome_kind="NO_RESPONSE")
        result = LearningEngine().learn(
            strategy=strategy, proposal=proposal, receipt=receipt, outcome=outcome,
            policy=LEARNING_POLICY, now=NOW + 20,
        )
        self.assertIn("rejection and irrelevance remain unproven", result.next_best_test.inferences[0])

    def test_mismatched_outcome_chain_is_rejected(self):
        strategy, proposal, receipt, outcome = self.fixtures()
        with self.assertRaises(PrecisionContractViolation):
            LearningEngine().learn(
                strategy=strategy, proposal=proposal, receipt=receipt,
                outcome=replace(outcome, receipt_id="other"),
                policy=LEARNING_POLICY, now=NOW + 20,
            )

    def test_self_authored_m08_evidence_is_rejected(self):
        strategy, proposal, receipt, outcome = self.fixtures(source="M08:learner")
        with self.assertRaises(PrecisionContractViolation):
            LearningEngine().learn(
                strategy=strategy, proposal=proposal, receipt=receipt, outcome=outcome,
                policy=LEARNING_POLICY, now=NOW + 20,
            )

    def test_m08_hidden_in_root_provenance_is_rejected(self):
        strategy, proposal, receipt, outcome = self.fixtures()
        bad = EvidenceRef(
            "evidence:hidden-m08", "external-observer", "root:M08:derived", NOW + 20,
            "CURRENT", "VERIFIED", "A", ("root:M08:derived",),
        )
        with self.assertRaises(PrecisionContractViolation):
            LearningEngine().learn(
                strategy=strategy, proposal=proposal, receipt=receipt,
                outcome=replace(outcome, evidence=bad),
                policy=LEARNING_POLICY, now=NOW + 20,
            )

    def test_executed_receipt_against_wait_proposal_is_rejected(self):
        strategy, proposal, receipt, outcome = self.fixtures()
        waiting = replace(proposal, disposition="WAIT")
        receipt = replace(receipt, proposal_id=waiting.proposal_id)
        with self.assertRaises(PrecisionContractViolation):
            LearningEngine().learn(
                strategy=strategy, proposal=waiting, receipt=receipt, outcome=outcome,
                policy=LEARNING_POLICY, now=NOW + 20,
            )


class AdaptivePipelineTests(unittest.TestCase):
    def planning_input(self, *, foundation_result=None, scopes=None):
        foundation_result = foundation_result or foundation(scopes=scopes or ("GLOBAL", "INDUSTRY", "ACCOUNT", "ROLE", "MOMENT"))
        return AdaptivePlanningInput(
            foundation=foundation_result,
            person_id="person-1", insight_id="insight-1", target_id="account-1",
            policy_version="bundle-v1", persona_policy=PERSONA_POLICY,
            ceiling_policy=CEILING_POLICY, relevance_policy=RELEVANCE_POLICY,
            adaptive_policy=ADAPTIVE_POLICY, adaptive_evidence=ADAPTIVE_EVIDENCE,
            hard_constraints=ALL_CONSTRAINTS, message_policy=MESSAGE_POLICY,
            assets=(ASSET,), channel_policy=CHANNEL_POLICY,
            channel_history=ChannelHistory(
                "history", "person-1", "EMAIL", None, 0, NOW - 1, evidence("history"),
            ),
            requested_channel="EMAIL",
        )

    def test_pipeline_produces_send_candidate_without_effect(self):
        result = PrecisionAdaptivePipeline().plan(self.planning_input(), now=NOW)
        self.assertEqual("SEND_CANDIDATE", result.disposition)
        self.assertIn("PROPOSAL_NOT_EXECUTION", result.delivery.proposal.restrictions)

    def test_low_relevance_stops_before_m06(self):
        result = PrecisionAdaptivePipeline().plan(
            self.planning_input(scopes=("GLOBAL",)), now=NOW,
        )
        self.assertEqual("DO_NOT_SEND", result.disposition)
        self.assertIsNone(result.message)

    def test_blocked_foundation_stops_before_context_pack(self):
        result = PrecisionAdaptivePipeline().plan(
            self.planning_input(foundation_result=foundation(scopes=("ACCOUNT",))), now=NOW,
        )
        self.assertEqual("RETURN_UPSTREAM", result.disposition)
        self.assertIsNone(result.context_pack)


if __name__ == "__main__":
    unittest.main()
