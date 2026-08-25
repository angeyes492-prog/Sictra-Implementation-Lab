import unittest
from dataclasses import replace
from sictra.context_integrity import ProvenancePayload, MaterialContextRecord, validate_integrity, handoff, independent_evidence_count

class ContextIntegrityTests(unittest.TestCase):
    def record(self,rid="r1",root="root-1",source="source-1",temporal="CURRENT",eclass="OBSERVED"):
        return MaterialContextRecord(rid,"rate=10","support decision","doc://1","2026-08-24","1.0","ops","VERIFIED","A",("conflict",),("dep-1",),("unknown-1",),"REASSESSED",("Precision","Intelligence"),("Notion","GitHub"),ProvenancePayload(source,root,("raw",),temporal,eclass))
    def test_all_integrity_fields_present(self): self.assertEqual((True,()),validate_integrity(self.record()))
    def test_missing_material_field_rejected(self):
        ok,missing=validate_integrity(replace(self.record(),source="")); self.assertFalse(ok); self.assertIn("source",missing)
    def test_missing_provenance_rejected(self):
        r=self.record(); bad=replace(r,provenance=replace(r.provenance,root_provenance="")); self.assertFalse(validate_integrity(bad)[0])
    def test_handoff_preserves_provenance_exactly(self):
        r=self.record(); h=handoff(r,scope="precision",related_agents=("Precision",)); self.assertEqual(r.provenance,h.provenance); self.assertEqual("precision",h.scope)
    def test_duplicate_root_does_not_inflate_independence(self): self.assertEqual(1,independent_evidence_count((self.record("r1"),self.record("r2"))))
    def test_distinct_admissible_roots_increase_independence(self): self.assertEqual(2,independent_evidence_count((self.record("r1"),self.record("r2","root-2","source-2"))))
    def test_synthetic_and_historical_do_not_corroborate_current_runtime(self): self.assertEqual(1,independent_evidence_count((self.record("r1"),self.record("r2","root-2","source-2",eclass="SYNTHETIC"),self.record("r3","root-3","source-3",temporal="HISTORICAL"))))
