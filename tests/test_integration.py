import unittest
from sictra import ContextRecord, ContextEngine, expected_set, reassess, promotion_decision

class IntegratedRuntimeTests(unittest.TestCase):
    def records(self):
        return [
            ContextRecord("e1","A","C1","ops","current","evidence","p1"),
            ContextRecord("e2","A","C1","ops","stale","evidence","p2"),
            ContextRecord("e3","B","C1","ops","current","evidence","p3"),
            ContextRecord("e4","A","C1","ops","current","dependency","p4"),
            ContextRecord("e5","A","C1","ops","current","evidence",""),
            ContextRecord("e6","A","C1","ops","current","evidence","p6","explicit"),
        ]

    def test_engine_contract_context_matches_independent_oracle(self):
        rs=self.records()
        obs=ContextEngine("A").execute("run-1","C1",rs,agent="ops",temporal_state="current",relation="evidence")
        expected=expected_set(rs,engine_id="A",contract_id="C1",agent="ops",temporal_state="current",relation="evidence")
        self.assertEqual(("e1","e6"), obs.selected_ids)
        self.assertEqual(expected, obs.selected_ids)
        self.assertEqual("VALIDATED", reassess(obs, expected).result)

    def test_cross_engine_isolation(self):
        obs=ContextEngine("A").execute("run-2","C1",self.records(),agent="ops",temporal_state="current",relation="evidence")
        self.assertNotIn("e3", obs.selected_ids)

    def test_temporal_mutation(self):
        rs=self.records(); rs[1]=ContextRecord("e2","A","C1","ops","current","evidence","p2")
        obs=ContextEngine("A").execute("run-3","C1",rs,agent="ops",temporal_state="current",relation="evidence")
        self.assertEqual(("e1","e2","e6"), obs.selected_ids)

    def test_engine_identity_mutation(self):
        rs=self.records(); rs[2]=ContextRecord("e3","A","C1","ops","current","evidence","p3")
        obs=ContextEngine("A").execute("run-4","C1",rs,agent="ops",temporal_state="current",relation="evidence")
        self.assertEqual(("e1","e3","e6"), obs.selected_ids)

    def test_provenance_mutation(self):
        rs=self.records(); rs[0]=ContextRecord("e1","A","C1","ops","current","evidence","")
        obs=ContextEngine("A").execute("run-5","C1",rs,agent="ops",temporal_state="current",relation="evidence")
        self.assertEqual(("e6",), obs.selected_ids)

    def test_reassessment_rejects_mismatch(self):
        obs=ContextEngine("A").execute("run-6","C1",self.records(),agent="ops",temporal_state="current",relation="evidence")
        self.assertEqual("REJECTED", reassess(obs,("bogus",)).result)

    def test_promotion_guard_requires_ci_and_cross_engine(self):
        rs=self.records(); obs=ContextEngine("A").execute("run-7","C1",rs,agent="ops",temporal_state="current",relation="evidence")
        rr=reassess(obs,expected_set(rs,engine_id="A",contract_id="C1",agent="ops",temporal_state="current",relation="evidence"))
        self.assertEqual("DO_NOT_PROMOTE", promotion_decision(rr,ci_executed=False,cross_engine_observed=True))
        self.assertEqual("DO_NOT_PROMOTE", promotion_decision(rr,ci_executed=True,cross_engine_observed=False))
        self.assertEqual("CANDIDATE_FOR_ACCEPTANCE", promotion_decision(rr,ci_executed=True,cross_engine_observed=True))

if __name__ == '__main__':
    unittest.main()
