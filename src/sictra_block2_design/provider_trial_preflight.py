"""Non-operational governance preflight for a future Block 2 provider trial.

The preflight deliberately has no network adapter, credential resolver or
execution method.  It makes the evidence package required before a real trial
explicit while preserving MAR and external credential verification as separate
human/operational gates.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Literal


Lane = Literal["GENERATIVE_MEDIA", "DESIGN_PLATFORM"]
CredentialState = Literal["AVAILABLE", "MISSING", "EXPIRED", "REVOKED"]
PreflightDisposition = Literal["PRECONDITIONS_DECLARED", "RETURN_UPSTREAM"]
_LANE_SCOPES = {
    "GENERATIVE_MEDIA": frozenset({"IMAGE_GENERATION"}),
    "DESIGN_PLATFORM": frozenset({"DESIGN_CREATE", "DESIGN_EXPORT"}),
}
_HASH = re.compile(r"^[0-9a-f]{64}$")
_SECRET_MARKERS = ("sk-", "bearer ", "api_key=", "apikey=")


class ProviderTrialPreflightViolation(ValueError):
    """A provider-trial declaration is malformed or leaks a secret."""


def _required(**fields: str) -> None:
    missing = [name for name, value in fields.items() if not isinstance(value, str) or not value.strip()]
    if missing:
        raise ProviderTrialPreflightViolation(f"missing required fields: {', '.join(missing)}")


@dataclass(frozen=True, slots=True)
class ProviderTrialReadinessRecord:
    """A non-secret declaration of the governance package for one provider lane."""

    preflight_id: str
    contract_version: str
    lane: str
    provider_id: str
    provider_snapshot: str
    credential_handle: str
    credential_state: str
    terms_reference: str
    data_policy_reference: str
    rights_manifest_hash: str
    budget_policy_reference: str
    trial_authority_reference: str
    mar_reference: str
    declared_scopes: tuple[str, ...]
    reviewed_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        _required(
            preflight_id=self.preflight_id, contract_version=self.contract_version,
            lane=self.lane, provider_id=self.provider_id, provider_snapshot=self.provider_snapshot,
            credential_handle=self.credential_handle, terms_reference=self.terms_reference,
            data_policy_reference=self.data_policy_reference,
            budget_policy_reference=self.budget_policy_reference,
            trial_authority_reference=self.trial_authority_reference, mar_reference=self.mar_reference,
        )
        if not self.contract_version.startswith("0.1."):
            raise ProviderTrialPreflightViolation("provider trial preflight version is unsupported")
        if self.lane not in _LANE_SCOPES:
            raise ProviderTrialPreflightViolation("provider lane is not governed")
        if self.credential_state not in {"AVAILABLE", "MISSING", "EXPIRED", "REVOKED"}:
            raise ProviderTrialPreflightViolation("credential state is not governed")
        if not _HASH.fullmatch(self.rights_manifest_hash):
            raise ProviderTrialPreflightViolation("rights_manifest_hash must be a lowercase SHA-256")
        handle = self.credential_handle.lower()
        if any(marker in handle for marker in _SECRET_MARKERS):
            raise ProviderTrialPreflightViolation("credential_handle must be a non-secret vault reference")
        if not self.declared_scopes or any(not isinstance(scope, str) or not scope.strip() for scope in self.declared_scopes):
            raise ProviderTrialPreflightViolation("declared_scopes must be non-empty strings")
        if not isinstance(self.reviewed_at, datetime) or self.reviewed_at.tzinfo is None:
            raise ProviderTrialPreflightViolation("reviewed_at must be timezone-aware")
        if not isinstance(self.expires_at, datetime) or self.expires_at.tzinfo is None:
            raise ProviderTrialPreflightViolation("expires_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class ProviderTrialPreflightAssessment:
    disposition: PreflightDisposition
    reasons: tuple[str, ...]
    lane: str
    execution_authorized: bool = False
    acceptance_state: str = "NOT_ACCEPTED"


def assess_provider_trial_readiness(
    record: ProviderTrialReadinessRecord,
    *,
    now: datetime,
) -> ProviderTrialPreflightAssessment:
    """Classify declared prerequisites without resolving or using credentials.

    A clean declaration remains non-operational.  MAR and credential validity
    must be independently verified at the actual provider boundary before any
    remote call is allowed.
    """

    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ProviderTrialPreflightViolation("assessment time must be timezone-aware")
    reasons: list[str] = []
    if record.credential_state != "AVAILABLE":
        reasons.append(f"CREDENTIAL_{record.credential_state}")
    if record.expires_at <= now:
        reasons.append("PREFLIGHT_EXPIRED")
    required_scopes = _LANE_SCOPES[record.lane]
    missing_scopes = sorted(required_scopes.difference(record.declared_scopes))
    reasons.extend(f"SCOPE_MISSING_{scope}" for scope in missing_scopes)
    if reasons:
        return ProviderTrialPreflightAssessment("RETURN_UPSTREAM", tuple(reasons), record.lane)
    return ProviderTrialPreflightAssessment("PRECONDITIONS_DECLARED", (), record.lane)
