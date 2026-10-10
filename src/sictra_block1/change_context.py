"""Classify literal version semantics without explaining the cause of a change."""
from hashlib import sha256
import json
from math import isfinite
import re

from .common import ContractViolation


class ChangeContextViolation(ContractViolation):
    pass


def _reject(condition, reason):
    if condition:
        raise ChangeContextViolation(reason)


def _finite_number(value):
    try:
        return type(value) in (int, float) and isfinite(value)
    except OverflowError:
        return False


def _number(value):
    return _finite_number(value) and value >= 0


def project_change_context(dossier):
    """Pure candidate projection; the caller owns integrity/currentness checks."""
    _reject(not isinstance(dossier, dict), "DOSSIER_INVALID")
    source = dossier.get("source")
    _reject(not isinstance(source, dict), "SOURCE_INVALID")
    eurostat = source.get("source_id") == "eurostat"
    customs = source.get("source_id") == "HN_ADUANAS_BULLETINS"
    expected = (("0.1.0", "BLOCK1_LOCAL_INTELLIGENCE_DOSSIER", "eurostat:") if eurostat else
                ("HN_CUSTOMS_DOSSIER_V1", "BLOCK1_LOCAL_HN_CUSTOMS_PERIOD_PIPELINE", "hn-customs:"))
    _reject(not (eurostat or customs) or (dossier.get("schema_version"), dossier.get("scope")) != expected[:2],
            "DOSSIER_SCHEMA_UNSUPPORTED")
    for field in ("content_sha256", "delta_sha256"):
        _reject(not isinstance(source.get(field), str) or
                re.fullmatch(r"[0-9a-f]{64}", source[field]) is None, "SOURCE_LINEAGE_INVALID")
    _reject(dossier.get("dossier_id") != expected[2] + source["delta_sha256"], "DOSSIER_ID_INVALID")
    _reject(dossier.get("publication_state") != "BLOCKED" or dossier.get("interpretations") != []
            or dossier.get("hypotheses") != [] or dossier.get("review_state") != "REQUIRES_HUMAN_INTERPRETATION",
            "DOSSIER_AUTHORITY_INVALID")
    facts = dossier.get("facts")
    _reject(not isinstance(facts, list) or not facts, "FACTS_REQUIRED")
    seen, observations, contexts = set(), set(), []
    for fact in facts:
        _reject(not isinstance(fact, dict), "FACT_INVALID")
        identity, change, refs = fact.get("fact_id"), fact.get("observed_change"), fact.get("evidence_refs")
        _reject(not isinstance(identity, str) or not identity or identity in seen or
                not isinstance(change, dict) or not isinstance(refs, dict), "FACT_INVALID_OR_DUPLICATED")
        seen.add(identity)
        _reject(fact.get("certainty") != "VERIFIED" or refs.get("source_id") != source["source_id"] or
                refs.get("content_sha256" if eurostat else "current_content_sha256") != source["content_sha256"],
                "FACT_LINEAGE_INVALID")
        if eurostat:
            _reject(set(change) != {"geo_code", "geo_label", "time_period", "change_type",
                    "before_value_thousand_tonnes", "after_value_thousand_tonnes",
                    "absolute_delta_thousand_tonnes", "before_status_flag", "after_status_flag"},
                    "CHANGE_SCHEMA_INVALID")
            _reject(refs.get("delta_sha256") != source["delta_sha256"], "FACT_LINEAGE_INVALID")
            period, geography = change.get("time_period"), change.get("geo_code")
            _reject(type(period) is not int or not 1900 <= period <= 2200 or
                    not isinstance(geography, str) or not geography, "MEASUREMENT_SCOPE_INVALID")
            before_period = after_period = str(period)
            before, after = change.get("before_value_thousand_tonnes"), change.get("after_value_thousand_tonnes")
            delta = change.get("absolute_delta_thousand_tonnes")
            unit = "THOUSAND_TONNES"
            flags = (change.get("before_status_flag"), change.get("after_status_flag"))
            _reject(any(flag is not None and not isinstance(flag, str) for flag in flags), "STATUS_FLAG_INVALID")
            kind = change.get("change_type")
            if kind in {"VALUE_CHANGED", "FLAG_CHANGED"}:
                _reject(not _number(before) or not _number(after) or not _finite_number(delta)
                        or delta != after - before, "MEASUREMENT_INVALID")
                _reject((kind == "VALUE_CHANGED" and before == after) or
                        (kind == "FLAG_CHANGED" and (before != after or flags[0] == flags[1])), "CHANGE_TYPE_INCONSISTENT")
                context = "SAME_PERIOD_REPORTED_VALUE_CHANGE" if kind == "VALUE_CHANGED" else "SAME_PERIOD_STATUS_FLAG_CHANGE"
            elif kind == "ADDED_OBSERVATION":
                _reject(before is not None or not _number(after) or delta is not None or flags[0] is not None,
                        "COVERAGE_CHANGE_INVALID")
                context = "OBSERVATION_COVERAGE_ADDED"
            elif kind == "REMOVED_OBSERVATION":
                _reject(not _number(before) or after is not None or delta is not None or flags[1] is not None,
                        "COVERAGE_CHANGE_INVALID")
                context = "OBSERVATION_COVERAGE_REMOVED"
            else:
                raise ChangeContextViolation("CHANGE_TYPE_UNSUPPORTED")
        else:
            _reject(set(change) != {"customs_point", "before_period", "after_period", "change_type",
                    "before_value_usd_million", "after_value_usd_million", "absolute_delta_usd_million",
                    "relative_delta"}, "CHANGE_SCHEMA_INVALID")
            before_period, after_period = change.get("before_period"), change.get("after_period")
            _reject(any(not isinstance(p, str) or re.fullmatch(r"[0-9]{4}Q1", p) is None
                        for p in (before_period, after_period)) or before_period >= after_period,
                    "DISTINCT_ORDERED_PERIODS_REQUIRED")
            geography = change.get("customs_point")
            _reject(not isinstance(geography, str) or not geography, "MEASUREMENT_SCOPE_INVALID")
            before, after = change.get("before_value_usd_million"), change.get("after_value_usd_million")
            delta = change.get("absolute_delta_usd_million")
            _reject(change.get("change_type") != "VALUE_CHANGED" or not _number(before) or not _number(after)
                    or before == after or not _finite_number(delta)
                    or delta != after - before, "MEASUREMENT_INVALID")
            _reject(change["relative_delta"] != (None if before == 0 else delta / before),
                    "RELATIVE_DELTA_INVALID")
            unit, context = "USD_MILLION", "DISTINCT_PERIOD_VALUE_COMPARISON"
        observation = (geography, before_period, after_period)
        _reject(observation in observations, "OBSERVATION_DUPLICATED")
        observations.add(observation)
        contexts.append({"fact_id": identity, "kind": context, "geography": geography,
                         "before_period": before_period, "after_period": after_period, "unit": unit})
    try:
        digest = sha256(json.dumps(dossier, sort_keys=True, separators=(",", ":"),
                                  ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    except (ValueError, TypeError, OverflowError) as error:
        raise ChangeContextViolation("DOSSIER_ENCODING_INVALID") from error
    return {"version": "0.1.0", "scope": "LOCAL_LITERAL_CHANGE_CONTEXT",
            "dossier_id": dossier["dossier_id"], "source_hash": source["content_sha256"],
            "dossier_sha256": digest,
            "facts": contexts, "cause_certainty": "UNCONFIRMED", "resolution": "NOT_RESOLVED",
            "acceptance": "NOT_ACCEPTED", "publication": "BLOCKED"}
