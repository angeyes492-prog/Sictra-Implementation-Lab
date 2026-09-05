import unittest

from sictra_block1 import (
    ContractViolation,
    EvidenceIssuer,
    SourceGateway,
    SourceRegistration,
)


NOW = 1_700_000_000


def unctad_datahub_draft() -> SourceRegistration:
    return SourceRegistration(
        source_id="unctad",
        publisher="UN Trade and Development — Data Hub",
        scope="BLOCK1_GLOBAL_MARITIME_INTELLIGENCE",
        allowed_hosts=("unctadstat.unctad.org",),
        claim_keys=frozenset((
            "liner_shipping_connectivity",
            "port_call_performance",
            "container_port_throughput",
        )),
        access_method="MANUAL_SOURCE_BUNDLE",
        max_content_bytes=131_072,
        status="PROPOSED",
    )


class UnctadDataHubDraftTests(unittest.TestCase):
    def test_draft_preserves_the_narrow_host_claim_and_byte_bounds(self):
        draft = unctad_datahub_draft()
        self.assertEqual(draft.allowed_hosts, ("unctadstat.unctad.org",))
        self.assertEqual(
            draft.claim_keys,
            frozenset((
                "liner_shipping_connectivity",
                "port_call_performance",
                "container_port_throughput",
            )),
        )
        self.assertEqual(draft.max_content_bytes, 131_072)
        self.assertEqual(draft.status, "PROPOSED")

    def test_proposed_draft_cannot_admit_a_manual_bundle_without_approval_binding(self):
        draft = unctad_datahub_draft()
        gateway = SourceGateway(
            registrations=(draft,),
            issuer=EvidenceIssuer("test-gateway", b"e" * 32),
            binding_keys={},
            bindings={},
            now=NOW,
        )
        with self.assertRaises(ContractViolation):
            gateway.attest_manual_bundle(
                {
                    "source_id": "unctad",
                    "source_url": "https://unctadstat.unctad.org/EN/FAQ.html",
                    "content": "Synthetic test payload only; not a source observation.",
                    "observed_at": NOW - 1,
                    "claim_key": "liner_shipping_connectivity",
                    "polarity": 1,
                    "correlation_id": "synthetic-regression-only",
                },
                now=NOW,
            )


if __name__ == "__main__":
    unittest.main()
