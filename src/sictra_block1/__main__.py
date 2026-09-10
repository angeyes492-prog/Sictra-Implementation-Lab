"""Run the bounded local execution slice against a JSON fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .context import ContextRecord, build_context_pack
from .reassessment import reassess


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--agent", default="Intelligence")
    args = parser.parse_args()
    payload = json.loads(args.fixture.read_text(encoding="utf-8"))
    records = [
        ContextRecord(
            record_id=item["record_id"], agent=item["agent"], layer=item["layer"],
            temporal_state=item["temporal_state"], selectable=item["selectable"],
            context_eligibility=item["context_eligibility"],
            contradiction_state=item["contradiction_state"], relation_type=item["relation_type"],
            source_identity=item["source_identity"], root_provenance=item["root_provenance"],
            derivation_graph=tuple(item["derivation_graph"]), temporal_scope=item["temporal_scope"],
            evidence_class=item["evidence_class"], notes=item.get("notes", ""),
        ) for item in payload
    ]
    pack = build_context_pack(records, args.agent)
    result = reassess(pack)
    manifest = {
        "scope": "LOCAL_BOUNDED_CONTEXT_TO_REASSESSMENT",
        "target_agent": args.agent,
        "selected_record_ids": [record.record_id for record in pack.records],
        "excluded_record_ids": list(pack.excluded_record_ids),
        "open_contradiction_ids": [record.record_id for record in pack.open_contradictions],
        "reassessment": {
            "record_count": result.record_count,
            "independent_evidence_count": result.independent_evidence_count,
            "runtime_evidence_admissible": result.runtime_evidence_admissible,
            "status": result.status,
            "reasons": list(result.reasons),
        },
    }
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    manifest["execution_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
