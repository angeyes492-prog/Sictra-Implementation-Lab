import unittest
from sictra.intelligence_context import KnowledgeItem, assemble_intelligence_context
from sictra.intelligence_oracle import expected_context_ids

class IntelligenceContextTests(unittest.TestCase):
    def items(self):
        return [
            KnowledgeItem("f1","FACT","RUNTIME","CURRENT","rate","Observed rate = 10"),
            KnowledgeItem("h1","HYPOTHESIS","SYNTHETIC","CURRENT","rate","Rate may rise"),
            KnowledgeItem("e1","EVIDENCE","DOCUMENTARY","CURRENT","rate","Source report"),
            KnowledgeItem("c1","CONTRADICTION","DOCUMENTARY","CURRENT","rate","Conflicting source"),
            KnowledgeItem("u1","UNCERTAINTY","DOCUMENTARY","CURRENT","rate","Date uncertain"),
            KnowledgeItem("d1","DEPENDENCY","DOCUMENTARY","CURRENT","rate","Depends on tariff"),
            KnowledgeItem("old1","FACT","RUNTIME","HISTORICAL","rate","Old observed rate = 8"),
            KnowledgeItem("formal1","FACT","FORMAL","CURRENT","rate","Model output = 11"),
        ]

    def ids(self, pack):
        return {name: tuple(x.item_id for x in getattr(pack,name)) for name in (
            "facts","evidence","uncertainties","contradictions","hypotheses","dependencies","historical"
        )}

    def test_pack_matches_independent_oracle(self):
        items=self.items(); self.assertEqual(expected_context_ids(items), self.ids(assemble_intelligence_context(items)))

    def test_hypothesis_never_becomes_fact(self):
        pack=assemble_intelligence_context(self.items())
        self.assertNotIn("h1", [x.item_id for x in pack.facts])
        self.assertIn("h1", [x.item_id for x in pack.hypotheses])

    def test_formal_result_never_becomes_runtime_fact(self):
        pack=assemble_intelligence_context(self.items())
        self.assertNotIn("formal1", [x.item_id for x in pack.facts])
        self.assertIn("formal1", [x.item_id for x in pack.evidence])

    def test_historical_never_leaks_into_current_fact(self):
        pack=assemble_intelligence_context(self.items())
        self.assertNotIn("old1", [x.item_id for x in pack.facts])
        self.assertIn("old1", [x.item_id for x in pack.historical])

    def test_contradiction_survives_context_assembly(self):
        pack=assemble_intelligence_context(self.items())
        self.assertIn("c1", [x.item_id for x in pack.contradictions])

    def test_same_claim_key_does_not_collapse_epistemic_classes(self):
        pack=assemble_intelligence_context(self.items())
        self.assertEqual(("f1",), tuple(x.item_id for x in pack.facts))
        self.assertEqual(("h1",), tuple(x.item_id for x in pack.hypotheses))
        self.assertEqual(("c1",), tuple(x.item_id for x in pack.contradictions))
