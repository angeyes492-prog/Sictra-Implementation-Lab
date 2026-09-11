"""Run the deterministic local Block 2 reference fixture."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json

from .project_graph import ProjectGraphStore
from .reference_fixture import reference_run_input, run_reference_fixture
from .traceable_runtime import execute_traceable_block2


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute the bounded SICTrA Block 2 reference fixture")
    parser.add_argument("--trace-db", help="Append run lineage and a CDD to this local SQLite database")
    parser.add_argument("--project-id", default="PROJECT-DEMO")
    parser.add_argument("--document-id", default="DOCUMENT-DEMO")
    parser.add_argument("--actor-id", default="ACTOR-LOCAL-DEMO")
    parser.add_argument("--run-id", help="Stable idempotency identity; otherwise derived from project, envelope and --run-at")
    parser.add_argument(
        "--run-at",
        help="Timezone-aware ISO timestamp used as the idempotent run identity; defaults to now",
    )
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    now = datetime.fromisoformat(args.run_at) if args.run_at else datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise SystemExit("--run-at must include a timezone offset")
    trace = None
    if args.trace_db:
        with ProjectGraphStore(args.trace_db) as graph:
            trace = execute_traceable_block2(
                reference_run_input(now), graph=graph, project_id=args.project_id,
                document_id=args.document_id, actor_id=args.actor_id, run_id=args.run_id, now=now,
            )
        result = trace.run
    else:
        result = run_reference_fixture(now)
    candidate = result.production.candidate if result.production else None
    print(json.dumps({
        "completed": result.completed,
        "stopped_at": result.stopped_at,
        "stages": [{"engine": item.engine, "disposition": item.disposition, "reasons": item.reasons} for item in result.stages],
        "artifact": None if candidate is None else {
            "media_type": candidate.artifact.media_type,
            "sha256": candidate.artifact.sha256,
            "accessibility_media_type": candidate.artifact.accessibility_media_type,
        },
        "publication_state": result.publication_state,
        "acceptance_state": result.acceptance_state,
        "memory_store_action": result.memory_store_action,
        "model_gateway": None if result.gateway_receipt is None else {
            "receipt_id": result.gateway_receipt.receipt_id,
            "provider_manifest_id": result.gateway_receipt.provider_manifest_id,
            "outcome": result.gateway_receipt.outcome,
            "output_sha256": result.gateway_receipt.output_hash,
            "quarantine_state": result.gateway_receipt.quarantine_state,
        },
        "trace": None if trace is None else {
            "graph_action": trace.graph_action,
            "run_id": trace.run_id,
            "database": args.trace_db,
            "project_id": args.project_id,
            "document_id": None if trace.document is None else trace.document.document_id,
            "document_version_id": None if trace.document is None else trace.document.version_id,
            "document_sha256": None if trace.document is None else trace.document.content_hash,
            "state": None if trace.document is None else trace.document.state,
        },
    }, indent=2))
    return 0 if result.completed else 1


if __name__ == "__main__":
    raise SystemExit(main())
