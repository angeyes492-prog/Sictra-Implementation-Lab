import unittest

from sictra_block2_design.upstream import UpstreamRecord, normalize_upstream


def record(**changes):
    value = UpstreamRecord(
        object_id="INTEL-001",
        source_identity="github:angeyes492-prog/Sictra-Implementation-Lab#INTEL-001",
        fact_ids=("FACT-001",),
        evidence_refs=("EVIDENCE-001",),
        certainty="VERIFIED",
        authority_reference="AUTHORITY-001",
        audience_context="export-operations-lead",
        decision_context="prioritize outreach segments",
        provenance_refs=("PROVENANCE-001",),
        temporal_state="CURRENT",
    )
    return UpstreamRecord(**{
        name: changes.get(name, getattr(value, name))
        for name in value.__dataclass_fields__
    })


class E01UpstreamNormalizationTests(unittest.TestCase):
    def test_current_explicit_record_normalizes_without_authority_upgrade(self):
        result = normalize_upstream(record())
        self.assertEqual("NORMALIZED", result.disposition)
        self.assertTrue(result.ready_for_preflight)
        self.assertEqual("AUTHORITY-001", result.normalized.authority_reference)
        self.assertEqual("VERIFIED", result.normalized.evidence_status)

    def test_missing_facts_and_evidence_return_upstream_without_payload(self):
        result = normalize_upstream(record(fact_ids=(), evidence_refs=()))
        self.assertEqual("RETURN_UPSTREAM", result.disposition)
        self.assertIsNone(result.normalized)
        self.assertEqual(("FACTS_MISSING", "EVIDENCE_MISSING"), result.reasons)

    def test_ungoverned_certainty_is_not_silently_coerced(self):
        result = normalize_upstream(record(certainty="HIGH_CONFIDENCE"))
        self.assertEqual("RETURN_UPSTREAM", result.disposition)
        self.assertIn("CERTAINTY_UNGOVERNED", result.reasons)

    def test_stale_record_cannot_be_presented_as_current(self):
        result = normalize_upstream(record(temporal_state="STALE"))
        self.assertEqual("RETURN_UPSTREAM", result.disposition)
        self.assertIn("UPSTREAM_NOT_CURRENT", result.reasons)

    def test_missing_provenance_blocks_identity_laundering(self):
        result = normalize_upstream(record(provenance_refs=()))
        self.assertEqual("RETURN_UPSTREAM", result.disposition)
        self.assertIn("PROVENANCE_MISSING", result.reasons)

    def test_missing_audience_and_authority_stay_explicit(self):
        result = normalize_upstream(record(audience_context="", authority_reference=""))
        self.assertEqual("RETURN_UPSTREAM", result.disposition)
        self.assertEqual(("AUTHORITY_REFERENCE", "AUDIENCE_CONTEXT"), result.reasons)


if __name__ == "__main__":
    unittest.main()
