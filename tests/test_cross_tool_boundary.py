import json, unittest
from pathlib import Path
from sictra.cross_tool_boundary import ToolObservation,validate_lineage,role_valid,reconcile,current_contradictions

ROOT=Path(__file__).resolve().parents[1]

def load():
    raw=json.loads((ROOT/'evidence'/'cross-tool-observation-1.6.json').read_text())
    return tuple(ToolObservation(**o) for o in raw['observations'])

class CrossToolBoundaryTests(unittest.TestCase):
    def test_actual_snapshot_has_all_four_tools(self):
        tools={o.tool for o in load() if o.temporal_state=='CURRENT' and o.claim_key=='confidence_vector'}
        self.assertEqual({'Notion','Slack','GitHub','Wolfram'},tools)
    def test_required_lineage_present(self): self.assertTrue(all(validate_lineage(o)[0] for o in load()))
    def test_roles_do_not_gain_acceptance_or_promotion_authority(self): self.assertTrue(all(role_valid(o) for o in load()))
    def test_actual_confidence_vector_has_no_current_cross_tool_contradiction(self):
        result=reconcile(load(),'confidence_vector'); self.assertTrue(result['valid']); self.assertFalse(result['current_contradiction']); self.assertEqual(('GitHub','Notion','Slack','Wolfram'),result['current_tools'])
    def test_historical_github_write_false_does_not_contradict_current_true(self):
        result=reconcile(load(),'github_write_capability'); self.assertFalse(result['current_contradiction']); self.assertIn((False,True),result['historical_transitions'])
    def test_current_contradiction_is_detected(self):
        obs=list(load()); base=next(o for o in obs if o.tool=='Slack' and o.claim_key=='confidence_vector'); obs.append(ToolObservation(base.tool,'mutation',base.source,base.scope,base.version,base.status,base.confidence,base.relation,'CURRENT',base.claim_key,{'A':99},base.authority)); self.assertTrue(current_contradictions(tuple(obs),'confidence_vector'))
    def test_reference_is_not_automatic_evidence_authority(self):
        self.assertEqual('CONTEXT_ONLY',next(o.authority for o in load() if o.tool=='Notion' and o.claim_key=='confidence_vector'))
        self.assertEqual('SIGNAL_ONLY',next(o.authority for o in load() if o.tool=='Slack' and o.claim_key=='confidence_vector'))
        self.assertEqual('FORMAL_ONLY',next(o.authority for o in load() if o.tool=='Wolfram' and o.claim_key=='confidence_vector'))
