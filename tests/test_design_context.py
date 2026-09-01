import unittest
from sictra.design_context import DesignItem, assemble_design_context
from sictra.design_oracle import expected_design_ids

class DesignContextTests(unittest.TestCase):
    def items(self):
        return [DesignItem("a1","Design","ARCHITECTURE","CURRENT","RUNTIME","Current architecture"),DesignItem("c1","Design","CONTRACT","CURRENT","DOCUMENTARY","Contract"),DesignItem("d1","Design","DEPENDENCY","CURRENT","DOCUMENTARY","Dependency"),DesignItem("old","Design","DECISION","SUPERSEDED","DOCUMENTARY","Old decision"),DesignItem("x1","Design","CONTRADICTION","CURRENT","DOCUMENTARY","Conflict"),DesignItem("q1","Design","QUESTION","CURRENT","DOCUMENTARY","Open question"),DesignItem("foreign","Precision","CONTRACT","CURRENT","DOCUMENTARY","Wrong agent"),DesignItem("noise","Design","UNRELATED","CURRENT","DOCUMENTARY","Over-context noise")]
    def ids(self,p): return {k:tuple(x.item_id for x in getattr(p,k)) for k in ("architecture","contracts","dependencies","constraints","historical_decisions","contradictions","open_questions","implementation_implications","unknowns")}
    def test_matches_independent_oracle(self): self.assertEqual(expected_design_ids(self.items()),self.ids(assemble_design_context(self.items())))
    def test_stale_decision_not_current(self): self.assertIn("old",[x.item_id for x in assemble_design_context(self.items()).historical_decisions])
    def test_cross_agent_contamination_excluded(self): self.assertNotIn("foreign",sum((list(v) for v in self.ids(assemble_design_context(self.items())).values()),[]))
    def test_contradiction_preserved(self): self.assertIn("x1",[x.item_id for x in assemble_design_context(self.items()).contradictions])
    def test_no_acceptance_authority(self): self.assertFalse(assemble_design_context(self.items()).acceptance_authority)
