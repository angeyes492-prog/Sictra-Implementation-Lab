from dataclasses import replace
import unittest

from sictra_block1 import ContractViolation, SourceApprovalRecord, SourceCandidate


NOW = 50_000


def source_candidate(source_id="unctad"):
    return SourceCandidate(
        source_id=source_id,
        publisher="UN Trade and Development",
        candidate_hosts=("unctad.org",),
        regions=frozenset(("GLOBAL",)),
        domains=frozenset(("MARITIME",)),
        cadence="ANNUAL",
    )


def approval(**changes):
    value = SourceApprovalRecord(
        source_id="unctad",
        reviewer_id="reviewer-01",
        reviewed_at=NOW - 1,
        terms_evidence_ref="review://terms/unctad/2026-08-29",
        approved_hosts=("unctad.org",),
        approved_claim_keys=frozenset(("logistics-connectivity",)),
        max_content_bytes=1024,
        access_method="MANUAL_SOURCE_BUNDLE",
        decision="APPROVED",
    )
    return replace(value, **changes) if changes else value


class SourceApprovalTests(unittest.TestCase):
    def test_approved_record_is_ready_for_configuration_but_candidate_stays_proposed(self):
        result = approval().readiness_for(source_candidate(), now=NOW)
        self.assertEqual(result["status"], "READY_FOR_GATEWAY_CONFIGURATION_REVIEW")
        self.assertEqual(result["candidate_status"], "PROPOSED")
        self.assertEqual(result["access_method"], "MANUAL_SOURCE_BUNDLE")
        self.assertFalse(hasattr(approval(), "to_source_registration"))

    def test_rejected_record_remains_not_approved(self):
        result = approval(decision="REJECTED").readiness_for(source_candidate(), now=NOW)
        self.assertEqual(result["status"], "NOT_APPROVED")

    def test_rejects_unsafe_values_and_unsupported_activation_method(self):
        with self.assertRaises(ContractViolation):
            approval(approved_hosts=("127.0.0.1",))
        with self.assertRaises(ContractViolation):
            approval(approved_claim_keys=frozenset())
        with self.assertRaises(ContractViolation):
            approval(access_method="HTTP_CONNECTOR")
        with self.assertRaises(ContractViolation):
            approval(decision="BOUND")

    def test_rejects_future_review_identity_substitution_and_host_expansion(self):
        with self.assertRaises(ContractViolation):
            approval(reviewed_at=NOW + 1).readiness_for(source_candidate(), now=NOW)
        with self.assertRaises(ContractViolation):
            approval(source_id="wto").readiness_for(source_candidate(), now=NOW)
        with self.assertRaises(ContractViolation):
            approval(approved_hosts=("other.example",)).readiness_for(source_candidate(), now=NOW)


if __name__ == "__main__":
    unittest.main()
