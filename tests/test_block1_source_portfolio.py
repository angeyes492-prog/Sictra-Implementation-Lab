import unittest

from sictra_block1 import ContractViolation, source_readiness


class SourcePortfolioTests(unittest.TestCase):
    def test_regional_query_is_proposed_only_and_cannot_claim_evidence(self):
        result = source_readiness(region="AMERICAS", domain="TRADE")
        self.assertEqual(result["status"], "RESEARCH_BLOCKED_PENDING_SOURCE_BINDING")
        self.assertEqual(result["admissible_source_count"], 0)
        self.assertIn("cepal", {item["source_id"] for item in result["candidates"]})
        self.assertTrue(all(item["status"] == "PROPOSED" for item in result["candidates"]))

    def test_unknown_query_fails_closed(self):
        with self.assertRaises(ContractViolation):
            source_readiness(region="MOON", domain="TRADE")
        with self.assertRaises(ContractViolation):
            source_readiness(region="EUROPE", domain="UNKNOWN")
        with self.assertRaises(ContractViolation):
            source_readiness(region=None, domain="TRADE")


if __name__ == "__main__":
    unittest.main()
