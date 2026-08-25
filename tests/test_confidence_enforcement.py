import unittest
from sictra.confidence_enforcement import EvidenceRecord, compute_corroboration
from sictra.confidence_oracle import expected_independent_count

class ConfidenceDifferentialTests(unittest.TestCase):
    def e(self,rid,root="root-1",kind="PRIMARY",state="CURRENT",admissible=True): return EvidenceRecord(rid,root,kind,state,admissible)
    def assert_case(self,records,expected):
        result=compute_corroboration(tuple(records)); self.assertEqual(expected,result.independent_evidence_count); self.assertEqual(expected_independent_count(tuple(records)),result.independent_evidence_count)
    def test_A_one_root_one_record(self): self.assert_case([self.e("a1")],1)
    def test_B_same_root_five_duplicates(self): self.assert_case([self.e("b0")]+[self.e(f"b{i}",kind="DUPLICATE") for i in range(1,6)],1)
    def test_C_derived_agent_amplification(self): self.assert_case([self.e("c0"),self.e("c1",kind="DERIVED"),self.e("c2",kind="AGENT")],1)
    def test_D_contextual_repetition(self): self.assert_case([self.e("d0"),self.e("d1",kind="CONTEXTUAL"),self.e("d2",kind="DUPLICATE")],1)
    def test_E_two_independent_roots(self): self.assert_case([self.e("e1","root-1","PRIMARY"),self.e("e2","root-2","SECONDARY")],2)
    def test_F_synthetic_amplification(self): self.assert_case([self.e("f0")]+[self.e(f"f{i}",f"synthetic-{i}","SYNTHETIC",admissible=False) for i in range(1,5)],1)
    def test_G_historical_amplification(self): self.assert_case([self.e("g0")]+[self.e(f"g{i}",f"old-{i}","PRIMARY","HISTORICAL") for i in range(1,5)],1)
    def test_unknown_root_never_counts(self): self.assert_case([self.e("u1",root="")],0)
