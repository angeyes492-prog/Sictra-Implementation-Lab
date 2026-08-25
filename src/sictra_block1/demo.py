"""Emit a deterministic bounded-operational evidence manifest."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile

from .common import AuthorityIssuer
from .evidence import EvidenceIssuer
from .runtime import IntelligenceRuntime


def main() -> int:
    now = 1_000
    authority_key = b"ci-authority-fixture-key-32bytes!"
    evidence_key = b"ci-evidence-fixture-key--32bytes!"
    decision_key = b"ci-decision-fixture-key--32bytes!"
    execution_key = b"ci-execution-fixture-key-32bytes!"
    authority_issuer = AuthorityIssuer("ci-governance", authority_key, "block1-runtime", 3)
    evidence_issuer = EvidenceIssuer("ci-acquisition", evidence_key)
    source = evidence_issuer.attest({
        "source_id": "fixture-observation-1", "content": "bounded observation",
        "observed_at": now, "root_provenance": "fixture-root-1",
        "evidence_class": "OBSERVED", "scope": "intelligence",
        "correlation_id": "fixture-correlation-1", "claim_key": "fixture-claim",
        "polarity": 1,
    })
    authority = authority_issuer.issue(
        task_id="reference-task", run_id="reference-run",
        actions=("store_candidate",), now=now, ttl=10, nonce="ci-fixed-nonce",
    )
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "operational.sqlite3"
        runtime = IntelligenceRuntime.operational(
            store_path=database, authority_keys={"ci-governance": authority_key},
            authority_audience="block1-runtime", authority_epoch=3,
            evidence_keys={"ci-acquisition": evidence_key}, evidence_scope="intelligence",
            evidence_max_age=100, evidence_claims=frozenset({"fixture-claim"}),
            execution_key=execution_key, decision_key=decision_key,
            clock=lambda: now,
        )
        result = runtime.run(
            task_id="reference-task", run_id="reference-run",
            objective="demonstrate bounded operational Intelligence",
            sources=[source], authority=authority,
        )
        replay = runtime.run(
            task_id="reference-task", run_id="reference-run",
            objective="demonstrate bounded operational Intelligence",
            sources=[source], authority=authority,
        )
        manifest = {
            "scope": "BLOCK1_BOUNDED_OPERATIONAL_RUNTIME",
            "contract_version": result.contract_version,
            "trace": list(result.trace),
            "integration_audit": runtime.integration.audit,
            "epistemic_state": result.epistemic_state,
            "governance": dict(result.payload["governance"]),
            "enforcement": dict(result.payload["enforcement"]),
            "memory_record_count": len(runtime.memory.history("reference-task")),
            "replay_mode": replay.payload["replay"]["mode"],
            "replay_new_effect": replay.payload["replay"]["new_effect"],
            "replay_same_enforcement": replay.payload["enforcement"] == result.payload["enforcement"],
            "execution_fingerprint": result.fingerprint,
            "non_claims": [
                "production key management", "high availability",
                "global normative acceptance", "truth of source content",
            ],
        }
        runtime.close()
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

