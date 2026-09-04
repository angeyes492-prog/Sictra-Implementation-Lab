"""Generate actual Block 2 export packages and audit them in a browser.

This remains a local visual check.  It does not publish either package or
substitute for real-client or assistive-technology acceptance.
"""

from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import replace
from pathlib import Path
import os
import subprocess
import tempfile

from sictra_block2_design.export_service import ExportRequest, build_export_package, persist_export
from sictra_block2_design.project_graph import ProjectGraphStore
from sictra_block2_design.reference_fixture import reference_run_input
from sictra_block2_design.traceable_runtime import execute_traceable_block2


NOW = datetime(2026, 9, 1, 12, tzinfo=timezone.utc)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    node = os.environ.get("SICTRA_A11Y_NODE", "node")
    with tempfile.TemporaryDirectory() as folder:
        database = Path(folder) / "render-probe.sqlite3"
        with ProjectGraphStore(database) as graph:
            trace = execute_traceable_block2(
                reference_run_input(NOW), graph=graph, project_id="PROJECT-RENDER-PROBE",
                document_id="DOCUMENT-RENDER-PROBE", actor_id="RENDER-PROBE",
                run_id="RUN-RENDER-PROBE", now=NOW,
            )
            packages = []
            for target in ("HTML", "SVG"):
                assessment = persist_export(graph, ExportRequest(
                    f"EXPORT-RENDER-{target}", "0.1.0", trace.document.project_id,
                    trace.document.version_id, target, "RENDER-PROBE", NOW,
                ))
                if not assessment.ready or assessment.package is None:
                    raise RuntimeError(f"could not build {target} export: {assessment.reasons}")
                suffix = ".html" if target == "HTML" else ".svg"
                path = Path(folder) / f"export{suffix}"
                path.write_bytes(assessment.package.content)
                packages.append(str(path))
        completed = subprocess.run(
            [node, str(root / "tools" / "block2_export_render_probe.js"), *packages],
            cwd=root, check=False, text=True,
        )
        if completed.returncode:
            raise SystemExit(completed.returncode)
        long_copy = " ".join(["evidencia-trazable"] * 120)
        long_element = replace(trace.document.elements[0], content=long_copy)
        long_document = replace(trace.document, elements=(long_element, *trace.document.elements[1:]))
        long_svg = build_export_package(long_document, ExportRequest(
            "EXPORT-RENDER-LONG-SVG", "0.1.0", trace.document.project_id,
            long_document.version_id, "SVG", "RENDER-PROBE", NOW,
        )).package
        if long_svg is None:
            raise RuntimeError("could not build long SVG render vector")
        long_path = Path(folder) / "long-export.svg"
        long_path.write_bytes(long_svg.content)
        long_check = subprocess.run(
            [node, str(root / "tools" / "block2_export_render_probe.js"), packages[0], str(long_path)],
            cwd=root, check=False, text=True,
        )
        raise SystemExit(long_check.returncode)


if __name__ == "__main__":
    main()
