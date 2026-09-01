import unittest
from sictra.precision_context import ClaimRecord, assemble_precision_context
from sictra.precision_oracle import expected_precision

class PrecisionContextTests(unittest.TestCase):
    def records(self):
        return [ClaimRecord("r1","claim-A","source-1","EVIDENCE","DOCUMENTARY","B","CURRENT",False,"Evidence 1"),ClaimRecord("r2","claim-A","source-1","EVIDENCE","DOCUMENTARY","B","CURRENT",False,"Duplicate same source"),ClaimRecord("r3","claim-A","source-2","EVIDENCE","DOCUMENTARY","C","CURRENT",True,"Counterclaim"),ClaimRecord("r4","claim-A","source-3","EVIDENCE","DOCUMENTARY","A","STALE",False,"Stale evidence"),ClaimRecord("r5","claim-A","source-4","UNCERTAINTY","DOCUMENTARY","D","CURRENT",False,"Unknown"),ClaimRecord("other","claim-B","source-9","EVIDENCE","DOCUMENTARY","A","CURRENT",False,"Wrong claim")]
    def test_matches_independent_oracle(self):
        rs=self.records(); p=assemble_precision_context(rs,"claim-A"); e=expected_precision(rs,"claim-A"); self.assertEqual(e["current"],tuple(x.record_id for x in p.current_records)); self.assertEqual(e["source_count"],p.independent_source_count)
    def test_false_corroboration_same_source_not_double_counted(self): self.assertEqual(2,assemble_precision_context(self.records(),"claim-A").independent_source_count)
    def test_stale_evidence_is_separate(self): self.assertEqual(("r4",),tuple(x.record_id for x in assemble_precision_context(self.records(),"claim-A").stale_records))
    def test_contradiction_survives(self): self.assertEqual(("r3",),tuple(x.record_id for x in assemble_precision_context(self.records(),"claim-A").counterclaims))
    def test_pack_does_not_issue_precision_judgement(self): self.assertIsNone(assemble_precision_context(self.records(),"claim-A").precision_judgement)
