"""Explicit, versioned rules for producing bounded M02 decision signals."""

from __future__ import annotations

from dataclasses import dataclass
import hmac
from typing import Mapping

from .account_context import AccountContextAdmission, admission_attestation
from .contracts import EngineAssessment, PrecisionContractViolation, fingerprint, require_text
from .decision import DecisionDimension, DecisionSignal, _VALUES


@dataclass(frozen=True, slots=True)
class DecisionSignalRule:
    rule_id: str
    dimension: DecisionDimension
    value: str
    required_account_tags: tuple[str, ...]
    polarity: int = 1

    def __post_init__(self) -> None:
        require_text("rule_id", self.rule_id)
        if self.dimension not in _VALUES or self.value not in _VALUES[self.dimension]:
            raise PrecisionContractViolation("decision rule dimension/value is not governed")
        if self.polarity not in {-1, 1}:
            raise PrecisionContractViolation("decision rule polarity must be -1 or 1")
        if not isinstance(self.required_account_tags, tuple) or any(
            not isinstance(tag, str) for tag in self.required_account_tags
        ):
            raise PrecisionContractViolation("decision rule tags must be a tuple of strings")
        normalized = tuple(sorted({tag.casefold().strip() for tag in self.required_account_tags}))
        if not normalized or any(not tag for tag in normalized):
            raise PrecisionContractViolation("decision rule requires at least one account tag")
        object.__setattr__(self, "required_account_tags", normalized)


@dataclass(frozen=True, slots=True)
class DecisionSignalCatalogPolicy:
    policy_id: str
    authority_reference: str
    rules: tuple[DecisionSignalRule, ...]
    max_emitted_signals: int = 1_000
    accepted_admission_policy_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        require_text("policy_id", self.policy_id)
        require_text("authority_reference", self.authority_reference)
        if not isinstance(self.max_emitted_signals, int) or isinstance(self.max_emitted_signals, bool) or self.max_emitted_signals < 1:
            raise PrecisionContractViolation("max_emitted_signals must be a positive integer")
        if not isinstance(self.rules, tuple) or any(not isinstance(rule, DecisionSignalRule) for rule in self.rules):
            raise PrecisionContractViolation("decision signal policy rules must be a tuple of DecisionSignalRule")
        if not self.rules or len(self.rules) > self.max_emitted_signals:
            raise PrecisionContractViolation("decision signal policy must contain a bounded non-empty rule catalog")
        if len({rule.rule_id for rule in self.rules}) != len(self.rules):
            raise PrecisionContractViolation("decision signal rule IDs must be unique")
        if not isinstance(self.accepted_admission_policy_ids, tuple) or not self.accepted_admission_policy_ids:
            raise PrecisionContractViolation("decision signal policy requires declared admission policy IDs")
        if any(not isinstance(policy_id, str) or not policy_id.strip() for policy_id in self.accepted_admission_policy_ids):
            raise PrecisionContractViolation("accepted admission policy IDs must be non-empty strings")
        if len(set(self.accepted_admission_policy_ids)) != len(self.accepted_admission_policy_ids):
            raise PrecisionContractViolation("accepted admission policy IDs must be unique")
        object.__setattr__(self, "rules", tuple(self.rules))
        object.__setattr__(self, "accepted_admission_policy_ids", tuple(self.accepted_admission_policy_ids))


@dataclass(frozen=True, slots=True)
class DecisionSignalCatalogResult:
    assessment: EngineAssessment
    signals: tuple[DecisionSignal, ...]
    policy_id: str
    admission_fingerprint: str
    restrictions: tuple[str, ...]


class GovernedDecisionSignalCatalog:
    """Maps declared account tags to falsifiable M02 hypotheses by explicit rule."""

    name = "M02_DECISION_SIGNAL_CATALOG"

    def __init__(self, *, policy: DecisionSignalCatalogPolicy, admission_keys: Mapping[str, bytes]) -> None:
        self._policy = policy
        if not isinstance(admission_keys, Mapping) or not admission_keys:
            raise PrecisionContractViolation("decision catalog requires configured admission attestation keys")
        normalized: dict[str, bytes] = {}
        for issuer_id, key in admission_keys.items():
            require_text("admission attestation issuer", issuer_id)
            if not isinstance(key, bytes) or len(key) < 16:
                raise PrecisionContractViolation("decision catalog admission attestation key is invalid")
            normalized[issuer_id] = key
        self._admission_keys = normalized

    def _verify_admission(self, admission: AccountContextAdmission) -> None:
        if admission.policy_id not in self._policy.accepted_admission_policy_ids:
            raise PrecisionContractViolation("account context admission policy does not match decision catalog policy")
        key = self._admission_keys.get(admission.issuer_id)
        if key is None:
            raise PrecisionContractViolation("account context admission issuer is not trusted by decision catalog")
        expected = admission_attestation(admission=admission, key=key)
        if not hmac.compare_digest(admission.attestation, expected):
            raise PrecisionContractViolation("account context admission attestation is invalid")

    def derive(self, *, person_id: str, admission: AccountContextAdmission, now: int) -> DecisionSignalCatalogResult:
        require_text("person_id", person_id)
        if not isinstance(admission, AccountContextAdmission):
            raise PrecisionContractViolation("decision catalog requires an account context admission")
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise PrecisionContractViolation("decision catalog requires non-negative logical time")
        if admission.admitted_at > now or admission.expires_at < now:
            raise PrecisionContractViolation("account context admission is not current")
        self._verify_admission(admission)
        emitted: list[DecisionSignal] = []
        for context_signal in admission.context_signals:
            if not context_signal.active_at(now):
                continue
            tags = frozenset(tag.casefold() for tag in context_signal.tags)
            for rule in self._policy.rules:
                if set(rule.required_account_tags).issubset(tags):
                    emitted.append(DecisionSignal(
                        signal_id=f"decision-rule:{self._policy.policy_id}:{rule.rule_id}:{context_signal.signal_id}",
                        person_id=person_id, insight_id=admission.insight_id, dimension=rule.dimension,
                        value=rule.value, polarity=rule.polarity, basis_kind="HYPOTHESIS",
                        source_engine="GOVERNED_RULE",
                        basis_reference=f"admission:{admission.admission_id}:rule:{rule.rule_id}:account-signal:{context_signal.signal_id}",
                        evidence=context_signal.evidence,
                    ))
        if len(emitted) > self._policy.max_emitted_signals:
            raise PrecisionContractViolation("decision signal catalog output exceeds policy")
        signals = tuple(sorted(emitted, key=lambda signal: signal.signal_id))
        if not signals:
            return DecisionSignalCatalogResult(
                EngineAssessment(self.name, "RETURN_UPSTREAM", ("NO_GOVERNED_RULE_MATCH",), (), None), (),
                self._policy.policy_id, admission.output_fingerprint, ("NO_UNGOVERNED_DECISION_INFERENCE",),
            )
        return DecisionSignalCatalogResult(
            EngineAssessment(self.name, "PARTIAL", ("ACCOUNT_TAG_RULE_OUTPUT_REMAINS_HYPOTHESIS",), tuple(signal.evidence.evidence_id for signal in signals), fingerprint((self._policy.policy_id, admission.output_fingerprint, signals))),
            signals, self._policy.policy_id, admission.output_fingerprint,
            (
                "RULE_MATCH_IS_NOT_PERSONAL_PREFERENCE", "RULE_OUTPUT_IS_NOT_FACT",
                "NO_CONTACT_OR_DELIVERY_AUTHORITY", "RULES_REQUIRE_SEPARATE_GOVERNANCE_AND_REVIEW",
            ),
        )
