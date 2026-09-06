"""Admit only one current attested Eurostat record into the manual watchlist."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .attested_evidence_store import AttestedEvidenceStore
from .common import ContractViolation
from .manual_watchlist_cycle import ManualWatchlistCycle


class AttestedWatchlistBridgeViolation(ContractViolation):
    """A watchlist advance is not uniquely bound to current attested evidence."""


class AttestedWatchlistBridge:
    """Bounded admission adapter; delta interpretation remains outside this class."""

    def __init__(self, evidence_store: AttestedEvidenceStore, watchlist: ManualWatchlistCycle) -> None:
        if not isinstance(evidence_store, AttestedEvidenceStore) or not isinstance(watchlist, ManualWatchlistCycle):
            raise AttestedWatchlistBridgeViolation("bridge requires attested evidence store and manual watchlist")
        self._evidence_store = evidence_store
        self._watchlist = watchlist

    def ingest(self, source_id: object, *, now: object) -> dict[str, Any]:
        if not isinstance(source_id, str) or not source_id.strip():
            raise AttestedWatchlistBridgeViolation("source_id must be non-empty text")
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise AttestedWatchlistBridgeViolation("watchlist bridge time is invalid")
        records = [record for record in self._evidence_store.runtime_records(now=now)
                   if record["source_id"] == source_id.strip()]
        if len(records) != 1:
            raise AttestedWatchlistBridgeViolation("watchlist requires exactly one current attested source record")
        evidence = records[0]
        bundle = {key: evidence[key] for key in (
            "source_id", "source_url", "content", "observed_at", "claim_key",
            "polarity", "correlation_id",
        )}
        receipt = self._watchlist.ingest(bundle)
        return {
            "scope": "BLOCK1_LOCAL_ATTESTED_WATCHLIST_BRIDGE",
            "source_id": evidence["source_id"],
            "observed_at": evidence["observed_at"],
            "content_sha256": evidence["content_sha256"],
            "source_approval_fingerprint": evidence["source_approval_fingerprint"],
            "source_binding_fingerprint": evidence["source_binding_fingerprint"],
            "watchlist_receipt": deepcopy(receipt),
            "next_state": "REQUIRES_REVIEW" if receipt["change_count"] else "AWAIT_NEWER_SOURCE",
            "evidence_state": "ATTESTED_INPUT_DELTA_NOT_EVIDENCE",
        }
