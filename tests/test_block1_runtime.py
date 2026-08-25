from dataclasses import replace
import unittest

from sictra_block1 import AuthorityContext, IdentityCollision, IntelligenceRuntime


def source(source_id="s1", root="root-1", **extra):
    return {"source_id": source_id, "content": "observed fact", "observed_at": 10,
            "root_provenance": root, **extra}


class Block1RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.runtime = IntelligenceRuntime.reference()
        self.authority = AuthorityContext("E08-authority", 1, ("store_candidate",), 100, True)

    def test_all_eight_engines_execute_in_trace(self):
        out = self.runtime.run(task_id="t1", run_id="r1", objective="build intelligence",
            sources=[source()], authority=self.authority, now=50)
        self.assertEqual(out.payload["governance"]["decision"], "ALLOW_REFERENCE_ACTION")
        for engine in ("E01", "E02", "E03", "E05", "E06", "E07", "E08"):
            self.assertTrue(any(engine in step for step in out.trace), engine)
        self.assertEqual(len(self.runtime.integration._seen), 7)
        self.assertEqual(len(self.runtime.integration.audit), 7)
        self.assertTrue(all(item[2] == "ROUTED" for item in self.runtime.integration.audit))
        self.assertFalse(out.payload["governance"]["decision_is_enforcement"])

    def test_stale_authority_never_allows(self):
        stale = AuthorityContext("E08-authority", 0, ("store_candidate",), 100, True)
        out = self.runtime.run(task_id="t2", run_id="r2", objective="x",
            sources=[source()], authority=stale, now=50, known_epoch=1)
        self.assertEqual(out.payload["governance"]["decision"], "QUARANTINE")

    def test_expired_and_future_authority_never_allow(self):
        expired = AuthorityContext("E08-authority", 1, ("store_candidate",), 10, True)
        future = AuthorityContext("E08-authority", 2, ("store_candidate",), 100, True)
        for index, authority in enumerate((expired, future)):
            out = IntelligenceRuntime.reference().run(task_id=f"ta{index}", run_id=f"ra{index}",
                objective="x", sources=[source()], authority=authority, now=50, known_epoch=1)
            self.assertEqual(out.payload["governance"]["decision"], "QUARANTINE")

    def test_contradiction_survives_and_forces_revalidation(self):
        out = self.runtime.run(task_id="t3", run_id="r3", objective="x",
            sources=[source(contradicts=True)], authority=self.authority, now=50)
        self.assertEqual(out.epistemic_state, "CONTRADICTED")
        self.assertEqual(out.payload["assessment"]["contradictions"], ("s1",))
        self.assertEqual(out.payload["governance"]["decision"], "REVALIDATE")

    def test_missing_evidence_is_not_coerced_to_pass(self):
        out = self.runtime.run(task_id="t4", run_id="r4", objective="x",
            sources=[{"source_id": "broken"}], authority=self.authority, now=50)
        self.assertEqual(out.epistemic_state, "INSUFFICIENT EVIDENCE")
        self.assertEqual(out.payload["stability"]["health"], "AT_RISK")
        self.assertEqual(out.payload["governance"]["decision"], "REVALIDATE")

    def test_repeated_roots_do_not_inflate_independence(self):
        out = self.runtime.run(task_id="t5", run_id="r5", objective="x",
            sources=[source("s1", "same"), source("s2", "same")],
            authority=self.authority, now=50)
        self.assertEqual(out.payload["assessment"]["independent_root_count"], 1)

    def test_storage_is_versioned_and_never_implicitly_promoted(self):
        self.runtime.run(task_id="t6", run_id="r6a", objective="x",
            sources=[source()], authority=self.authority, now=50)
        self.runtime.run(task_id="t6", run_id="r6b", objective="x",
            sources=[source("s2")], authority=self.authority, now=50)
        history = self.runtime.memory.history("t6")
        self.assertEqual([item["version"] for item in history], [1, 2])
        self.assertTrue(all(not item["promoted"] for item in history))

    def test_duplicate_is_idempotent_but_collision_is_rejected(self):
        envelope = self.runtime.agent.request(task_id="t7", run_id="r7", objective="x",
            sources=[source()], authority=self.authority)
        self.assertEqual(self.runtime.integration.route(envelope, "E01").disposition, "ROUTED")
        self.assertEqual(self.runtime.integration.route(envelope, "E01").disposition, "DUPLICATE")
        mutated = replace(envelope, payload={"objective": "changed", "sources": []})
        with self.assertRaises(IdentityCollision):
            self.runtime.integration.route(mutated, "E01")

    def test_provenance_and_unknown_fields_survive(self):
        item = source(extra_extension={"future": True})
        out = self.runtime.run(task_id="t8", run_id="r8", objective="x",
            sources=[item], authority=self.authority, now=50)
        self.assertEqual(out.root_provenance, "request:t8")
        self.assertEqual(out.lineage[0], "request:t8")
        self.assertEqual(out.payload["evidence"][0]["extra_extension"], {"future": True})
        with self.assertRaises(TypeError):
            out.payload["evidence"][0]["content"] = "rewritten"


if __name__ == "__main__":
    unittest.main()
