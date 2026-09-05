import unittest

from sictra_block1 import ContractViolation, source_readiness


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

    def test_sieca_remains_available_after_flexport_withdrawal(self):
        regional = source_readiness(region="AMERICAS", domain="TRADE")
        candidates = {item["source_id"]: item for item in regional["candidates"]}
        self.assertEqual(candidates["sieca"]["source_class"], "PUBLIC_INSTITUTIONAL")
        self.assertNotIn("flexport", candidates)
        self.assertEqual(regional["admissible_source_count"], 0)

    def test_unknown_query_fails_closed(self):
        with self.assertRaises(ContractViolation):
            source_readiness(region="MOON", domain="TRADE")
        with self.assertRaises(ContractViolation):
            source_readiness(region="EUROPE", domain="UNKNOWN")
        with self.assertRaises(ContractViolation):
            source_readiness(region=None, domain="TRADE")


if __name__ == "__main__":
    unittest.main()
