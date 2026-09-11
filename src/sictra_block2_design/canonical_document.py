"""Canonical, immutable design-document primitives for Block 2 Slice 1.

This module represents design candidates and their lineage.  It does not grant
rights, publish artifacts, accept visual quality, or authorize engine gates.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass, replace
from datetime import datetime
from hashlib import sha256
import json
import re
from typing import Any

from .runtime import Block2RunInput, Block2RunResult


_HASH = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_TEXT = re.compile(
    r"(?:<\s*script\b|javascript\s*:|https?://|file\s*:|(?:^|[\\/])\.\.(?:[\\/]|$))",
    re.IGNORECASE,
)


class CanonicalDocumentViolation(ValueError):
    """A CDD cannot be represented without violating its contract."""


def _text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise CanonicalDocumentViolation(f"{name} must be a non-empty string")


def _safe_text(value: str, name: str, *, allow_empty: bool = False) -> None:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise CanonicalDocumentViolation(f"{name} must be a string with contracted content")
    if _FORBIDDEN_TEXT.search(value):
        raise CanonicalDocumentViolation(f"{name} contains a forbidden executable or remote reference")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise CanonicalDocumentViolation("timestamps must be timezone-aware")
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in sorted(value.items())}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    """Return the stable JSON representation used by hashes and persistence."""

    material = asdict(value) if hasattr(value, "__dataclass_fields__") else value
    return json.dumps(_json_ready(material), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def document_from_mapping(value: dict[str, Any]) -> "DesignDocumentVersion":
    """Rehydrate a validated persisted CDD representation."""

    pages = tuple(DesignPage(
        item["page_id"], item["name"], item["width"], item["height"],
        tuple(item["reading_order"]),
    ) for item in value["pages"])
    elements = tuple(DesignElement(
        item["element_id"], item["element_type"], item["page_id"], item["z_index"],
        tuple(item["geometry"]), item["content"], tuple(item["token_refs"]),
        tuple(item["asset_refs"]), tuple(item["claim_refs"]),
        tuple(item["evidence_refs"]), tuple(item["limitation_refs"]),
        item["accessibility_label"], tuple(item["lineage_refs"]),
        item["editable"], item["rights_state"],
    ) for item in value["elements"])
    return DesignDocumentVersion(
        value["document_id"], value["project_id"], value["version_id"],
        value["parent_version_id"], value["profile_id"], value["blueprint_id"],
        value["direction_id"], pages, elements, tuple(value["asset_hashes"]),
        tuple(value["decision_refs"]), tuple(value["validation_refs"]),
        value["actor_id"], datetime.fromisoformat(value["created_at"]), value["state"],
    )


@dataclass(frozen=True, slots=True)
class DesignPage:
    page_id: str
    name: str
    width: int
    height: int
    reading_order: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.page_id, "page_id")
        _safe_text(self.name, "page name")
        if not isinstance(self.width, int) or not isinstance(self.height, int) or self.width < 1 or self.height < 1:
            raise CanonicalDocumentViolation("page dimensions must be positive integers")
        if len(set(self.reading_order)) != len(self.reading_order):
            raise CanonicalDocumentViolation("page reading order cannot contain duplicate elements")


@dataclass(frozen=True, slots=True)
class DesignElement:
    element_id: str
    element_type: str
    page_id: str
    z_index: int
    geometry: tuple[int, int, int, int]
    content: str
    token_refs: tuple[str, ...]
    asset_refs: tuple[str, ...]
    claim_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    limitation_refs: tuple[str, ...]
    accessibility_label: str
    lineage_refs: tuple[str, ...]
    editable: bool
    rights_state: str

    def __post_init__(self) -> None:
        for name, value in (
            ("element_id", self.element_id), ("element_type", self.element_type),
            ("page_id", self.page_id), ("rights_state", self.rights_state),
        ):
            _text(value, name)
        _safe_text(self.content, "element content", allow_empty=True)
        _safe_text(self.accessibility_label, "accessibility_label")
        if not isinstance(self.z_index, int):
            raise CanonicalDocumentViolation("z_index must be an integer")
        if len(self.geometry) != 4 or any(not isinstance(value, int) or value < 0 for value in self.geometry):
            raise CanonicalDocumentViolation("geometry must be four non-negative integers")
        if any(not _HASH.fullmatch(value) for value in self.asset_refs):
            raise CanonicalDocumentViolation("asset_refs must be lowercase SHA-256 identities")
        if not isinstance(self.editable, bool):
            raise CanonicalDocumentViolation("editable must be boolean")


@dataclass(frozen=True, slots=True)
class DesignDocumentVersion:
    document_id: str
    project_id: str
    version_id: str
    parent_version_id: str | None
    profile_id: str
    blueprint_id: str
    direction_id: str
    pages: tuple[DesignPage, ...]
    elements: tuple[DesignElement, ...]
    asset_hashes: tuple[str, ...]
    decision_refs: tuple[str, ...]
    validation_refs: tuple[str, ...]
    actor_id: str
    created_at: datetime
    state: str = "CANDIDATE_NOT_ACCEPTED"

    def __post_init__(self) -> None:
        for name, value in (
            ("document_id", self.document_id), ("project_id", self.project_id),
            ("version_id", self.version_id), ("profile_id", self.profile_id),
            ("blueprint_id", self.blueprint_id), ("direction_id", self.direction_id),
            ("actor_id", self.actor_id), ("state", self.state),
        ):
            _text(value, name)
        if self.parent_version_id is not None:
            _text(self.parent_version_id, "parent_version_id")
            if self.parent_version_id == self.version_id:
                raise CanonicalDocumentViolation("a version cannot be its own parent")
        if not isinstance(self.created_at, datetime) or self.created_at.tzinfo is None:
            raise CanonicalDocumentViolation("created_at must be timezone-aware")
        if not self.pages or not self.elements:
            raise CanonicalDocumentViolation("a design document needs pages and elements")
        page_ids = {page.page_id for page in self.pages}
        element_ids = {element.element_id for element in self.elements}
        if len(page_ids) != len(self.pages) or len(element_ids) != len(self.elements):
            raise CanonicalDocumentViolation("page and element identities must be unique")
        for page in self.pages:
            page_elements = {item.element_id for item in self.elements if item.page_id == page.page_id}
            if set(page.reading_order) != page_elements or len(page.reading_order) != len(page_elements):
                raise CanonicalDocumentViolation("page reading order must cover its elements exactly once")
        if any(element.page_id not in page_ids for element in self.elements):
            raise CanonicalDocumentViolation("every element must bind to a known page")
        if any(not _HASH.fullmatch(value) for value in self.asset_hashes):
            raise CanonicalDocumentViolation("asset_hashes must be lowercase SHA-256 identities")
        if not set(ref for item in self.elements for ref in item.asset_refs).issubset(self.asset_hashes):
            raise CanonicalDocumentViolation("element assets must be declared by the document")

    @property
    def content_hash(self) -> str:
        return sha256(canonical_json(self).encode("utf-8")).hexdigest()

    def next_version(
        self,
        *,
        version_id: str,
        elements: tuple[DesignElement, ...],
        actor_id: str,
        created_at: datetime,
    ) -> "DesignDocumentVersion":
        """Create a child version without mutating historical state."""

        return replace(
            self,
            version_id=version_id,
            parent_version_id=self.version_id,
            elements=elements,
            actor_id=actor_id,
            created_at=created_at,
            validation_refs=(),
            state="EDITED_CANDIDATE_NOT_VALIDATED",
        )


def document_from_completed_run(
    request: Block2RunInput,
    result: Block2RunResult,
    *,
    project_id: str,
    document_id: str,
    actor_id: str,
    created_at: datetime,
) -> DesignDocumentVersion:
    """Adapt a completed bounded run into a CDD without changing engine output."""

    if not result.completed or result.production is None or result.production.candidate is None:
        raise CanonicalDocumentViolation("only a completed run with an E06 candidate can produce a CDD")
    candidate = result.production.candidate
    page_id = f"PAGE-{request.blueprint.blueprint_id}"
    copy_by_claim = dict(request.production_request.content.claim_copy)
    token_refs = tuple(token.token_id for token in request.system_profile.tokens)
    elements = tuple(
        DesignElement(
            element_id=item.element_id,
            element_type=item.element_type,
            page_id=page_id,
            z_index=index,
            geometry=(0, index * 120, 1200, 100),
            content="\n".join(copy_by_claim.get(claim_id, "") for claim_id in item.claim_ids),
            token_refs=token_refs,
            asset_refs=(candidate.artifact.sha256,),
            claim_refs=item.claim_ids,
            evidence_refs=item.evidence_refs,
            limitation_refs=item.limitation_ids,
            accessibility_label=request.production_request.content.accessible_description,
            lineage_refs=(request.blueprint.blueprint_id, candidate.candidate_id),
            editable=True,
            rights_state="REFERENCED_NOT_GRANTED",
        )
        for index, item in enumerate(request.blueprint.elements)
    )
    page = DesignPage(
        page_id,
        request.production_request.content.title,
        1200,
        max(120, len(elements) * 120),
        request.blueprint.reading_order,
    )
    version_material = "\x1f".join((candidate.artifact.sha256, actor_id, created_at.isoformat()))
    version_id = "CDD-" + sha256(version_material.encode("utf-8")).hexdigest()[:20]
    return DesignDocumentVersion(
        document_id=document_id,
        project_id=project_id,
        version_id=version_id,
        parent_version_id=None,
        profile_id=request.system_profile.profile_id,
        blueprint_id=request.blueprint.blueprint_id,
        direction_id=request.selected_direction.direction_id,
        pages=(page,),
        elements=elements,
        asset_hashes=(candidate.artifact.sha256,),
        decision_refs=(request.system_profile.selection.authority_reference,),
        validation_refs=(request.external_validation.validation_id,),
        actor_id=actor_id,
        created_at=created_at,
    )
