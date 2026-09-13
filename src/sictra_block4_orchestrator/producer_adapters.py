"""Candidate adapters that invoke the existing Block 2 and 3 runtimes."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import hmac
from typing import Callable

from sictra_block2_design.design_context import CreateDesignRequest, compile_design_context
from sictra_block2_design.reference_fixture import reference_run_input
from sictra_block2_design.runtime import execute_block2
from sictra_block1.operator_pipeline import (
    EVIDENCE_MAX_AGE_SECONDS, OperatorPipelineViolation, load_operator_pipeline,
)
from sictra_block3_precision.pipeline import PrecisionFoundationPipeline, PrecisionInput
from sictra_block3_precision.adaptive import AdaptiveEvidence, AdaptivePolicy, HardConstraints
from sictra_block3_precision.adaptive_pipeline import AdaptivePlanningInput, PrecisionAdaptivePipeline
from sictra_block3_precision.delivery import ChannelHistory, ChannelPolicy
from sictra_block3_precision.message import AuthorizedAsset, MessagePolicy
from sictra_block3_precision.precision_context import CeilingPolicy, PersonaStatePolicy
from sictra_block3_precision.relevance import RelevancePolicy

from .execution_receipt import ExecutionReceipt, output_fingerprint, sign_receipt
from .runtime import (CONTRACT_VERSION, FederatedContractError, _canonical, _fingerprint,
                      _iso, _without_signature, _validate_package)


def _now(value: datetime | None) -> datetime:
    result = value or datetime.now(timezone.utc)
    if result.tzinfo is None: raise FederatedContractError("ADAPTER_TIME_NOT_AWARE")
    return result.astimezone(timezone.utc)


class Block1DossierPackageAdapter:
    """Export one currently attested durable dossier without adding interpretation."""
    def __init__(self, *, pipeline, package_key: bytes):
        if not isinstance(package_key, bytes) or len(package_key) < 32:
            raise FederatedContractError("PACKAGE_KEY_INVALID")
        self.pipeline, self.package_key = pipeline, package_key

    def export(self, dossier_id: str, *, now: datetime | None = None) -> dict:
        if not isinstance(dossier_id, str) or not dossier_id.strip():
            raise FederatedContractError("BLOCK1_DOSSIER_ID_INVALID")
        current = _now(now)
        epoch = int(current.timestamp())
        try:
            pipeline = load_operator_pipeline(self.pipeline, clock=lambda: epoch)
        except OperatorPipelineViolation as error:
            raise FederatedContractError("BLOCK1_PIPELINE_INTEGRITY_ERROR") from error
        dossiers = [item for item in pipeline.dossiers.list_dossiers()
                    if item["dossier_id"] == dossier_id]
        if len(dossiers) != 1:
            raise FederatedContractError("BLOCK1_DOSSIER_NOT_FOUND")
        dossier = dossiers[0]
        if (not dossier["facts"] or dossier["interpretations"] or dossier["hypotheses"]
                or dossier["review_state"] != "REQUIRES_HUMAN_INTERPRETATION"
                or dossier["publication_state"] != "BLOCKED"):
            raise FederatedContractError("BLOCK1_DOSSIER_BOUNDARY_INVALID")
        source = dossier["source"]
        receipts = [item for item in pipeline.evidence_store.list_receipts(now=epoch)
                    if item["status"] == "CURRENT" and item["source_id"] == source["source_id"]
                    and item["observed_at"] == source["observed_at"]]
        evidence = [item for item in pipeline.evidence_store.runtime_records(now=epoch)
                    if item["source_id"] == source["source_id"]
                    and item["observed_at"] == source["observed_at"]
                    and item.get("content_sha256") == source["content_sha256"]
                    and item.get("source_approval_fingerprint") == source["approval_fingerprint"]
                    and item.get("source_binding_fingerprint") == source["binding_fingerprint"]]
        binding = pipeline.source_control.active_record(source["source_id"], now=epoch)
        if len(receipts) != 1 or len(evidence) != 1 or binding is None:
            raise FederatedContractError("BLOCK1_DOSSIER_EVIDENCE_NOT_CURRENT")
        expires = min(source["observed_at"] + EVIDENCE_MAX_AGE_SECONDS + 1,
                      binding["binding"]["expires_at"] + 1)
        if epoch >= expires:
            raise FederatedContractError("BLOCK1_DOSSIER_EVIDENCE_NOT_CURRENT")
        identity = sha256((dossier_id + "|" + receipts[0]["evidence_id"]).encode()).hexdigest()
        package = {
            "case_id": "CASE-" + identity[:24], "run_id": "RUN-" + identity[24:48],
            "message_id": "MSG-" + identity[8:32], "evidence_id": receipts[0]["evidence_id"],
            "dossier_id": dossier_id, "producer": "BLOCK1", "contract_version": CONTRACT_VERSION,
            "source_hash": source["content_sha256"], "provenance_root": evidence[0]["root_provenance"],
            "observed_at": datetime.fromtimestamp(source["observed_at"], timezone.utc).isoformat(),
            "expires_at": datetime.fromtimestamp(expires, timezone.utc).isoformat(),
            "currentness": "CURRENT", "certainty": dossier["certainty"],
            "uncertainty": list(dossier["uncertainties"]), "disposition": "REVIEW_REQUIRED",
            "lineage": ["BLOCK1"],
            "payload": {"summary": " ".join(fact["statement"] for fact in dossier["facts"][:3]),
                        "limitations": list(dossier["limitations"]) + ["NO_INTERPRETATION_ADDED"]},
        }
        package["signature"] = hmac.new(self.package_key, _canonical(package), "sha256").hexdigest()
        return package


class Block2RuntimeAdapter:
    """Compile a package-bound design context and run real E01-E08 code."""
    def __init__(self, *, package_key: bytes, receipt_key: bytes):
        self.package_key, self.receipt_key = package_key, receipt_key

    def execute(self, package: dict, *, now: datetime | None = None) -> ExecutionReceipt:
        current = _now(now)
        _validate_package(package, self.package_key, current)
        if (package["currentness"] != "CURRENT" or _iso(package["expires_at"]) <= current
                or package["certainty"] in {"CONTRADICTED", "INSUFFICIENT EVIDENCE"}):
            raise FederatedContractError("BLOCK1_PACKAGE_NOT_EXECUTABLE")
        parent = _fingerprint(_without_signature(package))
        request = CreateDesignRequest(
            "B2-CREATE-" + parent[:20], CONTRACT_VERSION, package["case_id"], package["message_id"],
            package["dossier_id"], package["run_id"], "BLOCK1", "BLOCK2-E01",
            "BLOCK4-LOCAL-ORCHESTRATOR", current, package["dossier_id"], package["provenance_root"],
            (package["dossier_id"],), (package["evidence_id"],), package["certainty"], (),
            "FEDERATED-CONTRACT-" + CONTRACT_VERSION, package["currentness"],
            (package["provenance_root"], package["source_hash"]), "LOGISTICS_DECISION_MAKER",
            "review a bounded evidence-backed change", "prepare a traceable local design candidate",
            ("WEB",), "claim identity and limitations remain visible", ("WCAG-AA",),
            ("NO_PUBLICATION", "NO_DECEPTION"), ("LOCAL_RENDER_ONLY",), False, None, None,
            tuple(package["uncertainty"]), tuple(package["payload"]["limitations"]),
        )
        assessment = compile_design_context(request)
        if assessment.envelope is None:
            disposition, components, result_payload = "RETURN_UPSTREAM", ("B2-CREATE",), {
                "completed": False, "stopped_at": "CREATE", "reasons": list(assessment.reasons),
                "publication_state": assessment.publication_state, "acceptance_state": assessment.acceptance_state,
            }
            input_fp, output_fp = output_fingerprint(request), output_fingerprint(assessment)
        else:
            runtime_input = reference_run_input(current, assessment.envelope)
            result = execute_block2(runtime_input, now=current)
            disposition = "COMPLETED" if result.completed else "RETURN_UPSTREAM"
            components = result.executed_engines or tuple(stage.engine for stage in result.stages)
            result_payload = {"completed": result.completed, "stopped_at": result.stopped_at,
                              "reasons": sorted({reason for stage in result.stages for reason in stage.reasons}),
                              "publication_state": result.publication_state, "acceptance_state": result.acceptance_state}
            input_fp, output_fp = output_fingerprint(runtime_input), output_fingerprint(result)
        receipt = ExecutionReceipt(package["case_id"], package["run_id"], "B2-" + sha256((parent+input_fp).encode()).hexdigest()[:24],
            "BLOCK2", CONTRACT_VERSION, parent, input_fp, output_fp, disposition, tuple(components),
            ("REFERENCE_MECHANISM_NOT_CONTENT_ACCEPTANCE", "NO_PUBLICATION", "NO_DELIVERY"),
            current.isoformat(), result_payload)
        return sign_receipt(receipt, self.receipt_key)


@dataclass(frozen=True, slots=True)
class AdaptivePlanningPolicyBundle:
    policy_version: str
    persona_policy: PersonaStatePolicy
    ceiling_policy: CeilingPolicy
    relevance_policy: RelevancePolicy
    adaptive_policy: AdaptivePolicy
    adaptive_evidence: AdaptiveEvidence
    hard_constraints: HardConstraints
    message_policy: MessagePolicy
    assets: tuple[AuthorizedAsset, ...]
    channel_policy: ChannelPolicy
    channel_history: ChannelHistory
    requested_channel: str


class Block3RuntimeAdapter:
    """Run M01-M05 and, when supplied, the no-effect M06-M07 planning path."""
    def __init__(self, *, receipt_key: bytes): self.receipt_key = receipt_key

    def execute(self, *, case_id: str, run_id: str, parent_fingerprint: str,
                request: PrecisionInput, now: int,
                planning: AdaptivePlanningPolicyBundle | None = None) -> ExecutionReceipt:
        if request.insight_id != case_id:
            raise FederatedContractError("PRECISION_CASE_IDENTITY_MISMATCH")
        result = PrecisionFoundationPipeline().execute(request, now=now)
        disposition, final_result = result.disposition, result
        components = ("M01", "M03", "M04", "M05") + (("M02",) if result.decision else ())
        restrictions = ["NO_PERSON_ATTRIBUTE_INFERENCE", "NO_DELIVERY", "NO_PUBLICATION"]
        if planning is not None and result.decision is not None:
            if (not planning.assets or any(asset.owner_block != "BLOCK2"
                    or parent_fingerprint not in {asset.evidence.root_provenance, *asset.evidence.provenance_refs}
                    for asset in planning.assets)):
                raise FederatedContractError("BLOCK2_ASSET_RECEIPT_BINDING_MISSING")
            adaptive_request = AdaptivePlanningInput(result, request.person_id, request.insight_id,
                request.target_id, planning.policy_version, planning.persona_policy,
                planning.ceiling_policy, planning.relevance_policy, planning.adaptive_policy,
                planning.adaptive_evidence, planning.hard_constraints, planning.message_policy,
                planning.assets, planning.channel_policy, planning.channel_history,
                planning.requested_channel)
            final_result = PrecisionAdaptivePipeline().plan(adaptive_request, now=now)
            disposition = final_result.disposition
            if final_result.message is not None:
                components += ("M06",)
            if final_result.delivery is not None:
                components += ("M07",)
            restrictions.extend(("PROPOSAL_NOT_EXECUTION", "NO_CONTACT"))
        input_fp = output_fingerprint({"foundation": request, "planning": planning})
        receipt = ExecutionReceipt(case_id, run_id,
            "B3-" + sha256((parent_fingerprint + input_fp).encode()).hexdigest()[:24],
            "BLOCK3", CONTRACT_VERSION, parent_fingerprint, input_fp,
            final_result.output_fingerprint, disposition, components, tuple(restrictions),
            datetime.fromtimestamp(now, timezone.utc).isoformat(),
            {"disposition": disposition, "reasons": list(final_result.reasons), "decision_present": result.decision is not None})
        return sign_receipt(receipt, self.receipt_key)


class SupervisedFederatedRunner:
    """Run verified producer adapters in order and stop at the human boundary."""
    def __init__(self, *, store, block2: Block2RuntimeAdapter, block3: Block3RuntimeAdapter):
        self.store, self.block2, self.block3 = store, block2, block3

    def execute(self, package: dict, *, precision_request: PrecisionInput,
                adaptive_planning: AdaptivePlanningPolicyBundle | Callable[[str], AdaptivePlanningPolicyBundle],
                now: datetime | None = None):
        current = _now(now)
        snapshot = self.store.ingest(package, now=current)
        if snapshot.state in {"RETURN_UPSTREAM", "REJECTED", "ABSTAINED", "HUMAN_REVIEW_REQUIRED"}:
            return snapshot
        receipts = self.store.execution_receipts(snapshot.case_id)
        block2_receipt = next((receipt for receipt in reversed(receipts) if receipt.producer == "BLOCK2"), None)
        if snapshot.state == "BLOCK1_ATTESTED":
            block2_receipt = self.block2.execute(package, now=current)
            snapshot = self.store.record_execution(block2_receipt, now=current)
        if snapshot.state != "BLOCK2_CANDIDATE":
            return snapshot
        if block2_receipt is None:
            raise FederatedContractError("BLOCK2_EXECUTION_RECEIPT_MISSING")
        block3_receipt = next((receipt for receipt in reversed(receipts) if receipt.producer == "BLOCK3"), None)
        if block3_receipt is None:
            planning = adaptive_planning(block2_receipt.fingerprint) if callable(adaptive_planning) else adaptive_planning
            if not isinstance(planning, AdaptivePlanningPolicyBundle):
                raise FederatedContractError("ADAPTIVE_PLANNING_INVALID")
            block3_receipt = self.block3.execute(case_id=package["case_id"], run_id=package["run_id"],
                parent_fingerprint=block2_receipt.fingerprint, request=precision_request,
                planning=planning, now=int(current.timestamp()))
            snapshot = self.store.record_execution(block3_receipt, now=current)
        if snapshot.state == "BLOCK3_GOVERNED":
            snapshot = self.store.stop_for_human_review(snapshot.case_id, now=current)
        return snapshot
