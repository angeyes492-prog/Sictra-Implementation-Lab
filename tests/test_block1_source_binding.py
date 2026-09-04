from dataclasses import replace
import unittest

from sictra_block1 import (
    ContractViolation, SourceApprovalRecord, SourceBindingIssuer,
    SourceBindingVerifier, SourceCandidate, SourceRegistration,
)


NOW = 70_000
KEY = b"k" * 32


def candidate():
    return SourceCandidate(
        source_id="source-a",
        publisher="Publisher A",
        candidate_hosts=("source-a.example.org", "data.source-a.example.org"),
        regions=frozenset(("GLOBAL",)),
        domains=frozenset(("TRADE",)),
        cadence="MONTHLY",
    )


def approval(**changes):
    value = SourceApprovalRecord(
        source_id="source-a",
        reviewer_id="reviewer-a",
        reviewed_at=NOW - 1,
        terms_evidence_ref="review://source-a/terms",
        approved_hosts=("source-a.example.org",),
        approved_claim_keys=frozenset(("trade-flow",)),
        max_content_bytes=2048,
        access_method="MANUAL_SOURCE_BUNDLE",
        decision="APPROVED",
    )
    return replace(value, **changes) if changes else value


def registration(**changes):
    value = SourceRegistration(
        source_id="source-a",
        publisher="Publisher A",
        scope="intelligence",
        allowed_hosts=("source-a.example.org",),
        claim_keys=frozenset(("trade-flow",)),
        status="BOUND",
        max_content_bytes=2048,
    )
    return replace(value, **changes) if changes else value


class SourceBindingTests(unittest.TestCase):
    def setUp(self):
        self.issuer = SourceBindingIssuer("review-control", KEY)
        self.verifier = SourceBindingVerifier({"review-control": KEY}, "intelligence")

    def test_signed_authorization_matches_exact_configuration(self):
        token = self.issuer.issue(approval=approval(), candidate=candidate(), scope="intelligence", now=NOW, ttl=10)
        self.assertEqual(self.verifier.verify(token, registration(), now=NOW), (True, "SOURCE_BINDING_VERIFIED"))

    def test_tamper_expiry_and_configuration_expansion_fail_closed(self):
        token = self.issuer.issue(approval=approval(), candidate=candidate(), scope="intelligence", now=NOW, ttl=10)
        altered = replace(token, max_content_bytes=2049)
        self.assertEqual(self.verifier.verify(altered, registration(), now=NOW)[0], False)
        self.assertEqual(self.verifier.verify(token, registration(), now=NOW + 11), (False, "SOURCE_BINDING_NOT_CURRENT"))
        expanded = registration(allowed_hosts=("source-a.example.org", "data.source-a.example.org"))
        self.assertEqual(self.verifier.verify(token, expanded, now=NOW), (False, "SOURCE_BINDING_HOST_MISMATCH"))

    def test_rejected_approval_cannot_receive_a_binding_authorization(self):
        with self.assertRaises(ContractViolation):
            self.issuer.issue(
                approval=approval(decision="REJECTED"), candidate=candidate(),
                scope="intelligence", now=NOW, ttl=10,
            )


if __name__ == "__main__":
    unittest.main()
