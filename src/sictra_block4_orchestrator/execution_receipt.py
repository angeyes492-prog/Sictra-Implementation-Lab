"""Signed, typed receipts proving a producer runtime was actually invoked."""
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass, replace
from datetime import datetime
from hashlib import sha256
import hmac
import json
from typing import Any

from .runtime import CONTRACT_VERSION, FederatedContractError

_PRODUCERS = frozenset({"BLOCK2", "BLOCK3"})
_DISPOSITIONS = frozenset({"COMPLETED", "ACCEPTED", "PARTIAL", "SEND_CANDIDATE", "WAIT",
                           "RETURN_UPSTREAM", "CONTRADICTED", "DO_NOT_SEND"})


def _plain(value: Any) -> Any:
    if is_dataclass(value): return _plain(asdict(value))
    if isinstance(value, datetime): return value.isoformat()
    if isinstance(value, bytes): return {"bytes_sha256": sha256(value).hexdigest()}
    if isinstance(value, (set, frozenset)): return sorted(_plain(item) for item in value)
    if isinstance(value, dict): return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)): return [_plain(item) for item in value]
    return value


def _canonical(value: Any) -> bytes:
    return json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


@dataclass(frozen=True, slots=True)
class ExecutionReceipt:
    case_id: str
    run_id: str
    execution_id: str
    producer: str
    contract_version: str
    parent_fingerprint: str
    input_fingerprint: str
    output_fingerprint: str
    disposition: str
    executed_components: tuple[str, ...]
    restrictions: tuple[str, ...]
    created_at: str
    payload: dict[str, Any]
    signature: str = ""

    @property
    def signed_material(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if key != "signature"}

    @property
    def fingerprint(self) -> str:
        return sha256(_canonical(self.signed_material)).hexdigest()


def sign_receipt(receipt: ExecutionReceipt, key: bytes) -> ExecutionReceipt:
    if not isinstance(key, bytes) or len(key) < 32: raise FederatedContractError("PRODUCER_KEY_INVALID")
    if receipt.signature: raise FederatedContractError("RECEIPT_ALREADY_SIGNED")
    return replace(receipt, signature=hmac.new(key, _canonical(receipt.signed_material), "sha256").hexdigest())


def verify_receipt(receipt: ExecutionReceipt, key: bytes) -> None:
    if not isinstance(receipt, ExecutionReceipt): raise FederatedContractError("EXECUTION_RECEIPT_TYPE_INVALID")
    strings = (receipt.case_id, receipt.run_id, receipt.execution_id, receipt.parent_fingerprint,
               receipt.input_fingerprint, receipt.output_fingerprint, receipt.created_at)
    if any(not isinstance(value, str) or not value.strip() for value in strings):
        raise FederatedContractError("EXECUTION_RECEIPT_IDENTITY_INVALID")
    if receipt.producer not in _PRODUCERS or receipt.contract_version != CONTRACT_VERSION:
        raise FederatedContractError("EXECUTION_RECEIPT_CONTRACT_INVALID")
    if receipt.disposition not in _DISPOSITIONS:
        raise FederatedContractError("EXECUTION_RECEIPT_DISPOSITION_INVALID")
    hashes = (receipt.parent_fingerprint, receipt.input_fingerprint, receipt.output_fingerprint)
    if any(len(value) != 64 or any(character not in "0123456789abcdef" for character in value) for value in hashes):
        raise FederatedContractError("EXECUTION_RECEIPT_FINGERPRINT_INVALID")
    if (not receipt.executed_components or len(set(receipt.executed_components)) != len(receipt.executed_components)
            or any(not isinstance(item, str) or not item for item in receipt.executed_components)
            or not receipt.restrictions or len(set(receipt.restrictions)) != len(receipt.restrictions)
            or any(not isinstance(item, str) or not item for item in receipt.restrictions)):
        raise FederatedContractError("EXECUTION_RECEIPT_CONTENT_INVALID")
    if not isinstance(receipt.payload, dict): raise FederatedContractError("EXECUTION_RECEIPT_PAYLOAD_INVALID")
    if receipt.producer == "BLOCK2":
        if set(receipt.payload) != {"completed", "stopped_at", "reasons", "publication_state", "acceptance_state"}:
            raise FederatedContractError("EXECUTION_RECEIPT_PAYLOAD_INVALID")
        if (type(receipt.payload["completed"]) is not bool
                or not isinstance(receipt.payload["reasons"], list)
                or not all(isinstance(reason, str) and reason for reason in receipt.payload["reasons"])
                or receipt.payload["publication_state"] not in {"NOT_PUBLISHED", "BLOCKED"}
                or receipt.payload["acceptance_state"] != "NOT_ACCEPTED"):
            raise FederatedContractError("EXECUTION_RECEIPT_PAYLOAD_INVALID")
    elif (set(receipt.payload) != {"disposition", "reasons", "decision_present"}
          or receipt.payload["disposition"] != receipt.disposition
          or not isinstance(receipt.payload["reasons"], list)
          or not all(isinstance(reason, str) and reason for reason in receipt.payload["reasons"])
          or type(receipt.payload["decision_present"]) is not bool):
        raise FederatedContractError("EXECUTION_RECEIPT_PAYLOAD_INVALID")
    if not isinstance(key, bytes) or len(key) < 32: raise FederatedContractError("PRODUCER_KEY_INVALID")
    expected = hmac.new(key, _canonical(receipt.signed_material), "sha256").hexdigest()
    if not hmac.compare_digest(expected, receipt.signature): raise FederatedContractError("EXECUTION_RECEIPT_SIGNATURE_INVALID")


def output_fingerprint(value: Any) -> str:
    return sha256(_canonical(value)).hexdigest()
