"""Read-only candidate comparison of checkpoint-verified statistical releases."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json

from .common import ContractViolation
from .research_acquisition import canonical
from .research_admission import _time
from .statistical_retention import StatisticalEvidenceStore


class StatisticalWatchlistViolation(ContractViolation):
    pass


def _require(condition, reason):
    if not condition:
        raise StatisticalWatchlistViolation(reason)


def _body(record):
    return json.loads(record["evidence"]["content"])


def _release(record):
    # The retention verifier already rejects unordered/unrepresentable releases
    # as current heads. This helper is used only after a current head exists.
    return datetime.fromisoformat(_body(record)["provenance"]["publisher_updated_raw"].replace(
        "Z", "+00:00")).astimezone(timezone.utc)


def _copy_order(record):
    return record["evidence"]["observed_at"], record["admitted_at"], record["evidence_id"]


def _ref(record, state):
    source, body = record["evidence"], _body(record)
    return {**deepcopy(body["provenance"]), "evidence_id": record["evidence_id"],
        "record_hash": record["record_hash"], "admitted_at": record["admitted_at"],
        "source_url": source["source_url"], "content_sha256": source["content_sha256"],
        "source_binding_fingerprint": source["source_binding_fingerprint"],
        "expires_at": body["expires_at"], "state": state}


def _compare(before, after):
    _require(before["source_scope"] == after["source_scope"] and before["filters"] == after["filters"]
        and before["grain"] == after["grain"]
        and before["provenance"]["dataset_code"] == after["provenance"]["dataset_code"],
        "WATCHLIST_SCOPE_MISMATCH")
    previous = {(r["geo_code"], r["time_period"]): r for r in before["observations"]}
    current = {(r["geo_code"], r["time_period"]): r for r in after["observations"]}
    _require(previous.keys() == current.keys() and len(previous) == len(before["observations"])
        and len(current) == len(after["observations"]), "WATCHLIST_GRAIN_MISMATCH")
    changes = []
    for coordinate, row in sorted(current.items()):
        old = previous[coordinate]
        missing_before, missing_after = old["missing"], row["missing"]
        bv, av = old["value_thousand_tonnes"], row["value_thousand_tonnes"]
        flags_changed = old["status_flag"] != row["status_flag"]
        if missing_before and not missing_after:
            kind = "OBSERVATION_AVAILABLE"
        elif not missing_before and missing_after:
            kind = "OBSERVATION_UNAVAILABLE"
        elif missing_before and missing_after:
            kind = "MISSING_FLAG_CHANGED" if flags_changed else None
        elif bv != av:
            kind = "VALUE_CHANGED"
        else:
            kind = "FLAG_CHANGED" if flags_changed else None
        if kind:
            changes.append({"geo_code": coordinate[0], "time_period": coordinate[1], "unit": "THS_T",
                "change_type": kind, "before_value": bv, "after_value": av,
                "absolute_delta": None if missing_before or missing_after else av - bv,
                "before_missing": missing_before, "after_missing": missing_after,
                "before_status_flag": old["status_flag"], "after_status_flag": row["status_flag"]})
    return changes


class StatisticalWatchlist:
    """Derived view, not an attested source, accepted dossier or runtime port."""
    def __init__(self, store):
        _require(isinstance(store, StatisticalEvidenceStore), "WATCHLIST_TRUSTED_STORE_REQUIRED")
        self._store = store

    def _compose(self, records, receipts):
        reasons = sorted({r["verification_reason"] for r in receipts})
        selected = [record for record, receipt in zip(records, receipts) if receipt["status"] == "CURRENT"]
        _require(len(selected) <= 1, "WATCHLIST_CURRENT_HEAD_AMBIGUOUS")
        current = selected[0] if selected else None
        report = {"schema_version": "0.1.0", "scope": "BLOCK1_STATISTICAL_WATCHLIST_PROJECTION",
            "input_fingerprint": sha256(canonical([records, receipts])).hexdigest(),
            "custody_checkpoints": self._store.checkpoint(),
            "source_state": "CURRENT" if current else "NOT_CURRENT", "reasons": reasons,
            "evidence_refs": [], "facts": [], "interpretations": [], "hypotheses": [],
            "uncertainty": [], "contradictions": [], "limitations": [
                "One Eurostat root is not independent corroboration",
                "A technical change does not establish its cause or strategic significance",
                "Historical baseline is context only, never current authority or an engine input",
                "Candidate projection is not an accepted or persisted Intelligence dossier"],
            "affected_scope": {}, "executive_questions": [
                "What source-specific evidence explains any reported revision?"],
            "next_data_needs": ["SOURCE_SPECIFIC_REVISION_EXPLANATION", "INDEPENDENT_COMPARABLE_EVIDENCE"],
            "independent_corroboration": "INSUFFICIENT EVIDENCE", "resolution": "NOT_RESOLVED",
            "editorial_state": "RESEARCH_NEEDED", "runtime_effect": "NONE", "publication": "BLOCKED",
            "acceptance": "NOT_ACCEPTED", "projection_persistence": "NOT_PERSISTED", "expires_at": None}
        review = any(r in {"LATEST_RELEASE_AMBIGUOUS", "PUBLISHER_TIME_UNORDERED"} for r in reasons)
        comparison = {"status": "REVIEW_REQUIRED" if review else "INSUFFICIENT_EVIDENCE",
            "reason": "NO_CURRENT_RELEASE", "changes": [], "before": None, "current": None}
        report["comparison"] = comparison
        if not current:
            report["uncertainty"].append("NO_CURRENT_ADMISSIBLE_MEASUREMENTS")
            report["next_data_needs"].append("CURRENT_ADMITTED_RELEASE")
            if review:
                report["contradictions"].append("PUBLISHER_RELEASE_IDENTITY_REQUIRES_REVIEW")
        else:
            body, reference = _body(current), _ref(current, "CURRENT")
            report["evidence_refs"].append(reference)
            comparison["current"] = reference["evidence_id"]
            report["affected_scope"] = {"source_scope": body["source_scope"],
                "dataset_code": body["provenance"]["dataset_code"], "filters": deepcopy(body["filters"]),
                "grain": deepcopy(body["grain"]),
                "coordinates": [[r["geo_code"], r["time_period"]] for r in body["observations"]]}
            report["expires_at"] = min(body["expires_at"], current["evidence"]["observed_at"]
                + self._store._history._max_age + 1)
            for row in body["observations"]:
                if row["missing"]:
                    report["uncertainty"].append({"geo_code": row["geo_code"], "time_period": row["time_period"],
                        "reason": "MISSING_MEASUREMENT", "status_flag": row["status_flag"]})
                    continue
                fact = {"geo_code": row["geo_code"], "time_period": row["time_period"], "unit": "THS_T",
                    "value": row["value_thousand_tonnes"], "status_flag": row["status_flag"],
                    "evidence_id": reference["evidence_id"], "certainty": "UNCONFIRMED", "confidence": "C"}
                fact["fact_id"] = sha256(canonical(fact)).hexdigest()
                report["facts"].append(fact)
            prior = [r for r in records if _release(r) < _release(current)]
            if prior:
                latest = max(_release(r) for r in prior)
                candidates = [r for r in prior if _release(r) == latest]
                if len({_body(r)["provenance"]["source_file_sha256"] for r in candidates}) != 1:
                    comparison.update(status="REVIEW_REQUIRED", reason="BASELINE_RELEASE_AMBIGUOUS")
                    report["contradictions"].append("BASELINE_RELEASE_IDENTITY_REQUIRES_REVIEW")
                else:
                    previous = max(candidates, key=_copy_order)
                    report["evidence_refs"].append(_ref(previous, "HISTORICAL_CONTEXT_ONLY"))
                    comparison["before"] = previous["evidence_id"]
                    comparison["changes"] = _compare(_body(previous), body)
                    comparison.update(status="CHANGE_DETECTED" if comparison["changes"] else "NO_CHANGE",
                        reason="SAME_PERIOD_RELEASE_COMPARISON")
            elif sum(_body(r)["provenance"]["source_file_sha256"] == body["provenance"]["source_file_sha256"]
                     for r in records) > 1:
                comparison.update(status="NO_CHANGE", reason="SAME_RELEASE_RECOLLECTED")
            else:
                comparison["reason"] = "SECOND_RELEASE_REQUIRED"
                report["next_data_needs"].append("SECOND_RELEASE_OF_SAME_OBSERVATIONS")
        report["projection_id"] = sha256(canonical(report)).hexdigest()
        return report

    def read(self):
        start = _time(self._store._clock)
        snapshot = self._store._snapshot()
        checkpoint = self._store.checkpoint()
        report = self._compose(*snapshot)
        _require(snapshot == self._store._snapshot() and checkpoint == self._store.checkpoint(),
                 "WATCHLIST_INPUT_CHANGED")
        end = _time(self._store._clock)
        _require(end >= start, "WATCHLIST_CLOCK_REGRESSED")
        _require(report["expires_at"] is None or end < report["expires_at"], "WATCHLIST_READ_EXPIRED")
        return deepcopy(report)

    def verify_projection(self, report):
        _require(type(report) is dict, "WATCHLIST_PROJECTION_MISMATCH")
        try:
            submitted = canonical(report)
        except (TypeError, ValueError, OverflowError, RecursionError) as error:
            raise StatisticalWatchlistViolation("WATCHLIST_PROJECTION_INVALID") from error
        current = self.read()
        # Python dict equality accepts int/float/bool substitutions and custom
        # equality methods. Exact canonical JSON is the candidate contract.
        _require(submitted == canonical(current), "WATCHLIST_PROJECTION_MISMATCH")
        return {"status": "VERIFIED_LOCAL_EQUIVALENCE", "projection_id": current["projection_id"],
                "runtime_effect": "NONE", "acceptance": "NOT_ACCEPTED"}
