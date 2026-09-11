"""Fail-closed orchestration for the bounded Block 2 design runtime."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .preflight import Fixture, assess_fixture
from .e02_direction import Direction, DirectionSet, E02Envelope, VisualThesis, assess_direction_set
from .e03_design_system import SystemProfileProposal, assess_system_profile
from .e04_information_design import (
    ChannelTarget, InformationBlueprint, InformationPayload, assess_information_blueprint,
)
from .e05_reference_research import ReferenceResearchProposal, assess_reference_research
from .e06_production import ProductionAssessment, ProductionRequest
from .e07_visual_red_team import VisualAssessment, VisualReview, assess_visual_candidate
from .e08_creative_memory import (
    CreativeMemoryStore, ExternalValidationRecord, MemoryAssessment, MemoryProposal,
    assess_memory_candidate,
)
from .model_gateway import (
    GatewayReceipt, LocalDeterministicModelGateway, execution_spec_for,
)
from .engine_registry import EngineRegistry, EngineRegistryViolation, default_engine_registry


_ENGINES = tuple(f"E0{number}" for number in range(1, 9))


@dataclass(frozen=True, slots=True)
class Block2RunInput:
    fixture: Fixture
    envelope: E02Envelope
    thesis: VisualThesis
    directions: DirectionSet
    selected_direction: Direction
    system_profile: SystemProfileProposal
    payload: InformationPayload
    channel_target: ChannelTarget
    blueprint: InformationBlueprint
    research: ReferenceResearchProposal
    production_request: ProductionRequest
    visual_review: VisualReview
    external_validation: ExternalValidationRecord
    memory_proposal: MemoryProposal


@dataclass(frozen=True, slots=True)
class StageResult:
    engine: str
    disposition: str
    reasons: tuple[str, ...]
    execution_state: str = "EXECUTED"


@dataclass(frozen=True, slots=True)
class Block2RunResult:
    completed: bool
    stopped_at: str | None
    stages: tuple[StageResult, ...]
    production: ProductionAssessment | None = None
    visual: VisualAssessment | None = None
    memory: MemoryAssessment | None = None
    memory_store_action: str | None = None
    publication_state: str = "NOT_PUBLISHED"
    acceptance_state: str = "NOT_ACCEPTED"
    gateway_receipt: GatewayReceipt | None = None
    executed_engines: tuple[str, ...] = ()
    reused_engines: tuple[str, ...] = ()
    engine_registry_hash: str | None = None


def execute_block2(
    request: Block2RunInput,
    *,
    now: datetime | None = None,
    memory_store: CreativeMemoryStore | None = None,
    model_gateway: LocalDeterministicModelGateway | None = None,
    engine_registry: EngineRegistry | None = None,
) -> Block2RunResult:
    """Execute E01-E08 locally and stop at the first non-ready boundary."""

    return execute_block2_partial(
        request, reused_engines=(), previous_result=None, now=now,
        memory_store=memory_store, model_gateway=model_gateway,
        engine_registry=engine_registry,
    )


def execute_block2_partial(
    request: Block2RunInput,
    *,
    reused_engines: tuple[str, ...],
    previous_result: Block2RunResult | None,
    now: datetime | None = None,
    memory_store: CreativeMemoryStore | None = None,
    model_gateway: LocalDeterministicModelGateway | None = None,
    engine_registry: EngineRegistry | None = None,
) -> Block2RunResult:
    """Execute only the suffix after a verified, contiguous reusable prefix."""

    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    if reused_engines != _ENGINES[:len(reused_engines)]:
        raise ValueError("reused engines must be a contiguous canonical prefix")
    if reused_engines and previous_result is None:
        raise ValueError("reused engines require a previous result")

    registry = engine_registry or default_engine_registry()
    registry.verify_bindings()
    registry_hash = registry.content_hash
    if previous_result is not None and previous_result.engine_registry_hash not in {None, registry_hash}:
        raise EngineRegistryViolation("previous result was produced by another engine registry")

    prior = {} if previous_result is None else {stage.engine: stage for stage in previous_result.stages}
    if any(engine not in prior for engine in reused_engines):
        raise ValueError("previous result does not contain the reusable prefix")
    stages: list[StageResult] = [
        StageResult(engine, prior[engine].disposition, prior[engine].reasons, "REUSED_CHECKPOINT")
        for engine in reused_engines
    ]
    executed: list[str] = []

    def record(engine: str, disposition: str, reasons: tuple[str, ...]) -> None:
        stages.append(StageResult(engine, disposition, reasons))
        executed.append(engine)

    def result(
        completed: bool,
        stopped_at: str | None,
        *,
        production: ProductionAssessment | None = None,
        visual: VisualAssessment | None = None,
        memory: MemoryAssessment | None = None,
        memory_store_action: str | None = None,
        receipt: GatewayReceipt | None = None,
    ) -> Block2RunResult:
        return Block2RunResult(
            completed, stopped_at, tuple(stages), production, visual, memory,
            memory_store_action, "NOT_PUBLISHED", "NOT_ACCEPTED", receipt,
            tuple(executed), reused_engines, registry_hash,
        )

    start = len(reused_engines)

    if start <= 0:
        e01 = assess_fixture(request.fixture)
        record("E01", e01.disposition, e01.reasons)
        if not e01.ready_for_observation:
            return result(False, "E01")

    if start <= 1:
        e02 = assess_direction_set(request.envelope, request.thesis, request.directions)
        record("E02", e02.disposition, e02.reasons)
        if not e02.ready_for_selection:
            return result(False, "E02")
    if start <= 2:
        if request.selected_direction.direction_id not in {item.direction_id for item in request.directions.directions}:
            record("E03", "RETURN_TO_PREVIOUS", ("EXTERNAL_SELECTION_NOT_IN_DIRECTION_SET",))
            return result(False, "E03")
        e03 = assess_system_profile(
            request.envelope.fingerprint, request.selected_direction, request.system_profile, now,
        )
        record("E03", e03.disposition, e03.reasons)
        if not e03.ready_for_blueprint:
            return result(False, "E03")

    e03_disposition = stages[2].disposition

    if start <= 3:
        e04 = assess_information_blueprint(
            request.envelope.fingerprint, request.system_profile, e03_disposition,
            request.payload, request.channel_target, request.blueprint,
        )
        record("E04", e04.disposition, e04.reasons)
        if not e04.ready_for_production_review:
            return result(False, "E04")
    e04_disposition = stages[3].disposition

    if start <= 4:
        e05 = assess_reference_research(request.blueprint, e04_disposition, request.research, now)
        record("E05", e05.disposition, e05.reasons)
        if not e05.ready_for_production:
            return result(False, "E05")
    e05_disposition = stages[4].disposition

    if start <= 5:
        gateway = model_gateway or LocalDeterministicModelGateway()
        spec_builder = getattr(gateway, "execution_spec_for", None)
        execution_spec = (
            spec_builder(request.production_request)
            if callable(spec_builder) else execution_spec_for(request.production_request)
        )
        gateway_execution = gateway.execute(
            execution_spec,
            profile=request.system_profile, blueprint=request.blueprint,
            blueprint_disposition=e04_disposition, payload=request.payload,
            research=request.research, research_disposition=e05_disposition,
            request=request.production_request, now=now,
        )
        production = gateway_execution.production
        receipt = gateway_execution.receipt
        record("E06", production.disposition, production.reasons)
        if not production.ready_for_review:
            return result(False, "E06", production=production, receipt=receipt)
    else:
        production = previous_result.production
        receipt = previous_result.gateway_receipt
        if production is None or receipt is None:
            raise ValueError("reusing E06 requires production and receipt state")

    if start <= 6:
        visual = assess_visual_candidate(production.candidate, production.disposition, request.visual_review)
        record("E07", visual.disposition, visual.reasons)
        if not visual.recommended_for_external_review:
            return result(False, "E07", production=production, visual=visual, receipt=receipt)
    else:
        visual = previous_result.visual
        if visual is None:
            raise ValueError("reusing E07 requires visual state")

    if start <= 7:
        memory = assess_memory_candidate(visual, request.external_validation, request.memory_proposal, now)
        record("E08", memory.disposition, memory.reasons)
        if not memory.ready:
            return result(False, "E08", production=production, visual=visual, memory=memory, receipt=receipt)

        store = memory_store or CreativeMemoryStore()
        action, _ = store.write(memory, request.memory_proposal)
        if action not in {"STORED", "IDEMPOTENT"}:
            record("E08", action, ("MEMORY_STORE_REJECTED",))
            return result(False, "E08", production=production, visual=visual, memory=memory, memory_store_action=action, receipt=receipt)
    else:
        memory = previous_result.memory
        if memory is None:
            raise ValueError("reusing E08 requires memory state")
        action = "REUSED_CHECKPOINT"
    return result(
        True, None, production=production, visual=visual, memory=memory,
        memory_store_action=action, receipt=receipt,
    )
