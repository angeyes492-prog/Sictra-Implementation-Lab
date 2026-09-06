import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from sictra_block1 import (
    AttestedEvidenceStore,
    AttestedEvidenceStoreViolation,
    EvidenceIssuer,
    SourceApprovalRecord,
    SourceBindingIssuer,
    SourceGateway,
    SourceRegistration,
    build_eurostat_manual_bundle,
)
from test_block1_eurostat_maritime_mapper import workbook


NOW = 10_000
BINDING_KEY = b"b" * 32
EVIDENCE_KEY = b"e" * 32
INTEGRITY_KEY = b"i" * 32
SCOPE = "BLOCK1_EUROPE_MARITIME_INTELLIGENCE"
CLAIM = "maritime_freight_weight_thousand_tonnes"
URL = "https://ec.europa.eu/eurostat/databrowser/view/tran_r_mago_nm/default/table"


def observed_source(*, correlation="evidence-001", observed=NOW - 1):
    registration = SourceRegistration(
        "eurostat", "Eurostat / European Commission", SCOPE,
        ("ec.europa.eu",), frozenset((CLAIM,)),
        "MANUAL_SOURCE_BUNDLE", 131_072, "BOUND",
    )
    approval = SourceApprovalRecord(
        "eurostat", "PROJECT_OWNER", NOW - 2,
        "evidence/block1_eurostat_maritime_registration_draft_v0.1.md",
        registration.allowed_hosts, registration.claim_keys,
        registration.access_method, registration.max_content_bytes, "APPROVED",
    )
    binding = SourceBindingIssuer("review-control", BINDING_KEY).issue(
        registration, approval, now=NOW - 2, ttl=100,
    )
    gateway = SourceGateway(
        registrations=(registration,), issuer=EvidenceIssuer("gateway", EVIDENCE_KEY),
        binding_keys={"review-control": BINDING_KEY},
        bindings={"eurostat": binding}, now=NOW,
    )
    bundle = build_eurostat_manual_bundle(
        "eurostat.xlsx", workbook(), "COUNTRY", source_url=URL,
        observed_at=observed, correlation_id=correlation,
    )
    return gateway.attest_manual_bundle(bundle, now=NOW)


class AttestedEvidenceStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.path = Path(self.temp.name) / "evidence.json"
        self.current = NOW
        self.store = AttestedEvidenceStore(
            self.path, evidence_keys={"gateway": EVIDENCE_KEY},
            evidence_scope=SCOPE, evidence_max_age=10,
            evidence_claims=frozenset((CLAIM,)), integrity_key=INTEGRITY_KEY,
            clock=lambda: self.current,
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_persists_replays_reopens_and_returns_defensive_runtime_evidence(self):
        source = observed_source()
        receipt = self.store.persist(source)
        self.assertEqual(receipt["status"], "CURRENT")
        self.assertEqual(receipt["verification_reason"], "SOURCE_VERIFIED")
        self.assertTrue(self.store.persist(source)["replay"])
        self.assertEqual(len(self.store.list_receipts(now=NOW)), 1)

        reopened = AttestedEvidenceStore(
            self.path, evidence_keys={"gateway": EVIDENCE_KEY},
            evidence_scope=SCOPE, evidence_max_age=10,
            evidence_claims=frozenset((CLAIM,)), integrity_key=INTEGRITY_KEY,
            clock=lambda: NOW,
        )
        runtime = reopened.runtime_records(now=NOW)
        self.assertEqual(runtime, [source])
        runtime[0]["content"] = "mutated"
        self.assertEqual(reopened.runtime_records(now=NOW), [source])

    def test_stale_record_remains_history_but_is_excluded_from_runtime(self):
        self.store.persist(observed_source())
        receipt = self.store.list_receipts(now=NOW + 10)[0]
        self.assertEqual(receipt["status"], "NOT_CURRENT")
        self.assertEqual(receipt["verification_reason"], "SOURCE_STALE")
        self.assertEqual(self.store.runtime_records(now=NOW + 10), [])

    def test_resigned_bad_content_hash_lineage_and_bundle_fail_closed(self):
        issuer = EvidenceIssuer("gateway", EVIDENCE_KEY)
        source = observed_source()
        unsigned = {key: value for key, value in source.items() if key != "attestation"}
        mutations = (
            {"content_sha256": "0" * 64},
            {"source_binding_fingerprint": "z" * 64},
            {"root_provenance": "gateway-source:other"},
            {"content": "{}"},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(AttestedEvidenceStoreViolation):
                self.store.persist(issuer.attest({**unsigned, **mutation}))
        self.assertFalse(self.path.exists())

    def test_disk_tampering_wrong_evidence_key_and_config_drift_fail_closed(self):
        self.store.persist(observed_source())
        document = json.loads(self.path.read_text(encoding="utf-8"))
        document["records"][0]["evidence"]["publisher"] = "substitute"
        self.path.write_text(json.dumps(document), encoding="utf-8")
        configurations = (
            ({"gateway": EVIDENCE_KEY}, INTEGRITY_KEY, SCOPE, 10),
            ({"gateway": b"z" * 32}, INTEGRITY_KEY, SCOPE, 10),
            ({"gateway": EVIDENCE_KEY}, b"z" * 32, SCOPE, 10),
            ({"gateway": EVIDENCE_KEY}, INTEGRITY_KEY, "other-scope", 10),
            ({"gateway": EVIDENCE_KEY}, INTEGRITY_KEY, SCOPE, 11),
        )
        for keys, integrity, scope, age in configurations:
            with self.subTest(scope=scope, age=age), self.assertRaises(AttestedEvidenceStoreViolation):
                AttestedEvidenceStore(
                    self.path, evidence_keys=keys, evidence_scope=scope,
                    evidence_max_age=age, evidence_claims=frozenset((CLAIM,)),
                    integrity_key=integrity, clock=lambda: NOW,
                ).list_receipts(now=NOW)

    def test_atomic_failure_and_capacity_do_not_damage_prior_evidence(self):
        self.store.persist(observed_source())
        prior = self.path.read_bytes()
        self.store.failure_injector = lambda point: (_ for _ in ()).throw(OSError(point))
        with self.assertRaises(AttestedEvidenceStoreViolation):
            self.store.persist(observed_source(correlation="evidence-002"))
        self.assertEqual(self.path.read_bytes(), prior)

        limited = AttestedEvidenceStore(
            Path(self.temp.name) / "limited.json",
            evidence_keys={"gateway": EVIDENCE_KEY}, evidence_scope=SCOPE,
            evidence_max_age=10, evidence_claims=frozenset((CLAIM,)),
            integrity_key=INTEGRITY_KEY, clock=lambda: NOW, max_records=1,
        )
        limited.persist(observed_source())
        with self.assertRaises(AttestedEvidenceStoreViolation):
            limited.persist(observed_source(correlation="evidence-003"))


if __name__ == "__main__":
    unittest.main()
