"""Bounded SICTrA Block 2 design validation and candidate-production runtime.

The package can create deterministic local candidates.  It does not publish,
grant rights, replace human review, or establish global acceptance.
"""

from .preflight import (
    Candidate,
    ClaimComposition,
    Confounder,
    E01PreflightViolation,
    Fixture,
    ObserverProfile,
    PreflightAssessment,
    TaskDefinition,
    UpstreamIntelligence,
    assess_fixture,
)
from .runtime import (
    Block2RunInput, Block2RunResult, StageResult, execute_block2,
    execute_block2_partial,
)
from .engine_registry import (
    EngineManifest, EngineRegistry, EngineRegistryViolation, default_engine_registry,
    persist_engine_registry,
)
from .orchestrator import (
    OrchestratedResume, execute_resumed_block2, persist_orchestrated_resume,
)
from .canonical_document import DesignDocumentVersion, DesignElement, DesignPage
from .project_graph import ProjectGraphStore
from .traceable_runtime import TraceableBlock2RunResult, execute_traceable_block2
from .model_gateway import (
    CreativeExecutionSpec, GatewayReceipt, LocalDeterministicModelGateway,
    ModelGatewayViolation, ProviderManifest,
)
from .document_evolution import (
    DocumentDiff, DocumentEditProposal, DocumentEvolutionViolation, ElementEdit,
    EvolutionResult, InvalidationPlan, apply_document_edit, persist_document_evolution,
)
from .checkpoint import (
    CheckpointViolation, ResumeDecision, RunCheckpoint, checkpoint_from_run,
    persist_checkpoint, plan_resume, request_hash,
)
from .export_service import (
    ExportAssessment, ExportPackage, ExportRequest, ExportServiceViolation,
    build_export_package, persist_export,
)
from .design_context import (
    CreateAssessment, CreateDesignRequest, DesignContextEnvelope,
    DesignContextViolation, RuntimeBindingAssessment, assess_runtime_binding,
    compile_design_context, persist_create_assessment,
)
from .provider_sandbox import (
    CancellationRegistry, GovernedProviderSandbox, ProviderResponse, SandboxPolicy,
)
from .reference_fixture import reference_run_input, run_reference_fixture

__all__ = [
    "Candidate",
    "ClaimComposition",
    "Confounder",
    "E01PreflightViolation",
    "Fixture",
    "ObserverProfile",
    "PreflightAssessment",
    "TaskDefinition",
    "UpstreamIntelligence",
    "assess_fixture",
    "Block2RunInput",
    "Block2RunResult",
    "StageResult",
    "execute_block2",
    "execute_block2_partial",
    "EngineManifest",
    "EngineRegistry",
    "EngineRegistryViolation",
    "default_engine_registry",
    "persist_engine_registry",
    "OrchestratedResume",
    "execute_resumed_block2",
    "persist_orchestrated_resume",
    "DesignDocumentVersion",
    "DesignElement",
    "DesignPage",
    "ProjectGraphStore",
    "TraceableBlock2RunResult",
    "execute_traceable_block2",
    "CreativeExecutionSpec",
    "GatewayReceipt",
    "LocalDeterministicModelGateway",
    "ModelGatewayViolation",
    "ProviderManifest",
    "DocumentDiff",
    "DocumentEditProposal",
    "DocumentEvolutionViolation",
    "ElementEdit",
    "EvolutionResult",
    "InvalidationPlan",
    "apply_document_edit",
    "persist_document_evolution",
    "CheckpointViolation",
    "ResumeDecision",
    "RunCheckpoint",
    "checkpoint_from_run",
    "persist_checkpoint",
    "plan_resume",
    "request_hash",
    "ExportAssessment",
    "ExportPackage",
    "ExportRequest",
    "ExportServiceViolation",
    "build_export_package",
    "persist_export",
    "CreateAssessment",
    "CreateDesignRequest",
    "DesignContextEnvelope",
    "DesignContextViolation",
    "RuntimeBindingAssessment",
    "assess_runtime_binding",
    "compile_design_context",
    "persist_create_assessment",
    "CancellationRegistry",
    "GovernedProviderSandbox",
    "ProviderResponse",
    "SandboxPolicy",
    "reference_run_input",
    "run_reference_fixture",
]
