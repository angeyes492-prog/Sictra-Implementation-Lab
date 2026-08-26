Use '--' to separate paths from revisions, like this:
'git <command> [<revision>...] -- [<file>...]'
e07a88cd5091c5c5c7ad89aee4f6c6d72e42002e
-encodedCommand
dAByAGUAZQA=
"""Interactive, local-only laboratory for the Block 1 bounded runtime.

This is deliberately a test harness.  Its fixture keys, generated observations
and SQLite store are not production configuration or an external integration.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
from typing import Any, Mapping

from .common import AuthorityIssuer, plain_copy
from .evidence import EvidenceIssuer
from .runtime import IntelligenceRuntime


LAB_SCOPE = "BLOCK1_LOCAL_INTERACTIVE_LAB"
SCENARIOS = ("valid", "missing-authority", "stale-evidence", "wrong-scope")
_NOW = 1_000
_AUTHORITY_KEY = b"lab-authority-fixture-key--32bytes!"
_EVIDENCE_KEY = b"lab-evidence-fixture-key---32bytes!"
_DECISION_KEY = b"lab-decision-fixture-key---32bytes!"
_EXECUTION_KEY = b"lab-execution-fixture-key--32bytes!"
_STORAGE_KEY = b"lab-storage-integrity-key---32bytes!"


def _runtime(store_path: str | Path) -> IntelligenceRuntime:
    return IntelligenceRuntime.operational(
        store_path=store_path,
        authority_keys={"lab-governance": _AUTHORITY_KEY},
        authority_audience="block1-lab",
        authority_epoch=1,
        evidence_keys={"lab-acquisition": _EVIDENCE_KEY},
        evidence_scope="intelligence",
        evidence_max_age=100,
        evidence_claims=frozenset({"lab-claim"}),
        execution_key=_EXECUTION_KEY,
        decision_key=_DECISION_KEY,
        storage_integrity_key=_STORAGE_KEY,
        clock=lambda: _NOW,
    )


def _source(scenario: str) -> dict[str, Any]:
    observed_at, scope = _NOW, "intelligence"
    if scenario == "stale-evidence":
        observed_at = _NOW - 101
    if scenario == "wrong-scope":
        scope = "design"
    return EvidenceIssuer("lab-acquisition", _EVIDENCE_KEY).attest({
        "source_id": f"lab-source-{scenario}",
        "content": "local fixture observation; no external source was contacted",
        "observed_at": observed_at,
        "root_provenance": "lab-generated-fixture",
        "evidence_class": "OBSERVED",
        "scope": scope,
        "correlation_id": f"lab-correlation-{scenario}",
        "claim_key": "lab-claim",
        "polarity": 1,
    })


def execute_scenario(scenario: str, *, store_path: str | Path) -> Mapping[str, Any]:
    """Run one deterministic scenario and return inspectable lab evidence."""
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown lab scenario: {scenario}")
    task_id, run_id = f"lab-task-{scenario}", f"lab-run-{scenario}"
    authority = None
    if scenario != "missing-authority":
        authority = AuthorityIssuer(
            "lab-governance", _AUTHORITY_KEY, "block1-lab", 1
        ).issue(
            task_id=task_id, run_id=run_id, actions=("store_candidate",),
            now=_NOW, ttl=10, nonce=f"lab-nonce-{scenario}",
        )
    runtime = _runtime(store_path)
    try:
        result = runtime.run(
            task_id=task_id, run_id=run_id, objective="exercise local bounded runtime",
            sources=[_source(scenario)], authority=authority,
        )
        return {
            "scope": LAB_SCOPE,
            "scenario": scenario,
            "result": {
                "trace": list(result.trace),
                "epistemic_state": result.epistemic_state,
                "governance": plain_copy(result.payload["governance"]),
                "enforcement": plain_copy(result.payload["enforcement"]),
                "restrictions": list(result.restrictions),
            },
            "journal": plain_copy(runtime.store.journal(run_id)),
            "memory_record_count": len(runtime.memory.history(task_id)),
            "non_claims": [
                "production user interface", "external data acquisition",
                "production credentials or key management", "global gate acceptance",
            ],
        }
    finally:
        runtime.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=SCENARIOS)
    parser.add_argument(
        "--store", type=Path,
        help="Optional local SQLite path. Without it, an ephemeral store is used.",
    )
    args = parser.parse_args()
    if args.store:
        manifest = execute_scenario(args.scenario, store_path=args.store)
    else:
        with tempfile.TemporaryDirectory(prefix="sictra-block1-lab-") as directory:
            manifest = execute_scenario(args.scenario, store_path=Path(directory) / "lab.sqlite3")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
