import unittest
from sictra.six_layer import LayerObject,LayerEdge,temporal_partitions,latest_current,epistemic_is_fact,dependency_closure,lineage_descendants,proactive_context,evaluate_six_layer
from sictra.six_layer_oracle import oracle_proactive

class SixLayerAttackMatrixTests(unittest.TestCase):
    def o(self,oid,key,layer,agent="Precision",state="CURRENT",eclass="EVIDENCE",root=None,version=1,parents=()): return LayerObject(oid,key,layer,agent,state,eclass,root or "root-"+oid,version,parents)
    def base(self):
        return (
            self.o("decision-old","decision","C3",state="SUPERSEDED",version=1),
            self.o("decision","decision","C3",version=2),
            self.o("req-old","requirement","C3",state="SUPERSEDED",version=1,parents=("decision-old",)),
            self.o("req","requirement","C3",version=2,parents=("decision",)),
            self.o("context","context","C1",parents=("req",)),
            self.o("memory","memory","C2",eclass="AGENT_OUTPUT",parents=("context",)),
            self.o("reassess","reassessment","C4",parents=("memory",)),
            self.o("dep","dependency","C5",agent="SHARED",parents=("req",)),
            self.o("proactive","proactive","C6",parents=("reassess",)),
            self.o("foreign","foreign","C2",agent="Design",parents=("decision",)),
            self.o("stale-context","stale-context","C1",state="HISTORICAL",parents=("req-old",)),
            self.o("repeat-1","signal","C6",root="signal-root",parents=("req",)),
            self.o("repeat-2","signal","C6",root="signal-root",parents=("req",)),
            self.o("unrelated","unrelated","C6",parents=()),
        )
    def edges(self): return (
        LayerEdge("req","dep","REQUIRES"),
        LayerEdge("req","foreign","RELATED_TO"),
        LayerEdge("req","unrelated","RELATED_TO"),
        LayerEdge("decision-old","stale-context","REQUIRES","STALE"),
        LayerEdge("dep","req","RELATED_TO"),
    )
    def selected(self,changed=("decision",)): return proactive_context(self.base(),self.edges(),"Precision",changed)

    def test_C1_C2_agent_context_contamination(self): self.assertNotIn("foreign",[o.object_id for o in self.selected()])
    def test_C1_C3_wrong_decision_context_lineage_loss(self): self.assertIn("req",lineage_descendants(("decision",),self.base())); self.assertNotIn("req-old",lineage_descendants(("decision",),self.base()))
    def test_C1_C4_stale_context_during_reassessment(self): self.assertNotIn("stale-context",[o.object_id for o in self.selected()])
    def test_C1_C5_relation_not_dependency(self): self.assertNotIn("foreign",dependency_closure(("req",),self.edges()))
    def test_C1_C6_no_over_or_under_retrieval(self):
        ids={o.object_id for o in self.selected()}; self.assertIn("context",ids); self.assertNotIn("unrelated",ids)
    def test_C2_C3_agent_output_not_promoted_to_fact(self):
        memory=next(o for o in self.base() if o.object_id=="memory"); self.assertFalse(epistemic_is_fact(memory))
    def test_C2_C4_historical_state_preserved(self):
        _,historical=temporal_partitions(self.base()); self.assertIn("stale-context",[o.object_id for o in historical])
    def test_C2_C5_cross_agent_relation_does_not_become_dependency(self): self.assertNotIn("foreign",dependency_closure(("req",),self.edges()))
    def test_C2_C6_repeated_signal_deduplicated(self):
        ids=[o.object_id for o in self.selected()]; self.assertEqual(1,len([x for x in ids if x.startswith("repeat-")]))
    def test_C3_C4_superseded_requirement_not_current(self): self.assertNotIn("req-old",[o.object_id for o in latest_current(self.base())])
    def test_C3_C5_requirement_edge_direction(self):
        self.assertIn("dep",dependency_closure(("req",),self.edges())); self.assertNotIn("req",dependency_closure(("dep",),self.edges()))
    def test_C3_C6_affected_requirement_is_retrieved(self): self.assertIn("req",[o.object_id for o in self.selected()])
    def test_C4_C5_stale_dependency_graph_not_current(self): self.assertNotIn("stale-context",dependency_closure(("decision-old",),self.edges()))
    def test_C4_C6_new_current_evidence_replaces_stale_context(self):
        ids={o.object_id for o in self.selected()}; self.assertIn("context",ids); self.assertNotIn("stale-context",ids)
    def test_C5_C6_false_dependency_does_not_drive_context(self): self.assertNotIn("unrelated",[o.object_id for o in self.selected()])
    def test_full_system_matches_independent_oracle_and_has_no_promotion_authority(self):
        result=evaluate_six_layer(self.base(),self.edges(),"Precision",("decision",)); expected=oracle_proactive(self.base(),self.edges(),"Precision",("decision",)); self.assertEqual(expected,result.selected_ids); self.assertFalse(result.promotion_authorized); self.assertTrue({"req","context","memory","reassess","proactive","dep"}.issubset(set(result.selected_ids)))
