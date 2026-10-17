from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import test_statistical_retention as retention
from test_agent_research_acquisition import NOW, Response
from test_research_methodology import html_sections
from test_research_statistics import dataset
from sictra_block1.common import ContractViolation
from sictra_block1.intelligence_dossier import _validated_input
from sictra_block1.manual_bundle_ledger import validate_unattested_manual_bundle
from sictra_block1.research_acquisition import canonical, ResearchQuarantine
from sictra_block1.source_control_store import SourceControlStore
from sictra_block1.statistical_watchlist import StatisticalWatchlist, StatisticalWatchlistViolation, _compare


class StatisticalWatchlistTests(unittest.TestCase):
    def setUp(self):
        self.fixture = retention.StatisticalRetentionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.view = StatisticalWatchlist(self.fixture.store)

    def first(self, value=None):
        source = self.fixture.source if value is None else self.fixture.acquire(value, at=NOW + 1)
        return self.fixture.store.retain(source)

    def second(self, **changes):
        value = {**dataset(), "updated": "2025-02-15T12:00:00Z", **changes}
        source = self.fixture.acquire(value, at=NOW + 2)
        return self.fixture.store.retain(source)

    def test_single_release_has_literal_facts_but_no_change_resolution_or_legacy_admission(self):
        self.first()
        before = self.fixture.fixture.files()
        report = self.view.read()
        self.assertEqual([(2023, 10.0), (2024, 12.5)], [(r["time_period"], r["value"]) for r in report["facts"]])
        self.assertEqual("INSUFFICIENT_EVIDENCE", report["comparison"]["status"])
        self.assertEqual("SECOND_RELEASE_REQUIRED", report["comparison"]["reason"])
        self.assertEqual(NOW + 86400, report["expires_at"])
        self.assertEqual(self.fixture.fixture.metadata, report["evidence_refs"][0]["methodology_candidate_id"])
        self.assertEqual([], report["interpretations"])
        self.assertEqual([], report["hypotheses"])
        self.assertEqual("NOT_RESOLVED", report["resolution"])
        self.assertEqual("RESEARCH_NEEDED", report["editorial_state"])
        self.assertEqual("NOT_PERSISTED", report["projection_persistence"])
        self.assertEqual({("UNCONFIRMED", "C")}, {(r["certainty"], r["confidence"]) for r in report["facts"]})
        with self.assertRaises(ContractViolation):
            validate_unattested_manual_bundle(report)
        with self.assertRaises(ContractViolation):
            _validated_input(report, {"fixture": b"x" * 32})
        self.assertEqual(before, self.fixture.fixture.files())

    def test_same_period_values_not_cross_year_values_are_compared(self):
        first = self.first()
        last = self.second(value=[18.0, 14.0])
        report = self.view.read()
        self.assertEqual("CHANGE_DETECTED", report["comparison"]["status"])
        self.assertEqual([(2023, 10.0, 14.0, 4.0), (2024, 12.5, 18.0, 5.5)],
            [(r["time_period"], r["before_value"], r["after_value"], r["absolute_delta"])
             for r in report["comparison"]["changes"]])
        self.assertEqual(first["evidence_id"], report["comparison"]["before"])
        self.assertEqual(last["evidence_id"], report["comparison"]["current"])
        self.assertEqual(["CURRENT", "HISTORICAL_CONTEXT_ONLY"], [r["state"] for r in report["evidence_refs"]])
        self.assertEqual([14.0, 18.0], [r["value"] for r in report["facts"]])

    def test_new_release_identical_measurements_is_not_a_numeric_change(self):
        self.first()
        self.second()
        report = self.view.read()
        self.assertEqual("NO_CHANGE", report["comparison"]["status"])
        self.assertEqual([], report["comparison"]["changes"])
        self.assertNotEqual(report["evidence_refs"][0]["source_file_sha256"], report["evidence_refs"][1]["source_file_sha256"])

    def test_same_release_recollection_restart_and_replay_preserve_read_only_view(self):
        self.first()
        source = self.fixture.acquire(dataset(), at=NOW + 2)
        self.fixture.store.retain(source)
        report = self.view.read()
        self.assertEqual(("NO_CHANGE", "SAME_RELEASE_RECOLLECTED"),
            (report["comparison"]["status"], report["comparison"]["reason"]))
        self.assertIsNone(report["comparison"]["before"])
        before = self.fixture.fixture.files()
        restarted = StatisticalWatchlist(self.fixture.open_store())
        self.assertEqual(report, restarted.read())
        self.assertTrue(self.fixture.store.retain(source)["replay"])
        self.assertEqual(report, self.view.read())
        self.assertEqual(before, self.fixture.fixture.files())
        report["facts"][0]["value"] = 999
        self.assertEqual(10.0, self.view.read()["facts"][0]["value"])

    def test_flag_only_change_keeps_zero_numeric_delta_without_value_change_claim(self):
        self.first()
        self.second(status={"0": "e"})
        changes = self.view.read()["comparison"]["changes"]
        self.assertEqual(1, len(changes))
        self.assertEqual((2024, "FLAG_CHANGED", 0.0, "p", "e"),
            tuple(changes[0][k] for k in ("time_period", "change_type", "absolute_delta", "before_status_flag", "after_status_flag")))

    def test_value_and_flag_change_remain_separate_from_causal_explanation(self):
        self.first()
        self.second(value=[18.0, 10.0], status={"0": "e"})
        report = self.view.read()
        change = report["comparison"]["changes"][0]
        self.assertEqual(("VALUE_CHANGED", 5.5, "p", "e"),
            tuple(change[k] for k in ("change_type", "absolute_delta", "before_status_flag", "after_status_flag")))
        self.assertEqual([], report["interpretations"])
        self.assertEqual("NOT_RESOLVED", report["resolution"])

    def test_typed_comparison_rejects_unit_scope_or_coordinate_substitution(self):
        # Fixed normalized reference case exercises defense in depth, not an
        # alternative public entry point for unverified packets.
        body = {"source_scope": "fixture", "filters": {"unit": "THS_T"},
            "grain": ["geo_code", "time_period"], "provenance": {"dataset_code": "fixture"},
            "observations": [{"geo_code": "BE", "time_period": 2024,
                "value_thousand_tonnes": 12.5, "missing": False, "status_flag": "p"}]}
        self.assertEqual([], _compare(body, deepcopy(body)))
        changed_unit = deepcopy(body)
        changed_unit["filters"]["unit"] = "USD"
        changed_period = deepcopy(body)
        changed_period["observations"][0]["time_period"] = 2023
        changed_scope = {**deepcopy(body), "source_scope": "other"}
        for invalid in (changed_unit, changed_period, changed_scope):
            with self.assertRaises(ContractViolation):
                _compare(body, invalid)

    def test_missing_to_observed_is_coverage_not_zero_based_delta(self):
        self.first({**dataset(), "value": [None, 10.0]})
        self.second()
        report = self.view.read()
        change = report["comparison"]["changes"][0]
        self.assertEqual((2024, "OBSERVATION_AVAILABLE", None, None, 12.5),
            tuple(change[k] for k in ("time_period", "change_type", "absolute_delta", "before_value", "after_value")))
        self.assertEqual(2, len(report["facts"]))

    def test_observed_to_missing_withholds_measurement_fact_and_delta(self):
        self.first()
        self.second(value=[None, 10.0])
        report = self.view.read()
        self.assertEqual([2023], [r["time_period"] for r in report["facts"]])
        self.assertEqual("OBSERVATION_UNAVAILABLE", report["comparison"]["changes"][0]["change_type"])
        self.assertIsNone(report["comparison"]["changes"][0]["absolute_delta"])
        self.assertEqual("MISSING_MEASUREMENT", report["uncertainty"][0]["reason"])

    def test_two_missing_flags_can_change_but_do_not_create_a_value(self):
        self.first({**dataset(), "value": [None, 10.0]})
        self.second(value=[None, 10.0], status={"0": "e"})
        report = self.view.read()
        change = report["comparison"]["changes"][0]
        self.assertEqual("MISSING_FLAG_CHANGED", change["change_type"])
        self.assertIsNone(change["absolute_delta"])
        self.assertEqual([10.0], [r["value"] for r in report["facts"]])

    def test_empty_and_expired_history_never_produce_current_facts(self):
        empty = self.view.read()
        self.assertEqual([], empty["facts"])
        self.assertEqual("INSUFFICIENT_EVIDENCE", empty["comparison"]["status"])
        self.first()
        self.fixture.fixture.now = NOW + 86400
        stale = self.view.read()
        self.assertEqual([], stale["facts"])
        self.assertEqual([], stale["evidence_refs"])
        self.assertEqual("NOT_CURRENT", stale["source_state"])

    def test_same_instant_different_payload_requires_review_not_arbitrary_fact(self):
        self.first()
        self.second(updated="2025-01-15T13:00:00+0100", value=[13.0, 10.0])
        report = self.view.read()
        self.assertEqual("REVIEW_REQUIRED", report["comparison"]["status"])
        self.assertEqual([], report["facts"])
        self.assertIn("LATEST_RELEASE_AMBIGUOUS", report["reasons"])

    def test_unordered_publisher_identity_requires_review(self):
        self.first({**dataset(), "updated": "2025-01-15"})
        report = self.view.read()
        self.assertEqual("REVIEW_REQUIRED", report["comparison"]["status"])
        self.assertEqual([], report["facts"])

    def test_ambiguous_baseline_does_not_discard_current_facts_or_choose_an_old_value(self):
        self.first()
        alternative = self.fixture.acquire({**dataset(), "value": [13.0, 11.0]}, at=NOW + 1)
        self.fixture.store.retain(alternative)
        self.second(value=[18.0, 14.0])
        report = self.view.read()
        self.assertEqual("CURRENT", report["source_state"])
        self.assertEqual([14.0, 18.0], [r["value"] for r in report["facts"]])
        self.assertEqual("REVIEW_REQUIRED", report["comparison"]["status"])
        self.assertEqual("BASELINE_RELEASE_AMBIGUOUS", report["comparison"]["reason"])
        self.assertEqual([], report["comparison"]["changes"])
        self.assertEqual(1, len(report["evidence_refs"]))

    def test_rehashed_forgery_false_resolution_or_false_lineage_is_rejected(self):
        self.first()
        report = self.view.read()
        self.assertEqual("VERIFIED_LOCAL_EQUIVALENCE", self.view.verify_projection(report)["status"])
        for field, value in (("resolution", "RESOLVED"), ("interpretations", ["Invented cause"]),
                             ("acceptance", "ACCEPTED"), ("runtime_effect", "EXECUTED")):
            forged = {**deepcopy(report), field: value}
            forged.pop("projection_id")
            forged["projection_id"] = sha256(canonical(forged)).hexdigest()
            with self.assertRaisesRegex(StatisticalWatchlistViolation, "PROJECTION_MISMATCH"):
                self.view.verify_projection(forged)
        for field, value in (("value", 999), ("confidence", "A"), ("evidence_id", "other-root")):
            forged = deepcopy(report)
            forged["facts"][0][field] = value
            with self.assertRaises(ContractViolation):
                self.view.verify_projection(forged)
        self.fixture.fixture.now = NOW + 86400
        with self.assertRaises(ContractViolation):
            self.view.verify_projection(report)

    def test_python_equality_cannot_substitute_json_types_or_override_projection_verification(self):
        self.first()
        report = self.view.read()
        altered_type = deepcopy(report)
        altered_type["expires_at"] = float(report["expires_at"])
        class LyingProjection(dict):
            def __eq__(self, other):
                return True
        lie = LyingProjection(deepcopy(report))
        lie["resolution"] = "RESOLVED"
        for forged in (altered_type, lie):
            with self.subTest(kind=type(forged).__name__):
                with self.assertRaises(ContractViolation):
                    self.view.verify_projection(forged)

    def test_projection_time_expiry_rotation_and_new_release_withhold_output(self):
        self.first()
        compose = self.view._compose
        def expire(*args):
            result = compose(*args)
            self.fixture.fixture.now = NOW + 86400
            return result
        with patch.object(self.view, "_compose", side_effect=expire):
            with self.assertRaises(ContractViolation):
                self.view.read()
        self.fixture.fixture.now = NOW
        def rotate(*args):
            result = compose(*args)
            self.fixture.fixture.now = self.fixture.fixture.fixture.now = NOW + 1
            self.fixture.fixture.approve_fixture()
            return result
        with patch.object(self.view, "_compose", side_effect=rotate):
            with self.assertRaises(ContractViolation):
                self.view.read()
        # A new attested release under the rotated authority is not silently
        # substituted for the snapshot used to compose a view.
        def append(*args):
            result = compose(*args)
            self.second()
            return result
        with patch.object(self.view, "_compose", side_effect=append):
            with self.assertRaises(ContractViolation):
                self.view.read()

    def test_tampered_dependency_is_rejected_without_history_write(self):
        self.first()
        before = self.fixture.path.read_bytes()
        content = self.fixture.fixture.quarantine.root / self.fixture.fixture.data / "content.bin"
        content.write_bytes(content.read_bytes() + b"tamper")
        with self.assertRaises(ContractViolation):
            self.view.read()
        self.assertEqual(before, self.fixture.path.read_bytes())

    def test_data_only_recovery_with_original_keys_and_external_heads_reproduces_projection(self):
        self.first()
        self.second(value=[18.0, 14.0])
        report = self.view.read()
        f = self.fixture.fixture
        with TemporaryDirectory() as folder:
            restored = Path(folder) / "restored"
            copytree(f.root, restored)
            quarantine = ResearchQuarantine(restored / f.quarantine.root.relative_to(f.root))
            control = SourceControlStore(restored / f.control.path.name,
                binding_keys={"fixture-review": retention.admission.BINDING_KEY},
                integrity_key=retention.admission.CONTROL_KEY, clock=lambda: f.now)
            recovered = self.fixture.open_store(path=restored / self.fixture.path.name, quarantine=quarantine, control=control)
            self.assertEqual(report, StatisticalWatchlist(recovered).read())

    def test_expired_baseline_is_historical_context_only_when_fresh_dependencies_are_admitted(self):
        first = self.first()
        f = self.fixture.fixture
        f.now = f.fixture.now = NOW + 86410
        f.terms = f.fixture.terms()
        f.fixture.response = Response(body=html_sections())
        f.metadata = f.fixture.session.acquire("EUROSTAT_MAR_METADATA", terms_candidate_id=f.terms)["candidate_id"]
        f.data = f.acquire_data({**dataset(), "updated": "2025-02-15T12:00:00Z", "value": [18.0, 14.0]})
        f.approve_fixture(ttl=100000)
        self.fixture.store.retain(f.attest())
        report = self.view.read()
        self.assertEqual("CHANGE_DETECTED", report["comparison"]["status"])
        self.assertEqual("HISTORICAL_CONTEXT_ONLY", report["evidence_refs"][1]["state"])
        self.assertLess(report["evidence_refs"][1]["expires_at"], f.now)
        self.assertGreater(report["expires_at"], f.now)
        with self.assertRaises(ContractViolation):
            self.fixture.store.select(first["evidence_id"])

    def test_final_expiry_fence_and_caller_time_override_are_rejected(self):
        self.first()
        original = self.fixture.store._snapshot
        calls = 0
        def slow():
            nonlocal calls
            result = original()
            calls += 1
            if calls == 2:
                self.fixture.fixture.now = NOW + 86400
            return result
        with patch.object(self.fixture.store, "_snapshot", side_effect=slow):
            with self.assertRaisesRegex(StatisticalWatchlistViolation, "READ_EXPIRED"):
                self.view.read()
        with self.assertRaises(TypeError):
            self.view.read(now=NOW)
        with self.assertRaisesRegex(StatisticalWatchlistViolation, "TRUSTED_STORE"):
            StatisticalWatchlist({})


if __name__ == "__main__":
    unittest.main()
