"""Emit a deterministic reference-runtime evidence manifest."""

from __future__ import annotations

import json

from .common import AuthorityContext
from .runtime import IntelligenceRuntime


def main() -> int:
    runtime = IntelligenceRuntime.reference()
    result = runtime.run(
        task_id="reference-task", run_id="reference-run",
        objective="demonstrate the bounded eight-engine Intelligence flow",
        sources=[{"source_id": "fixture-observation-1", "content": "bounded observation",
                  "observed_at": 1, "root_provenance": "fixture-root-1"}],
        authority=AuthorityContext("reference-authority", 1, ("store_candidate",), 10, True),
        action="store_candidate", now=1, known_epoch=1,
    )
    manifest = {
        "scope": "BLOCK1_REFERENCE_RUNTIME",
        "contract_version": result.contract_version,
        "task_id": result.task_id,
        "run_id": result.run_id,
        "trace": list(result.trace),
        "integration_audit": runtime.integration.audit,
        "epistemic_state": result.epistemic_state,
        "governance": dict(result.payload["governance"]),
        "execution_fingerprint": result.fingerprint,
        "non_claims": ["production runtime", "global acceptance", "enforcement evidence"],
    }
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
