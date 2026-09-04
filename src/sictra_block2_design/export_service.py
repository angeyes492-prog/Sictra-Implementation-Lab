"""Deterministic local HTML/SVG export packages from validated CDD versions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from html import escape

from .canonical_document import DesignDocumentVersion
from .project_graph import GraphEdge, GraphNode, ProjectGraphStore


class ExportServiceViolation(ValueError):
    """An export request is malformed or exceeds the local authority boundary."""


@dataclass(frozen=True, slots=True)
class ExportRequest:
    export_id: str
    contract_version: str
    project_id: str
    document_version_id: str
    target: str
    exporter_id: str
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.contract_version.startswith("0.1."):
            raise ExportServiceViolation("export contract version is unsupported")
        if self.target not in {"HTML", "SVG"}:
            raise ExportServiceViolation("export target is not contracted")
        if not isinstance(self.created_at, datetime) or self.created_at.tzinfo is None:
            raise ExportServiceViolation("export timestamp must be timezone-aware")


@dataclass(frozen=True, slots=True)
class ExportPackage:
    export_id: str
    document_version_id: str
    document_hash: str
    target: str
    media_type: str
    content: bytes
    content_hash: str
    accessibility_content: bytes
    accessibility_hash: str
    exporter_id: str
    created_at: datetime
    publication_state: str = "NOT_PUBLISHED"
    acceptance_state: str = "NOT_ACCEPTED"


@dataclass(frozen=True, slots=True)
class ExportAssessment:
    disposition: str
    reasons: tuple[str, ...]
    package: ExportPackage | None
    graph_action: str = "NOT_PERSISTED"

    @property
    def ready(self) -> bool:
        return self.disposition == "EXPORT_PACKAGE_READY"


def _plain(document: DesignDocumentVersion) -> str:
    page_names = "\n".join(page.name for page in document.pages)
    content = "\n\n".join(item.content or item.accessibility_label for item in document.elements)
    return page_names + "\n\n" + content


def _html(document: DesignDocumentVersion) -> str:
    pages = []
    for page in document.pages:
        elements = []
        by_id = {item.element_id: item for item in document.elements if item.page_id == page.page_id}
        for element_id in page.reading_order:
            element = by_id[element_id]
            elements.append(
                f'<section data-element="{escape(element.element_id, quote=True)}" '
                f'aria-label="{escape(element.accessibility_label, quote=True)}">'
                f'<p>{escape(element.content)}</p></section>'
            )
        pages.append(
            f'<article data-page="{escape(page.page_id, quote=True)}"><h1>{escape(page.name)}</h1>'
            + "".join(elements) + "</article>"
        )
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{escape(document.pages[0].name)}</title></head><body><main>'
        + "".join(pages) + "</main></body></html>"
    )


def _svg_lines(value: str, *, columns: int = 76) -> tuple[str, ...]:
    """Wrap untrusted CDD copy deterministically before placing it in SVG.

    SVG ``text`` does not wrap by default.  Keeping every line below a bounded
    character budget prevents a long, valid CDD field from leaving the declared
    1200-unit canvas.  The accessibility description still carries the complete
    source content, so this is a visual layout guard rather than a truncation.
    """

    lines: list[str] = []
    for paragraph in value.splitlines() or [""]:
        words = paragraph.split() or [""]
        current = ""
        for word in words:
            fragments = [word[index:index + columns] for index in range(0, len(word), columns)] or [""]
            for fragment in fragments:
                proposed = fragment if not current else f"{current} {fragment}"
                if current and len(proposed) > columns:
                    lines.append(current)
                    current = fragment
                else:
                    current = proposed
        lines.append(current)
    return tuple(lines)


def _svg(document: DesignDocumentVersion) -> str:
    pages = {page.page_id: page for page in document.pages}
    ordered = tuple(
        (pages[page_id], element_id)
        for page_id in (page.page_id for page in document.pages)
        for element_id in pages[page_id].reading_order
    )
    by_id = {item.element_id: item for item in document.elements}
    wrapped = {
        element_id: _svg_lines(by_id[element_id].content or by_id[element_id].accessibility_label)
        for _, element_id in ordered
    }
    height = max(220, 88 + len(document.pages) * 52 + sum(34 * len(lines) + 22 for lines in wrapped.values()))
    chunks = [
        f'<svg xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-labelledby="title desc" viewBox="0 0 1200 {height}">',
        f'<title id="title">{escape(document.pages[0].name)}</title>',
        f'<desc id="desc">{escape(_plain(document))}</desc>',
        '<rect width="1200" height="100%" fill="#ffffff"/>',
    ]
    y = 56
    active_page: str | None = None
    for page, element_id in ordered:
        element = by_id[element_id]
        if page.page_id != active_page:
            active_page = page.page_id
            chunks.append(
                f'<text x="56" y="{y}" fill="#182033" font-size="32" font-weight="700">'
                f'{escape(page.name)}</text>'
            )
            y += 52
        lines = wrapped[element_id]
        chunks.append(
            f'<text data-element="{escape(element.element_id, quote=True)}" x="56" y="{y}" '
            f'fill="#182033" font-size="24">'
            + "".join(
                f'<tspan x="56" dy="{0 if index == 0 else 34}">{escape(line)}</tspan>'
                for index, line in enumerate(lines)
            )
            + '</text>'
        )
        y += 34 * len(lines) + 22
    chunks.append('</svg>')
    return "".join(chunks)


def build_export_package(
    document: DesignDocumentVersion,
    request: ExportRequest,
) -> ExportAssessment:
    failures: list[str] = []
    if request.project_id != document.project_id:
        failures.append("PROJECT_ID_MISMATCH")
    if request.document_version_id != document.version_id:
        failures.append("DOCUMENT_VERSION_MISMATCH")
    if document.state == "EDITED_CANDIDATE_NOT_VALIDATED" or not document.validation_refs:
        failures.append("REVALIDATION_REQUIRED")
    if failures:
        return ExportAssessment("REVALIDATION_REQUIRED", tuple(failures), None)
    rendered = _html(document) if request.target == "HTML" else _svg(document)
    media_type = "text/html" if request.target == "HTML" else "image/svg+xml"
    content = rendered.encode("utf-8")
    accessible = _plain(document).encode("utf-8")
    package = ExportPackage(
        request.export_id, document.version_id, document.content_hash, request.target,
        media_type, content, sha256(content).hexdigest(), accessible,
        sha256(accessible).hexdigest(), request.exporter_id, request.created_at,
    )
    return ExportAssessment("EXPORT_PACKAGE_READY", (), package)


def persist_export(graph: ProjectGraphStore, request: ExportRequest) -> ExportAssessment:
    document = graph.load_document(request.project_id, request.document_version_id)
    if document is None:
        return ExportAssessment("RETURN_TO_DOCUMENT", ("DOCUMENT_VERSION_NOT_FOUND",), None)
    assessment = build_export_package(document, request)
    if not assessment.ready:
        return assessment
    package = assessment.package
    try:
        action = graph.append_node(GraphNode(
            request.project_id, package.export_id, "EXPORT_PACKAGE", package.content_hash,
            {"document_version_id": package.document_version_id, "target": package.target,
             "media_type": package.media_type, "publication_state": package.publication_state,
             "acceptance_state": package.acceptance_state}, request.created_at,
        ))
        edge_action = graph.append_edge(GraphEdge(
            request.project_id, f"DOCUMENT-{document.version_id}", "EXPORTED_AS",
            package.export_id, package.content_hash, request.created_at,
        ))
        graph.commit()
    except Exception:
        graph.rollback()
        raise
    graph_action = "IDEMPOTENT" if action == edge_action == "IDEMPOTENT" else "APPENDED"
    return ExportAssessment(assessment.disposition, assessment.reasons, package, graph_action)
