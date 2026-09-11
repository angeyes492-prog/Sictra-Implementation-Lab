"""Pinned, executable engine manifests for the bounded Block 2 runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from importlib import import_module
import json
import re
from datetime import datetime


_ENGINE_IDS = tuple(f"E0{number}" for number in range(1, 9))
_SEMVER = re.compile(r"^0\.1\.\d+$")


class EngineRegistryViolation(ValueError):
    """A registry cannot safely identify the executable engine plane."""


@dataclass(frozen=True, slots=True)
class EngineManifest:
    engine_id: str
    manifest_version: str
    contract_version: str
    implementation_ref: str
    dependencies: tuple[str, ...]
    owned_semantics: str
    authority_boundary: str
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.engine_id not in _ENGINE_IDS:
            raise EngineRegistryViolation("manifest contains an unknown engine")
        if not _SEMVER.fullmatch(self.manifest_version):
            raise EngineRegistryViolation("manifest version is unsupported")
        if not _SEMVER.fullmatch(self.contract_version):
            raise EngineRegistryViolation("contract version is unsupported")
        if self.implementation_ref.count(":") != 1:
            raise EngineRegistryViolation("implementation_ref must be module:attribute")
        if not self.owned_semantics.strip() or not self.authority_boundary.strip():
            raise EngineRegistryViolation("manifest semantics and authority must be explicit")

    @property
    def content_hash(self) -> str:
        material = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return sha256(material.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class EngineRegistry:
    registry_id: str
    registry_version: str
    manifests: tuple[EngineManifest, ...]
    state: str = "PINNED_NOT_ACCEPTED"

    def __post_init__(self) -> None:
        if not self.registry_id.strip() or not _SEMVER.fullmatch(self.registry_version):
            raise EngineRegistryViolation("registry identity or version is invalid")
        ids = tuple(item.engine_id for item in self.manifests)
        if ids != _ENGINE_IDS:
            raise EngineRegistryViolation("registry must contain E01-E08 in canonical order")
        for index, item in enumerate(self.manifests):
            expected = () if index == 0 else (_ENGINE_IDS[index - 1],)
            if item.dependencies != expected:
                raise EngineRegistryViolation(f"{item.engine_id} dependencies are not canonical")
            if not item.enabled:
                raise EngineRegistryViolation(f"{item.engine_id} is not enabled")

    @property
    def content_hash(self) -> str:
        material = {
            "registry_id": self.registry_id,
            "registry_version": self.registry_version,
            "state": self.state,
            "manifest_hashes": [item.content_hash for item in self.manifests],
        }
        encoded = json.dumps(material, sort_keys=True, separators=(",", ":"))
        return sha256(encoded.encode("utf-8")).hexdigest()

    def resolve(self, engine_id: str) -> EngineManifest:
        for manifest in self.manifests:
            if manifest.engine_id == engine_id:
                return manifest
        raise EngineRegistryViolation(f"engine is not registered: {engine_id}")

    def verify_bindings(self) -> tuple[str, ...]:
        """Import every pinned entrypoint; this verifies identity, not correctness."""

        verified: list[str] = []
        for manifest in self.manifests:
            module_name, attribute = manifest.implementation_ref.split(":", 1)
            try:
                value = getattr(import_module(module_name), attribute)
            except (ImportError, AttributeError) as exc:
                raise EngineRegistryViolation(
                    f"binding unavailable for {manifest.engine_id}"
                ) from exc
            if not callable(value):
                raise EngineRegistryViolation(f"binding is not callable for {manifest.engine_id}")
            verified.append(manifest.engine_id)
        return tuple(verified)


def default_engine_registry() -> EngineRegistry:
    """Return the locally pinned E01-E08 registry candidate."""

    definitions = (
        ("E01", "sictra_block2_design.preflight:assess_fixture", "fixture readiness", "cannot invent upstream evidence"),
        ("E02", "sictra_block2_design.e02_direction:assess_direction_set", "creative direction candidates", "cannot select a direction"),
        ("E03", "sictra_block2_design.e03_design_system:assess_system_profile", "design-system profile", "cannot approve downstream content"),
        ("E04", "sictra_block2_design.e04_information_design:assess_information_blueprint", "information architecture", "cannot create or validate assets"),
        ("E05", "sictra_block2_design.e05_reference_research:assess_reference_research", "reference and rights constraints", "cannot grant missing rights"),
        ("E06", "sictra_block2_design.model_gateway:execution_spec_for", "production request routing", "cannot publish or accept output"),
        ("E07", "sictra_block2_design.e07_visual_red_team:assess_visual_candidate", "visual quality recommendation", "cannot replace external acceptance"),
        ("E08", "sictra_block2_design.e08_creative_memory:assess_memory_candidate", "future-generation memory candidate", "cannot rewrite historical evidence"),
    )
    manifests = tuple(
        EngineManifest(
            engine_id, "0.1.0", "0.1.0", binding,
            () if index == 0 else (_ENGINE_IDS[index - 1],), semantics, authority,
        )
        for index, (engine_id, binding, semantics, authority) in enumerate(definitions)
    )
    return EngineRegistry("BLOCK2-ENGINE-REGISTRY", "0.1.0", manifests)


def persist_engine_registry(graph, registry: EngineRegistry, *, project_id: str, created_at: datetime) -> str:
    """Append registry and manifest identities to a Project Graph atomically."""

    from .project_graph import GraphEdge, GraphNode

    actions: list[str] = []
    try:
        actions.append(graph.append_node(GraphNode(
            project_id, registry.registry_id, "ENGINE_REGISTRY", registry.content_hash,
            {
                "registry_version": registry.registry_version,
                "state": registry.state,
                "manifest_hashes": [item.content_hash for item in registry.manifests],
            },
            created_at,
        )))
        for manifest in registry.manifests:
            node_id = f"MANIFEST-{manifest.engine_id}-{manifest.content_hash[:16]}"
            actions.append(graph.append_node(GraphNode(
                project_id, node_id, "ENGINE_MANIFEST", manifest.content_hash,
                {
                    "engine_id": manifest.engine_id,
                    "manifest_version": manifest.manifest_version,
                    "contract_version": manifest.contract_version,
                    "implementation_ref": manifest.implementation_ref,
                    "dependencies": list(manifest.dependencies),
                    "owned_semantics": manifest.owned_semantics,
                    "authority_boundary": manifest.authority_boundary,
                    "enabled": manifest.enabled,
                },
                created_at,
            )))
            actions.append(graph.append_edge(GraphEdge(
                project_id, node_id, "DERIVED_FROM", registry.registry_id,
                manifest.content_hash, created_at,
            )))
        graph.commit()
    except Exception:
        graph.rollback()
        raise
    return "IDEMPOTENT" if actions and all(item == "IDEMPOTENT" for item in actions) else "APPENDED"
