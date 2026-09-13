"""Deterministic manual-release comparison for bounded Eurostat maritime data."""

from __future__ import annotations

from datetime import datetime
import json
from typing import Any

from .common import ContractViolation
from .eurostat_maritime_mapper import (
    EurostatMaritimeMappingViolation,
    map_eurostat_maritime_workbook,
    select_eurostat_geography_level,
)
from .manual_bundle_ledger import (
    ManualBundleLedgerViolation,
    validate_unattested_manual_bundle,
)


class EurostatMaritimeDeltaViolation(ContractViolation):
    """Two workbook releases cannot be compared without ambiguity."""


def _compare(previous: dict[str, Any], current: dict[str, Any], geo_level: str) -> dict[str, Any]:
    identity = previous["content_sha256"] == current["content_sha256"]
    previous_time = datetime.fromisoformat(previous["last_updated"])
    current_time = datetime.fromisoformat(current["last_updated"])
    if not identity and current_time == previous_time:
        raise EurostatMaritimeDeltaViolation("same Eurostat release timestamp has different content")
    if current_time < previous_time:
        raise EurostatMaritimeDeltaViolation("Eurostat release time regressed")
    if current.get("observed_at") is not None and previous.get("observed_at") is not None and current["observed_at"] < previous["observed_at"]:
        raise EurostatMaritimeDeltaViolation("manual observation time regressed")

    previous_values = {
        (item["geo_code"], item["time_period"]): item for item in previous["observations"]
    }
    current_values = {
        (item["geo_code"], item["time_period"]): item for item in current["observations"]
    }
    changes = []
    for geo_code, year in sorted(set(previous_values) | set(current_values)):
        before = previous_values.get((geo_code, year))
        after = current_values.get((geo_code, year))
        if before is None:
            change_type = "ADDED_OBSERVATION"
        elif after is None:
            change_type = "REMOVED_OBSERVATION"
        elif before["value_thousand_tonnes"] != after["value_thousand_tonnes"]:
            change_type = "VALUE_CHANGED"
        elif before["status_flag"] != after["status_flag"]:
            change_type = "FLAG_CHANGED"
        else:
            continue
        changes.append({
            "geo_code": geo_code,
            "geo_label": (after or before)["geo_label"],
            "time_period": year,
            "change_type": change_type,
            "before_value_thousand_tonnes": None if before is None else before["value_thousand_tonnes"],
            "after_value_thousand_tonnes": None if after is None else after["value_thousand_tonnes"],
            "absolute_delta_thousand_tonnes": (
                None if before is None or after is None
                else after["value_thousand_tonnes"] - before["value_thousand_tonnes"]
            ),
            "before_status_flag": None if before is None else before["status_flag"],
            "after_status_flag": None if after is None else after["status_flag"],
        })
    if identity:
        status = "IDENTICAL_FILE_NOT_EVIDENCE"
    elif changes:
        status = "DELTA_DETECTED_NOT_EVIDENCE"
    else:
        status = "NO_DELTA_NOT_EVIDENCE"
    return {
        "scope": "BLOCK1_EUROSTAT_MARITIME_MANUAL_WATCHLIST",
        "source_id": "eurostat",
        "dataset_code": "tran_r_mago_nm",
        "selected_geo_level": geo_level,
        "previous": {
            "content_sha256": previous["content_sha256"],
            "last_updated": previous["last_updated"],
            "coverage": previous["coverage"],
        },
        "current": {
            "content_sha256": current["content_sha256"],
            "last_updated": current["last_updated"],
            "coverage": current["coverage"],
        },
        "change_count": len(changes),
        "changes": changes,
        "status": status,
        "evidence_state": "NOT_EVIDENCE",
        "next_state": "REQUIRES_SOURCE_ATTESTATION_AND_REVIEW" if changes else "NO_REVIEWABLE_DELTA",
    }


def compare_eurostat_maritime_workbooks(
    previous_file_name: object,
    previous_payload: object,
    current_file_name: object,
    current_payload: object,
    geo_level: object,
) -> dict[str, Any]:
    """Compare two independently mapped releases at one geographic grain."""

    if not isinstance(geo_level, str) or geo_level not in {"COUNTRY", "NUTS1", "NUTS2"}:
        raise EurostatMaritimeDeltaViolation("Eurostat geography level is unsupported")
    try:
        previous_map = map_eurostat_maritime_workbook(previous_file_name, previous_payload)
        current_map = map_eurostat_maritime_workbook(current_file_name, current_payload)
        previous = select_eurostat_geography_level(previous_file_name, previous_payload, geo_level)
        current = select_eurostat_geography_level(current_file_name, current_payload, geo_level)
    except EurostatMaritimeMappingViolation as error:
        raise EurostatMaritimeDeltaViolation("Eurostat release cannot be compared") from error
    return _compare(
        {"content_sha256": previous_map["content_sha256"], "last_updated": previous_map["last_updated"], "coverage": previous["coverage"], "observations": previous["observations"]},
        {"content_sha256": current_map["content_sha256"], "last_updated": current_map["last_updated"], "coverage": current["coverage"], "observations": current["observations"]},
        geo_level,
    )


def compare_eurostat_manual_bundles(
    previous_bundle: object, current_bundle: object,
) -> dict[str, Any]:
    """Compare two revalidated ledger-compatible bundle checkpoints."""

    try:
        previous_outer = validate_unattested_manual_bundle(previous_bundle)
        current_outer = validate_unattested_manual_bundle(current_bundle)
    except ManualBundleLedgerViolation as error:
        raise EurostatMaritimeDeltaViolation("manual bundle checkpoint is invalid") from error
    previous_content = json.loads(previous_outer["content"])
    current_content = json.loads(current_outer["content"])
    previous_selection = previous_content["selection"]
    current_selection = current_content["selection"]
    geo_level = previous_selection["geo_level"]
    if current_selection["geo_level"] != geo_level:
        raise EurostatMaritimeDeltaViolation("manual bundle geography levels differ")
    return _compare(
        {"content_sha256": previous_content["provenance"]["source_file_sha256"], "last_updated": previous_content["provenance"]["dataset_last_updated"], "observed_at": previous_outer["observed_at"], "coverage": previous_selection["coverage"], "observations": previous_content["observations"]},
        {"content_sha256": current_content["provenance"]["source_file_sha256"], "last_updated": current_content["provenance"]["dataset_last_updated"], "observed_at": current_outer["observed_at"], "coverage": current_selection["coverage"], "observations": current_content["observations"]},
        geo_level,
    )
