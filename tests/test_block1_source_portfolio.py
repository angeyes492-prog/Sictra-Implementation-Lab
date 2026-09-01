from dataclasses import replace
import unittest

from sictra_block1 import ContractViolation, SourceCandidate, SourcePortfolio, default_source_portfolio


def candidate(source_id="candidate", **changes):
    value = SourceCandidate(
        source_id=source_id,
        publisher="Candidate Publisher",
        candidate_hosts=(f"{source_id}.example.org",),
        regions=frozenset(("AMERICAS",)),
        domains=frozenset(("TRADE",)),
        cadence="MONTHLY",
    )
    return replace(value, **changes) if changes else value


class SourcePortfolioTests(unittest.TestCase):
    def test_default_catalog_is_proposed_only_and_covers_all_planned_regions(self):
        summary = default_source_portfolio().summary()
        self.assertEqual(summary["candidate_count"], 12)
        self.assertEqual(summary["capacity"], 50)
        self.assertEqual(summary["status"], "PROPOSED_CATALOG")
        self.assertTrue(all(summary["region_counts"][region] > 0 for region in (
            "GLOBAL", "AMERICAS", "EUROPE", "ASIA_PACIFIC", "OCEANIA",
        )))
        self.assertEqual(len(summary["promotion_blockers"]), 4)

    def test_regional_query_includes_global_candidates_but_never_bound_sources(self):
        result = default_source_portfolio().candidates_for(
            regions=("AMERICAS",), domains=("TRADE",),
        )
        self.assertIn("cepal", {value["source_id"] for value in result})
        self.assertIn("unctad", {value["source_id"] for value in result})
        self.assertTrue(all(value["status"] == "PROPOSED" for value in result))

    def test_catalog_rejects_fifty_first_duplicate_identity_and_duplicate_host(self):
        with self.assertRaises(ContractViolation):
            SourcePortfolio(tuple(candidate(f"s{number}") for number in range(51)))
        with self.assertRaises(ContractViolation):
            SourcePortfolio((candidate(), candidate()))
        with self.assertRaises(ContractViolation):
            SourcePortfolio((candidate("one"), candidate("two", candidate_hosts=("one.example.org",))))

    def test_candidate_rejects_bound_status_and_unsafe_or_unknown_values(self):
        with self.assertRaises(ContractViolation):
            candidate(status="BOUND")
        with self.assertRaises(ContractViolation):
            candidate(candidate_hosts=("127.0.0.1",))
        with self.assertRaises(ContractViolation):
            candidate(regions=frozenset(("MOON",)))
        with self.assertRaises(ContractViolation):
            candidate(domains=frozenset())

    def test_query_rejects_unknown_scope_and_returns_defensive_snapshots(self):
        portfolio = default_source_portfolio()
        with self.assertRaises(ContractViolation):
            portfolio.candidates_for(regions=("GLOBAL",), domains=("TRADE",))
        with self.assertRaises(ContractViolation):
            portfolio.candidates_for(regions=("AMERICAS",), domains=("UNKNOWN",))
        first = portfolio.candidates_for(regions=("EUROPE",), domains=("TRADE",))
        first[0]["publisher"] = "mutated"
        second = portfolio.candidates_for(regions=("EUROPE",), domains=("TRADE",))
        self.assertNotEqual(second[0]["publisher"], "mutated")


if __name__ == "__main__":
    unittest.main()
