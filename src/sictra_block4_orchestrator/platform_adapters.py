"""Typed, no-network admission contracts for optional platform adapters.

Binding an operation only proves that its declared metadata satisfies the local
candidate contract. It deliberately does not call Figma, Framer, HubSpot, or
any other external service.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256


ADAPTER_CONTRACT_VERSION = "0.1.0"
PLATFORMS = frozenset(("FIGMA", "FRAMER", "HUBSPOT"))
MODES = frozenset(("DISABLED", "CONFIGURED", "ACTIVE", "FAILED"))
OPERATIONS = {
    "FIGMA": frozenset(("READ_DESIGN_REFERENCE", "OBSERVE_DESIGN_CHANGE")),
    "FRAMER": frozenset(("EXPORT_REVIEW_DRAFT",)),
    "HUBSPOT": frozenset(("READ_AUDIENCE_CONTEXT",)),
}
SAFE_HUBSPOT_FIELDS = frozenset((
    "company_size_band", "content_interests", "industry", "lifecycle_stage",
    "preferred_language", "region", "segment", "subscription_status",
))
DIRECT_IDENTIFIER_FIELDS = frozenset(("email", "firstname", "lastname", "phone", "mobilephone", "address"))


class AdapterContractError(ValueError):
    """Raised before an optional platform operation can leave Telecare OS."""


def _required(value: str | None, code: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AdapterContractError(code)
    return value.strip()


def _credential_reference(value: str | None) -> str:
    reference = _required(value, "CREDENTIAL_REFERENCE_REQUIRED")
    if not reference.startswith("vault://") or any(character.isspace() for character in reference):
        raise AdapterContractError("CREDENTIAL_REFERENCE_NOT_VAULT_URI")
    return reference


@dataclass(frozen=True)
class AdapterConfiguration:
    adapter_id: str
    platform: str
    mode: str
    allowed_operations: tuple[str, ...]
    credential_reference: str | None = None
    activation_receipt: str | None = None


@dataclass(frozen=True)
class AdapterOperation:
    case_id: str
    run_id: str
    artifact_id: str
    source_hash: str
    platform: str
    operation: str
    input_fields: tuple[str, ...]
    human_authorization: str | None = None


@dataclass(frozen=True)
class PlannedAdapterOperation:
    operation_id: str
    state: str
    platform: str
    operation: str
    restrictions: tuple[str, ...]


def _validate_configuration(config: AdapterConfiguration) -> None:
    _required(config.adapter_id, "ADAPTER_ID_REQUIRED")
    if config.platform not in PLATFORMS:
        raise AdapterContractError("PLATFORM_NOT_ALLOWLISTED")
    if config.mode not in MODES:
        raise AdapterContractError("ADAPTER_MODE_INVALID")
    if not isinstance(config.allowed_operations, tuple) or not config.allowed_operations:
        raise AdapterContractError("ALLOWED_OPERATIONS_REQUIRED")
    if any(operation not in OPERATIONS[config.platform] for operation in config.allowed_operations):
        raise AdapterContractError("OPERATION_NOT_ALLOWLISTED")
    if config.mode == "DISABLED":
        if config.credential_reference is not None or config.activation_receipt is not None:
            raise AdapterContractError("DISABLED_ADAPTER_MUST_NOT_BIND_CREDENTIALS")
    elif config.mode in {"CONFIGURED", "ACTIVE"}:
        _credential_reference(config.credential_reference)
    if config.mode == "ACTIVE":
        _required(config.activation_receipt, "ACTIVATION_RECEIPT_REQUIRED")


def _validate_operation(config: AdapterConfiguration, request: AdapterOperation) -> None:
    for value, code in ((request.case_id, "CASE_ID_REQUIRED"), (request.run_id, "RUN_ID_REQUIRED"),
                        (request.artifact_id, "ARTIFACT_ID_REQUIRED"), (request.source_hash, "SOURCE_HASH_REQUIRED")):
        _required(value, code)
    if request.platform != config.platform:
        raise AdapterContractError("PLATFORM_CONFIGURATION_MISMATCH")
    if request.operation not in config.allowed_operations:
        raise AdapterContractError("OPERATION_NOT_APPROVED")
    if not isinstance(request.input_fields, tuple) or any(not isinstance(field, str) or not field for field in request.input_fields):
        raise AdapterContractError("INPUT_FIELDS_INVALID")
    if request.platform == "HUBSPOT":
        fields = frozenset(request.input_fields)
        if request.operation != "READ_AUDIENCE_CONTEXT" or not fields:
            raise AdapterContractError("HUBSPOT_READ_ONLY_CONTEXT_REQUIRED")
        if fields & DIRECT_IDENTIFIER_FIELDS or not fields <= SAFE_HUBSPOT_FIELDS:
            raise AdapterContractError("HUBSPOT_FIELD_NOT_MINIMIZED")
    elif request.input_fields:
        raise AdapterContractError("DESIGN_ADAPTER_MUST_NOT_RECEIVE_AUDIENCE_FIELDS")


def _operation_id(request: AdapterOperation) -> str:
    material = "|".join((ADAPTER_CONTRACT_VERSION, request.case_id, request.run_id, request.artifact_id,
                         request.source_hash, request.platform, request.operation, ",".join(request.input_fields)))
    return sha256(material.encode("utf-8")).hexdigest()[:32]


def plan_adapter_operation(config: AdapterConfiguration, request: AdapterOperation) -> PlannedAdapterOperation:
    """Validate a future operation while every adapter remains locally inert."""
    _validate_configuration(config)
    _validate_operation(config, request)
    return PlannedAdapterOperation(
        operation_id=_operation_id(request), state="PLANNED", platform=request.platform,
        operation=request.operation,
        restrictions=("NO_NETWORK_EXECUTED", "NO_PUBLICATION", "NO_CRM_WRITE", "HUMAN_ACTIVATION_REQUIRED"),
    )


def admit_adapter_operation(config: AdapterConfiguration, request: AdapterOperation) -> PlannedAdapterOperation:
    """Bind a request for a future adapter worker; never executes that worker."""
    planned = plan_adapter_operation(config, request)
    if config.mode != "ACTIVE":
        raise AdapterContractError("ADAPTER_NOT_ACTIVE")
    _required(request.human_authorization, "HUMAN_AUTHORIZATION_REQUIRED")
    return PlannedAdapterOperation(
        operation_id=planned.operation_id, state="BOUND_NOT_EXECUTED", platform=planned.platform,
        operation=planned.operation,
        restrictions=("EXECUTION_REQUIRES_ADAPTER_WORKER", "NO_PUBLICATION", "AUDIT_REQUIRED"),
    )
