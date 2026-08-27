import unittest

from sictra_block3_precision.behavioral import BehaviorEvent, BehavioralIntelligenceEngine
from sictra_block3_precision.context import ContextIntelligenceEngine, ContextSignal
from sictra_block3_precision.contracts import (
    EvidenceRef,
    PrecisionCapacityExceeded,
    PrecisionContractViolation,
    PrecisionIdentityCollision,
)
from sictra_block3_precision.decision import DecisionIntelligenceEngine, DecisionSignal
from sictra_block3_precision.person import PersonIntelligenceEngine, ProfessionalFact
from sictra_block3_precision.pipeline import PrecisionFoundationPipeline, PrecisionInput
from sictra_block3_precision.relationship import (
    RelationshipEvent,
    RelationshipIntelligenceEngine,
    RelationshipPolicy,
)


NOW = 10_000_000


def evidence(identity, *, at=NOW - 10, temporal="CURRENT", root=None,
             state="VERIFIED", confidence="B"):
    root = root or f"root:{identity}"
    return EvidenceRef(
        evidence_id=f"evidence:{identity}",
        source_identity=f"source:{identity}",
        root_provenance=root,
        observed_at=at,
        temporal_state=temporal,
        epistemic_state=state,
        confidence=confidence,
        provenance_refs=(root, f"record:{identity}"),
    )


def fact(identity, field, value, *, person="person-1", kind="FACT", **evidence_changes):
    return ProfessionalFact(
        fact_id=f"fact:{identity}", person_id=person, field=field, value=value,
        kind=kind, evidence=evidence(identity, **evidence_changes),
    )


def behavior(identity, event_type, *, person="person-1", topic="", format="",
             channel="", cta="", at=NOW - 10, **evidence_changes):
    return BehaviorEvent(
        event_id=f"behavior:{identity}", person_id=person, event_type=event_type,
        occurred_at=at, topic=topic, format=format, channel=channel, cta=cta,
        evidence=evidence(identity, at=at, **evidence_changes),
    )


def relationship_event(identity, kind, *, person="person-1", at=NOW - 10,
                       **evidence_changes):
    return RelationshipEvent(
        event_id=f"relationship:{identity}", person_id=person, kind=kind,
        occurred_at=at, evidence=evidence(identity, at=at, **evidence_changes),
    )


def context_signal(identity, scope, statement, *, insight="insight-1", target="account-1",
                   claim=None, kind="FACT", polarity=1, tags=(), at=NOW - 10,
                   valid_from=NOW - 100, valid_until=NOW + 100, **evidence_changes):
    return ContextSignal(
        signal_id=f"context:{identity}", insight_id=insight, target_id=target,
        scope=scope, claim_key=claim or f"claim:{identity}", statement=statement,
        kind=kind, polarity=polarity, tags=tuple(tags), valid_from=valid_from,
        valid_until=valid_until, evidence=evidence(identity, at=at, **evidence_changes),
    )


def decision_signal(identity, dimension, value, *, person="person-1", insight="insight-1",
                    polarity=1, basis_kind="HYPOTHESIS", source_engine="M05", **changes):
    return DecisionSignal(
        signal_id=f"decision:{identity}", person_id=person, insight_id=insight,
        dimension=dimension, value=value, polarity=polarity, basis_kind=basis_kind,
        source_engine=source_engine, basis_reference=f"basis:{identity}",
        evidence=evidence(identity, **changes),
    )


POLICY = RelationshipPolicy("policy-1", "authority:relationship-policy", 30 * 24 * 3600)


class EvidenceContractTests(unittest.TestCase):
    def test_provenance_must_begin_at_root(self):
        with self.assertRaises(PrecisionContractViolation):
            EvidenceRef("e", "s", "root", 1, "CURRENT", "VERIFIED", "A", ("other",))

    def test_future_observation_is_not_current_at_now(self):
        self.assertFalse(evidence("future", at=NOW + 1).current_at(NOW))


class PersonEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = PersonIntelligenceEngine()

    def test_builds_professional_profile_and_proximity(self):
        result = self.engine.build(person_id="person-1", now=NOW, facts=(
            fact("title", "title", "VP Supply Chain"),
            fact("proximity", "decision_proximity", "Influencer", kind="HYPOTHESIS"),
        ))
        self.assertEqual("ACCEPTED", result.assessment.disposition)
        self.assertEqual("Influencer", result.profile.decision_proximity)
        self.assertIn("supply", result.profile.searchable_tokens)

    def test_rejects_prohibited_persuasion_attribute(self):
        with self.assertRaises(PrecisionContractViolation):
            fact("age", "age", "42")

    def test_no_current_evidence_returns_upstream_without_profile(self):
        result = self.engine.build(
            person_id="person-1", now=NOW,
            facts=(fact("old", "title", "Manager", temporal="STALE"),),
        )
        self.assertEqual("RETURN_UPSTREAM", result.assessment.disposition)
        self.assertIsNone(result.profile)

    def test_duplicate_identity_with_changed_content_is_collision(self):
        first = fact("same", "title", "Manager")
        second = ProfessionalFact(
            first.fact_id, first.person_id, first.field, "Director", first.kind, first.evidence,
        )
        with self.assertRaises(PrecisionIdentityCollision):
            self.engine.build(person_id="person-1", facts=(first, second), now=NOW)

    def test_cross_person_merge_is_rejected(self):
        with self.assertRaises(PrecisionContractViolation):
            self.engine.build(
                person_id="person-1", facts=(fact("x", "title", "Manager", person="person-2"),),
                now=NOW,
            )

    def test_conflicting_facts_are_preserved_as_contradiction(self):
        result = self.engine.build(person_id="person-1", now=NOW, facts=(
            fact("t1", "title", "Manager"), fact("t2", "title", "Director"),
        ))
        self.assertEqual("CONTRADICTED", result.assessment.disposition)
        self.assertIn("CONTRADICTORY_TITLE", result.profile.contradictions)

    def test_functional_mailbox_is_not_decision_authority(self):
        result = self.engine.build(person_id="person-1", now=NOW, facts=(
            fact("kind", "contact_kind", "FUNCTIONAL_MAILBOX"),
            fact("function", "contact_function", "CUSTOMER_SERVICE"),
        ))
        self.assertEqual("UNKNOWN", result.profile.decision_proximity)
        self.assertIn("CONTACT_KIND_IS_NOT_DECISION_AUTHORITY", result.profile.restrictions)

    def test_capacity_is_bounded(self):
        engine = PersonIntelligenceEngine(max_facts=1)
        with self.assertRaises(PrecisionCapacityExceeded):
            engine.build(person_id="person-1", facts=(
                fact("a", "title", "A"), fact("b", "department", "B"),
            ), now=NOW)


class BehavioralEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = BehavioralIntelligenceEngine()

    def test_reply_and_click_create_observed_topic_pattern(self):
        result = self.engine.interpret(person_id="person-1", now=NOW, events=(
            behavior("click", "CLICK", topic="port disruption"),
            behavior("reply", "REPLY", topic="port disruption"),
        ))
        signal = next(item for item in result.profile.signals if item.dimension == "topic")
        self.assertEqual(2, signal.observed_event_count)
        self.assertEqual(1, signal.high_information_event_count)
        self.assertIn("preference", signal.interpretation)

    def test_open_is_neutral_not_interest(self):
        result = self.engine.interpret(
            person_id="person-1", now=NOW,
            events=(behavior("open", "OPEN", topic="cost"),),
        )
        self.assertEqual((), result.profile.signals)
        self.assertIn("behavior:open", result.profile.neutral_event_ids)

    def test_silence_is_not_rejection(self):
        result = self.engine.interpret(
            person_id="person-1", now=NOW, events=(behavior("quiet", "SILENCE"),),
        )
        self.assertIn("SILENCE_RETAINED_WITHOUT_REJECTION_INFERENCE", result.assessment.reasons)
        self.assertIn("SILENCE_NOT_REJECTION", result.profile.restrictions)

    def test_unsubscribe_is_explicit_observation_not_local_delivery_authority(self):
        result = self.engine.interpret(
            person_id="person-1", now=NOW, events=(behavior("u", "UNSUBSCRIBE"),),
        )
        self.assertIn("UNSUBSCRIBE_OBSERVED", result.assessment.reasons)
        self.assertIn("UNSUBSCRIBE_OBSERVED_REQUIRES_DELIVERY_ENFORCEMENT", result.profile.restrictions)

    def test_non_current_event_is_omitted(self):
        result = self.engine.interpret(person_id="person-1", now=NOW, events=(
            behavior("old", "REPLY", topic="risk", temporal="STALE"),
        ))
        self.assertEqual((), result.profile.signals)
        self.assertIn("evidence:old", result.profile.omitted_evidence_ids)


class RelationshipEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = RelationshipIntelligenceEngine()

    def test_empty_history_is_cold(self):
        result = self.engine.determine(person_id="person-1", events=(), policy=POLICY, now=NOW)
        self.assertEqual("COLD", result.profile.state)
        self.assertEqual("LOW_CONTEXT", result.profile.communication_permission_level)

    def test_confirmed_exposure_is_aware(self):
        result = self.engine.determine(
            person_id="person-1", events=(relationship_event("seen", "EXPOSURE_CONFIRMED"),),
            policy=POLICY, now=NOW,
        )
        self.assertEqual("AWARE", result.profile.state)

    def test_bilateral_exchange_is_conversational(self):
        result = self.engine.determine(
            person_id="person-1", events=(relationship_event("talk", "BILATERAL_EXCHANGE"),),
            policy=POLICY, now=NOW,
        )
        self.assertEqual("CONVERSATIONAL", result.profile.state)
        self.assertEqual("BILATERAL_CONTEXT", result.profile.communication_permission_level)

    def test_active_opportunity_has_commercial_context(self):
        result = self.engine.determine(
            person_id="person-1", events=(relationship_event("opp", "OPPORTUNITY_ACTIVE"),),
            policy=POLICY, now=NOW,
        )
        self.assertEqual("OPPORTUNITY", result.profile.state)
        self.assertEqual("COMMERCIAL_CONTEXT", result.profile.communication_permission_level)

    def test_latest_opportunity_transition_wins_over_old_closed_event(self):
        result = self.engine.determine(
            person_id="person-1", events=(
                relationship_event("closed", "OPPORTUNITY_CLOSED", at=NOW - 20),
                relationship_event("active", "OPPORTUNITY_ACTIVE", at=NOW - 10),
            ), policy=POLICY, now=NOW,
        )
        self.assertEqual("OPPORTUNITY", result.profile.state)

    def test_same_time_opportunity_conflict_is_not_silently_resolved(self):
        result = self.engine.determine(
            person_id="person-1", events=(
                relationship_event("closed", "OPPORTUNITY_CLOSED", at=NOW - 10),
                relationship_event("active", "OPPORTUNITY_ACTIVE", at=NOW - 10),
            ), policy=POLICY, now=NOW,
        )
        self.assertEqual("CONTRADICTED", result.assessment.disposition)
        self.assertIn("CONTRADICTORY_OPPORTUNITY_STATE_AT_SAME_TIME", result.assessment.reasons)

    def test_dormancy_uses_versioned_policy_not_hidden_threshold(self):
        old = NOW - POLICY.dormancy_after_seconds - 1
        result = self.engine.determine(
            person_id="person-1",
            events=(relationship_event("old-talk", "BILATERAL_EXCHANGE", at=old),),
            policy=POLICY, now=NOW,
        )
        self.assertEqual("DORMANT", result.profile.state)
        self.assertEqual(POLICY.policy_id, result.profile.policy_id)

    def test_unsubscribe_reduces_context_permission_to_none(self):
        result = self.engine.determine(
            person_id="person-1", events=(
                relationship_event("talk", "BILATERAL_EXCHANGE"),
                relationship_event("u", "UNSUBSCRIBE"),
            ), policy=POLICY, now=NOW,
        )
        self.assertEqual("NONE", result.profile.communication_permission_level)
        self.assertTrue(result.profile.unsubscribe_observed)


class ContextEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = ContextIntelligenceEngine()

    def full_signals(self):
        return tuple(
            context_signal(scope.lower(), scope, f"{scope} statement", tags=(scope.lower(),))
            for scope in ("GLOBAL", "INDUSTRY", "ACCOUNT", "ROLE", "MOMENT")
        )

    def test_builds_complete_global_to_moment_map(self):
        result = self.engine.map_relevance(
            insight_id="insight-1", target_id="account-1", signals=self.full_signals(), now=NOW,
        )
        self.assertEqual("ACCEPTED", result.assessment.disposition)
        self.assertEqual((), result.relevance_map.missing_scopes)

    def test_missing_global_input_returns_upstream(self):
        result = self.engine.map_relevance(
            insight_id="insight-1", target_id="account-1",
            signals=(context_signal("account", "ACCOUNT", "Account statement"),), now=NOW,
        )
        self.assertEqual("RETURN_UPSTREAM", result.assessment.disposition)
        self.assertIsNone(result.relevance_map)

    def test_missing_scopes_are_explicit_partial_not_fabricated(self):
        result = self.engine.map_relevance(
            insight_id="insight-1", target_id="account-1",
            signals=(context_signal("global", "GLOBAL", "Global fact"),), now=NOW,
        )
        self.assertEqual("PARTIAL", result.assessment.disposition)
        self.assertIn("ACCOUNT", result.relevance_map.missing_scopes)

    def test_fact_and_hypothesis_remain_separate(self):
        result = self.engine.map_relevance(
            insight_id="insight-1", target_id="account-1", signals=(
                context_signal("global", "GLOBAL", "Tariffs increased"),
                context_signal("account", "ACCOUNT", "May affect exposure", kind="HYPOTHESIS"),
            ), now=NOW,
        )
        account = next(stage for stage in result.relevance_map.stages if stage.scope == "ACCOUNT")
        self.assertEqual((), account.fact_statements)
        self.assertEqual(("May affect exposure",), account.hypothesis_statements)

    def test_opposite_polarities_preserve_contradiction(self):
        result = self.engine.map_relevance(
            insight_id="insight-1", target_id="account-1", signals=(
                context_signal("g1", "GLOBAL", "Congestion rose", claim="congestion", polarity=1),
                context_signal("g2", "GLOBAL", "Congestion did not rise", claim="congestion", polarity=-1),
            ), now=NOW,
        )
        self.assertEqual("CONTRADICTED", result.assessment.disposition)
        self.assertIn("congestion", result.relevance_map.contradicted_claim_keys)

    def test_expired_signal_is_omitted(self):
        result = self.engine.map_relevance(
            insight_id="insight-1", target_id="account-1", signals=(
                context_signal("global", "GLOBAL", "Current"),
                context_signal("old", "ACCOUNT", "Expired", valid_until=NOW - 1),
            ), now=NOW,
        )
        self.assertIn("evidence:old", result.relevance_map.omitted_evidence_ids)


class DecisionAndPipelineTests(unittest.TestCase):
    def foundation_profiles(self):
        person = PersonIntelligenceEngine().build(person_id="person-1", now=NOW, facts=(
            fact("title", "title", "VP Supply Chain"),
        )).profile
        behavioral_profile = BehavioralIntelligenceEngine().interpret(
            person_id="person-1", now=NOW,
            events=(behavior("reply", "REPLY", topic="disruption"),),
        ).profile
        relationship_profile = RelationshipIntelligenceEngine().determine(
            person_id="person-1", events=(relationship_event("talk", "BILATERAL_EXCHANGE"),),
            policy=POLICY, now=NOW,
        ).profile
        context_map = ContextIntelligenceEngine().map_relevance(
            insight_id="insight-1", target_id="account-1", signals=tuple(
                context_signal(scope.lower(), scope, scope, tags=(scope.lower(),))
                for scope in ("GLOBAL", "INDUSTRY", "ACCOUNT", "ROLE", "MOMENT")
            ), now=NOW,
        ).relevance_map
        return person, context_map, behavioral_profile, relationship_profile

    def test_decision_engine_selects_unique_supported_values(self):
        person, context_map, behavioral_profile, relationship_profile = self.foundation_profiles()
        result = DecisionIntelligenceEngine().formulate(
            person=person, context=context_map, behavioral=behavioral_profile,
            relationship=relationship_profile, now=NOW, signals=(
                decision_signal("driver", "DRIVER", "Control"),
                decision_signal("horizon", "HORIZON", "Quarter"),
                decision_signal("proof", "EVIDENCE_PREFERENCE", "Benchmark"),
                decision_signal("frame", "FRAMING", "Resilience"),
            ),
        )
        self.assertEqual("Control", result.hypothesis.primary_driver)
        self.assertEqual("Quarter", result.hypothesis.horizon)
        self.assertIn("HYPOTHESIS_NOT_FACT", result.hypothesis.restrictions)

    def test_tied_drivers_remain_ambiguous(self):
        person, context_map, behavioral_profile, relationship_profile = self.foundation_profiles()
        result = DecisionIntelligenceEngine().formulate(
            person=person, context=context_map, behavioral=behavioral_profile,
            relationship=relationship_profile, now=NOW, signals=(
                decision_signal("risk", "DRIVER", "Risk"),
                decision_signal("cost", "DRIVER", "Cost"),
            ),
        )
        self.assertIsNone(result.hypothesis.primary_driver)
        self.assertIn("DRIVER_AMBIGUOUS", result.assessment.reasons)

    def test_opposite_decision_signals_are_contradicted(self):
        person, context_map, behavioral_profile, relationship_profile = self.foundation_profiles()
        result = DecisionIntelligenceEngine().formulate(
            person=person, context=context_map, behavioral=behavioral_profile,
            relationship=relationship_profile, now=NOW, signals=(
                decision_signal("for", "DRIVER", "Cost", root="root:a"),
                decision_signal("against", "DRIVER", "Cost", polarity=-1, root="root:b"),
            ),
        )
        self.assertEqual("CONTRADICTED", result.assessment.disposition)

    def test_repeated_signal_root_does_not_inflate_support(self):
        person, context_map, behavioral_profile, relationship_profile = self.foundation_profiles()
        result = DecisionIntelligenceEngine().formulate(
            person=person, context=context_map, behavioral=behavioral_profile,
            relationship=relationship_profile, now=NOW, signals=(
                decision_signal("one", "DRIVER", "Cost", root="root:shared"),
                decision_signal("two", "DRIVER", "Cost", root="root:shared"),
            ),
        )
        candidate = next(item for item in result.hypothesis.candidates if item.value == "Cost")
        self.assertEqual(1, candidate.positive_root_count)

    def test_ungoverned_decision_signal_source_is_rejected(self):
        with self.assertRaises(PrecisionContractViolation):
            decision_signal("foreign", "DRIVER", "Cost", source_engine="FOREIGN_ENGINE")

    def test_derived_confidence_cannot_exceed_weakest_support(self):
        person, context_map, behavioral_profile, relationship_profile = self.foundation_profiles()
        result = DecisionIntelligenceEngine().formulate(
            person=person, context=context_map, behavioral=behavioral_profile,
            relationship=relationship_profile, now=NOW, signals=(
                decision_signal("a", "DRIVER", "Cost", confidence="A"),
                decision_signal("d", "DRIVER", "Cost", confidence="D"),
            ),
        )
        candidate = next(item for item in result.hypothesis.candidates if item.value == "Cost")
        self.assertEqual("D", candidate.confidence)

    def test_real_functional_mailbox_case_remains_partial_and_forwardable_candidate_only(self):
        request = PrecisionInput(
            person_id="person-1", insight_id="insight-1", target_id="account-1",
            professional_facts=(
                fact("mailbox", "contact_kind", "FUNCTIONAL_MAILBOX"),
                fact("function", "contact_function", "CUSTOMER_SERVICE"),
                fact("company", "company", "Example Importer"),
            ),
            behavior_events=(), relationship_events=(),
            context_signals=tuple(
                context_signal(scope.lower(), scope, f"{scope} relevance", tags=(scope.lower(),))
                for scope in ("GLOBAL", "INDUSTRY", "ACCOUNT", "ROLE", "MOMENT")
            ),
            decision_signals=(
                decision_signal("control", "DRIVER", "Control"),
                decision_signal("quarter", "HORIZON", "Quarter"),
                decision_signal("benchmark", "EVIDENCE_PREFERENCE", "Benchmark"),
                decision_signal("resilience", "FRAMING", "Resilience"),
            ),
            relationship_policy=POLICY,
        )
        result = PrecisionFoundationPipeline().execute(request, now=NOW)
        self.assertEqual("PARTIAL", result.disposition)
        self.assertEqual("UNKNOWN", result.person.profile.decision_proximity)
        self.assertEqual("COLD", result.relationship.profile.state)
        self.assertEqual("Control", result.decision.hypothesis.primary_driver)
        self.assertIn("NO_DELIVERY_AUTHORITY", result.decision.hypothesis.restrictions)

    def test_pipeline_stops_before_decision_when_global_truth_is_missing(self):
        request = PrecisionInput(
            person_id="person-1", insight_id="insight-1", target_id="account-1",
            professional_facts=(fact("title", "title", "Manager"),),
            behavior_events=(), relationship_events=(),
            context_signals=(context_signal("account", "ACCOUNT", "Account only"),),
            decision_signals=(decision_signal("cost", "DRIVER", "Cost"),),
            relationship_policy=POLICY,
        )
        result = PrecisionFoundationPipeline().execute(request, now=NOW)
        self.assertEqual("RETURN_UPSTREAM", result.disposition)
        self.assertIsNone(result.decision)


if __name__ == "__main__":
    unittest.main()
