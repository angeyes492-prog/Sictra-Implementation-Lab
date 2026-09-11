"""Deterministic local Model Gateway boundary for E06.

The gateway executes a pinned local adapter and emits a receipt.  It cannot
change design semantics, grant rights, publish, accept, or use remote I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json

from .e03_design_system import SystemProfileProposal
from .e04_information_design import InformationBlueprint, InformationPayload
from .e05_reference_research import ReferenceResearchProposal
from .e06_production import (
    ProductionAssessment, ProductionRequest, build_production_candidate,
)


class ModelGatewayViolation(ValueError):
    """A gateway request violates identity, authority, or capability bounds."""


def _text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ModelGatewayViolation(f"{name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class ProviderManifest:
    manifest_id: str
    provider_id: str
    adapter: str
    contract_version: str
    healthy: bool
    rights_current: bool
    remote_io: bool = False

    def __post_init__(self) -> None:
        for name, value in (
            ("manifest_id", self.manifest_id), ("provider_id", self.provider_id),
            ("adapter", self.adapter), ("contract_version", self.contract_version),
        ):
            _text(value, name)
        if not all(isinstance(value, bool) for value in (self.healthy, self.rights_current, self.remote_io)):
            raise ModelGatewayViolation("manifest state flags must be boolean")

    @property
    def content_hash(self) -> str:
        material = json.dumps({
            "manifest_id": self.manifest_id, "provider_id": self.provider_id,
            "adapter": self.adapter, "contract_version": self.contract_version,
            "healthy": self.healthy, "rights_current": self.rights_current,
            "remote_io": self.remote_io,
        }, sort_keys=True, separators=(",", ":"))
        return sha256(material.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class CreativeExecutionSpec:
    spec_id: str
    contract_version: str
    producer_engine: str
    adapter: str
    candidate_id: str
    envelope_fingerprint: str
    profile_id: str
    blueprint_id: str
    research_pack_id: str
    provider_manifest_id: str
    provider_manifest_hash: str
    idempotency_key: str

    def __post_init__(self) -> None:
        for name, value in (
            ("spec_id", self.spec_id), ("contract_version", self.contract_version),
            ("producer_engine", self.producer_engine), ("adapter", self.adapter),
            ("candidate_id", self.candidate_id),
            ("envelope_fingerprint", self.envelope_fingerprint),
            ("profile_id", self.profile_id), ("blueprint_id", self.blueprint_id),
            ("research_pack_id", self.research_pack_id),
            ("provider_manifest_id", self.provider_manifest_id),
            ("provider_manifest_hash", self.provider_manifest_hash),
            ("idempotency_key", self.idempotency_key),
        ):
            _text(value, name)
        if self.producer_engine != "E06":
            raise ModelGatewayViolation("only E06 may produce a CreativeExecutionSpec")
        if not self.contract_version.startswith("0.1."):
            raise ModelGatewayViolation("CreativeExecutionSpec version is unsupported")

    @property
    def input_hash(self) -> str:
        material = json.dumps({
            "spec_id": self.spec_id,
            "version": self.contract_version,
            "engine": self.producer_engine,
            "adapter": self.adapter,
            "candidate": self.candidate_id,
            "envelope": self.envelope_fingerprint,
            "profile": self.profile_id,
            "blueprint": self.blueprint_id,
            "research": self.research_pack_id,
            "manifest": self.provider_manifest_id,
            "manifest_hash": self.provider_manifest_hash,
        }, sort_keys=True, separators=(",", ":"))
        return sha256(material.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class GatewayReceipt:
    receipt_id: str
    spec_id: str
    provider_manifest_id: str
    adapter: str
    idempotency_key: str
    input_hash: str
    output_hash: str | None
    outcome: str
    quarantine_state: str
    retries: int
    cost_units: int
    executed_at: datetime
    latency_ms: int = 0
    cancel_state: str = "NOT_REQUESTED"
    budget_limit_units: int = 0
    timeout_ms: int = 0
    policy_hash: str = "LOCAL_POLICY_UNBOUND"
    rights_hash: str = "LOCAL_RIGHTS_UNBOUND"

    def __post_init__(self) -> None:
        if not isinstance(self.executed_at, datetime) or self.executed_at.tzinfo is None:
            raise ModelGatewayViolation("receipt timestamp must be timezone-aware")


@dataclass(frozen=True, slots=True)
class GatewayExecution:
    production: ProductionAssessment
    receipt: GatewayReceipt


class LocalDeterministicModelGateway:
    """Pinned no-network provider stub with idempotency collision controls."""

    def __init__(self, manifest: ProviderManifest | None = None) -> None:
        self.manifest = manifest or ProviderManifest(
            "MANIFEST-LOCAL-STUB-0.1.0", "LOCAL_DETERMINISTIC_STUB", "HTML_EMAIL_OR_SVG",
            "0.1.0", True, True, False,
        )
        self._receipts: dict[str, GatewayReceipt] = {}

    def execute(
        self,
        spec: CreativeExecutionSpec,
        *,
        profile: SystemProfileProposal,
        blueprint: InformationBlueprint,
        blueprint_disposition: str,
        payload: InformationPayload,
        research: ReferenceResearchProposal,
        research_disposition: str,
        request: ProductionRequest,
        now: datetime,
    ) -> GatewayExecution:
        if now.tzinfo is None:
            raise ModelGatewayViolation("gateway execution time must be timezone-aware")
        failures: list[str] = []
        if spec.provider_manifest_id != self.manifest.manifest_id:
            failures.append("PROVIDER_MANIFEST_SUBSTITUTION")
        if spec.provider_manifest_hash != self.manifest.content_hash:
            failures.append("PROVIDER_MANIFEST_HASH_MISMATCH")
        if not self.manifest.healthy:
            failures.append("PROVIDER_MANIFEST_UNHEALTHY")
        if not self.manifest.rights_current:
            failures.append("PROVIDER_RIGHTS_NOT_CURRENT")
        if self.manifest.remote_io:
            failures.append("REMOTE_IO_FORBIDDEN_IN_LOCAL_STUB")
        for label, expected, actual in (
            ("ADAPTER", spec.adapter, request.adapter),
            ("CANDIDATE", spec.candidate_id, request.candidate_id),
            ("ENVELOPE", spec.envelope_fingerprint, request.envelope_fingerprint),
            ("PROFILE", spec.profile_id, request.profile_id),
            ("BLUEPRINT", spec.blueprint_id, request.blueprint_id),
            ("RESEARCH", spec.research_pack_id, request.research_pack_id),
        ):
            if expected != actual:
                failures.append(f"SPEC_{label}_MISMATCH")
        existing = self._receipts.get(spec.idempotency_key)
        if existing is not None:
            if existing.input_hash != spec.input_hash:
                failures.append("IDEMPOTENCY_IDENTITY_COLLISION")
            elif not failures:
                production = build_production_candidate(
                    profile, blueprint, blueprint_disposition, payload, research,
                    research_disposition, request,
                )
                replay = GatewayReceipt(
                    existing.receipt_id, existing.spec_id, existing.provider_manifest_id,
                    existing.adapter, existing.idempotency_key, existing.input_hash,
                    existing.output_hash, "IDEMPOTENT_REPLAY", existing.quarantine_state,
                    existing.retries, existing.cost_units, existing.executed_at,
                )
                return GatewayExecution(production, replay)
        if failures:
            production = ProductionAssessment("SCOPE_VIOLATION", tuple(failures), None)
            receipt = GatewayReceipt(
                "RECEIPT-" + sha256((spec.input_hash + "|REJECTED").encode("utf-8")).hexdigest()[:24],
                spec.spec_id, self.manifest.manifest_id, spec.adapter, spec.idempotency_key,
                spec.input_hash, None, "REJECTED", "QUARANTINED", 0, 0, now,
            )
            return GatewayExecution(production, receipt)
        production = build_production_candidate(
            profile, blueprint, blueprint_disposition, payload, research,
            research_disposition, request,
        )
        output_hash = None if production.candidate is None else production.candidate.artifact.sha256
        outcome = "EXECUTED" if production.ready_for_review else "REJECTED_BY_E06"
        receipt = GatewayReceipt(
            "RECEIPT-" + sha256((spec.input_hash + "|" + (output_hash or outcome)).encode("utf-8")).hexdigest()[:24],
            spec.spec_id, self.manifest.manifest_id, spec.adapter, spec.idempotency_key,
            spec.input_hash, output_hash, outcome,
            "LOCAL_VALIDATED" if production.ready_for_review else "QUARANTINED",
            0, 0, now,
        )
        self._receipts[spec.idempotency_key] = receipt
        return GatewayExecution(production, receipt)


def execution_spec_for(
    request: ProductionRequest,
    manifest: ProviderManifest | None = None,
) -> CreativeExecutionSpec:
    """Create the exact E06-owned local execution request."""

    identity = sha256("\x1f".join((
        request.candidate_id, request.envelope_fingerprint, request.profile_id,
        request.blueprint_id, request.research_pack_id, request.adapter,
    )).encode("utf-8")).hexdigest()
    manifest = manifest or ProviderManifest(
        "MANIFEST-LOCAL-STUB-0.1.0", "LOCAL_DETERMINISTIC_STUB", "HTML_EMAIL_OR_SVG",
        "0.1.0", True, True, False,
    )
    return CreativeExecutionSpec(
        "SPEC-" + identity[:24], "0.1.0", "E06", request.adapter,
        request.candidate_id, request.envelope_fingerprint, request.profile_id,
        request.blueprint_id, request.research_pack_id,
        manifest.manifest_id, manifest.content_hash, "IDEMPOTENCY-" + identity,
    )
