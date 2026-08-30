from dataclasses import replace
import unittest

from sictra_block1 import ContractViolation, EvidenceIssuer, SourceApprovalRecord, SourceBindingIssuer, SourceGateway, SourceRegistration


NOW = 10_000
KEY = b"b" * 32
EVIDENCE_KEY = b"e" * 32


def registration(**changes):
    value = SourceRegistration("unctad", "UN Trade and Development", "intelligence", ("unctad.org",), frozenset(("logistics-connectivity",)), 512, "BOUND")
    return replace(value, **changes) if changes else value


def approval(**changes):
    value = SourceApprovalRecord("unctad", "reviewer-01", NOW - 1, "review://terms/unctad", ("unctad.org",), frozenset(("logistics-connectivity",)), 512, "APPROVED")
    return replace(value, **changes) if changes else value


def gateway(*, binding=None, now=NOW):
    value = registration()
    token = SourceBindingIssuer("review-control", KEY).issue(value, approval(), now=NOW, ttl=100) if binding is None else binding
    return SourceGateway(registrations=(value,), issuer=EvidenceIssuer("gateway", EVIDENCE_KEY), binding_keys={"review-control": KEY}, bindings={"unctad": token}, now=now)


class SourceGatewayTests(unittest.TestCase):
    def bundle(self, **changes):
        value = {"source_id": "unctad", "source_url": "https://unctad.org/report", "content": "observation", "observed_at": NOW - 1, "claim_key": "logistics-connectivity", "polarity": 1, "correlation_id": "report-1"}
        value.update(changes)
        return value

    def test_signed_bound_source_attests_manual_bundle(self):
        source = gateway().attest_manual_bundle(self.bundle(), now=NOW)
        self.assertEqual(source["root_provenance"], "gateway-source:unctad")
        self.assertEqual(source["ingestion_method"], "MANUAL_SOURCE_BUNDLE")

    def test_missing_tampered_or_expired_binding_fails_closed(self):
        value = registration()
        with self.assertRaises(ContractViolation):
            SourceGateway(registrations=(value,), issuer=EvidenceIssuer("gateway", EVIDENCE_KEY), binding_keys={"review-control": KEY}, bindings={}, now=NOW)
        token = SourceBindingIssuer("review-control", KEY).issue(value, approval(), now=NOW, ttl=1)
        with self.assertRaises(ContractViolation):
            gateway(binding=token, now=NOW + 2)
        altered = dict(SourceBindingIssuer("review-control", KEY).issue(value, approval(), now=NOW, ttl=10))
        altered["max_content_bytes"] = 513
        with self.assertRaises(ContractViolation):
            gateway(binding=altered)

    def test_rejected_stale_or_mismatched_approval_cannot_issue_binding(self):
        issuer = SourceBindingIssuer("review-control", KEY)
        for record in (approval(decision="REJECTED"), approval(reviewed_at=NOW + 1), approval(allowed_hosts=("other.example",))):
            with self.subTest(record=record):
                with self.assertRaises(ContractViolation):
                    issuer.issue(registration(), record, now=NOW, ttl=10)

    def test_url_escape_bundle_mutation_and_network_are_rejected(self):
        guarded = gateway()
        for bundle in (self.bundle(source_url="http://unctad.org/report"), self.bundle(source_url="https://127.0.0.1/report"), self.bundle(source_url="https://unctad.org:invalid/report"), self.bundle(claim_key="unknown"), self.bundle(observed_at=NOW + 1), {**self.bundle(), "extra": "x"}):
            with self.subTest(bundle=bundle):
                with self.assertRaises(ContractViolation):
                    guarded.attest_manual_bundle(bundle, now=NOW)
        with self.assertRaises(ContractViolation):
            guarded.fetch_network_source("https://unctad.org/report")


if __name__ == "__main__":
    unittest.main()
