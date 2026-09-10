import unittest

from sictra_block1 import ContractViolation, SourceCandidate, source_readiness


class SourcePortfolioTests(unittest.TestCase):
    def test_regional_query_is_proposed_only_and_cannot_claim_evidence(self):
        result = source_readiness(region="AMERICAS", domain="TRADE")
        self.assertEqual(result["status"], "RESEARCH_BLOCKED_PENDING_SOURCE_BINDING")
        self.assertEqual(result["admissible_source_count"], 0)
        source_ids = {item["source_id"] for item in result["candidates"]}
        self.assertIn("cepal", source_ids)
        self.assertIn("sieca", source_ids)
        self.assertNotIn("flexport", source_ids)
        self.assertNotIn("unctad", source_ids)
        self.assertTrue(all(item["status"] == "PROPOSED" for item in result["candidates"]))
        self.assertEqual(result["admissible_source_count"], 0)
        self.assertIn("PUBLIC_ACCESS_IS_NOT_REUSE_PERMISSION", result["non_claims"])

    def test_sieca_remains_available_after_flexport_withdrawal(self):
        regional = source_readiness(region="AMERICAS", domain="TRADE")
        candidates = {item["source_id"]: item for item in regional["candidates"]}
        self.assertEqual(candidates["sieca"]["source_class"], "PUBLIC_INSTITUTIONAL")
        self.assertNotIn("flexport", candidates)
        self.assertEqual(regional["admissible_source_count"], 0)

    def test_eurostat_maritime_coverage_remains_proposed_only(self):
        regional = source_readiness(region="EUROPE", domain="MARITIME")
        candidates = {item["source_id"]: item for item in regional["candidates"]}
        self.assertIn("eurostat", candidates)
        self.assertEqual(candidates["eurostat"]["status"], "PROPOSED")
        self.assertEqual(regional["admissible_source_count"], 0)

    def test_source_registry_exposes_governance_metadata_without_authorizing_ingress(self):
        regional = source_readiness(region="AMERICAS", domain="TRADE")
        candidates = {item["source_id"]: item for item in regional["candidates"]}
        sat = candidates["sat-guatemala"]
        self.assertEqual(sat["source_role"], "E1_CANDIDATE")
        self.assertEqual(sat["license_status"], "PUBLIC_TERMS_UNCLEAR")
        self.assertEqual(sat["access_posture"], "MANUAL_REVIEW_REQUIRED")
        self.assertEqual(sat["allowed_actions"], ["DISCOVER", "REVIEW"])
        self.assertTrue(sat["official_reference"].startswith("https://portal.sat.gob.gt/"))
        self.assertEqual(regional["admissible_source_count"], 0)

    def test_regulatory_candidate_is_discoverable_but_not_admissible(self):
        result = source_readiness(region="AMERICAS", domain="REGULATION")
        candidates = {item["source_id"]: item for item in result["candidates"]}
        self.assertEqual(candidates["wto-eping"]["status"], "PROPOSED")
        self.assertEqual(candidates["wto-eping"]["license_status"], "PUBLIC_TERMS_UNCLEAR")
        self.assertEqual(result["admissible_source_count"], 0)

    def test_candidate_rejects_unrecognized_role_or_reference_outside_declared_host(self):
        base = {
            "source_id": "test-source", "publisher": "Test publisher", "hosts": ("source.example",),
            "regions": frozenset(("AMERICAS",)), "domains": frozenset(("TRADE",)), "cadence": "MONTHLY",
            "reference_url": "https://source.example/catalog",
        }
        with self.assertRaises(ContractViolation):
            SourceCandidate(**{**base, "source_role": "E1_CONFIRMED"})
        with self.assertRaises(ContractViolation):
            SourceCandidate(**{**base, "reference_url": "https://other.example/catalog"})

    def test_unknown_query_fails_closed(self):
        with self.assertRaises(ContractViolation):
            source_readiness(region="MOON", domain="TRADE")
        with self.assertRaises(ContractViolation):
            source_readiness(region="EUROPE", domain="UNKNOWN")
        with self.assertRaises(ContractViolation):
            source_readiness(region=None, domain="TRADE")


if __name__ == "__main__":
    unittest.main()
