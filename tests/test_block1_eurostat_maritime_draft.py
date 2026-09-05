import unittest
from dataclasses import replace

from sictra_block1 import (
    ContractViolation,
    EvidenceIssuer,
    SourceApprovalRecord,
    SourceBindingIssuer,
    SourceGateway,
    SourceRegistration,
)


NOW = 10_000
EVIDENCE_KEY = b"e" * 32
BINDING_KEY = b"b" * 32


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

    def test_matching_owner_approval_can_only_bind_the_declared_scope(self):
        proposed = eurostat_maritime_draft()
        bound = replace(proposed, status="BOUND")
        approval = SourceApprovalRecord(
            "eurostat",
            "PROJECT_OWNER",
            NOW - 1,
            "evidence/block1_eurostat_maritime_registration_draft_v0.1.md",
            proposed.allowed_hosts,
            proposed.claim_keys,
            proposed.access_method,
            proposed.max_content_bytes,
            "APPROVED",
        )
        token = SourceBindingIssuer("review-control", BINDING_KEY).issue(
            bound, approval, now=NOW, ttl=100
        )
        gateway = SourceGateway(
            registrations=(bound,),
            issuer=EvidenceIssuer("gateway", EVIDENCE_KEY),
            binding_keys={"review-control": BINDING_KEY},
            bindings={"eurostat": token},
            now=NOW,
        )
        bundle = {
            "source_id": "eurostat",
            "source_url": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/tran_r_mago_nm",
            "content": "fixture only; source content is not represented by this test",
            "observed_at": NOW - 1,
            "claim_key": "maritime_freight_weight_thousand_tonnes",
            "polarity": 1,
            "correlation_id": "eurostat-bound-fixture-001",
        }
        observed = gateway.attest_manual_bundle(bundle, now=NOW)
        self.assertEqual(observed["scope"], "BLOCK1_EUROPE_MARITIME_INTELLIGENCE")
        self.assertEqual(observed["root_provenance"], "gateway-source:eurostat")
        with self.assertRaises(ContractViolation):
            gateway.attest_manual_bundle({**bundle, "claim_key": "out-of-scope"}, now=NOW)


if __name__ == "__main__":
    unittest.main()
