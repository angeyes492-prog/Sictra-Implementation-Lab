from dataclasses import replace
from hashlib import sha256
import hmac
import json
import unittest

from sictra_block1 import ContractViolation, EvidenceIssuer, SourceApprovalRecord, SourceBindingIssuer, SourceGateway, SourceRegistration, source_approval_fingerprint


NOW = 10_000
KEY = b"b" * 32
EVIDENCE_KEY = b"e" * 32


def registration(**changes):
    value = SourceRegistration("sample-public-source", "Sample public source", "intelligence", ("source.example",), frozenset(("logistics-connectivity",)), "MANUAL_SOURCE_BUNDLE", 512, "BOUND")
    return replace(value, **changes) if changes else value


def approval(**changes):
    value = SourceApprovalRecord("sample-public-source", "reviewer-01", NOW - 1, "review://terms/sample-public-source", ("source.example",), frozenset(("logistics-connectivity",)), "MANUAL_SOURCE_BUNDLE", 512, "APPROVED")
    return replace(value, **changes) if changes else value


def gateway(*, binding=None, now=NOW):
    value = registration()
    token = SourceBindingIssuer("review-control", KEY).issue(value, approval(), now=NOW, ttl=100) if binding is None else binding
    return SourceGateway(registrations=(value,), issuer=EvidenceIssuer("gateway", EVIDENCE_KEY), binding_keys={"review-control": KEY}, bindings={"sample-public-source": token}, now=now)


def resign(binding):
    material = json.dumps({key: value for key, value in binding.items() if key != "signature"}, sort_keys=True, separators=(",", ":")).encode()
    binding["signature"] = hmac.new(KEY, material, sha256).hexdigest()
    return binding


class SourceGatewayTests(unittest.TestCase):
    def test_content_is_preserved_and_hashed_without_silent_trimming(self):
        content = "  observation\n"
        source = gateway().attest_manual_bundle(self.bundle(content=content), now=NOW)
        self.assertEqual(source["content"], content)
        self.assertEqual(source["content_sha256"], sha256(content.encode()).hexdigest())

    def test_limit_applies_to_original_utf8_payload(self):
        for content in (" " * 512 + "x", "é" * 257):
            with self.subTest(content_bytes=len(content.encode())):
                with self.assertRaises(ContractViolation):
                    gateway().attest_manual_bundle(self.bundle(content=content), now=NOW)

    def test_boolean_ttl_and_non_integer_polarities_are_rejected(self):
        with self.assertRaises(ContractViolation):
            SourceBindingIssuer("review-control", KEY).issue(registration(), approval(), now=NOW, ttl=True)
        for polarity in (1.0, -1.0, [], {}):
            with self.subTest(polarity=polarity):
                with self.assertRaises(ContractViolation):
                    gateway().attest_manual_bundle(self.bundle(polarity=polarity), now=NOW)

    def bundle(self, **changes):
        value = {"source_id": "sample-public-source", "source_url": "https://source.example/report", "content": "observation", "observed_at": NOW - 1, "claim_key": "logistics-connectivity", "polarity": 1, "correlation_id": "report-1"}
        value.update(changes)
        return value

    def test_signed_bound_source_attests_manual_bundle(self):
        source = gateway().attest_manual_bundle(self.bundle(), now=NOW)
        self.assertEqual(source["root_provenance"], "gateway-source:sample-public-source")
        self.assertEqual(source["ingestion_method"], "MANUAL_SOURCE_BUNDLE")
        self.assertEqual(source["source_approval_fingerprint"], source_approval_fingerprint(approval()))
        self.assertEqual(len(source["source_binding_fingerprint"]), 64)

    def test_binding_cryptographically_identifies_the_exact_human_approval(self):
        issuer = SourceBindingIssuer("review-control", KEY)
        first = issuer.issue(registration(), approval(), now=NOW, ttl=10)
        second = issuer.issue(
            registration(), approval(reviewer_id="reviewer-02"), now=NOW, ttl=10
        )
        self.assertEqual(first["approval_fingerprint"], source_approval_fingerprint(approval()))
        self.assertNotEqual(first["approval_fingerprint"], second["approval_fingerprint"])
        altered = dict(first)
        altered["approval_fingerprint"] = "0" * 64
        with self.assertRaises(ContractViolation):
            gateway(binding=altered)
        malformed = dict(first)
        malformed["approval_fingerprint"] = "z" * 64
        with self.assertRaises(ContractViolation):
            gateway(binding=resign(malformed))
        with self.assertRaises(ContractViolation):
            source_approval_fingerprint("not-an-approval")

    def test_missing_tampered_or_expired_binding_fails_closed(self):
        value = registration()
        with self.assertRaises(ContractViolation):
            SourceGateway(registrations=(value,), issuer=EvidenceIssuer("gateway", EVIDENCE_KEY), binding_keys={"review-control": KEY}, bindings={}, now=NOW)
        token = SourceBindingIssuer("review-control", KEY).issue(value, approval(), now=NOW, ttl=1)
        with self.assertRaises(ContractViolation):
            gateway(binding=token, now=NOW + 2)
        altered = dict(SourceBindingIssuer("review-control", KEY).issue(value, approval(), now=NOW, ttl=10))
        altered["access_method"] = "NETWORK_FETCH"
        with self.assertRaises(ContractViolation):
            gateway(binding=altered)
        boolean_time = dict(SourceBindingIssuer("review-control", KEY).issue(value, approval(), now=NOW, ttl=10))
        boolean_time["issued_at"] = True
        with self.assertRaises(ContractViolation):
            gateway(binding=resign(boolean_time))

    def test_rejected_stale_or_mismatched_approval_cannot_issue_binding(self):
        issuer = SourceBindingIssuer("review-control", KEY)
        for record in (approval(decision="REJECTED"), approval(reviewed_at=NOW + 1), approval(allowed_hosts=("other.example",))):
            with self.subTest(record=record):
                with self.assertRaises(ContractViolation):
                    issuer.issue(registration(), record, now=NOW, ttl=10)
        with self.assertRaises(ContractViolation):
            approval(access_method="NETWORK_FETCH")

    def test_url_escape_bundle_mutation_and_network_are_rejected(self):
        guarded = gateway()
        for bundle in (self.bundle(source_url="http://source.example/report"), self.bundle(source_url="https://127.0.0.1/report"), self.bundle(source_url="https://source.example:invalid/report"), self.bundle(claim_key="unknown"), self.bundle(observed_at=NOW + 1), {**self.bundle(), "extra": "x"}):
            with self.subTest(bundle=bundle):
                with self.assertRaises(ContractViolation):
                    guarded.attest_manual_bundle(bundle, now=NOW)
        with self.assertRaises(ContractViolation):
            guarded.fetch_network_source("https://source.example/report")


if __name__ == "__main__":
    unittest.main()
