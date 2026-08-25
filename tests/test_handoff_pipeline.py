import unittest
from sictra.context_integrity import ProvenancePayload, MaterialContextRecord
from sictra.context_fabric import FabricRelation
from sictra.confidence_enforcement import EvidenceRecord
from sictra.handoff_pipeline import execute_handoff

class HandoffPipelineTests(unittest.TestCase):
    def record(self,rid="r1",agent="Precision",temporal="CURRENT"):
        return MaterialContextRecord(rid,"what","why","notion://record","2026-08-24","1.0","scope","VERIFIED","A",("open-conflict",),("dep",),("unknown",),"REASSESS",(agent,),("Notion",),ProvenancePayload("source-1","root-1",("raw",),temporal,"OBSERVED"))
    def test_notion_to_precision_reassessment_to_orchestration_handoff(self):
        records=(self.record(),); evidence=(EvidenceRecord("e1","root-1","PRIMARY","CURRENT",True),)
        result=execute_handoff(records,(),evidence,"Precision")
        self.assertEqual("VALIDATED",result.reassessment_status); self.assertEqual(1,result.independent_evidence_count); self.assertEqual("REASSESS_NEXT_ACTION",result.orchestration_candidate)
    def test_confidence_authority_is_not_notion(self): self.assertEqual("PRECISION_REASSESSMENT",execute_handoff((self.record(),),(),(EvidenceRecord("e1","root-1","PRIMARY","CURRENT",True),),"Precision").confidence_authority_layer)
    def test_pipeline_never_promotes(self): self.assertFalse(execute_handoff((self.record(),),(),(EvidenceRecord("e1","root-1","PRIMARY","CURRENT",True),),"Precision").promotion_authorized)
    def test_duplicate_volume_does_not_change_corroboration(self):
        evidence=(EvidenceRecord("e1","root-1","PRIMARY","CURRENT",True),EvidenceRecord("e2","root-1","DUPLICATE","CURRENT",True),EvidenceRecord("e3","root-1","DERIVED","CURRENT",True))
        self.assertEqual(1,execute_handoff((self.record(),),(),evidence,"Precision").independent_evidence_count)
    def test_historical_context_remains_historical_in_fabric_signature(self):
        result=execute_handoff((self.record("old",temporal="HISTORICAL"),),(),(),"Precision")
        signature=result.fabric_signature; self.assertEqual((),signature[1]); self.assertEqual(("old",),signature[2])
