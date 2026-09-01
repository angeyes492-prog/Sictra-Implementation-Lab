"""Governed provider sandbox for bounded E06 adapter execution."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from threading import Lock
from time import monotonic
from typing import Protocol

from .canonical_document import canonical_json
from .e03_design_system import SystemProfileProposal
from .e04_information_design import InformationBlueprint, InformationPayload
from .e05_reference_research import ReferenceResearchProposal
from .e06_production import ProductionAssessment, ProductionRequest, build_production_candidate
from .model_gateway import (
    CreativeExecutionSpec, GatewayExecution, GatewayReceipt, ModelGatewayViolation,
    ProviderManifest, execution_spec_for,
)


@dataclass(frozen=True, slots=True)
class SandboxPolicy:
    policy_id: str
    contract_version: str
    max_cost_units: int
    timeout_ms: int
    max_output_bytes: int
    allowed_adapters: tuple[str, ...]
    rights_hash: str
    allow_remote_io: bool = True

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or not self.contract_version.startswith("0.1."):
            raise ModelGatewayViolation("sandbox policy identity or version is invalid")
        if self.max_cost_units < 0 or not 1 <= self.timeout_ms <= 60_000:
            raise ModelGatewayViolation("sandbox budget or timeout is invalid")
        if not 1 <= self.max_output_bytes <= 20_000_000:
            raise ModelGatewayViolation("sandbox output limit is invalid")
        if not self.allowed_adapters or not self.rights_hash.strip():
            raise ModelGatewayViolation("sandbox adapters and rights must be explicit")

    @property
    def content_hash(self) -> str:
        return sha256(canonical_json(self).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    content: bytes
    media_type: str
    cost_units: int


class ProviderAdapter(Protocol):
    def invoke(self, spec: CreativeExecutionSpec, expected_content: bytes) -> ProviderResponse: ...


class CancellationRegistry:
    def __init__(self) -> None:
        self._cancelled: set[str] = set()
        self._lock = Lock()

    def cancel(self, idempotency_key: str) -> None:
        with self._lock:
            self._cancelled.add(idempotency_key)

    def is_cancelled(self, idempotency_key: str) -> bool:
        with self._lock:
            return idempotency_key in self._cancelled


class GovernedProviderSandbox:
    """Execute one pinned adapter inside currentness, budget and quarantine bounds."""

    def __init__(
        self,
        manifest: ProviderManifest,
        policy: SandboxPolicy,
        adapter: ProviderAdapter,
        *,
        cancellations: CancellationRegistry | None = None,
    ) -> None:
        self.manifest = manifest
        self.policy = policy
        self.adapter = adapter
        self.cancellations = cancellations or CancellationRegistry()
        self._receipts: dict[str, GatewayReceipt] = {}

    def execution_spec_for(self, request: ProductionRequest) -> CreativeExecutionSpec:
        """Bind E06 execution to this already-governed manifest identity."""

        return execution_spec_for(request, self.manifest)

    def _receipt(
        self, spec: CreativeExecutionSpec, *, now: datetime, outcome: str,
        output_hash: str | None, cost: int, latency_ms: int, cancel_state: str,
    ) -> GatewayReceipt:
        identity = sha256(
            f"{spec.input_hash}|{outcome}|{output_hash or ''}".encode("utf-8")
        ).hexdigest()[:24]
        return GatewayReceipt(
            "RECEIPT-" + identity, spec.spec_id, self.manifest.manifest_id,
            spec.adapter, spec.idempotency_key, spec.input_hash, output_hash,
            outcome, "VALIDATED_LOCAL_BOUNDARY" if outcome == "EXECUTED" else "QUARANTINED",
            0, cost, now, latency_ms, cancel_state, self.policy.max_cost_units,
            self.policy.timeout_ms, self.policy.content_hash, self.policy.rights_hash,
        )

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
            raise ModelGatewayViolation("sandbox time must be timezone-aware")
        failures: list[str] = []
        if spec.provider_manifest_id != self.manifest.manifest_id:
            failures.append("PROVIDER_MANIFEST_SUBSTITUTION")
        if spec.provider_manifest_hash != self.manifest.content_hash:
            failures.append("PROVIDER_MANIFEST_HASH_MISMATCH")
        if not self.manifest.healthy:
            failures.append("PROVIDER_MANIFEST_UNHEALTHY")
        if not self.manifest.rights_current:
            failures.append("PROVIDER_RIGHTS_NOT_CURRENT")
        if self.manifest.remote_io and not self.policy.allow_remote_io:
            failures.append("REMOTE_IO_POLICY_FORBIDDEN")
        if spec.adapter not in self.policy.allowed_adapters:
            failures.append("ADAPTER_NOT_ALLOWLISTED")
        if self.manifest.adapter != spec.adapter:
            failures.append("PROVIDER_ADAPTER_MISMATCH")
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
                    existing.latency_ms, existing.cancel_state, existing.budget_limit_units,
                    existing.timeout_ms, existing.policy_hash, existing.rights_hash,
                )
                return GatewayExecution(production, replay)
        if self.cancellations.is_cancelled(spec.idempotency_key):
            receipt = self._receipt(
                spec, now=now, outcome="CANCELED", output_hash=None, cost=0,
                latency_ms=0, cancel_state="CANCELED_BEFORE_EXECUTION",
            )
            return GatewayExecution(
                ProductionAssessment("SCOPE_VIOLATION", ("EXECUTION_CANCELED",), None), receipt,
            )
        if failures:
            receipt = self._receipt(
                spec, now=now, outcome="REJECTED", output_hash=None, cost=0,
                latency_ms=0, cancel_state="NOT_REQUESTED",
            )
            return GatewayExecution(ProductionAssessment("SCOPE_VIOLATION", tuple(failures), None), receipt)

        production = build_production_candidate(
            profile, blueprint, blueprint_disposition, payload, research,
            research_disposition, request,
        )
        if not production.ready_for_review:
            receipt = self._receipt(
                spec, now=now, outcome="REJECTED_BY_E06", output_hash=None, cost=0,
                latency_ms=0, cancel_state="NOT_REQUESTED",
            )
            return GatewayExecution(production, receipt)
        expected = production.candidate.artifact
        started = monotonic()
        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="sictra-provider")
        future = executor.submit(self.adapter.invoke, spec, expected.content)
        try:
            response = future.result(timeout=self.policy.timeout_ms / 1000)
        except FutureTimeout:
            future.cancel()
            latency = max(self.policy.timeout_ms, int((monotonic() - started) * 1000))
            executor.shutdown(wait=False, cancel_futures=True)
            receipt = self._receipt(
                spec, now=now, outcome="TIMEOUT", output_hash=None, cost=0,
                latency_ms=latency, cancel_state="CANCEL_REQUESTED_AFTER_TIMEOUT",
            )
            return GatewayExecution(ProductionAssessment("SCOPE_VIOLATION", ("PROVIDER_TIMEOUT",), None), receipt)
        except Exception:
            executor.shutdown(wait=False, cancel_futures=True)
            receipt = self._receipt(
                spec, now=now, outcome="PROVIDER_ERROR", output_hash=None, cost=0,
                latency_ms=int((monotonic() - started) * 1000), cancel_state="NOT_REQUESTED",
            )
            return GatewayExecution(ProductionAssessment("SCOPE_VIOLATION", ("PROVIDER_EXCEPTION",), None), receipt)
        executor.shutdown(wait=True)
        latency = int((monotonic() - started) * 1000)
        response_hash = sha256(response.content).hexdigest() if isinstance(response.content, bytes) else None
        output_failures: list[str] = []
        if not isinstance(response.content, bytes) or not isinstance(response.media_type, str):
            output_failures.append("PROVIDER_OUTPUT_MALFORMED")
        elif len(response.content) > self.policy.max_output_bytes:
            output_failures.append("PROVIDER_OUTPUT_TOO_LARGE")
        elif response.media_type != expected.media_type:
            output_failures.append("PROVIDER_MEDIA_TYPE_MISMATCH")
        elif response_hash != expected.sha256:
            output_failures.append("PROVIDER_OUTPUT_HASH_MISMATCH")
        if not isinstance(response.cost_units, int) or response.cost_units < 0:
            output_failures.append("PROVIDER_COST_INVALID")
            cost = 0
        else:
            cost = response.cost_units
            if cost > self.policy.max_cost_units:
                output_failures.append("PROVIDER_BUDGET_EXCEEDED")
        if self.cancellations.is_cancelled(spec.idempotency_key):
            output_failures.append("EXECUTION_CANCELED_DURING_PROVIDER_CALL")
        if output_failures:
            receipt = self._receipt(
                spec, now=now, outcome="QUARANTINED", output_hash=response_hash,
                cost=cost, latency_ms=latency, cancel_state=(
                    "CANCEL_OBSERVED_AFTER_EXECUTION" if "EXECUTION_CANCELED_DURING_PROVIDER_CALL" in output_failures
                    else "NOT_REQUESTED"
                ),
            )
            return GatewayExecution(ProductionAssessment("SCOPE_VIOLATION", tuple(output_failures), None), receipt)
        receipt = self._receipt(
            spec, now=now, outcome="EXECUTED", output_hash=response_hash, cost=cost,
            latency_ms=latency, cancel_state="NOT_REQUESTED",
        )
        self._receipts[spec.idempotency_key] = receipt
        return GatewayExecution(production, receipt)
