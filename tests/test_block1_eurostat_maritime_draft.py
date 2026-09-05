import unittest

from sictra_block1 import ContractViolation, EvidenceIssuer, SourceGateway, SourceRegistration


NOW = 10_000
EVIDENCE_KEY = b"e" * 32


def eurostat_maritime_draft():
    return SourceRegistration(
        "eurostat",
        "Eurostat / European Commission",
        "BLOCK1_EUROPE_MARITIME_INTELLIGENCE",
        ("ec.europa.eu",),
        frozenset((
            "maritime_freight_weight_thousand_tonnes",
            "maritime_freight_load_unload_split",
            "maritime_freight_nuts2_coverage",
        )),
        "MANUAL_SOURCE_BUNDLE",
        131_072,
        "PROPOSED",
    )


class EurostatMaritimeDraftTests(unittest.TestCase):
    def test_draft_declares_a_narrow_manual_scope(self):
        draft = eurostat_maritime_draft()
        self.assertEqual(draft.status, "PROPOSED")
        self.assertEqual(draft.allowed_hosts, ("ec.europa.eu",))
        self.assertEqual(draft.max_content_bytes, 131_072)
        self.assertEqual(draft.access_method, "MANUAL_SOURCE_BUNDLE")

    def test_proposed_draft_cannot_attest_a_real_or_fixture_bundle(self):
        gateway = SourceGateway(
            registrations=(eurostat_maritime_draft(),),
            issuer=EvidenceIssuer("gateway", EVIDENCE_KEY),
            binding_keys={},
            bindings={},
            now=NOW,
        )
        bundle = {
            "source_id": "eurostat",
            "source_url": "https://ec.europa.eu/eurostat/cache/metadata/en/mar_esms.htm",
            "content": "fixture only; no source content has been ingested",
            "observed_at": NOW - 1,
            "claim_key": "maritime_freight_weight_thousand_tonnes",
            "polarity": 1,
            "correlation_id": "eurostat-draft-001",
        }
        with self.assertRaises(ContractViolation):
            gateway.attest_manual_bundle(bundle, now=NOW)


if __name__ == "__main__":
    unittest.main()
