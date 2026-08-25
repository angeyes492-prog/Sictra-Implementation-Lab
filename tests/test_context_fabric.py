import unittest
from dataclasses import replace
from sictra.context_integrity import ProvenancePayload, MaterialContextRecord
from sictra.context_fabric import FabricRelation, prepare_agent_context, fabric_signature
from sictra.fabric_oracle import expected_fabric

class ContextFabricTests(unittest.TestCase):
    def rec(self,rid,agents=("Precision",),temporal="CURRENT",root=None,source=None,contradictions=(),eclass="OBSERVED"):
        return MaterialContextRecord(rid,"what "+rid,"why","src://"+rid,"2026-08-24","1.0","scope","VERIFIED","A",contradictions,(),(),"REASSESSED",agents,("Notion",),ProvenancePayload(source or "src-"+rid,root or "root-"+rid,("raw",),temporal,eclass))
    def records(self): return (self.rec("p1"),self.rec("shared",("Precision","Design"),contradictions=("open-conflict",)),self.rec("old",temporal="HISTORICAL"),self.rec("d1",("Design",)),self.rec("dup",root="root-p1",source="src-p1"))
    def relations(self): return (FabricRelation("p1","shared","REQUIRES"),FabricRelation("p1","d1","RELATED_TO"),FabricRelation("shared","d1","RELATED_TO"))
    def test_fabric_matches_independent_oracle(self):
        rs=self.records(); rel=self.relations(); p=prepare_agent_context(rs,rel,"Precision"); e=expected_fabric(rs,rel,"Precision"); self.assertEqual(e["current"],tuple(r.record_id for r in p.current)); self.assertEqual(e["historical"],tuple(r.record_id for r in p.historical)); self.assertEqual(e["independent_evidence_count"],p.independent_evidence_count)
    def test_cross_agent_isolation_with_explicit_shared_record(self):
        p=prepare_agent_context(self.records(),self.relations(),"Precision"); ids={r.record_id for r in p.current+p.historical}; self.assertNotIn("d1",ids); self.assertIn("shared",ids)
    def test_current_and_historical_never_collapse(self):
        p=prepare_agent_context(self.records(),self.relations(),"Precision"); self.assertNotIn("old",[r.record_id for r in p.current]); self.assertIn("old",[r.record_id for r in p.historical])
    def test_relation_never_becomes_dependency(self):
        p=prepare_agent_context(self.records(),self.relations(),"Precision"); self.assertEqual(("REQUIRES",),tuple(x.relation_type for x in p.dependencies)); self.assertTrue(all(x.relation_type=="RELATED_TO" for x in p.related))
    def test_contradiction_survives(self): self.assertIn("shared",[r.record_id for r in prepare_agent_context(self.records(),self.relations(),"Precision").contradictions])
    def test_duplicate_root_does_not_inflate_fabric_independence(self): self.assertEqual(2,prepare_agent_context(self.records(),self.relations(),"Precision").independent_evidence_count)
    def test_fabric_has_no_verification_or_promotion_authority(self):
        p=prepare_agent_context(self.records(),self.relations(),"Precision"); self.assertFalse(p.promotion_authority); self.assertFalse(p.verification_authority)
    def test_reproducibility_signature_is_deterministic(self):
        a=fabric_signature(prepare_agent_context(self.records(),self.relations(),"Precision")); b=fabric_signature(prepare_agent_context(tuple(reversed(self.records())),tuple(reversed(self.relations())),"Precision")); self.assertEqual(a,b)
