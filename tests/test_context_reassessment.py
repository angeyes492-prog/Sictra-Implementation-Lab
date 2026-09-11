import json
from pathlib import Path
import unittest

from sictra_block1.context import ContractViolation, ContextRecord, build_context_pack
from sictra_block1.reassessment import reassess


FIXTURE = Path(__file__).parent / "fixtures" / "notion_exp05_context_matrix.json"


def load_records():
    return [ContextRecord(**{**item, "derivation_graph": tuple(item["derivation_graph"])})
            for item in json.loads(FIXTURE.read_text(encoding="utf-8"))]


class ContextReassessmentTests(unittest.TestCase):
    def test_current_precision_pack_keeps_open_contradiction(self):
        pack = build_context_pack(load_records(), "Precision")
        self.assertEqual(
            [record.record_id for record in pack.records],
            ["ASSEMBLY-Decision-B", "ASSEMBLY-Open-Contradiction", "ASSEMBLY-Requirement-v3"],
        )
        self.assertEqual(
            [record.record_id for record in pack.open_contradictions],
            ["ASSEMBLY-Open-Contradiction"],
        )

    def test_stale_and_cross_agent_records_are_excluded(self):
        pack = build_context_pack(load_records(), "Precision")
        self.assertIn("ASSEMBLY-Stale-A", pack.excluded_record_ids)
        self.assertIn("ASSEMBLY-Design-Relation", pack.excluded_record_ids)
        self.assertIn("ASSEMBLY-Intelligence-Foreign", pack.excluded_record_ids)

    def test_synthetic_and_adversarial_fixture_is_local_only(self):
        result = reassess(build_context_pack(load_records(), "Precision"))
        self.assertEqual(result.status, "LOCAL_ONLY")
        self.assertFalse(result.runtime_evidence_admissible)
        self.assertEqual(result.independent_evidence_count, 0)

    def test_missing_provenance_is_rejected(self):
        record = load_records()[0]
        broken = ContextRecord(
            **{field: getattr(record, field) for field in record.__dataclass_fields__} | {"root_provenance": ""}
        )
        with self.assertRaises(ContractViolation):
            build_context_pack([broken], "Precision")

    def test_repeated_observed_root_does_not_inflate_independence(self):
        records = load_records()[:2]
        observed = [
            ContextRecord(
                **{field: getattr(record, field) for field in record.__dataclass_fields__} | {"evidence_class": "OBSERVED"}
            ) for record in records
        ]
        result = reassess(build_context_pack(observed, "Precision"))
        self.assertEqual(result.independent_evidence_count, 1)
        self.assertTrue(result.runtime_evidence_admissible)


if __name__ == "__main__":
    unittest.main()
