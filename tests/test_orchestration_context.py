import unittest
from sictra.orchestration_context import OrchestrationItem, assemble_orchestration_context
from sictra.orchestration_oracle import expected_orchestration

class OrchestrationContextTests(unittest.TestCase):
    def items(self):
        return [OrchestrationItem("state","Orchestration","STATE","CURRENT","RUNTIME",False,(),"Current"),OrchestrationItem("dep","Orchestration","DEPENDENCY","CURRENT","DOCUMENTARY",False,(),"Dependency"),OrchestrationItem("work","Orchestration","WORK","CURRENT","RUNTIME",False,("dep","missing"),"Open work"),OrchestrationItem("block","Orchestration","BLOCKER","CURRENT","RUNTIME",False,(),"Blocker"),OrchestrationItem("oldblock","Orchestration","BLOCKER","STALE","RUNTIME",False,(),"Old blocker"),OrchestrationItem("evidence","Orchestration","EVIDENCE","CURRENT","OBSERVED",False,(),"Evidence"),OrchestrationItem("action","Orchestration","ACTION","CURRENT","SYNTHETIC",True,(),"Proposed action"),OrchestrationItem("foreign","Design","EVIDENCE","CURRENT","OBSERVED",False,(),"Wrong agent")]
    def ids(self,p): return {k:tuple(x.item_id for x in getattr(p,k)) for k in ("current_state","open_work","dependencies","blockers","historical_blockers","capabilities","evidence","reassessment_requirements","pending_decisions")}
    def test_matches_independent_oracle(self):
        p=assemble_orchestration_context(self.items()); e=expected_orchestration(self.items()); self.assertEqual({k:e[k] for k in self.ids(p)},self.ids(p)); self.assertEqual(e["missing_dependencies"],p.missing_dependencies)
    def test_stale_blocker_separate(self): self.assertEqual(("oldblock",),tuple(x.item_id for x in assemble_orchestration_context(self.items()).historical_blockers))
    def test_missing_dependency_exposed(self): self.assertEqual(("missing",),assemble_orchestration_context(self.items()).missing_dependencies)
    def test_wrong_agent_excluded(self): self.assertNotIn("foreign",sum((list(v) for v in self.ids(assemble_orchestration_context(self.items())).values()),[]))
    def test_action_not_evidence_and_authority_not_granted(self):
        p=assemble_orchestration_context(self.items()); self.assertNotIn("action",[x.item_id for x in p.evidence]); self.assertFalse(p.execution_authorized); self.assertFalse(p.gate_promotion_authorized); self.assertIn("action",p.authority_violations)
