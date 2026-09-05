"""SICTrA Block 1 bounded execution slice.

This package is a local, executable harness. It is not a global gate decision
or evidence of an external production runtime.
"""

from .context import ContextPack, ContextRecord, build_context_pack
from .reassessment import ReassessmentResult, reassess
from .common import (
    AuthorityContext, AuthorityIssuer, AuthorityVerifier, ContractViolation,
    Envelope, IdentityCollision,
)
from .evidence import EvidenceIssuer, EvidenceVerifier
from .runtime import IntelligenceRuntime
from .storage import OperationalStore
from .source_portfolio import SourceCandidate, source_readiness
from .source_gateway import SourceApprovalRecord, SourceBindingIssuer, SourceGateway, SourceRegistration
from .manual_source_preflight import ManualSourcePreflightViolation, preflight_manual_source_file
from .eurostat_maritime_mapper import (
    EurostatMaritimeMappingViolation,
    map_eurostat_maritime_workbook,
    select_eurostat_geography_level,
)
from .eurostat_manual_bundle import (
    EurostatManualBundleViolation,
    build_eurostat_manual_bundle,
)
from .manual_bundle_ledger import (
    ManualBundleLedger,
    ManualBundleLedgerViolation,
    validate_unattested_manual_bundle,
)
from .eurostat_maritime_delta import (
    EurostatMaritimeDeltaViolation,
    compare_eurostat_manual_bundles,
    compare_eurostat_maritime_workbooks,
)
from .intelligence_layers import KNOWN_TOPICS, TOPIC_CATALOG, normalize_research_frame, validate_research_frame_bundle

__all__ = [
    "ContextPack",
    "ContextRecord",
    "ReassessmentResult",
    "build_context_pack",
    "reassess",
    "AuthorityContext",
    "AuthorityIssuer",
    "AuthorityVerifier",
    "ContractViolation",
    "Envelope",
    "IdentityCollision",
    "IntelligenceRuntime",
    "EvidenceIssuer",
    "EvidenceVerifier",
    "OperationalStore",
    "SourceCandidate",
    "source_readiness",
    "SourceBindingIssuer",
    "SourceApprovalRecord",
    "SourceGateway",
    "SourceRegistration",
    "ManualSourcePreflightViolation",
    "preflight_manual_source_file",
    "EurostatMaritimeMappingViolation",
    "map_eurostat_maritime_workbook",
    "select_eurostat_geography_level",
    "EurostatManualBundleViolation",
    "build_eurostat_manual_bundle",
    "ManualBundleLedger",
    "ManualBundleLedgerViolation",
    "validate_unattested_manual_bundle",
    "EurostatMaritimeDeltaViolation",
    "compare_eurostat_manual_bundles",
    "compare_eurostat_maritime_workbooks",
    "KNOWN_TOPICS",
    "TOPIC_CATALOG",
    "normalize_research_frame",
    "validate_research_frame_bundle",
]

