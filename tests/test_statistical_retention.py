from copy import deepcopy
import json
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import test_statistical_admission_bridge as admission
from test_agent_research_acquisition import NOW
from test_research_statistics import dataset
from sictra_block1.attested_evidence_store import AttestedEvidenceStore
from sictra_block1.common import ContractViolation
from sictra_block1.research_acquisition import ResearchQuarantine
from sictra_block1.source_control_store import SourceControlStore
from sictra_block1.statistical_retention import StatisticalEvidenceStore, StatisticalRetentionViolation

INTEGRITY_KEY = b"r" * 32


class StatisticalRetentionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = admission.StatisticalAdmissionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.approve_fixture(ttl=100000)
        self.path = self.fixture.root / "statistical-history.json"
        self.store = self.open_store()
        self.source = self.fixture.attest()

    def open_store(self, **kwargs):
        defaults = {"path": self.path, "quarantine": self.fixture.quarantine,
            "control": self.fixture.control, "evidence_keys": {"fixture-issuer": admission.EVIDENCE_KEY},
            "integrity_key": INTEGRITY_KEY, "clock": lambda: self.fixture.now,
            "control_checkpoint": self.fixture.control.list_records(now=self.fixture.now)[-1]["record_hash"]}
        if hasattr(self, "store"):
            defaults.update(self.store.checkpoint())
        return StatisticalEvidenceStore(**{**defaults, **kwargs})

    def acquire(self, value, *, at):
        self.fixture.now = self.fixture.fixture.now = at
        self.fixture.data = self.fixture.acquire_data(value)
        return self.fixture.attest()

    def test_retained_packet_selects_exact_values_and_replays_after_restart_without_writes(self):
        receipt = self.store.retain(self.source)
        self.assertEqual("CURRENT", receipt["status"])
        selected = self.store.select(receipt["evidence_id"])
        body = json.loads(selected["content"])
        self.assertEqual([10.0, 12.5], [r["value_thousand_tonnes"] for r in body["observations"]])
        self.assertEqual("NOT_RESOLVED", body["resolution"])
        before = self.path.read_bytes()
        reopened = self.open_store()
        self.assertTrue(reopened.retain(self.source)["replay"])
        self.assertEqual([receipt["evidence_id"]], [r["evidence_id"] for r in reopened.history()])
        selected["content"] = "changed by caller"
        self.assertEqual(self.source, reopened.select(receipt["evidence_id"]))
        self.assertEqual(before, self.path.read_bytes())

    def test_expired_data_is_still_historical_but_cannot_be_selected_or_replayed(self):
        receipt = self.store.retain(self.source)
        before = self.path.read_bytes()
        self.fixture.now = NOW + 86400
        current = self.open_store().history()[0]
        self.assertEqual("NOT_CURRENT", current["status"])
        self.assertNotIn("content", current)
        with self.assertRaisesRegex(StatisticalRetentionViolation, "NOT_CURRENT"):
            self.store.select(receipt["evidence_id"])
        with self.assertRaises(ContractViolation):
            self.store.retain(self.source)
        self.assertEqual(before, self.path.read_bytes())

    def test_current_authority_rotation_withdraws_old_packet_and_expiry_cannot_reinstate_it(self):
        receipt = self.store.retain(self.source)
        self.fixture.now = NOW + 1
        self.fixture.approve_fixture(ttl=1)
        self.assertEqual("NOT_CURRENT", self.store.history()[0]["status"])
        self.fixture.now = NOW + 3
        with self.assertRaisesRegex(StatisticalRetentionViolation, "SUPERSEDED"):
            self.store.select(receipt["evidence_id"])

    def test_latest_publisher_release_not_latest_collection_controls_selection(self):
        first = self.store.retain(self.source)
        new = self.acquire({**dataset(), "updated": "2025-02-15T12:00:00Z", "value": [20.0, 15.0]}, at=NOW + 1)
        latest = self.store.retain(new)
        old_download = self.acquire(dataset(), at=NOW + 2)
        older = self.store.retain(old_download)
        self.assertEqual("CURRENT", latest["status"])
        self.assertEqual("NOT_CURRENT", older["status"])
        self.assertEqual(new, self.store.select(latest["evidence_id"]))
        with self.assertRaisesRegex(StatisticalRetentionViolation, "SUPERSEDED"):
            self.store.select(first["evidence_id"])

    def test_equal_publisher_instant_different_raw_data_withholds_both(self):
        first = self.store.retain(self.source)
        # Same UTC instant, not a lexicographically later release.
        other = self.acquire({**dataset(), "updated": "2025-01-15T13:00:00+0100", "value": [13.0, 10.0]}, at=NOW + 1)
        second = self.store.retain(other)
        self.assertEqual("NOT_CURRENT", second["status"])
        self.assertEqual({"LATEST_RELEASE_AMBIGUOUS"}, {r["verification_reason"] for r in self.store.history()})
        for receipt in (first, second):
            with self.assertRaisesRegex(StatisticalRetentionViolation, "AMBIGUOUS"):
                self.store.select(receipt["evidence_id"])

    def test_same_raw_release_recollection_selects_newest_collection_only(self):
        first = self.store.retain(self.source)
        new = self.acquire(dataset(), at=NOW + 1)
        second = self.store.retain(new)
        self.assertEqual(new, self.store.select(second["evidence_id"]))
        with self.assertRaisesRegex(StatisticalRetentionViolation, "SUPERSEDED"):
            self.store.select(first["evidence_id"])

    def test_stale_newest_release_does_not_fall_back_to_fresher_older_publication(self):
        bounded = self.open_store(evidence_max_age=5)
        newest = bounded.retain(self.source)
        older = self.acquire({**dataset(), "updated": "2024-01-15T12:00:00Z"}, at=NOW + 4)
        previous = bounded.retain(older)
        self.fixture.now = NOW + 6
        self.assertTrue(self.fixture.verifier.verify(older, now=self.fixture.now)[0])
        history = bounded.history()
        self.assertEqual(["NOT_CURRENT", "NOT_CURRENT"], [r["status"] for r in history])
        self.assertIn("SOURCE_STALE", history[0]["verification_reason"])
        for identity in (newest["evidence_id"], previous["evidence_id"]):
            with self.assertRaisesRegex(StatisticalRetentionViolation, "NOT_CURRENT"):
                bounded.select(identity)

    def test_timezone_unspecified_and_unrepresentable_utc_withhold_selection(self):
        for index, timestamp in enumerate(("2025-01-15", "0001-01-01T00:00:00+2359")):
            separate = self.open_store(path=self.fixture.root / ("unordered-" + str(index) + ".json"))
            source = self.acquire({**dataset(), "updated": timestamp}, at=NOW + index + 1)
            receipt = separate.retain(source)
            self.assertEqual("PUBLISHER_TIME_UNORDERED", receipt["verification_reason"])
            with self.assertRaisesRegex(StatisticalRetentionViolation, "UNORDERED"):
                separate.select(receipt["evidence_id"])

    def test_invalid_signed_body_missing_approval_and_wrong_format_do_not_write(self):
        forged = self.fixture.issuer.attest({**self.source, "content": "{}"})
        with self.assertRaises(ContractViolation):
            self.store.retain(forged)
        self.assertFalse(self.path.exists())
        control = self.fixture.control_store("empty-control")
        with self.assertRaises(ContractViolation):
            self.open_store(control=control).retain(self.source)
        self.assertFalse(self.path.exists())

    def test_tampered_chain_dependency_missing_dependency_and_wrong_keys_fail_closed(self):
        self.store.retain(self.source)
        original = self.path.read_bytes()
        document = json.loads(original)
        document["records"][0]["admitted_at"] += 1
        self.path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(ContractViolation):
            self.store.history()
        self.path.write_bytes(original)
        for key in ("integrity_key", "evidence_keys"):
            wrong = {key: b"w" * 32 if key == "integrity_key" else {"fixture-issuer": b"w" * 32}}
            with self.assertRaises(ContractViolation):
                self.open_store(**wrong).history()
        content = self.fixture.quarantine.root / self.fixture.metadata / "content.bin"
        saved = content.read_bytes()
        content.write_bytes(saved + b"tampered")
        with self.assertRaises(ContractViolation):
            self.store.history()
        content.unlink()
        with self.assertRaises(ContractViolation):
            self.store.history()

    def test_data_only_restoration_under_original_keys_recovers_selection(self):
        receipt = self.store.retain(self.source)
        with TemporaryDirectory() as folder:
            restored = Path(folder) / "restored"
            copytree(self.fixture.root, restored)
            quarantine = ResearchQuarantine(restored / self.fixture.quarantine.root.relative_to(self.fixture.root))
            control = SourceControlStore(restored / self.fixture.control.path.name,
                binding_keys={"fixture-review": admission.BINDING_KEY}, integrity_key=admission.CONTROL_KEY,
                clock=lambda: self.fixture.now)
            recovered = self.open_store(path=restored / self.path.name, quarantine=quarantine, control=control)
            self.assertEqual(self.source, recovered.select(receipt["evidence_id"]))
            self.assertTrue(recovered.retain(self.source)["replay"])
            control.path.write_bytes(b"{}")
            with self.assertRaises(ContractViolation):
                recovered.select(receipt["evidence_id"])

    def test_failed_atomic_replace_preserves_prior_history_and_retry_has_one_append(self):
        first = self.store.retain(self.source)
        before = self.path.read_bytes()
        new = self.acquire({**dataset(), "updated": "2025-02-15T12:00:00Z"}, at=NOW + 1)
        def fail(stage):
            self.assertEqual("BEFORE_ATOMIC_REPLACE", stage)
            raise OSError("injected before replacement")
        self.store.failure_injector = fail
        with self.assertRaises(ContractViolation):
            self.store.retain(new)
        self.assertEqual(before, self.path.read_bytes())
        self.store.failure_injector = None
        result = self.store.retain(new)
        self.assertEqual(2, len(self.open_store().history()))
        self.assertEqual(new, self.open_store().select(result["evidence_id"]))
        self.assertEqual("NOT_CURRENT", self.store.history()[0]["status"])

    def test_write_time_expiry_retains_history_without_returning_current(self):
        def expire(_):
            self.fixture.now = NOW + 86400
        self.store.failure_injector = expire
        receipt = self.store.retain(self.source)
        self.assertEqual("NOT_CURRENT", receipt["status"])
        self.assertEqual("NOT_CURRENT", self.open_store().history()[0]["status"])
        with self.assertRaisesRegex(StatisticalRetentionViolation, "NOT_CURRENT"):
            self.store.select(receipt["evidence_id"])

    def test_slow_read_expiry_and_rotation_withhold_selected_packet(self):
        receipt = self.store.retain(self.source)
        original = self.store._history.verify
        def expire(source, *, clock):
            result = original(source, clock=clock)
            self.fixture.now = NOW + 86400
            return result
        with patch.object(self.store._history, "verify", side_effect=expire):
            with self.assertRaises(ContractViolation):
                self.store.select(receipt["evidence_id"])
        self.fixture.now = NOW
        rotated = False
        def rotate(source, *, clock):
            nonlocal rotated
            result = original(source, clock=clock)
            if not rotated:
                rotated = True
                self.fixture.now = NOW + 1
                self.fixture.approve_fixture()
            return result
        with patch.object(self.store._history, "verify", side_effect=rotate):
            with self.assertRaises(ContractViolation):
                self.store.select(receipt["evidence_id"])

    def test_capacity_config_path_key_and_legacy_consumer_isolation(self):
        limited = self.open_store(max_records=1)
        limited.retain(self.source)
        self.assertTrue(limited.retain(self.source)["replay"])
        next_source = self.acquire({**dataset(), "updated": "2025-02-15T12:00:00Z"}, at=NOW + 1)
        with self.assertRaises(ContractViolation):
            limited.retain(next_source)
        for path in (self.fixture.control.path, self.fixture.quarantine.root / "evidence.json"):
            with self.assertRaisesRegex(StatisticalRetentionViolation, "PATH_COLLISION"):
                self.open_store(path=path)
        with self.assertRaisesRegex(StatisticalRetentionViolation, "SEPARATE_KEYS"):
            self.open_store(integrity_key=admission.EVIDENCE_KEY)
        legacy = AttestedEvidenceStore(self.path, evidence_keys={"fixture-issuer": admission.EVIDENCE_KEY},
            evidence_scope="BLOCK1_EUROPE_MARITIME_INTELLIGENCE", evidence_max_age=86400,
            evidence_claims=frozenset((admission.CLAIM,)), integrity_key=INTEGRITY_KEY,
            clock=lambda: self.fixture.now, max_records=1)
        with self.assertRaises(ContractViolation):
            legacy.runtime_records(now=self.fixture.now)

    def test_selection_identity_and_trusted_clock_cannot_be_replaced_by_past_time(self):
        receipt = self.store.retain(self.source)
        for identity in (None, True, "other:abc", "eurostat:not-retained"):
            with self.assertRaises(ContractViolation):
                self.store.select(identity)
        with self.assertRaises(TypeError):
            self.store.select(receipt["evidence_id"], now=NOW)
        self.fixture.now = NOW - 1
        with self.assertRaisesRegex(StatisticalRetentionViolation, "CLOCK_REGRESSED"):
            self.store.history()
        self.fixture.now = True
        with self.assertRaises(ContractViolation):
            self.store.history()

    def test_expiry_during_last_history_reread_is_caught_by_return_fence(self):
        receipt = self.store.retain(self.source)
        original = self.store._history._load_unlocked
        reads = 0
        def delay():
            nonlocal reads
            records = original()
            reads += 1
            if reads == 3:
                self.fixture.now = NOW + 86400
            return records
        with patch.object(self.store._history, "_load_unlocked", side_effect=delay):
            with self.assertRaisesRegex(StatisticalRetentionViolation, "READ_EXPIRED"):
                self.store.select(receipt["evidence_id"])

    def test_replacing_valid_history_with_older_signed_copy_cannot_restore_old_head(self):
        first = self.store.retain(self.source)
        older_copy = self.path.read_bytes()
        new = self.acquire({**dataset(), "updated": "2025-02-15T12:00:00Z"}, at=NOW + 1)
        latest = self.store.retain(new)
        self.assertEqual(new, self.store.select(latest["evidence_id"]))
        checkpoint = self.store.checkpoint()
        self.path.write_bytes(older_copy)
        with self.assertRaisesRegex(StatisticalRetentionViolation, "HISTORY_CHECKPOINT"):
            self.store.select(first["evidence_id"])
        with self.assertRaisesRegex(StatisticalRetentionViolation, "HISTORY_CHECKPOINT"):
            self.open_store(**checkpoint).select(first["evidence_id"])

    def test_replacing_valid_authority_with_older_signed_copy_cannot_restore_grant(self):
        first = self.store.retain(self.source)
        older_authority = self.fixture.control.path.read_bytes()
        self.fixture.now = NOW + 1
        self.fixture.approve_fixture()
        self.assertEqual("NOT_CURRENT", self.store.history()[0]["status"])
        checkpoint = self.store.checkpoint()
        self.fixture.control.path.write_bytes(older_authority)
        with self.assertRaisesRegex(StatisticalRetentionViolation, "AUTHORITY_CHECKPOINT"):
            self.store.select(first["evidence_id"])
        with self.assertRaisesRegex(StatisticalRetentionViolation, "AUTHORITY_CHECKPOINT"):
            self.open_store(**checkpoint).select(first["evidence_id"])

    def test_missing_history_with_known_checkpoint_cannot_create_new_genesis(self):
        self.store.retain(self.source)
        checkpoint = self.store.checkpoint()
        self.path.unlink()
        with self.assertRaisesRegex(StatisticalRetentionViolation, "HISTORY_CHECKPOINT"):
            self.open_store(**checkpoint).retain(self.source)
        self.assertFalse(self.path.exists())

    def test_reopening_existing_history_requires_external_checkpoint(self):
        self.store.retain(self.source)
        with self.assertRaisesRegex(StatisticalRetentionViolation, "HISTORY_CHECKPOINT_REQUIRED"):
            self.open_store(history_checkpoint=None)
        for checkpoint in (True, "", "not-a-hash"):
            with self.assertRaisesRegex(StatisticalRetentionViolation, "CHECKPOINT_INVALID"):
                self.open_store(control_checkpoint=checkpoint)
        with self.assertRaisesRegex(StatisticalRetentionViolation, "AUTHORITY_CHECKPOINT"):
            self.open_store(control_checkpoint="f" * 64).history()
