"""Candidate adapters that invoke the existing Block 2 and 3 runtimes."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256

from sictra_block2_design.design_context import CreateDesignRequest, compile_design_context
from sictra_block2_design.reference_fixture import reference_run_input
from sictra_block2_design.runtime import execute_block2
from sictra_block3_precision.contracts import fingerprint as precision_fingerprint
from sictra_block3_precision.pipeline import PrecisionFoundationPipeline, PrecisionInput

from .execution_receipt import ExecutionReceipt, output_fingerprint, sign_receipt
from .runtime import CONTRACT_VERSION, FederatedContractError, _fingerprint, _iso, _without_signature, _validate_package


def _now(value: datetime | None) -> datetime:
    result = value or datetime.now(timezone.utc)
    if result.tzinfo is None: raise FederatedContractError("ADAPTER_TIME_NOT_AWARE")
    return result.astimezone(timezone.utc)


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


class Block3RuntimeAdapter:
    """Run the real M01-M05 foundation over an explicitly governed input."""
    def __init__(self, *, receipt_key: bytes): self.receipt_key = receipt_key

    def execute(self, *, case_id: str, run_id: str, parent_fingerprint: str,
                request: PrecisionInput, now: int) -> ExecutionReceipt:
        if request.insight_id != case_id:
            raise FederatedContractError("PRECISION_CASE_IDENTITY_MISMATCH")
        result = PrecisionFoundationPipeline().execute(request, now=now)
        disposition = result.disposition
        receipt = ExecutionReceipt(case_id, run_id,
            "B3-" + sha256((parent_fingerprint + precision_fingerprint(request)).encode()).hexdigest()[:24],
            "BLOCK3", CONTRACT_VERSION, parent_fingerprint, precision_fingerprint(request),
            result.output_fingerprint, disposition, ("M01", "M03", "M04", "M05") + (("M02",) if result.decision else ()),
            ("NO_PERSON_ATTRIBUTE_INFERENCE", "NO_DELIVERY", "NO_PUBLICATION"),
            datetime.fromtimestamp(now, timezone.utc).isoformat(),
            {"disposition": disposition, "reasons": list(result.reasons), "decision_present": result.decision is not None})
        return sign_receipt(receipt, self.receipt_key)


class SupervisedFederatedRunner:
    """Run verified producer adapters in order and stop at the human boundary."""
    def __init__(self, *, store, block2: Block2RuntimeAdapter, block3: Block3RuntimeAdapter):
        self.store, self.block2, self.block3 = store, block2, block3

    def execute(self, package: dict, *, precision_request: PrecisionInput,
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
            block3_receipt = self.block3.execute(case_id=package["case_id"], run_id=package["run_id"],
                parent_fingerprint=block2_receipt.fingerprint, request=precision_request,
                now=int(current.timestamp()))
            snapshot = self.store.record_execution(block3_receipt, now=current)
        if snapshot.state == "BLOCK3_GOVERNED":
            snapshot = self.store.stop_for_human_review(snapshot.case_id, now=current)
        return snapshot
