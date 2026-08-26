from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from hashlib import sha256
import json
import tempfile
from pathlib import Path
import sqlite3
import unittest

from sictra_block1 import (
    AuthorityIssuer, AuthorityVerifier, ContractViolation, EvidenceIssuer,
    EvidenceVerifier, IdentityCollision, IntelligenceRuntime, OperationalStore,
)
from sictra_block1.engines import IntegrationEngine

NOW = 1_000
AUTHORITY_KEY = b"a" * 32
EVIDENCE_KEY = b"e" * 32
DECISION_KEY = b"d" * 32
EXECUTION_KEY = b"x" * 32
STORAGE_KEY = b"s" * 32
_DEFAULT_AUTHORITY = object()


class Block1OperationalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "block1.sqlite3"
        self.authority_issuer = AuthorityIssuer("governance", AUTHORITY_KEY, "block1-runtime", 3)
        self.evidence_issuer = EvidenceIssuer("acquisition", EVIDENCE_KEY)
        self.current_time = NOW
        self.runtime = self.make_runtime()

    def tearDown(self):
        self.runtime.close()
        self.temp.cleanup()

    def make_runtime(self, **overrides):
        options = {
            "store_path": self.db, "authority_keys": {"governance": AUTHORITY_KEY},
            "authority_audience": "block1-runtime", "authority_epoch": 3,
            "evidence_keys": {"acquisition": EVIDENCE_KEY}, "evidence_scope": "intelligence",
            "evidence_max_age": 100, "evidence_claims": frozenset({"claim-1"}),
            "execution_key": EXECUTION_KEY, "decision_key": DECISION_KEY,
            "storage_integrity_key": STORAGE_KEY,
            "clock": lambda: self.current_time,
        }
        options.update(overrides)
        return IntelligenceRuntime.operational(
            **options,
        )

    def authority(self, task_id, run_id, **overrides):
        token = self.authority_issuer.issue(
            task_id=task_id, run_id=run_id, actions=("store_candidate",),
            now=NOW, ttl=50, nonce=f"nonce-{run_id}",
        )
        return replace(token, **overrides) if overrides else token

    def source(self, source_id="s1", correlation_id="root-1", **overrides):
        raw = {
            "source_id": source_id, "content": "observed fact", "observed_at": NOW,
            "root_provenance": f"provenance:{source_id}", "evidence_class": "OBSERVED",
            "scope": "intelligence", "correlation_id": correlation_id,
            "claim_key": "claim-1", "polarity": 1,
        }
        raw.update(overrides)
        return self.evidence_issuer.attest(raw)

    def execute(self, task_id="t1", run_id="r1", sources=None, authority=_DEFAULT_AUTHORITY):
        return self.runtime.run(
            task_id=task_id, run_id=run_id, objective="build intelligence",
            sources=sources if sources is not None else [self.source()],
            authority=self.authority(task_id, run_id) if authority is _DEFAULT_AUTHORITY else authority,
        )

    def test_e01_to_e08_authorize_before_durable_effect(self):
        output = self.execute()
        self.assertEqual(output.payload["governance"]["decision"], "ALLOW_BOUNDED_ACTION")
        self.assertFalse(output.payload["governance"]["decision_is_enforcement"])
        self.assertEqual(output.payload["enforcement"]["status"], "COMMITTED")
        self.assertTrue(output.payload["enforcement"]["runtime_effect_observed"])
        self.assertEqual(len(self.runtime.memory.history("t1")), 1)
        routed_consumers = [entry[1] for entry in self.runtime.integration.audit if entry[2] == "ROUTED"]
        self.assertEqual(routed_consumers, ["E01", "E02", "E03", "E05", "E06", "E07", "E08", "RUNTIME", "CALLER"])

    def test_missing_or_uncommitted_authority_never_writes(self):
        for index, authority in enumerate((None, "SIGNED_UNCOMMITTED")):
            task_id, run_id = f"t-u{index}", f"r-u{index}"
            if authority == "SIGNED_UNCOMMITTED":
                authority = self.authority_issuer.issue(
                    task_id=task_id, run_id=run_id, actions=("store_candidate",),
                    now=NOW, ttl=50, committed=False,
                )
            output = self.execute(task_id, run_id, authority=authority)
            self.assertEqual(output.payload["governance"]["decision"], "QUARANTINE")
            self.assertEqual(output.payload["enforcement"]["status"], "NOT_EXECUTED")
            self.assertEqual(self.runtime.memory.history(task_id), ())

    def test_forged_signature_untrusted_issuer_and_binding_fail_closed(self):
        def signed(issuer="governance", key=AUTHORITY_KEY, audience="block1-runtime",
                   epoch=3, task_id="unused", run_id="unused", actions=("store_candidate",),
                   issued_at=NOW, ttl=50, not_before=None):
            return AuthorityIssuer(issuer, key, audience, epoch).issue(
                task_id=task_id, run_id=run_id, actions=actions, now=issued_at,
                ttl=ttl, not_before=not_before,
            )
        for index in range(8):
            task_id, run_id = f"t-auth-{index}", f"r-auth-{index}"
            valid = signed(task_id=task_id, run_id=run_id)
            cases = (
                replace(valid, signature="0" * 64),
                signed(issuer="attacker", task_id=task_id, run_id=run_id),
                signed(task_id="other-task", run_id=run_id),
                signed(task_id=task_id, run_id="other-run"),
                signed(audience="other-audience", task_id=task_id, run_id=run_id),
                signed(epoch=4, task_id=task_id, run_id=run_id),
                signed(task_id=task_id, run_id=run_id, issued_at=NOW - 100, ttl=50),
                signed(task_id=task_id, run_id=run_id, actions=("read_only",)),
            )
            output = self.execute(task_id, run_id, authority=cases[index])
            self.assertEqual(output.payload["governance"]["decision"], "QUARANTINE")
            self.assertEqual(self.runtime.memory.history(task_id), ())

    def test_validly_signed_future_authority_is_not_current(self):
        token = self.authority_issuer.issue(
            task_id="tf", run_id="rf", actions=("store_candidate",),
            now=NOW, not_before=NOW + 10, ttl=50,
        )
        output = self.execute("tf", "rf", authority=token)
        self.assertEqual(output.payload["governance"]["authority_reason"], "AUTHORITY_NOT_CURRENT")
        self.assertEqual(self.runtime.memory.history("tf"), ())

    def test_exact_replay_returns_terminal_without_second_effect(self):
        first = self.execute()
        audit_count = len(self.runtime.integration.audit)
        second = self.execute()
        self.assertEqual(second.payload["replay"]["mode"], "HISTORICAL_TERMINAL")
        self.assertFalse(second.payload["replay"]["current_authority_revalidated"])
        self.assertFalse(second.payload["replay"]["new_effect"])
        self.assertIn("HISTORICAL_REPLAY_NOT_REAUTHORIZATION", second.restrictions)
        self.assertEqual(first.payload["enforcement"], second.payload["enforcement"])
        self.assertEqual(len(self.runtime.memory.history("t1")), 1)
        self.assertEqual(len(self.runtime.integration.audit), audit_count)

    def test_same_run_with_different_request_is_collision_without_mutation(self):
        self.execute()
        with self.assertRaises(IdentityCollision):
            self.runtime.run(
                task_id="t1", run_id="r1", objective="different",
                sources=[self.source()], authority=self.authority("t1", "r1"),
            )
        self.assertEqual(len(self.runtime.memory.history("t1")), 1)

    def test_concurrent_exact_replays_have_one_effect(self):
        def execute(_):
            result = self.execute()
            return result.payload["enforcement"]["record_version"]
        with ThreadPoolExecutor(max_workers=12) as pool:
            versions = list(pool.map(execute, range(40)))
        self.assertEqual(set(versions), {1})
        self.assertEqual(len(self.runtime.memory.history("t1")), 1)

    def test_repeated_concurrent_exact_replays_never_become_collisions(self):
        for batch in range(10):
            task_id, run_id = f"race-task-{batch}", f"race-run-{batch}"
            def execute(_):
                return self.execute(task_id, run_id).payload["enforcement"]["status"]
            with ThreadPoolExecutor(max_workers=10) as pool:
                outcomes = list(pool.map(execute, range(20)))
            self.assertEqual(set(outcomes), {"COMMITTED"})
            self.assertEqual(len(self.runtime.memory.history(task_id)), 1)

    def test_concurrent_distinct_runs_get_unique_versions(self):
        def execute(index):
            return self.execute("shared", f"run-{index}").payload["enforcement"]["record_version"]
        with ThreadPoolExecutor(max_workers=12) as pool:
            versions = list(pool.map(execute, range(40)))
        self.assertEqual(sorted(versions), list(range(1, 41)))
        self.assertEqual(len(self.runtime.memory.history("shared")), 40)

    def test_restart_recovers_terminal_and_memory(self):
        first = self.execute()
        self.runtime.close()
        self.runtime = self.make_runtime()
        second = self.execute()
        self.assertEqual(first.payload["enforcement"], second.payload["enforcement"])
        self.assertEqual(second.payload["replay"]["mode"], "HISTORICAL_TERMINAL")
        self.assertEqual(len(self.runtime.memory.history("t1")), 1)

    def test_atomic_rollback_and_retry_after_injected_commit_failure(self):
        calls = {"count": 0}
        def fail_once(point):
            self.assertEqual(point, "AFTER_EFFECT_BEFORE_TERMINAL")
            calls["count"] += 1
            if calls["count"] == 1:
                raise OSError("injected terminal write failure")
        self.runtime.store.failure_injector = fail_once
        with self.assertRaises(OSError):
            self.execute()
        self.assertEqual(self.runtime.memory.history("t1"), ())
        self.assertIsNone(self.runtime.store.get_terminal("r1"))
        result = self.execute()
        self.assertEqual(result.payload["enforcement"]["record_version"], 1)
        self.assertEqual(len(self.runtime.memory.history("t1")), 1)
        self.assertEqual(self.runtime.store.journal("r1")[-1]["state"], "EFFECT_AND_TERMINAL_COMMITTED")

    def test_failed_transaction_recovers_after_restart_and_clock_advance(self):
        self.runtime.store.failure_injector = lambda _point: (_ for _ in ()).throw(OSError("fault"))
        with self.assertRaises(OSError):
            self.execute()
        self.runtime.close()
        self.current_time = NOW + 10
        self.runtime = self.make_runtime()
        result = self.execute(authority=self.authority_issuer.issue(
            task_id="t1", run_id="r1", actions=("store_candidate",),
            now=self.current_time, ttl=50, nonce="recovery-authority",
        ))
        self.assertEqual(result.payload["enforcement"]["status"], "COMMITTED")
        self.assertEqual(len(self.runtime.memory.history("t1")), 1)

    def test_unattested_tampered_stale_future_foreign_and_synthetic_sources_do_not_write(self):
        valid = self.source()
        cases = [
            {key: value for key, value in valid.items() if key != "attestation"},
            {**valid, "content": "tampered"},
            self.source(observed_at=NOW - 101),
            self.source(observed_at=NOW + 1),
            self.source(scope="foreign"),
            self.source(evidence_class="SYNTHETIC"),
        ]
        for index, source in enumerate(cases):
            task_id, run_id = f"t-src-{index}", f"r-src-{index}"
            output = self.execute(task_id, run_id, sources=[source])
            self.assertIn(output.payload["governance"]["decision"], {"REVALIDATE", "QUARANTINE"})
            self.assertEqual(self.runtime.memory.history(task_id), ())

    def test_attested_extensions_are_covered_and_nested_extensions_round_trip(self):
        source = self.source(metadata={"nested": {"value": True}})
        output = self.execute(sources=[source])
        self.assertTrue(output.payload["evidence"][0]["metadata"]["nested"]["value"])
        tampered = {**source, "metadata": {"nested": {"value": False}}}
        rejected = self.execute("t-ext", "r-ext", sources=[tampered])
        self.assertEqual(rejected.payload["enforcement"]["status"], "NOT_EXECUTED")
        self.assertEqual(self.runtime.memory.history("t-ext"), ())

    def test_evidence_issuer_identity_is_signed_even_with_shared_key(self):
        source = self.source()
        relabeled = {**source, "attestation_issuer": "alias"}
        verifier = EvidenceVerifier(
            {"acquisition": EVIDENCE_KEY, "alias": EVIDENCE_KEY},
            "intelligence", 100, frozenset({"claim-1"}),
        )
        self.assertEqual(verifier.verify(relabeled, now=NOW)[1], "SOURCE_ATTESTATION_INVALID")

    def test_authority_issuer_identity_is_signed_even_with_shared_key(self):
        token = self.authority("t-shared", "r-shared")
        relabeled = replace(token, issuer="alias")
        request = self.runtime.agent.request(
            task_id="t-shared", run_id="r-shared", objective="x",
            sources=[self.source()], authority=relabeled,
        )
        verifier = AuthorityVerifier(
            {"governance": AUTHORITY_KEY, "alias": AUTHORITY_KEY},
            "block1-runtime", 3,
        )
        self.assertEqual(
            verifier.verify(relabeled, request, "store_candidate", NOW)[1],
            "SIGNATURE_INVALID",
        )

    def test_correlated_sources_do_not_inflate_independence(self):
        output = self.execute(sources=[self.source("s1", "same"), self.source("s2", "same")])
        self.assertEqual(output.payload["assessment"]["independent_root_count"], 1)

    def test_shared_root_with_different_correlations_is_one_independent_source(self):
        first = self.source("s1", "correlation-a", root_provenance="shared-root")
        second = self.source("s2", "correlation-b", root_provenance="shared-root")
        output = self.execute(sources=[first, second])
        self.assertEqual(output.payload["assessment"]["independent_root_count"], 1)

    def test_opposite_attested_claims_are_detected_without_self_declared_flag(self):
        output = self.execute(sources=[
            self.source("positive", "root-a", polarity=1),
            self.source("negative", "root-b", polarity=-1),
        ])
        self.assertEqual(output.epistemic_state, "CONTRADICTED")
        self.assertEqual(set(output.payload["assessment"]["contradictions"]), {"positive", "negative"})
        self.assertEqual(output.payload["enforcement"]["status"], "NOT_EXECUTED")

    def test_payload_contract_rejects_ambiguous_and_unsafe_types(self):
        bad_sources = [
            [{1: "numeric-key"}],
            [{"source_id": "x", "content": float("nan")}],
            ["not-a-mapping"],
        ]
        for index, sources in enumerate(bad_sources):
            with self.assertRaises(ContractViolation, msg=str(index)):
                self.runtime.run(
                    task_id=f"t-bad-{index}", run_id=f"r-bad-{index}", objective="x",
                    sources=sources, authority=self.authority(f"t-bad-{index}", f"r-bad-{index}"),
                )
        with self.assertRaises(ContractViolation):
            self.runtime.agent.request(
                task_id="none", run_id="none", objective="x", sources=None,
                authority=self.authority("none", "none"),
            )

    def test_contract_version_parser_rejects_malformed_versions(self):
        request = self.runtime.agent.request(
            task_id="tv", run_id="rv", objective="x", sources=[self.source()],
            authority=self.authority("tv", "rv"),
        )
        for version in ("0.3.", "0.3.evil", "0.3.0-evil", "0.3.1", "0.2.0", "1.0.0"):
            with self.assertRaises(ContractViolation):
                replace(request, contract_version=version)

    def test_memory_history_is_deeply_immutable(self):
        self.execute()
        record = self.runtime.memory.history("t1")[0]
        with self.assertRaises(TypeError):
            record["promoted"] = True
        with self.assertRaises(TypeError):
            record["assessment"]["authorization"] = True
        self.assertFalse(self.runtime.memory.history("t1")[0]["promoted"])

    def test_envelope_metadata_collections_are_deeply_string_typed(self):
        request = self.runtime.agent.request(
            task_id="tm", run_id="rm", objective="x", sources=[self.source()],
            authority=self.authority("tm", "rm"),
        )
        with self.assertRaises(ContractViolation):
            replace(request, uncertainty=(["mutable"],))
        with self.assertRaises(ContractViolation):
            replace(request, logical_time=True)
        with self.assertRaises(ContractViolation):
            replace(request, epistemic_state="NOT_A_STATE")

    def test_e04_concurrent_collision_has_exactly_one_route(self):
        original = self.runtime.agent.request(
            task_id="tc", run_id="rc", objective="x", sources=[self.source()],
            authority=self.authority("tc", "rc"),
        )
        altered = replace(original, payload={"objective": "altered", "sources": []})
        def route(envelope):
            try:
                return self.runtime.integration.route(envelope, "E01").disposition
            except IdentityCollision:
                return "COLLISION"
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(route, (original, altered)))
        self.assertEqual(sorted(outcomes), ["COLLISION", "ROUTED"])

    def test_structured_request_identity_prevents_delimiter_aliases(self):
        left_authority = self.authority_issuer.issue(
            task_id="alpha:beta", run_id="gamma", actions=("store_candidate",),
            now=NOW, ttl=50, nonce="shared-nonce",
        )
        right_authority = self.authority_issuer.issue(
            task_id="alpha", run_id="beta:gamma", actions=("store_candidate",),
            now=NOW, ttl=50, nonce="shared-nonce",
        )
        left = self.runtime.agent.request(
            task_id="alpha:beta", run_id="gamma", objective="x",
            sources=[self.source()], authority=left_authority,
        )
        right = self.runtime.agent.request(
            task_id="alpha", run_id="beta:gamma", objective="x",
            sources=[self.source()], authority=right_authority,
        )
        self.assertNotEqual(left.root_provenance, right.root_provenance)
        self.assertNotEqual(left.message_id, right.message_id)

    def test_e04_rejects_unknown_topology_and_mismatched_duplicate(self):
        envelope = self.runtime.agent.request(
            task_id="tt", run_id="rr", objective="x", sources=[self.source()],
            authority=self.authority("tt", "rr"),
        )
        self.runtime.integration.route(envelope, "E01")
        with self.assertRaises(ContractViolation):
            self.runtime.integration.route(envelope, "E99")
        evil = replace(envelope, producer="EVIL", consumer="EVIL", message_id="evil")
        with self.assertRaises(ContractViolation):
            self.runtime.integration.route(evil, "EVIL")
        self.assertTrue(any(item[2].startswith("REJECTED") for item in self.runtime.integration.audit))

    def test_direct_engine_boundary_substitution_is_rejected(self):
        envelope = self.runtime.agent.request(
            task_id="td", run_id="rd", objective="x", sources=[self.source()],
            authority=self.authority("td", "rd"),
        )
        with self.assertRaises(ContractViolation):
            self.runtime.experiment.execute(envelope)
        e02_target = envelope.handoff("E01", "E02", envelope.payload)
        with self.assertRaises(ContractViolation):
            self.runtime.acquisition.acquire(replace(e02_target, producer="EVIL"), now=NOW)
        with self.assertRaises(ContractViolation):
            self.runtime.memory.authorize_commit(envelope, action="store_candidate", now=NOW)
        self.assertEqual(self.runtime.memory.history("td"), ())

    def test_forged_e08_decision_cannot_bypass_pipeline(self):
        request = self.runtime.agent.request(
            task_id="t-forged-e08", run_id="r-forged-e08", objective="x",
            sources=[self.source()], authority=self.authority("t-forged-e08", "r-forged-e08"),
        )
        forged = replace(
            request, producer="E08", consumer="RUNTIME",
            payload={
                "memory_candidate": {"task_id": "t-forged-e08", "run_id": "r-forged-e08"},
                "governance": {
                    "decision": "ALLOW_BOUNDED_ACTION", "action": "store_candidate",
                    "decision_attestation": "0" * 64,
                },
            },
        )
        with self.assertRaises(ContractViolation):
            self.runtime.memory.authorize_commit(
                forged, action="store_candidate", now=NOW
            )
        self.assertEqual(self.runtime.memory.history("t-forged-e08"), ())

    def test_unsupported_action_cannot_reach_governance_or_effect(self):
        with self.assertRaises(ContractViolation):
            self.runtime.run(
                task_id="taction", run_id="raction", objective="x",
                sources=[self.source()], authority=self.authority_issuer.issue(
                    task_id="taction", run_id="raction", actions=("read_only",),
                    now=NOW, ttl=50,
                ), action="read_only",
            )
        self.assertEqual(self.runtime.memory.history("taction"), ())

    def test_store_unavailability_prevents_stable_and_effect(self):
        self.runtime.store.healthcheck = lambda **_kwargs: False
        result = self.execute("t-health", "r-health")
        self.assertEqual(result.payload["stability"]["health"], "AT_RISK")
        self.assertFalse(result.payload["stability"]["store_available"])
        self.assertEqual(result.payload["enforcement"]["status"], "NOT_EXECUTED")
        self.assertEqual(self.runtime.memory.history("t-health"), ())

    def test_e04_capacity_exhaustion_fails_closed(self):
        integration = IntegrationEngine(audit_limit=10, seen_limit=1)
        first = self.runtime.agent.request(
            task_id="cap-1", run_id="cap-1", objective="x", sources=[self.source()],
            authority=self.authority("cap-1", "cap-1"),
        )
        second = self.runtime.agent.request(
            task_id="cap-2", run_id="cap-2", objective="x", sources=[self.source("s2")],
            authority=self.authority("cap-2", "cap-2"),
        )
        integration.route(first, "E01")
        with self.assertRaises(ContractViolation):
            integration.route(second, "E01")
        self.assertEqual(integration.audit[-1][2], "REJECTED_CAPACITY")

    def test_execution_outcome_tamper_cannot_become_candidate(self):
        request = self.runtime.agent.request(
            task_id="t-digest", run_id="r-digest", objective="x", sources=[self.source()],
            authority=self.authority("t-digest", "r-digest"),
        )
        acquired = self.runtime.acquisition.acquire(
            request.handoff("E01", "E02", request.payload), now=NOW
        ).envelope
        executed = self.runtime.experiment.execute(acquired).envelope
        tampered = replace(executed, payload={**executed.payload, "method_version": "evil"})
        assessed = self.runtime.evaluation.evaluate(tampered).envelope
        self.assertEqual(assessed.payload["assessment"]["disposition"], "INSUFFICIENT")

    def test_evidence_substitution_after_e03_invalidates_execution_attestation(self):
        request = self.runtime.agent.request(
            task_id="t-sub", run_id="r-sub", objective="x", sources=[self.source()],
            authority=self.authority("t-sub", "r-sub"),
        )
        acquired = self.runtime.acquisition.acquire(
            request.handoff("E01", "E02", request.payload), now=NOW
        ).envelope
        executed = self.runtime.experiment.execute(acquired).envelope
        unsigned = {
            key: value for key, value in self.source("substitute").items()
            if key != "attestation"
        }
        substituted = replace(executed, payload={
            **executed.payload,
            "evidence": (unsigned,),
        })
        assessed = self.runtime.evaluation.evaluate(substituted).envelope
        self.assertEqual(assessed.payload["assessment"]["disposition"], "INSUFFICIENT")

    def test_memory_history_detects_durable_tampering(self):
        self.execute()
        self.runtime.store._db.execute(
            "UPDATE memory_candidates SET record_json = ? WHERE run_id = ?",
            ('{"tampered":true}', "r1"),
        )
        with self.assertRaises(ContractViolation):
            self.runtime.memory.history("t1")

    def test_database_writer_cannot_recalculate_keyed_memory_integrity(self):
        self.execute()
        row = self.runtime.store._db.execute(
            "SELECT previous_hash, record_json FROM memory_candidates WHERE run_id = ?",
            ("r1",),
        ).fetchone()
        record = json.loads(row["record_json"])
        record["promoted"] = True
        record.pop("record_hash")
        encoded = json.dumps(record, sort_keys=True, separators=(",", ":"))
        attacker_hash = sha256((row["previous_hash"] + encoded).encode()).hexdigest()
        record["record_hash"] = attacker_hash
        self.runtime.store._db.execute(
            "UPDATE memory_candidates SET record_hash = ?, record_json = ? WHERE run_id = ?",
            (
                attacker_hash,
                json.dumps(record, sort_keys=True, separators=(",", ":")),
                "r1",
            ),
        )
        with self.assertRaises(ContractViolation):
            self.runtime.memory.history("t1")

    def test_authorized_candidate_fingerprint_is_persisted_exactly(self):
        result = self.execute()
        stored = self.runtime.store._db.execute(
            "SELECT candidate_fingerprint FROM memory_candidates WHERE run_id = ?",
            ("r1",),
        ).fetchone()[0]
        self.assertEqual(stored, result.payload["governance"]["candidate_fingerprint"])
        self.assertEqual(stored, result.payload["enforcement"]["candidate_fingerprint"])

    def test_terminal_detects_durable_tampering(self):
        self.execute()
        self.runtime.store._db.execute(
            "UPDATE terminal_runs SET envelope_json = ? WHERE run_id = ?",
            ('{"tampered":true}', "r1"),
        )
        with self.assertRaises(ContractViolation):
            self.runtime.store.get_terminal("r1")

    def test_terminal_request_identity_detects_durable_tampering(self):
        self.execute()
        self.runtime.store._db.execute(
            "UPDATE terminal_runs SET request_fingerprint = ? WHERE run_id = ?",
            ("0" * 64, "r1"),
        )
        with self.assertRaises(ContractViolation):
            self.runtime.store.get_terminal("r1")

    def test_unversioned_incompatible_schema_is_rejected_without_promotion(self):
        self.runtime.close()
        self.db.unlink()
        connection = sqlite3.connect(self.db)
        connection.execute("CREATE TABLE memory_candidates(junk TEXT)")
        connection.commit()
        connection.close()
        with self.assertRaises(ContractViolation):
            self.runtime = self.make_runtime()
        connection = sqlite3.connect(self.db)
        self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 0)
        connection.close()
        self.runtime = self.make_runtime(store_path=Path(self.temp.name) / "replacement.sqlite3")

    def test_authority_expiring_during_pipeline_cannot_commit(self):
        self.runtime.close()
        moments = iter((NOW, NOW + 40, NOW + 60))
        self.runtime = self.make_runtime(clock=lambda: next(moments))
        token = self.authority_issuer.issue(
            task_id="t-expire", run_id="r-expire", actions=("store_candidate",),
            now=NOW, ttl=50,
        )
        with self.assertRaises(ContractViolation):
            self.execute("t-expire", "r-expire", authority=token)
        self.assertEqual(self.runtime.memory.history("t-expire"), ())

    def test_journal_capacity_is_bounded(self):
        self.runtime.close()
        self.runtime = self.make_runtime(
            store_path=Path(self.temp.name) / "journal-capacity.sqlite3",
            max_records=1, max_attempts=1,
        )
        first = self.execute("t-journal-1", "r-journal-1", authority=None)
        self.assertEqual(first.payload["enforcement"]["status"], "NOT_EXECUTED")
        with self.assertRaises(ContractViolation):
            self.execute("t-journal-2", "r-journal-2", authority=None)
        count = self.runtime.store._db.execute(
            "SELECT COUNT(*) FROM execution_journal"
        ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_journal_capacity_is_bounded_across_connections(self):
        self.runtime.close()
        capacity_db = Path(self.temp.name) / "journal-multiconnection.sqlite3"
        first = OperationalStore(
            capacity_db, integrity_key=STORAGE_KEY, max_records=10, max_attempts=1
        )
        second = OperationalStore(
            capacity_db, integrity_key=STORAGE_KEY, max_records=10, max_attempts=1
        )
        def write(item):
            store, fingerprint = item
            try:
                store.record_state(fingerprint, fingerprint, "STARTED", "test", NOW)
                return "OK"
            except ContractViolation:
                return "CAPACITY"
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(write, ((first, "one"), (second, "two"))))
        self.assertEqual(sorted(outcomes), ["CAPACITY", "OK"])
        self.assertEqual(first._db.execute("SELECT COUNT(*) FROM execution_journal").fetchone()[0], 1)
        first.close()
        second.close()
        self.runtime = self.make_runtime(store_path=Path(self.temp.name) / "replacement.sqlite3")

    def test_versioned_schema_missing_constraints_is_rejected(self):
        malformed = Path(self.temp.name) / "malformed-v5.sqlite3"
        connection = sqlite3.connect(malformed)
        connection.executescript("""
            CREATE TABLE memory_candidates(
                task_id TEXT, run_id TEXT, version INTEGER, candidate_fingerprint TEXT,
                previous_hash TEXT, record_hash TEXT, record_json TEXT
            );
            CREATE TABLE terminal_runs(
                request_fingerprint TEXT, run_id TEXT, result_fingerprint TEXT,
                terminal_hash TEXT, effect_committed INTEGER, envelope_json TEXT
            );
            CREATE TABLE execution_journal(
                attempt_fingerprint TEXT, run_id TEXT, state TEXT, reason TEXT, updated_at INTEGER
            );
            PRAGMA user_version = 7;
        """)
        connection.close()
        with self.assertRaises(ContractViolation):
            OperationalStore(malformed, integrity_key=STORAGE_KEY)

    def test_unapproved_sqlite_trigger_is_rejected_before_effect(self):
        self.runtime.store._db.execute("""
            CREATE TRIGGER forbidden_trigger AFTER INSERT ON terminal_runs
            BEGIN
                DELETE FROM memory_candidates;
            END
        """)
        with self.assertRaises(ContractViolation):
            self.execute("t-trigger", "r-trigger")
        self.assertEqual(self.runtime.memory.history("t-trigger"), ())

    def test_restart_rejects_extra_sqlite_schema_objects(self):
        self.runtime.close()
        connection = sqlite3.connect(self.db)
        connection.execute("CREATE TABLE unapproved_table(value TEXT)")
        connection.commit()
        connection.close()
        with self.assertRaises(ContractViolation):
            self.runtime = self.make_runtime()
        self.runtime = self.make_runtime(
            store_path=Path(self.temp.name) / "replacement.sqlite3"
        )

    def test_post_commit_delivery_failure_preserves_committed_journal(self):
        original = self.runtime.integration.route
        def fail_caller(envelope, consumer):
            if consumer == "CALLER":
                raise OSError("caller delivery unavailable")
            return original(envelope, consumer)
        self.runtime.integration.route = fail_caller
        with self.assertRaises(OSError):
            self.execute()
        self.assertIsNotNone(self.runtime.store.get_terminal("r1"))
        self.assertEqual(len(self.runtime.memory.history("t1")), 1)
        self.assertEqual(
            self.runtime.store.journal("r1")[-1]["state"],
            "EFFECT_AND_TERMINAL_COMMITTED",
        )

    def test_terminal_journal_state_cannot_regress_to_started(self):
        self.execute()
        fingerprint = self.runtime.store.get_terminal("r1")[0]
        self.runtime.store.record_state(
            fingerprint, "r1", "STARTED", "late concurrent replay", NOW + 1
        )
        entry = self.runtime.store.journal("r1")[-1]
        self.assertEqual(entry["state"], "EFFECT_AND_TERMINAL_COMMITTED")
        self.assertEqual(entry["reason"], "COMMITTED")

    def test_noncanonical_claim_alias_is_rejected(self):
        result = self.execute(
            "t-alias", "r-alias", sources=[self.source(claim_key="CLAIM-1")]
        )
        self.assertEqual(result.payload["enforcement"]["status"], "NOT_EXECUTED")

    def test_unauthorized_attempt_cannot_durably_squat_run_identity(self):
        first = self.execute("ts", "rs", authority=None)
        self.assertEqual(first.payload["governance"]["decision"], "QUARANTINE")
        self.assertEqual(
            self.runtime.store.get_terminal("rs")[1].payload["enforcement"]["status"],
            "NOT_EXECUTED",
        )
        second = self.execute("ts", "rs", authority=self.authority("ts", "rs"))
        self.assertEqual(second.payload["enforcement"]["status"], "COMMITTED")
        self.assertEqual(len(self.runtime.memory.history("ts")), 1)

    def test_exact_no_effect_replay_is_historical_and_restart_safe(self):
        first = self.execute("t-deny", "r-deny", authority=None)
        second = self.execute("t-deny", "r-deny", authority=None)
        self.assertEqual(first.payload["enforcement"]["status"], "NOT_EXECUTED")
        self.assertEqual(second.payload["replay"]["mode"], "HISTORICAL_TERMINAL")
        self.runtime.close()
        self.current_time += 10
        self.runtime = self.make_runtime()
        third = self.execute("t-deny", "r-deny", authority=None)
        self.assertEqual(third.payload["replay"]["mode"], "HISTORICAL_TERMINAL")

    def test_committed_terminal_requires_matching_durable_effect(self):
        self.execute()
        self.runtime.store._db.execute(
            "DELETE FROM memory_candidates WHERE run_id = ?", ("r1",)
        )
        with self.assertRaises(ContractViolation):
            self.runtime.store.get_terminal("r1")

    def test_committed_terminal_authenticates_effect_columns_and_record(self):
        self.execute()
        self.runtime.store._db.execute(
            "UPDATE memory_candidates SET task_id = ? WHERE run_id = ?",
            ("moved-task", "r1"),
        )
        with self.assertRaises(ContractViolation):
            self.runtime.store.get_terminal("r1")

    def test_restart_rejects_wrong_storage_key_and_capacity_drift(self):
        self.execute()
        self.runtime.close()
        with self.assertRaises(ContractViolation):
            self.runtime = self.make_runtime(storage_integrity_key=b"z" * 32)
        with self.assertRaises(ContractViolation):
            self.runtime = self.make_runtime(max_records=99_999)
        self.runtime = self.make_runtime()

    def test_full_memory_store_prevents_e07_false_green(self):
        self.runtime.close()
        self.runtime = self.make_runtime(
            store_path=Path(self.temp.name) / "full-memory.sqlite3",
            max_records=1, max_attempts=10,
        )
        self.execute("t-full-1", "r-full-1")
        result = self.execute("t-full-2", "r-full-2")
        self.assertEqual(result.payload["stability"]["health"], "AT_RISK")
        self.assertFalse(result.payload["stability"]["store_available"])
        self.assertEqual(result.payload["enforcement"]["status"], "NOT_EXECUTED")

    def test_concurrent_last_capacity_is_a_terminal_no_effect_not_failure(self):
        self.runtime.close()
        capacity_db = Path(self.temp.name) / "last-capacity.sqlite3"
        first_runtime = self.make_runtime(
            store_path=capacity_db, max_records=1, max_attempts=10
        )
        second_runtime = self.make_runtime(
            store_path=capacity_db, max_records=1, max_attempts=10
        )
        def run(item):
            runtime, task_id, run_id = item
            return runtime.run(
                task_id=task_id, run_id=run_id, objective="x",
                sources=[self.source(source_id=run_id)],
                authority=self.authority(task_id, run_id),
            )
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                outputs = list(pool.map(run, (
                    (first_runtime, "capacity-a", "capacity-a"),
                    (second_runtime, "capacity-b", "capacity-b"),
                )))
            self.assertEqual(
                sorted(item.payload["enforcement"]["status"] for item in outputs),
                ["COMMITTED", "NOT_EXECUTED"],
            )
            denied = next(
                item for item in outputs
                if item.payload["enforcement"]["status"] == "NOT_EXECUTED"
            )
            reason = denied.payload["enforcement"].get("reason")
            self.assertTrue(
                reason == "CAPACITY_CHANGED_AFTER_STABILITY_OBSERVATION"
                or denied.payload["stability"]["store_available"] is False
            )
        finally:
            first_runtime.close()
            second_runtime.close()
        self.runtime = self.make_runtime(store_path=Path(self.temp.name) / "replacement.sqlite3")

    def test_post_e08_context_mutation_invalidates_decision_binding(self):
        task_id, run_id = "t-e08-bind", "r-e08-bind"
        request = self.runtime.agent.request(
            task_id=task_id, run_id=run_id, objective="x", sources=[self.source()],
            authority=self.authority(task_id, run_id),
        )
        current = self.runtime.acquisition.acquire(
            request.handoff("E01", "E02", request.payload), now=NOW
        ).envelope
        current = self.runtime.experiment.execute(current).envelope
        current = self.runtime.evaluation.evaluate(current).envelope
        current = self.runtime.memory.prepare_candidate(current).envelope
        current = self.runtime.stability.assess(current, store_available=True).envelope
        decision = self.runtime.governance.decide(
            current, action="store_candidate", now=NOW
        ).envelope
        tampered = replace(decision, payload={
            **decision.payload,
            "stability": {**decision.payload["stability"], "health": "AT_RISK"},
        })
        with self.assertRaises(ContractViolation):
            self.runtime.memory.authorize_commit(
                tampered, action="store_candidate", now=NOW
            )
        governance_tampered = replace(decision, payload={
            **decision.payload,
            "governance": {
                **decision.payload["governance"],
                "decision_is_enforcement": True,
                "runtime_effect_observed": True,
                "authority_reason": "FABRICATED",
            },
        })
        with self.assertRaises(ContractViolation):
            self.runtime.memory.authorize_commit(
                governance_tampered, action="store_candidate", now=NOW
            )

    def test_commit_reauthorization_occurs_inside_lock_and_rejects_expiry(self):
        task_id, run_id = "t-lock-time", "r-lock-time"
        token = self.authority_issuer.issue(
            task_id=task_id, run_id=run_id, actions=("store_candidate",),
            now=NOW, ttl=50,
        )
        request = self.runtime.agent.request(
            task_id=task_id, run_id=run_id, objective="x",
            sources=[self.source()], authority=token,
        )
        request_fingerprint = request.fingerprint
        self.runtime.store.record_state(
            request_fingerprint, run_id, "STARTED", "test", NOW
        )
        current = self.runtime.acquisition.acquire(
            request.handoff("E01", "E02", request.payload), now=NOW
        ).envelope
        current = self.runtime.experiment.execute(current).envelope
        current = self.runtime.evaluation.evaluate(current).envelope
        current = self.runtime.memory.prepare_candidate(current).envelope
        current = self.runtime.stability.assess(current, store_available=True).envelope
        decision = self.runtime.governance.decide(
            current, action="store_candidate", now=NOW
        ).envelope
        observed = {"inside_transaction": False}
        def expired_authorization():
            observed["inside_transaction"] = self.runtime.store._db.in_transaction
            candidate = self.runtime.memory.authorize_commit(
                decision, action="store_candidate", now=NOW + 60
            )
            return candidate, NOW + 60
        with self.assertRaises(ContractViolation):
            self.runtime.store.commit_effect_and_terminal(
                request_fingerprint=request_fingerprint,
                decision_envelope=decision,
                candidate_fingerprint=decision.payload["governance"]["candidate_fingerprint"],
                authorize_effect=expired_authorization,
                action="store_candidate",
            )
        self.assertTrue(observed["inside_transaction"])
        self.assertEqual(self.runtime.memory.history(task_id), ())

    def test_execution_attestation_cannot_move_to_another_task_run(self):
        request = self.runtime.agent.request(
            task_id="source-task", run_id="source-run", objective="x",
            sources=[self.source()], authority=self.authority("source-task", "source-run"),
        )
        acquired = self.runtime.acquisition.acquire(
            request.handoff("E01", "E02", request.payload), now=NOW
        ).envelope
        executed = self.runtime.experiment.execute(acquired).envelope
        transplanted = replace(executed, task_id="target-task", run_id="target-run")
        assessed = self.runtime.evaluation.evaluate(transplanted).envelope
        self.assertEqual(assessed.payload["assessment"]["disposition"], "INSUFFICIENT")

    def test_malformed_authority_structure_is_rejected_before_verification(self):
        token = self.authority("ta-struct", "ra-struct")
        for mutation in (
            {"signature": None}, {"signature": "xyz"},
            {"committed": 1}, {"actions": "store_candidate"},
        ):
            with self.assertRaises(ContractViolation):
                replace(token, **mutation)

    def test_foreign_unversioned_sqlite_is_not_modified_or_left_open(self):
        self.runtime.close()
        foreign = Path(self.temp.name) / "foreign.sqlite3"
        connection = sqlite3.connect(foreign)
        connection.execute("CREATE TABLE user_data(value TEXT)")
        connection.commit()
        connection.close()
        with self.assertRaises(ContractViolation):
            OperationalStore(foreign, integrity_key=STORAGE_KEY)
        connection = sqlite3.connect(foreign)
        self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 0)
        self.assertEqual(
            connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall(),
            [("user_data",)],
        )
        connection.close()
        foreign.unlink()
        self.runtime = self.make_runtime(store_path=Path(self.temp.name) / "replacement.sqlite3")

    def test_cold_start_is_atomic_across_concurrent_openers(self):
        self.runtime.close()
        cold = Path(self.temp.name) / "cold.sqlite3"
        def open_store(_: int):
            store = OperationalStore(cold, integrity_key=STORAGE_KEY, max_records=10)
            try:
                return store._db.execute("PRAGMA user_version").fetchone()[0]
            finally:
                store.close()
        with ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(list(pool.map(open_store, range(4))), [8, 8, 8, 8])
        self.runtime = self.make_runtime(store_path=Path(self.temp.name) / "replacement.sqlite3")

    def test_schema_with_extra_check_is_rejected_exactly(self):
        self.runtime.close()
        altered = Path(self.temp.name) / "extra-check.sqlite3"
        probe = OperationalStore(":memory:", integrity_key=STORAGE_KEY)
        key_check = probe._metadata_mac()
        probe.close()
        connection = sqlite3.connect(altered)
        definitions = OperationalStore._SCHEMA_SQL
        connection.execute(definitions["memory_candidates"])
        connection.execute(definitions["terminal_runs"].replace(
            "envelope_json TEXT NOT NULL", "envelope_json TEXT NOT NULL CHECK(length(envelope_json) > 0)"
        ))
        connection.execute(definitions["execution_journal"])
        connection.execute(definitions["store_metadata"])
        connection.execute(definitions["one_committed_effect_per_run"])
        connection.execute(
            "INSERT INTO store_metadata VALUES (1, 100000, 100000, ?)", (key_check,)
        )
        connection.execute("PRAGMA user_version = 8")
        connection.commit()
        connection.close()
        with self.assertRaises(ContractViolation):
            OperationalStore(altered, integrity_key=STORAGE_KEY)
        self.runtime = self.make_runtime(store_path=Path(self.temp.name) / "replacement.sqlite3")

    def test_corrupt_predecessor_cannot_be_extended(self):
        self.execute("chain", "chain-1")
        self.runtime.store._db.execute(
            "UPDATE memory_candidates SET record_hash = ? WHERE run_id = ?", ("x" * 64, "chain-1")
        )
        result = self.execute("chain", "chain-2")
        self.assertEqual(result.payload["enforcement"]["status"], "NOT_EXECUTED")
        self.assertEqual(
            self.runtime.store._db.execute(
                "SELECT COUNT(*) FROM memory_candidates WHERE task_id = ?", ("chain",)
            ).fetchone()[0], 1,
        )

    def test_active_connection_rejects_metadata_tampering_before_write(self):
        self.runtime.store._db.execute("UPDATE store_metadata SET max_records = 9")
        with self.assertRaises(ContractViolation):
            self.execute("metadata", "metadata-1")
        self.assertFalse(self.runtime.store.healthcheck())

    def test_effect_transaction_requires_authenticated_started_journal(self):
        request = self.runtime.agent.request(
            task_id="journal", run_id="journal-1", objective="x", sources=[self.source()],
            authority=self.authority("journal", "journal-1"),
        )
        self.runtime.store.record_state(request.fingerprint, "journal-1", "STARTED", "test", NOW)
        current = self.runtime.acquisition.acquire(request.handoff("E01", "E02", request.payload), now=NOW).envelope
        current = self.runtime.experiment.execute(current).envelope
        current = self.runtime.evaluation.evaluate(current).envelope
        current = self.runtime.memory.prepare_candidate(current).envelope
        current = self.runtime.stability.assess(current, store_available=True).envelope
        decision = self.runtime.governance.decide(current, action="store_candidate", now=NOW).envelope
        def remove_journal(_: str):
            self.runtime.store._db.execute("DELETE FROM execution_journal WHERE attempt_fingerprint = ?", (request.fingerprint,))
        self.runtime.store.failure_injector = remove_journal
        with self.assertRaises(ContractViolation):
            self.runtime.store.commit_effect_and_terminal(
                request_fingerprint=request.fingerprint, decision_envelope=decision,
                candidate_fingerprint=decision.payload["governance"]["candidate_fingerprint"],
                authorize_effect=lambda: (self.runtime.memory.authorize_commit(decision, action="store_candidate", now=NOW), NOW),
                action="store_candidate",
            )
        self.assertIsNone(self.runtime.store.get_terminal("journal-1"))

    def test_failed_journal_cannot_transition_backwards_or_commit_effect(self):
        self.runtime.store.record_state("attempt", "failed-run", "STARTED", "test", 200)
        self.runtime.store.record_state("attempt", "failed-run", "FAILED", "failure", 200)
        with self.assertRaises(ContractViolation):
            self.runtime.store.record_state("attempt", "failed-run", "STARTED", "late", 50)
        self.assertEqual(self.runtime.store.journal("failed-run")[-1]["state"], "FAILED")

    def test_healthcheck_fails_closed_on_authenticated_row_corruption(self):
        self.execute("health", "health-1")
        original_hash = self.runtime.store._db.execute(
            "SELECT record_hash FROM memory_candidates WHERE run_id = ?", ("health-1",)
        ).fetchone()[0]
        self.runtime.store._db.execute(
            "UPDATE memory_candidates SET record_hash = ? WHERE run_id = ?", ("x" * 64, "health-1")
        )
        self.assertFalse(self.runtime.store.healthcheck(write_required=True))
        self.runtime.store._db.execute(
            "UPDATE memory_candidates SET record_hash = ? WHERE run_id = ?", (original_hash, "health-1")
        )
        self.runtime.store._db.execute(
            "UPDATE execution_journal SET journal_hash = ? WHERE run_id = ?", ("x" * 64, "health-1")
        )
        self.assertFalse(self.runtime.store.healthcheck(write_required=True))


if __name__ == "__main__":
    unittest.main()

