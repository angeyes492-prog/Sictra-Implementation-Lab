"""Versioned CDD edits, semantic diff, and conservative invalidation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from hashlib import sha256
from typing import Any

from .canonical_document import (
    DesignDocumentVersion, DesignElement, canonical_json,
)
from .project_graph import GraphEdge, GraphNode, ProjectGraphStore


class DocumentEvolutionViolation(ValueError):
    """An edit cannot be applied without breaking CDD or lineage invariants."""


_EDITABLE_FIELDS = frozenset({
    "content", "geometry", "token_refs", "asset_refs",
    "accessibility_label", "rights_state",
})
_DOMAIN_BY_FIELD = {
    "content": "CONTENT", "geometry": "GEOMETRY", "token_refs": "STYLE",
    "asset_refs": "ASSET", "accessibility_label": "ACCESSIBILITY",
    "rights_state": "RIGHTS",
}
_ROOT_BY_DOMAIN = {
    "STYLE": "E03", "CONTENT": "E04", "GEOMETRY": "E04",
    "ACCESSIBILITY": "E04", "ASSET": "E05", "RIGHTS": "E05",
}
_ENGINES = tuple(f"E0{number}" for number in range(1, 9))


def _text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise DocumentEvolutionViolation(f"{name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class ElementEdit:
    operation_id: str
    element_id: str
    field: str
    value: Any

    def __post_init__(self) -> None:
        _text(self.operation_id, "operation_id")
        _text(self.element_id, "element_id")
        if self.field not in _EDITABLE_FIELDS:
            raise DocumentEvolutionViolation("field is not editable from Design Studio")


@dataclass(frozen=True, slots=True)
class DocumentEditProposal:
    edit_id: str
    contract_version: str
    project_id: str
    document_id: str
    base_version_id: str
    base_content_hash: str
    new_version_id: str
    actor_id: str
    created_at: datetime
    operations: tuple[ElementEdit, ...]

    def __post_init__(self) -> None:
        for name, value in (
            ("edit_id", self.edit_id), ("contract_version", self.contract_version),
            ("project_id", self.project_id), ("document_id", self.document_id),
            ("base_version_id", self.base_version_id),
            ("base_content_hash", self.base_content_hash),
            ("new_version_id", self.new_version_id), ("actor_id", self.actor_id),
        ):
            _text(value, name)
        if not self.contract_version.startswith("0.1."):
            raise DocumentEvolutionViolation("edit contract version is unsupported")
        if not isinstance(self.created_at, datetime) or self.created_at.tzinfo is None:
            raise DocumentEvolutionViolation("created_at must be timezone-aware")
        if not self.operations:
            raise DocumentEvolutionViolation("at least one edit operation is required")
        identities = [item.operation_id for item in self.operations]
        targets = [(item.element_id, item.field) for item in self.operations]
        if len(set(identities)) != len(identities):
            raise DocumentEvolutionViolation("operation identities must be unique")
        if len(set(targets)) != len(targets):
            raise DocumentEvolutionViolation("an element field may be edited only once per proposal")

    @property
    def content_hash(self) -> str:
        return sha256(canonical_json(self).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class DiffEntry:
    element_id: str
    domain: str
    field: str
    before_hash: str
    after_hash: str


@dataclass(frozen=True, slots=True)
class DocumentDiff:
    diff_id: str
    document_id: str
    before_version_id: str
    after_version_id: str
    entries: tuple[DiffEntry, ...]

    @property
    def content_hash(self) -> str:
        return sha256(canonical_json(self).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class InvalidationPlan:
    plan_id: str
    diff_id: str
    root_engines: tuple[str, ...]
    invalidated_engines: tuple[str, ...]
    preserved_engines: tuple[str, ...]
    reason_domains: tuple[str, ...]
    state: str = "REQUIRES_REVALIDATION"

    @property
    def content_hash(self) -> str:
        return sha256(canonical_json(self).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class EvolutionResult:
    document: DesignDocumentVersion
    diff: DocumentDiff
    invalidation: InvalidationPlan
    store_action: str = "NOT_PERSISTED"


def _value_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def apply_document_edit(
    base: DesignDocumentVersion,
    proposal: DocumentEditProposal,
) -> EvolutionResult:
    """Apply a bounded edit to an immutable CDD and derive invalidation."""

    failures: list[str] = []
    if proposal.project_id != base.project_id:
        failures.append("PROJECT_ID_MISMATCH")
    if proposal.document_id != base.document_id:
        failures.append("DOCUMENT_ID_MISMATCH")
    if proposal.base_version_id != base.version_id:
        failures.append("BASE_VERSION_ID_MISMATCH")
    if proposal.base_content_hash != base.content_hash:
        failures.append("BASE_CONTENT_HASH_MISMATCH")
    if proposal.new_version_id == base.version_id:
        failures.append("NEW_VERSION_EQUALS_BASE")
    if failures:
        raise DocumentEvolutionViolation(";".join(failures))

    elements = {item.element_id: item for item in base.elements}
    changed = dict(elements)
    entries: list[DiffEntry] = []
    for operation in proposal.operations:
        element = changed.get(operation.element_id)
        if element is None:
            raise DocumentEvolutionViolation(f"ELEMENT_{operation.element_id}_NOT_FOUND")
        if not element.editable:
            raise DocumentEvolutionViolation(f"ELEMENT_{operation.element_id}_NOT_EDITABLE")
        before = getattr(element, operation.field)
        if before == operation.value:
            raise DocumentEvolutionViolation(f"OPERATION_{operation.operation_id}_NO_OP")
        try:
            updated = replace(element, **{operation.field: operation.value})
        except (TypeError, ValueError) as error:
            raise DocumentEvolutionViolation(f"OPERATION_{operation.operation_id}_INVALID_VALUE") from error
        changed[operation.element_id] = updated
        entries.append(DiffEntry(
            operation.element_id, _DOMAIN_BY_FIELD[operation.field], operation.field,
            _value_hash(before), _value_hash(operation.value),
        ))

    child = base.next_version(
        version_id=proposal.new_version_id,
        elements=tuple(changed[item.element_id] for item in base.elements),
        actor_id=proposal.actor_id,
        created_at=proposal.created_at,
    )
    entries_tuple = tuple(sorted(entries, key=lambda item: (item.element_id, item.field)))
    diff_id = "DIFF-" + sha256(canonical_json(entries_tuple).encode("utf-8")).hexdigest()[:24]
    diff = DocumentDiff(diff_id, base.document_id, base.version_id, child.version_id, entries_tuple)
    domains = tuple(sorted({entry.domain for entry in entries_tuple}))
    roots = tuple(sorted({_ROOT_BY_DOMAIN[domain] for domain in domains}))
    earliest_index = min(_ENGINES.index(root) for root in roots)
    invalidated = _ENGINES[earliest_index:]
    preserved = _ENGINES[:earliest_index]
    plan = InvalidationPlan(
        "INVALIDATION-" + sha256((diff.content_hash + "|" + "|".join(roots)).encode("utf-8")).hexdigest()[:24],
        diff.diff_id, roots, invalidated, preserved, domains,
    )
    return EvolutionResult(child, diff, plan)


def persist_document_evolution(
    graph: ProjectGraphStore,
    proposal: DocumentEditProposal,
) -> EvolutionResult:
    """Validate currentness and atomically append child, diff, and invalidation."""

    base = graph.load_document(proposal.project_id, proposal.base_version_id)
    if base is None:
        raise DocumentEvolutionViolation("BASE_VERSION_NOT_FOUND")
    result = apply_document_edit(base, proposal)
    latest = graph.latest_document_version_id(proposal.project_id, proposal.document_id)
    if latest not in {proposal.base_version_id, proposal.new_version_id}:
        raise DocumentEvolutionViolation("BASE_VERSION_STALE")
    if latest == proposal.new_version_id:
        existing_child = graph.load_document(proposal.project_id, proposal.new_version_id)
        if existing_child is None or existing_child.content_hash != result.document.content_hash:
            raise DocumentEvolutionViolation("EDIT_IDENTITY_COLLISION")
    actions: list[str] = []
    try:
        actions.append(graph.append_document(result.document))
        parent_node = f"DOCUMENT-{base.version_id}"
        child_node = f"DOCUMENT-{result.document.version_id}"
        actions.append(graph.append_node(GraphNode(
            proposal.project_id, child_node, "DESIGN_DOCUMENT_VERSION",
            result.document.content_hash,
            {"document_id": result.document.document_id, "version_id": result.document.version_id, "state": result.document.state},
            proposal.created_at,
        )))
        actions.append(graph.append_edge(GraphEdge(
            proposal.project_id, child_node, "SUPERSEDES", parent_node, proposal.edit_id,
            proposal.created_at,
        )))
        actions.append(graph.append_node(GraphNode(
            proposal.project_id, result.diff.diff_id, "DOCUMENT_DIFF", result.diff.content_hash,
            {"before": result.diff.before_version_id, "after": result.diff.after_version_id,
             "domains": list(result.invalidation.reason_domains), "entries": len(result.diff.entries)},
            proposal.created_at,
        )))
        actions.append(graph.append_edge(GraphEdge(
            proposal.project_id, result.diff.diff_id, "REPRESENTS", child_node,
            result.document.version_id, proposal.created_at,
        )))
        actions.append(graph.append_node(GraphNode(
            proposal.project_id, result.invalidation.plan_id, "INVALIDATION_PLAN",
            result.invalidation.content_hash,
            {"roots": list(result.invalidation.root_engines),
             "invalidated": list(result.invalidation.invalidated_engines),
             "preserved": list(result.invalidation.preserved_engines),
             "state": result.invalidation.state},
            proposal.created_at,
        )))
        actions.append(graph.append_edge(GraphEdge(
            proposal.project_id, result.invalidation.plan_id, "DERIVED_FROM",
            result.diff.diff_id, proposal.edit_id, proposal.created_at,
        )))
        graph.commit()
    except Exception:
        graph.rollback()
        raise
    action = "IDEMPOTENT" if actions and all(item == "IDEMPOTENT" for item in actions) else "APPENDED"
    return replace(result, store_action=action)
