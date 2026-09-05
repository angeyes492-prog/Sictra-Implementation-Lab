import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from sictra_block1 import (
    EvidenceIssuer,
    SourceApprovalRecord,
    SourceBindingIssuer,
    SourceControlStore,
    SourceControlStoreViolation,
    SourceRegistration,
)


NOW = 10_000
BINDING_KEY = b"b" * 32
INTEGRITY_KEY = b"i" * 32
EVIDENCE_KEY = b"e" * 32


def registration():
    return SourceRegistration(
        "eurostat", "Eurostat / European Commission",
        "BLOCK1_EUROPE_MARITIME_INTELLIGENCE", ("ec.europa.eu",),
        frozenset(("maritime_freight_weight_thousand_tonnes",)),
        "MANUAL_SOURCE_BUNDLE", 131_072, "BOUND",
    )


def approval(*, reviewer="PROJECT_OWNER"):
    item = registration()
    return SourceApprovalRecord(
        item.source_id, reviewer, NOW - 1,
        "evidence/block1_eurostat_maritime_registration_draft_v0.1.md",
        item.allowed_hosts, item.claim_keys, item.access_method,
        item.max_content_bytes, "APPROVED",
    )


def binding(*, issued=NOW, ttl=100, review=None):
    return SourceBindingIssuer("review-control", BINDING_KEY).issue(
        registration(), review or approval(), now=issued, ttl=ttl,
    )


def bundle():
    return {
        "source_id": "eurostat",
        "source_url": "https://ec.europa.eu/eurostat/databrowser/view/tran_r_mago_nm/default/table",
        "content": "bounded observation",
        "observed_at": NOW,
        "claim_key": "maritime_freight_weight_thousand_tonnes",
        "polarity": 1,
        "correlation_id": "eurostat-source-control-test",
    }


class SourceControlStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.path = Path(self.temp.name) / "source-control.json"
        self.current = NOW
        self.store = SourceControlStore(
            self.path, binding_keys={"review-control": BINDING_KEY},
            integrity_key=INTEGRITY_KEY, clock=lambda: self.current,
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_persists_replays_and_builds_gateway_without_storing_secrets(self):
        token = binding()
        receipt = self.store.persist(registration(), approval(), token)
        self.assertEqual(receipt["status"], "ACTIVE")
        self.assertFalse(receipt["replay"])
        self.assertTrue(self.store.persist(registration(), approval(), token)["replay"])
        self.assertEqual(len(self.store.list_records(now=NOW)), 1)
        raw = self.path.read_text(encoding="utf-8")
        self.assertNotIn(BINDING_KEY.decode(), raw)
        self.assertNotIn(INTEGRITY_KEY.decode(), raw)

        reopened = SourceControlStore(
            self.path, binding_keys={"review-control": BINDING_KEY},
            integrity_key=INTEGRITY_KEY, clock=lambda: NOW,
        )
        source = reopened.build_gateway(
            "eurostat", evidence_issuer=EvidenceIssuer("gateway", EVIDENCE_KEY), now=NOW,
        ).attest_manual_bundle(bundle(), now=NOW)
        self.assertEqual(source["source_approval_fingerprint"], token["approval_fingerprint"])
        self.assertEqual(len(source["source_binding_fingerprint"]), 64)

    def test_expired_binding_remains_history_but_cannot_build_gateway(self):
        self.store.persist(registration(), approval(), binding(ttl=1))
        self.assertEqual(self.store.list_records(now=NOW + 2)[0]["status"], "NOT_CURRENT")
        self.assertIsNone(self.store.active_record("eurostat", now=NOW + 2))
        with self.assertRaises(SourceControlStoreViolation):
            self.store.build_gateway(
                "eurostat", evidence_issuer=EvidenceIssuer("gateway", EVIDENCE_KEY),
                now=NOW + 2,
            )

    def test_approval_substitution_and_wrong_keys_fail_closed(self):
        self.store.persist(registration(), approval(), binding())
        document = json.loads(self.path.read_text(encoding="utf-8"))
        document["records"][0]["approval"]["reviewer_id"] = "substitute"
        self.path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(SourceControlStoreViolation):
            self.store.list_records(now=NOW)
        for binding_keys, integrity_key in (
            ({"review-control": b"z" * 32}, INTEGRITY_KEY),
            ({"review-control": BINDING_KEY}, b"z" * 32),
        ):
            with self.subTest(binding_keys=binding_keys, integrity_key=integrity_key):
                with self.assertRaises(SourceControlStoreViolation):
                    SourceControlStore(
                        self.path, binding_keys=binding_keys,
                        integrity_key=integrity_key, clock=lambda: NOW,
                    ).list_records(now=NOW)
        with self.assertRaises(SourceControlStoreViolation):
            SourceControlStore(
                Path(self.temp.name) / "types.json",
                binding_keys={"review-control": BINDING_KEY},
                integrity_key=INTEGRITY_KEY, clock=lambda: NOW,
            ).persist("registration", approval(), binding())

    def test_rotation_is_append_only_and_strictly_monotonic(self):
        self.store.persist(registration(), approval(), binding())
        self.current = NOW + 10
        rotated_approval = approval(reviewer="PROJECT_OWNER_ROTATION")
        rotated = binding(issued=NOW + 10, review=rotated_approval)
        self.store.persist(registration(), rotated_approval, rotated)
        records = self.store.list_records(now=NOW + 10)
        self.assertEqual(len(records), 2)
        self.assertNotEqual(records[0]["approval_fingerprint"], records[1]["approval_fingerprint"])
        with self.assertRaises(SourceControlStoreViolation):
            self.store.persist(
                registration(), approval(reviewer="late-but-old"),
                binding(issued=NOW, review=approval(reviewer="late-but-old")),
            )

    def test_failed_atomic_replace_and_capacity_preserve_prior_state(self):
        self.store.persist(registration(), approval(), binding())
        prior = self.path.read_bytes()
        self.current = NOW + 10
        rotated_approval = approval(reviewer="PROJECT_OWNER_ROTATION")
        self.store.failure_injector = lambda point: (_ for _ in ()).throw(OSError(point))
        with self.assertRaises(SourceControlStoreViolation):
            self.store.persist(
                registration(), rotated_approval,
                binding(issued=NOW + 10, review=rotated_approval),
            )
        self.assertEqual(self.path.read_bytes(), prior)

        limited_path = Path(self.temp.name) / "limited.json"
        limited_time = {"now": NOW}
        limited = SourceControlStore(
            limited_path, binding_keys={"review-control": BINDING_KEY},
            integrity_key=INTEGRITY_KEY, clock=lambda: limited_time["now"], max_records=1,
        )
        limited.persist(registration(), approval(), binding())
        limited_time["now"] = NOW + 1
        with self.assertRaises(SourceControlStoreViolation):
            limited.persist(
                registration(), approval(reviewer="rotation"),
                binding(issued=NOW + 1, review=approval(reviewer="rotation")),
            )


if __name__ == "__main__":
    unittest.main()
