"""M06 Message Intelligence: strategy without copy or delivery authority."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .adaptive import AdaptiveLevelDecision
from .contracts import (
    EngineAssessment, EvidenceRef, PrecisionContractViolation, fingerprint, require_text,
    validate_identity_set,
)
from .precision_context import PrecisionContextPack
from .relevance import RelevanceDecision


AudienceRoute = Literal["DIRECT", "INSTITUTIONALLY_FORWARDABLE", "INFORMATIVE"]


@dataclass(frozen=True, slots=True)
class AuthorizedAsset:
    asset_id: str
    owner_block: str
    asset_version: str
    format: str
    claim_refs: tuple[str, ...]
    maximum_personalization_level: int
    authority_reference: str
    evidence: EvidenceRef

    def __post_init__(self) -> None:
        for name in ("asset_id", "owner_block", "asset_version", "format"):
            require_text(name, getattr(self, name))
        require_text("authority_reference", self.authority_reference)
        if self.owner_block != "BLOCK2":
            raise PrecisionContractViolation("M06 accepts only Block 2 authorized assets")
        if self.evidence.source_identity != "BLOCK2_ASSET_REGISTRY":
            raise PrecisionContractViolation("asset evidence must come from Block 2 asset registry")
        if not self.claim_refs or any(not item.strip() for item in self.claim_refs):
            raise PrecisionContractViolation("asset claim references are required")
        object.__setattr__(self, "claim_refs", tuple(self.claim_refs))
        if not isinstance(self.maximum_personalization_level, int) or isinstance(self.maximum_personalization_level, bool) or not 0 <= self.maximum_personalization_level <= 5:
            raise PrecisionContractViolation("asset personalization level must be from 0 to 5")


@dataclass(frozen=True, slots=True)
class MessagePolicy:
    policy_id: str
    authority_reference: str
    maximum_personalization_level: int = 5
    allowed_formats: tuple[str, ...] = ("NEWSLETTER", "EMAIL", "BRIEF", "VIDEO", "FLYER")

    def __post_init__(self) -> None:
        require_text("policy_id", self.policy_id)
        require_text("authority_reference", self.authority_reference)
        if not isinstance(self.maximum_personalization_level, int) or isinstance(self.maximum_personalization_level, bool) or not 0 <= self.maximum_personalization_level <= 5:
            raise PrecisionContractViolation("message policy ceiling must be from 0 to 5")
        formats = tuple(item.strip().upper() for item in self.allowed_formats)
        if not formats or any(not item for item in formats):
            raise PrecisionContractViolation("message policy formats are required")
        object.__setattr__(self, "allowed_formats", formats)


@dataclass(frozen=True, slots=True)
class MessageStrategy:
    strategy_id: str
    context_snapshot_id: str
    relevance_decision_id: str
    adaptive_decision_id: str
    audience_route: AudienceRoute
    objective: str
    what: tuple[str, ...]
    why: tuple[str, ...]
    angle: str
    depth: str
    proof: str
    format: str
    cta: str
    friction: str
    maximum_ceiling: int
    applied_level: int
    asset_ids: tuple[str, ...]
    claim_refs: tuple[str, ...]
    uncertainty: tuple[str, ...]
    restrictions: tuple[str, ...]

    @property
    def output_fingerprint(self) -> str:
        return fingerprint(self)


@dataclass(frozen=True, slots=True)
class MessageResult:
    assessment: EngineAssessment
    strategy: MessageStrategy | None


class MessageIntelligenceEngine:
    name = "M06"

    def __init__(self, *, max_assets: int = 100) -> None:
        if max_assets < 1:
            raise PrecisionContractViolation("max_assets must be positive")
        self._max_assets = max_assets

    @staticmethod
    def _functional_mailbox(pack: PrecisionContextPack) -> bool:
        return any(
            attribute.field == "contact_kind" and "FUNCTIONAL_MAILBOX" in attribute.values
            for attribute in pack.person.attributes
        )

    def formulate(
        self, *, pack: PrecisionContextPack, relevance: RelevanceDecision,
        adaptive: AdaptiveLevelDecision, assets: tuple[AuthorizedAsset, ...],
        policy: MessagePolicy,
    ) -> MessageResult:
        if relevance.context_snapshot_id != pack.context_snapshot_id:
            raise PrecisionContractViolation("M06 relevance decision is not bound to context pack")
        if adaptive.relevance_decision_id != relevance.decision_id:
            raise PrecisionContractViolation("M06 adaptive decision is not bound to relevance")
        if relevance.level in {"LOW", "RETURN_UPSTREAM"}:
            reason = "LOW_RELEVANCE_DO_NOT_BUILD" if relevance.level == "LOW" else "RELEVANCE_RETURN_UPSTREAM"
            return MessageResult(
                EngineAssessment(self.name, "RETURN_UPSTREAM", (reason,), (), None), None,
            )
        assets = tuple(assets)
        validate_identity_set(assets, id_attribute="asset_id", limit=self._max_assets)
        unique_assets = tuple({asset.asset_id: asset for asset in assets}.values())
        if not unique_assets:
            return MessageResult(
                EngineAssessment(self.name, "RETURN_UPSTREAM", ("NO_AUTHORIZED_BLOCK2_ASSET",), (), None),
                None,
            )
        usable = tuple(
            asset for asset in unique_assets
            if asset.format.upper() in policy.allowed_formats
            and asset.evidence.current_at(pack.created_at)
        )
        if not usable:
            return MessageResult(
                EngineAssessment(self.name, "RETURN_UPSTREAM", ("NO_POLICY_COMPATIBLE_ASSET",), (), None),
                None,
            )
        maximum_ceiling = min(
            pack.ceiling.effective_level,
            relevance.ceiling_cap,
            policy.maximum_personalization_level,
            *(asset.maximum_personalization_level for asset in usable),
        )
        applied_level = min(maximum_ceiling, 1 + adaptive.level)
        functional = self._functional_mailbox(pack)
        if functional:
            route: AudienceRoute = "INSTITUTIONALLY_FORWARDABLE"
            objective = "provide institutionally useful information without claiming decision authority"
            cta = "LOW_FRICTION_INFORMATION"
            friction = "LOW"
        elif relevance.level == "MEDIUM":
            route = "INFORMATIVE"
            objective = "inform while preserving uncertainty and requesting no strong commitment"
            cta = "LEARN_MORE"
            friction = "LOW"
        else:
            route = "DIRECT"
            objective = "communicate the evidenced relevance chain to the professional role"
            cta = "CONVERSATION" if pack.relationship.state in {"CONVERSATIONAL", "OPPORTUNITY"} else "LEARN_MORE"
            friction = "MEDIUM" if cta == "CONVERSATION" else "LOW"
        stages = {stage.scope: stage for stage in pack.context.stages}
        what = tuple(
            statement
            for scope in ("GLOBAL", "INDUSTRY", "ACCOUNT", "ROLE", "MOMENT")
            for statement in (stages[scope].fact_statements if scope in stages else ())
        )
        if not what:
            return MessageResult(
                EngineAssessment(self.name, "RETURN_UPSTREAM", ("NO_FACTUAL_MESSAGE_BASIS",), (), None),
                None,
            )
        why = tuple(
            statement
            for scope in ("ACCOUNT", "ROLE", "MOMENT")
            for statement in (stages[scope].hypothesis_statements if scope in stages else ())
        )
        angle = pack.decision.framing or "Informative"
        proof = pack.decision.evidence_preference or "Source-linked evidence"
        depth = "DEEP" if applied_level >= 4 else "STANDARD" if applied_level >= 2 else "BRIEF"
        selected_format = usable[0].format.upper()
        claim_refs = tuple(sorted({ref for asset in usable for ref in asset.claim_refs}))
        uncertainty_items = list(pack.context.missing_scopes)
        if pack.decision.primary_driver is None:
            uncertainty_items.append("DECISION_DRIVER_UNKNOWN")
        if functional:
            uncertainty_items.append("FUNCTIONAL_MAILBOX_ROLE_UNKNOWN")
        uncertainty = tuple(sorted(set(uncertainty_items)))
        strategy = MessageStrategy(
            strategy_id=f"{pack.context_snapshot_id}:message:{policy.policy_id}",
            context_snapshot_id=pack.context_snapshot_id,
            relevance_decision_id=relevance.decision_id,
            adaptive_decision_id=adaptive.decision_id,
            audience_route=route,
            objective=objective,
            what=what,
            why=why,
            angle=angle,
            depth=depth,
            proof=proof,
            format=selected_format,
            cta=cta,
            friction=friction,
            maximum_ceiling=maximum_ceiling,
            applied_level=applied_level,
            asset_ids=tuple(asset.asset_id for asset in usable),
            claim_refs=claim_refs,
            uncertainty=uncertainty,
            restrictions=(
                "STRATEGY_NOT_FINAL_COPY",
                "NO_FACT_CREATION",
                "BLOCK2_IDENTITY_PRESERVED",
                "NO_DELIVERY_AUTHORITY",
            ),
        )
        disposition = "PARTIAL" if relevance.level == "MEDIUM" or uncertainty else "ACCEPTED"
        result_reasons: list[str] = []
        if relevance.level == "MEDIUM":
            result_reasons.append("MEDIUM_RELEVANCE_REDUCED_STRATEGY")
        if uncertainty:
            result_reasons.append("UNCERTAINTY_PRESERVED")
        return MessageResult(
            EngineAssessment(
                self.name, disposition, tuple(result_reasons),
                tuple(sorted({
                    evidence_id
                    for stage in pack.context.stages for evidence_id in stage.evidence_ids
                } | {asset.evidence.evidence_id for asset in usable})),
                strategy.output_fingerprint,
            ),
            strategy,
        )
