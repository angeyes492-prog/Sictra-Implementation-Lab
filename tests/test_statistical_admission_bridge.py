from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import test_agent_research_acquisition as acquisition
from test_agent_research_acquisition import Response, NOW
from test_research_methodology import html_sections
from test_research_statistics import dataset, raw
from sictra_block1.common import ContractViolation
from sictra_block1.evidence import EvidenceIssuer, EvidenceVerifier
from sictra_block1.manual_bundle_ledger import validate_unattested_manual_bundle
from sictra_block1.research_acquisition import ResearchQuarantine, STATISTICS_RECIPE
from sictra_block1.research_admission import (
    SCOPE, CLAIM, StatisticalAdmissionViolation, prepare_admission_review,
    attest_statistics_candidate, verify_statistics_candidate,
)
from sictra_block1.source_control_store import SourceControlStore
from sictra_block1.source_gateway import SourceRegistration, SourceApprovalRecord, SourceBindingIssuer

BINDING_KEY, CONTROL_KEY, EVIDENCE_KEY = b"b" * 32, b"c" * 32, b"e" * 32


class StatisticalAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = acquisition.AcquisitionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.now = NOW
        self.root = Path(self.fixture.temp.name)
        self.quarantine = self.fixture.session.quarantine
        self.terms = self.fixture.terms()
        self.fixture.response = Response(body=html_sections())
        self.metadata = self.fixture.session.acquire("EUROSTAT_MAR_METADATA", terms_candidate_id=self.terms)["candidate_id"]
        self.data = self.acquire_data(dataset())
        self.control = self.control_store("control")
        self.issuer = EvidenceIssuer("fixture-issuer", EVIDENCE_KEY)
        self.verifier = EvidenceVerifier({"fixture-issuer": EVIDENCE_KEY}, SCOPE, 86400, frozenset((CLAIM,)))

    def acquire_data(self, value, terms=None):
        self.fixture.response = Response(body=raw(value), headers=[("Content-Type", "application/json")])
        return self.fixture.session.acquire(STATISTICS_RECIPE, terms_candidate_id=terms or self.terms)["candidate_id"]

    def control_store(self, name):
        return SourceControlStore(self.root / (name + ".json"), binding_keys={"fixture-review": BINDING_KEY},
                                  integrity_key=CONTROL_KEY, clock=lambda: self.now)

    def approve_fixture(self, *, control=None, scope=SCOPE, terms_ref=None, reviewed=None,
                        claim=CLAIM, host="ec.europa.eu", max_bytes=131072, ttl=100):
        # Explicit fixture authority, never claimed to be actual human review.
        control = control or self.control
        review = self.review()
        registration = SourceRegistration("eurostat", "Eurostat / European Commission", scope,
            (host,), frozenset((claim,)), "MANUAL_SOURCE_BUNDLE", max_bytes, "BOUND")
        approval = SourceApprovalRecord("eurostat", "FIXTURE_ONLY", self.now if reviewed is None else reviewed,
            terms_ref or review["required_approval"]["terms_evidence_ref"], registration.allowed_hosts,
            registration.claim_keys, registration.access_method, registration.max_content_bytes, "APPROVED")
        token = SourceBindingIssuer("fixture-review", BINDING_KEY).issue(registration, approval, now=self.now, ttl=ttl)
        control.persist(registration, approval, token)
        return token

    def review(self, *, clock=None):
        return prepare_admission_review(self.quarantine, self.data, self.metadata, clock=clock or (lambda: self.now))

    def attest(self, *, clock=None):
        return attest_statistics_candidate(self.quarantine, self.data, self.metadata, self.control, self.issuer,
                                           clock=clock or (lambda: self.now))

    def verify(self, source, *, verifier=None, clock=None):
        return verify_statistics_candidate(source, self.quarantine, self.data, self.metadata, self.control,
            verifier or self.verifier, clock=clock or (lambda: self.now))

    def files(self):
        return {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}

    def test_concrete_review_contains_exact_dependencies_and_stays_pending_without_writes(self):
        before = self.files()
        review = self.review()
        self.assertEqual(SCOPE, review["required_registration"]["scope"])
        self.assertEqual("quarantine:" + self.terms + ":" + self.metadata,
                         review["required_approval"]["terms_evidence_ref"])
        self.assertEqual("PENDING", review["required_approval"]["decision"])
        self.assertIsNone(review["required_approval"]["reviewer_id"])
        self.assertEqual("NOT_ADMITTED", review["admission"])
        self.assertEqual([10.0, 12.5], [r["value_thousand_tonnes"] for r in review["data"]["observations"]])
        self.assertEqual(before, self.files())
        reopened = ResearchQuarantine(self.quarantine.root)
        self.assertEqual(review, prepare_admission_review(reopened, self.data, self.metadata, clock=lambda: self.now))

    def test_fixture_approval_attestation_independent_verification_and_restart_are_read_only(self):
        self.approve_fixture()
        before = self.files()
        source = self.attest()
        self.assertEqual((True, "SOURCE_VERIFIED"), self.verifier.verify(source, now=self.now))
        body = json.loads(source["content"])
        self.assertEqual([10.0, 12.5], [r["value_thousand_tonnes"] for r in body["observations"]])
        self.assertEqual(self.data, body["provenance"]["data_candidate_id"])
        self.assertEqual(self.metadata, body["provenance"]["methodology_candidate_id"])
        self.assertEqual("NOT_RESOLVED", body["resolution"])
        result = self.verify(source)
        self.assertEqual("VERIFIED_LOCAL_ADMISSION", result["status"])
        self.assertEqual("NONE", result["runtime_effect"])
        self.control = self.control_store("control")
        self.assertEqual(source, self.attest())
        self.assertEqual(result, self.verify(source))
        self.assertEqual(before, self.files())

    def test_missing_authority_and_legacy_xlsx_scope_never_call_issuer(self):
        with patch.object(self.issuer, "attest", wraps=self.issuer.attest) as emit:
            with self.assertRaisesRegex(StatisticalAdmissionViolation, "MISSING_OR_EXPIRED"):
                self.attest()
            emit.assert_not_called()
        self.approve_fixture(scope="BLOCK1_EUROPE_MARITIME_INTELLIGENCE")
        with self.assertRaisesRegex(StatisticalAdmissionViolation, "SCOPE_MISMATCH"):
            self.attest()

    def test_signed_wrong_terms_claim_host_or_oversized_grant_is_rejected(self):
        variants = [{"terms_ref": "historical-xlsx-terms"}, {"claim": "other_claim"},
                    {"host": "www.example.org"}, {"max_bytes": 8 * 1024 * 1024}]
        for index, args in enumerate(variants):
            self.control = self.control_store("different-" + str(index))
            self.approve_fixture(**args)
            with self.assertRaises(StatisticalAdmissionViolation):
                self.attest()

    def test_review_before_retained_terms_and_tiny_content_limit_reject(self):
        self.approve_fixture(reviewed=NOW - 1)
        with self.assertRaisesRegex(StatisticalAdmissionViolation, "REVIEW_TIME_INVALID"):
            self.attest()
        self.control = self.control_store("tiny")
        self.approve_fixture(max_bytes=100)
        with self.assertRaisesRegex(StatisticalAdmissionViolation, "CONTENT_LIMIT"):
            self.attest()

    def test_binding_expiry_boundary_and_quarantine_expiry_withhold_attestation(self):
        self.approve_fixture(ttl=1)
        source = self.attest()
        self.now = NOW + 1
        with self.assertRaisesRegex(StatisticalAdmissionViolation, "NOT_CURRENT"):
            self.verify(source)
        self.now = NOW + 86400
        with self.assertRaises(ContractViolation):
            self.attest()

    def test_issuer_signed_forged_values_and_extra_fields_cannot_pass_consumer(self):
        self.approve_fixture()
        original = self.attest()
        body = json.loads(original["content"])
        body["observations"][0]["value_thousand_tonnes"] = 999999
        forged = self.issuer.attest({**original, "content": json.dumps(body)})
        self.assertEqual((True, "SOURCE_VERIFIED"), self.verifier.verify(forged, now=self.now))
        with self.assertRaisesRegex(StatisticalAdmissionViolation, "LINEAGE_OR_CONTENT_MISMATCH"):
            self.verify(forged)
        forged = self.issuer.attest({**original, "resolved": True})
        with self.assertRaisesRegex(StatisticalAdmissionViolation, "LINEAGE_OR_CONTENT_MISMATCH"):
            self.verify(forged)
        with self.assertRaisesRegex(StatisticalAdmissionViolation, "ATTESTATION_REJECTED"):
            self.verify({**original, "content": "tampered"})

    def test_tampered_data_terms_metadata_and_control_cannot_be_used(self):
        self.approve_fixture()
        source = self.attest()
        for identity in (self.data, self.terms, self.metadata):
            path = self.quarantine.root / identity / "content.bin"
            original = path.read_bytes()
            path.write_bytes(original + b"tampered")
            with self.assertRaises(ContractViolation):
                self.verify(source)
            path.write_bytes(original)
        path = self.control.path
        document = json.loads(path.read_bytes())
        document["records"][0]["approval"]["reviewer_id"] = "substitution"
        path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(ContractViolation):
            self.verify(source)

    def test_distinct_terms_lineages_cannot_be_combined(self):
        self.fixture.now = NOW + 1
        second_terms = self.fixture.terms()
        self.data = self.acquire_data(dataset(), terms=second_terms)
        self.now = NOW + 1
        with self.assertRaisesRegex(StatisticalAdmissionViolation, "TERMS_LINEAGE_MISMATCH"):
            self.review()

    def test_empty_observed_coverage_and_legacy_consumer_are_rejected(self):
        self.approve_fixture()
        source = self.attest()
        bundle = {key: source[key] for key in ("source_id", "source_url", "content", "observed_at",
                                               "claim_key", "polarity", "correlation_id")}
        with self.assertRaises(ContractViolation):
            validate_unattested_manual_bundle(bundle)
        self.data = self.acquire_data({**dataset(), "value": {}})
        with self.assertRaisesRegex(StatisticalAdmissionViolation, "NO_OBSERVED_VALUES"):
            self.attest()

    def test_signature_age_and_expiry_during_verification_are_rechecked(self):
        self.approve_fixture()
        source = self.attest()
        original = self.verifier.verify
        def expire(record, *, now):
            result = original(record, now=now)
            self.now = NOW + 100
            return result
        with patch.object(self.verifier, "verify", side_effect=expire):
            with self.assertRaisesRegex(StatisticalAdmissionViolation, "NOT_CURRENT"):
                self.verify(source)

    def test_signed_authority_rotation_during_verification_withholds_old_packet(self):
        self.approve_fixture()
        source = self.attest()
        original = self.verifier.verify
        def rotate(record, *, now):
            result = original(record, now=now)
            self.now = NOW + 1
            self.approve_fixture()
            return result
        with patch.object(self.verifier, "verify", side_effect=rotate):
            with self.assertRaisesRegex(StatisticalAdmissionViolation, "INPUT_CHANGED"):
                self.verify(source)

    def test_bad_clocks_and_read_time_regression_reject(self):
        for value in (True, -1, 1.5):
            with self.assertRaisesRegex(StatisticalAdmissionViolation, "CLOCK_INVALID"):
                self.review(clock=lambda: value)
        with self.assertRaisesRegex(StatisticalAdmissionViolation, "CLOCK_REGRESSED"):
            self.review(clock=Mock(side_effect=[NOW + 1, NOW]))

    def test_slow_signing_expiry_does_not_return_admission(self):
        self.approve_fixture(ttl=1)
        original = self.issuer.attest
        def expire(source):
            result = original(source)
            self.now = NOW + 1
            return result
        with patch.object(self.issuer, "attest", side_effect=expire):
            with self.assertRaisesRegex(StatisticalAdmissionViolation, "NOT_CURRENT"):
                self.attest()

    def test_expired_rotation_cannot_resurrect_prior_still_live_grant(self):
        self.approve_fixture(ttl=100)
        prior = self.attest()
        self.now = NOW + 1
        self.approve_fixture(ttl=1)
        self.now = NOW + 3
        # The generic control lookup falls back to the older live token.
        # The statistical contract forbids reinstating superseded authority.
        self.assertIsNotNone(self.control.active_record("eurostat", now=self.now))
        with self.assertRaisesRegex(StatisticalAdmissionViolation, "SUPERSEDED"):
            self.verify(prior)
