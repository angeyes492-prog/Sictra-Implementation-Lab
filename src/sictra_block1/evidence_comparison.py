"""Literal measurement comparison between separately rooted Block 1 dossiers."""

from __future__ import annotations

from math import isfinite
import re

from .common import ContractViolation


class EvidenceComparisonViolation(ContractViolation):
    pass


def _observations(dossier):
    if (not isinstance(dossier, dict) or not isinstance(dossier.get("dossier_id"), str)
            or not dossier["dossier_id"].strip()
            or not isinstance(dossier.get("source"), dict)
            or not isinstance(dossier.get("facts"), list) or not dossier["facts"]
            or dossier.get("publication_state") != "BLOCKED"
            or dossier.get("interpretations") != [] or dossier.get("hypotheses") != []):
        raise EvidenceComparisonViolation("DOSSIER_BOUNDARY_INVALID")
    source = dossier["source"]
    if (not isinstance(source.get("content_sha256"), str)
            or re.fullmatch(r"[0-9a-f]{64}", source["content_sha256"]) is None):
        raise EvidenceComparisonViolation("SOURCE_HASH_INVALID")
    result = {}
    for fact in dossier["facts"]:
        if not isinstance(fact, dict) or not isinstance(fact.get("observed_change"), dict):
            raise EvidenceComparisonViolation("FACT_INVALID")
        change = fact["observed_change"]
        if "after_value_thousand_tonnes" in change:
            if (source.get("source_id") != "eurostat"
                    or not isinstance(change.get("geo_code"), str)
                    or not change["geo_code"].strip() or type(change.get("time_period")) is not int):
                raise EvidenceComparisonViolation("MEASUREMENT_SCOPE_INVALID")
            key = ("MARITIME_FREIGHT", "THOUSAND_TONNES", change["geo_code"], str(change["time_period"]))
            value = change["after_value_thousand_tonnes"]
        elif "after_value_usd_million" in change:
            if (source.get("source_id") != "HN_ADUANAS_BULLETINS"
                    or not isinstance(change.get("customs_point"), str)
                    or not change["customs_point"].strip()
                    or not isinstance(change.get("after_period"), str)
                    or not change["after_period"].strip()):
                raise EvidenceComparisonViolation("MEASUREMENT_SCOPE_INVALID")
            key = ("CUSTOMS_CIF_IMPORT", "USD_MILLION", change["customs_point"], change["after_period"])
            value = change["after_value_usd_million"]
        else:
            raise EvidenceComparisonViolation("MEASUREMENT_UNSUPPORTED")
        if (type(value) not in (int, float) or not isfinite(value)
                or not isinstance(fact.get("fact_id"), str) or not fact["fact_id"].strip()
                or key in result):
            raise EvidenceComparisonViolation("MEASUREMENT_INVALID_OR_DUPLICATED")
        result[key] = (fact["fact_id"], value)
    return result


def compare_dossier_measurements(primary, candidate):
    """Compare exact typed observations, without declaring corroboration."""
    left, right = _observations(primary), _observations(candidate)
    first, second = primary["source"], candidate["source"]
    left_root = first.get("root_source_identity", first.get("source_id"))
    right_root = second.get("root_source_identity", second.get("source_id"))
    if (not isinstance(left_root, str) or not left_root.strip()
            or left_root != left_root.strip()
            or not isinstance(right_root, str) or not right_root.strip()
            or right_root != right_root.strip()
            or left_root == right_root or primary["dossier_id"] == candidate["dossier_id"]):
        raise EvidenceComparisonViolation("INDEPENDENT_ROOT_REQUIRED")
    matched = []
    for key in sorted(left.keys() & right.keys()):
        left_id, left_value = left[key]
        right_id, right_value = right[key]
        matched.append({"metric": key[0], "unit": key[1], "geography": key[2],
                        "period": key[3], "primary_fact_id": left_id,
                        "candidate_fact_id": right_id, "primary_value": left_value,
                        "candidate_value": right_value,
                        "comparison": "EXACT_AFTER_VALUE" if left_value == right_value else "DIFFERENT_AFTER_VALUE"})
    if not matched:
        status = "NO_SHARED_MEASUREMENT"
    elif any(item["comparison"] == "DIFFERENT_AFTER_VALUE" for item in matched):
        status = "VALUE_DIFFERENCE_REVIEW_REQUIRED"
    elif len(matched) < len(left) or len(matched) < len(right):
        status = "PARTIAL_COVERAGE_REVIEW_REQUIRED"
    else:
        status = "EXACT_VALUE_AGREEMENT_REVIEW_REQUIRED"
    return {"version": "0.1.0", "primary_dossier_id": primary["dossier_id"],
            "candidate_dossier_id": candidate["dossier_id"],
            "source_roots": [left_root, right_root], "status": status,
            "matched": matched,
            "unmatched_primary_fact_ids": [left[key][0] for key in sorted(left.keys() - right.keys())],
            "unmatched_candidate_fact_ids": [right[key][0] for key in sorted(right.keys() - left.keys())],
            "resolution": "NOT_RESOLVED", "acceptance": "NOT_ACCEPTED",
            "publication": "BLOCKED"}
