from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import test_statistical_retention as retention
from test_agent_research_acquisition import NOW
from test_research_statistics import dataset
from sictra_block1.common import ContractViolation
from sictra_block1.intelligence_dossier import _validated_input
from sictra_block1.research_acquisition import ResearchQuarantine, canonical
from sictra_block1.source_control_store import SourceControlStore
from sictra_block1.statistical_dossier import StatisticalDossierProducer
from sictra_block1.editorial import assess_editorial_candidate
from sictra_block1.statistical_watchlist import StatisticalWatchlist
from sictra_block4_orchestrator.operations_store import OperationsError, OperationsStore
from sictra_block4_orchestrator.statistical_review_archive import KIND, StatisticalReviewArchive

OPS_KEY = b"o" * 32


class StatisticalReviewDossierTests(unittest.TestCase):
    def setUp(self):
        self.f = retention.StatisticalRetentionTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.ops = OperationsStore(self.f.fixture.root / "review.sqlite", OPS_KEY)
        self.producer = StatisticalDossierProducer(StatisticalWatchlist(self.f.store))
        self.stopped = False
        self.archive = self.open_archive()

    def open_archive(self, **kwargs):
        return StatisticalReviewArchive(**{"store": self.ops, "producer": self.producer,
            "stopped": lambda: self.stopped, **kwargs})

    def first(self):
        return self.f.store.retain(self.f.source)

    def second(self):
        source = self.f.acquire({**dataset(), "updated": "2025-02-15T12:00:00Z",
                                "value": [18.0, 14.0]}, at=NOW + 2)
        return self.f.store.retain(source)

    def test_attested_fixture_source_journals_separated_facts_and_replays_after_restart(self):
        evidence = self.first()
        receipt = self.archive.record()
        result = self.archive.read(receipt["dossier_id"])
        dossier = result["dossier"]
        self.assertEqual([(2023, 10.0), (2024, 12.5)],
                         [(x["time_period"], x["value"]) for x in dossier["facts"]])
        self.assertEqual(evidence["evidence_id"], dossier["evidence_refs"][0]["evidence_id"])
        self.assertEqual("INSUFFICIENT_EVIDENCE", dossier["comparison"]["status"])
        self.assertEqual(([], [], "NOT_RESOLVED", "RESEARCH_NEEDED", "BLOCKED", "NONE"),
                         tuple(dossier[k] for k in ("interpretations", "hypotheses", "resolution",
                                                  "editorial_state", "publication", "runtime_effect")))
        before = self.ops.records()
        restarted = self.open_archive(store=OperationsStore(self.ops.path, OPS_KEY),
            producer=StatisticalDossierProducer(StatisticalWatchlist(self.f.open_store())))
        self.assertTrue(restarted.record()["replay"])
        self.assertEqual(result, restarted.read(receipt["dossier_id"]))
        self.assertEqual(before, self.ops.records())
        dossier["facts"][0]["value"] = 999
        self.assertEqual(10.0, restarted.read(receipt["dossier_id"])["dossier"]["facts"][0]["value"])
        with self.assertRaises(ContractViolation):
            _validated_input(result["dossier"], {"fixture": b"x" * 32})

    def test_second_release_creates_new_identity_and_old_dossier_cannot_be_current(self):
        self.first()
        old = self.archive.record()
        self.second()
        with self.assertRaises(ContractViolation):
            self.archive.read(old["dossier_id"])
        new = self.archive.record()
        self.assertNotEqual(old["dossier_id"], new["dossier_id"])
        current = self.archive.read(new["dossier_id"])["dossier"]
        self.assertEqual([14.0, 18.0], [f["value"] for f in current["facts"]])
        self.assertEqual([4.0, 5.5], [c["absolute_delta"] for c in current["comparison"]["changes"]])
        self.assertEqual("HISTORICAL_CONTEXT_ONLY", current["evidence_refs"][1]["state"])
        self.assertEqual(2, len(self.ops.latest(KIND)))

    def test_missing_value_is_uncertainty_and_all_missing_admission_rejects(self):
        source = self.f.acquire({**dataset(), "value": [None, 10.0]}, at=NOW + 1)
        self.f.store.retain(source)
        receipt = self.archive.record()
        dossier = self.archive.read(receipt["dossier_id"])["dossier"]
        self.assertEqual([(2023, 10.0)], [(r["time_period"], r["value"]) for r in dossier["facts"]])
        self.assertEqual(["MISSING_MEASUREMENT"], [u["reason"] for u in dossier["uncertainty"]])
        self.assertEqual("NOT_RESOLVED", dossier["resolution"])
        before = self.ops.records()
        with self.assertRaisesRegex(ContractViolation, "ADMISSION_NO_OBSERVED_VALUES"):
            self.f.acquire({**dataset(), "value": [None, None]}, at=NOW + 2)
        self.assertEqual(before, self.ops.records())

    def test_absent_and_expired_source_reject_without_dossier_writes(self):
        before = self.ops.records()
        with self.assertRaises(ContractViolation):
            self.archive.record()
        self.assertEqual(before, self.ops.records())
        self.first()
        receipt = self.archive.record()
        before = self.ops.records()
        self.f.fixture.now = NOW + 86400
        for action in (self.archive.record, lambda: self.archive.read(receipt["dossier_id"])):
            with self.assertRaises(ContractViolation):
                action()
        self.assertEqual(before, self.ops.records())

    def test_signed_forgery_false_resolution_or_type_substitution_never_reads_as_current(self):
        self.first()
        receipt = self.archive.record()
        original = self.ops.latest(KIND)[receipt["dossier_id"]]
        for field, value in (("resolution", "RESOLVED"), ("interpretations", ["Cause invented"]),
                             ("confidence", "A"), ("expires_at", float(NOW + 86400))):
            forged = deepcopy(original)
            forged["dossier"][field] = value
            # A privileged signed mutation must actually reach stored bytes.
            # OperationsStore.put regards equal int/float values as replay.
            with self.ops.connect() as db:
                db.execute("BEGIN IMMEDIATE")
                self.ops._append(db, KIND, receipt["dossier_id"], forged)
            with self.assertRaises(ContractViolation):
                self.archive.read(receipt["dossier_id"])
            with self.assertRaises(OperationsError):
                self.archive.record()
            self.ops.put(KIND, receipt["dossier_id"], original)

    def test_partial_append_failure_rolls_back_then_retry_recovers(self):
        self.first()
        before = self.ops.records()
        append = self.ops._append
        def fail(*args):
            append(*args)
            raise OperationsError("INJECTED_AFTER_INSERT")
        with patch.object(self.ops, "_append", side_effect=fail):
            with self.assertRaisesRegex(OperationsError, "INJECTED_AFTER_INSERT"):
                self.archive.record()
        self.assertEqual(before, self.ops.records())
        self.assertFalse(self.archive.record()["replay"])

    def test_stop_before_write_and_after_insert_prevents_commit(self):
        self.first()
        before = self.ops.records()
        self.stopped = True
        self.assertEqual("STOPPED", self.archive.record()["status"])
        self.stopped = False
        append = self.ops._append
        def stop(*args):
            append(*args)
            self.stopped = True
        with patch.object(self.ops, "_append", side_effect=stop):
            with self.assertRaisesRegex(OperationsError, "ARCHIVE_STOPPED"):
                self.archive.record()
        self.assertEqual(before, self.ops.records())

    def test_expiry_clock_regression_and_authority_rotation_after_insert_roll_back(self):
        self.first()
        before = self.ops.records()
        append = self.ops._append
        def rotate():
            self.f.fixture.now = NOW + 1
            self.f.fixture.approve_fixture(ttl=100000)
        for mutation in (lambda: setattr(self.f.fixture, "now", NOW + 86400),
                         lambda: setattr(self.f.fixture, "now", NOW - 1),
                         rotate):
            self.f.fixture.now = NOW
            def change(*args):
                append(*args)
                mutation()
            with patch.object(self.ops, "_append", side_effect=change):
                with self.assertRaises((ContractViolation, OperationsError)):
                    self.archive.record()
            self.assertEqual(before, self.ops.records())

    def test_capacity_allows_exact_replay_but_rejects_new_release(self):
        self.first()
        bounded = self.open_archive(max_dossiers=1)
        bounded.record()
        self.assertTrue(bounded.record()["replay"])
        self.second()
        before = self.ops.records()
        with self.assertRaisesRegex(OperationsError, "CAPACITY_EXCEEDED"):
            bounded.record()
        self.assertEqual(before, self.ops.records())

    def test_tampered_source_or_journal_withholds_stored_candidate(self):
        self.first()
        receipt = self.archive.record()
        content = self.f.fixture.quarantine.root / self.f.fixture.data / "content.bin"
        raw = content.read_bytes()
        content.write_bytes(raw + b"tamper")
        with self.assertRaises(ContractViolation):
            self.archive.read(receipt["dossier_id"])
        content.write_bytes(raw)
        with self.ops.connect() as db:
            db.execute("UPDATE records SET body='{}' WHERE kind=?", (KIND,))
        with self.assertRaisesRegex(OperationsError, "INTEGRITY_ERROR"):
            self.archive.read(receipt["dossier_id"])

    def test_full_data_copy_recovery_requires_original_keys_and_source_checkpoints(self):
        self.first()
        receipt = self.archive.record()
        expected = self.archive.read(receipt["dossier_id"])
        f = self.f.fixture
        with TemporaryDirectory() as folder:
            restored = Path(folder) / "restored"
            copytree(f.root, restored)
            quarantine = ResearchQuarantine(restored / f.quarantine.root.relative_to(f.root))
            control = SourceControlStore(restored / f.control.path.name,
                binding_keys={"fixture-review": retention.admission.BINDING_KEY},
                integrity_key=retention.admission.CONTROL_KEY, clock=lambda: f.now)
            sources = self.f.open_store(path=restored / self.f.path.name,
                                       quarantine=quarantine, control=control)
            recovered = self.open_archive(store=OperationsStore(restored / self.ops.path.name, OPS_KEY),
                producer=StatisticalDossierProducer(StatisticalWatchlist(sources)))
            self.assertEqual(expected, recovered.read(receipt["dossier_id"]))
            self.assertTrue(recovered.record()["replay"])
            with self.assertRaises(OperationsError):
                OperationsStore(restored / self.ops.path.name, b"wrong" * 8)

    def test_configuration_selection_and_caller_payload_override_reject(self):
        for identity in (None, "", "other"):
            with self.assertRaises(OperationsError):
                self.archive.read(identity)
        with self.assertRaises(OperationsError):
            self.archive.read("STAT-DOSSIER-missing")
        for capacity in (0, 101, True):
            with self.assertRaises(OperationsError):
                self.open_archive(max_dossiers=capacity)
        with self.assertRaises(ContractViolation):
            StatisticalDossierProducer({})
        with self.assertRaises(TypeError):
            self.archive.record({"resolution": "RESOLVED"})
        with patch.object(self.ops, "path", self.f.path):
            with self.assertRaisesRegex(OperationsError, "PATH_COLLISION"):
                self.open_archive()

    def test_self_sealed_forgery_and_future_record_time_reject(self):
        self.first()
        dossier = self.producer.read()
        dossier["resolution"] = "RESOLVED"
        dossier.pop("dossier_id")
        dossier["dossier_id"] = "STAT-DOSSIER-" + sha256(canonical(dossier)).hexdigest()
        self.ops.put(KIND, dossier["dossier_id"], {"version": "0.1.0", "recorded_at": NOW, "dossier": dossier})
        with self.assertRaises(ContractViolation):
            self.archive.read(dossier["dossier_id"])
        current = self.producer.read()
        self.ops.put(KIND, current["dossier_id"], {"version": "0.1.0", "recorded_at": NOW + 1,
                                                "dossier": current})
        with self.assertRaisesRegex(OperationsError, "RECORD_INVALID"):
            self.archive.read(current["dossier_id"])

    def test_signed_null_record_is_invalid_identity_not_permission_to_replace(self):
        self.first()
        identity = self.producer.read()["dossier_id"]
        self.ops.put(KIND, identity, None)
        before = self.ops.records()
        with self.assertRaisesRegex(OperationsError, "RECORD_INVALID"):
            self.archive.record()
        with self.assertRaises(OperationsError):
            self.archive.read(identity)
        self.assertEqual(before, self.ops.records())

    def test_expiry_after_final_producer_check_withholds_read_without_writes(self):
        self.first()
        receipt = self.archive.record()
        before = self.ops.records()
        verify = self.producer.verify_dossier
        calls = 0
        def expire(value):
            nonlocal calls
            result = verify(value)
            calls += 1
            if calls == 2:
                self.f.fixture.now = NOW + 86400
            return result
        with patch.object(self.producer, "verify_dossier", side_effect=expire):
            with self.assertRaisesRegex(OperationsError, "READ_EXPIRED"):
                self.archive.read(receipt["dossier_id"])
        self.assertEqual(before, self.ops.records())

    def test_archived_dossier_composes_only_blocked_editorial_candidate_with_one_current_root(self):
        self.first()
        self.second()
        receipt = self.archive.record()
        before = self.ops.records()
        result = self.archive.editorial_candidate(receipt["dossier_id"])
        self.assertEqual(("RESEARCH_NEEDED", "BLOCKED"),
            (result["assessment"]["disposition"], result["assessment"]["editorial_readiness"]))
        self.assertEqual(["gateway-source:eurostat"], result["candidate"]["evidence"]["root_ids"])
        self.assertEqual(2, result["candidate"]["evidence"]["required_roots"])
        self.assertEqual(["7D", "30D", "90D"], [w["horizon"] for w in result["candidate"]["watchlist"]])
        text = result["candidate"]["editorial"]["what_changed"]
        self.assertIn("14.0 THS_T for BE in 2023", text)
        self.assertIn("18.0 THS_T for BE in 2024", text)
        self.assertEqual(receipt["dossier_id"], result["candidate"]["event_id"])
        self.assertEqual(["CURRENT", "HISTORICAL_CONTEXT_ONLY"], [e["state"] for e in result["evidence_refs"]])
        self.assertIsNone(result["handoff"])
        self.assertEqual(before, self.ops.records())

    def test_source_expiry_during_editorial_assessment_withholds_candidate(self):
        self.first()
        dossier = self.producer.read()
        before = self.ops.records()
        def expire(candidate):
            result = assess_editorial_candidate(candidate)
            self.f.fixture.now = NOW + 86400
            return result
        with patch("sictra_block1.statistical_dossier.assess_editorial_candidate", side_effect=expire):
            with self.assertRaises(ContractViolation):
                self.producer.editorial_candidate(dossier)
        self.assertEqual(before, self.ops.records())

    def test_false_editorial_readiness_and_forged_interpretation_reject(self):
        self.first()
        dossier = self.producer.read()
        with patch("sictra_block1.statistical_dossier.assess_editorial_candidate",
                   return_value={"disposition": "DELIVERABLE_BOUNDED", "editorial_readiness": "READY"}):
            with self.assertRaisesRegex(ContractViolation, "EDITORIAL_BOUNDARY"):
                self.producer.editorial_candidate(dossier)
        dossier["interpretations"] = ["Invented cause"]
        with self.assertRaises(ContractViolation):
            self.producer.editorial_candidate(dossier)


if __name__ == "__main__":
    unittest.main()
