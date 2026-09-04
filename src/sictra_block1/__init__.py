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
from .source_gateway import SourceGateway, SourceRegistration
from .source_portfolio import SourceCandidate, SourcePortfolio, default_source_portfolio
from .source_approval import SourceApprovalRecord
from .source_binding import SourceBindingAuthorization, SourceBindingIssuer, SourceBindingVerifier

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
    "SourceGateway",
    "SourceRegistration",
    "SourceCandidate",
    "SourcePortfolio",
    "default_source_portfolio",
    "SourceApprovalRecord",
    "SourceBindingAuthorization",
    "SourceBindingIssuer",
    "SourceBindingVerifier",
]
