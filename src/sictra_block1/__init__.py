"""SICTrA Block 1 bounded execution slice.

This package is a local, executable harness. It is not a global gate decision
or evidence of an external production runtime.
"""

from .context import ContextPack, ContextRecord, build_context_pack
from .reassessment import ReassessmentResult, reassess
from .common import AuthorityContext, ContractViolation, Envelope, IdentityCollision
from .runtime import IntelligenceRuntime

__all__ = [
    "ContextPack",
    "ContextRecord",
    "ReassessmentResult",
    "build_context_pack",
    "reassess",
    "AuthorityContext",
    "ContractViolation",
    "Envelope",
    "IdentityCollision",
    "IntelligenceRuntime",
]
