"""Read-only, fixed-scope JSON-stat inspection of quarantined Eurostat data."""
from datetime import datetime
from hashlib import sha256
import json
import math
import re
import time

from .research_acquisition import (
    ResearchAcquisitionError, ResearchQuarantine, STATISTICS_RECIPE, canonical,
)

EXPECTED = {"freq": {"A"}, "tra_meas": {"FR_LD_NLD"}, "unit": {"THS_T"},
            "geo": {"BE"}, "time": {"2023", "2024"}}


def require(condition, reason):
    if not condition:
        raise ResearchAcquisitionError("STATISTICS_" + reason)


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _cells(value, count, *, status=False):
    if status and value is None:
        return [None] * count
    if status and isinstance(value, str):
        return [value] * count
    if isinstance(value, list):
        require(len(value) == count, "CELL_COUNT_INVALID")
        return value
    require(isinstance(value, dict), "CELL_SHAPE_INVALID")
    result = [None] * count
    for key, item in value.items():
        require(isinstance(key, str) and re.fullmatch(r"0|[1-9][0-9]{0,3}", key) is not None,
                "CELL_INDEX_INVALID")
        position = int(key)
        require(position < count, "CELL_INDEX_INVALID")
        result[position] = item
    return result


def normalize_maritime_statistics(content):
    """Pure fixed-scope mapping. Parsed publisher claims are not attested facts."""
    require(isinstance(content, bytes) and 0 < len(content) <= 1024 * 1024, "CONTENT_SIZE_INVALID")
    def invalid_constant(_):
        raise ResearchAcquisitionError("STATISTICS_NONFINITE_JSON")
    try:
        data = json.loads(content.decode("utf-8-sig", errors="strict"),
                          object_pairs_hook=unique, parse_constant=invalid_constant)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ResearchAcquisitionError("STATISTICS_JSON_INVALID") from error
    require(isinstance(data, dict) and "error" not in data and "warning" not in data,
            "ERROR_OR_WARNING_RESPONSE")
    require(data.get("version") == "2.0" and data.get("class") == "dataset"
            and data.get("source") == "ESTAT", "IDENTITY_INVALID")
    label, updated = data.get("label"), data.get("updated")
    require(isinstance(label, str) and 0 < len(label.strip()) <= 1000, "TITLE_INVALID")
    require(isinstance(updated, str) and re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}(T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|[+-](?:[01][0-9]|2[0-3]):?[0-5][0-9])?)?",
        updated) is not None, "UPDATE_INVALID")
    try:
        parsed_update = datetime.fromisoformat(updated.replace("Z", "+00:00"))
    except ValueError as error:
        raise ResearchAcquisitionError("STATISTICS_UPDATE_INVALID") from error
    extension = data.get("extension", {})
    require(isinstance(extension, dict), "EXTENSION_INVALID")
    if "id" in extension:
        require(isinstance(extension["id"], str) and extension["id"].lower() == "tran_r_mago_nm",
                "DATASET_ID_INVALID")
    ids, sizes, dimensions = data.get("id"), data.get("size"), data.get("dimension")
    require(isinstance(ids, list) and len(ids) == 5 and all(isinstance(i, str) for i in ids)
            and set(ids) == set(EXPECTED), "DIMENSIONS_INVALID")
    require(isinstance(sizes, list) and len(sizes) == 5 and all(type(s) is int for s in sizes)
            and sizes == [len(EXPECTED[i]) for i in ids], "SIZES_INVALID")
    require(isinstance(dimensions, dict) and set(dimensions) == set(ids), "DIMENSION_BODY_INVALID")
    categories = {}
    labels = {}
    for identity, size in zip(ids, sizes):
        dim = dimensions[identity]
        require(isinstance(dim, dict) and isinstance(dim.get("category"), dict), "CATEGORY_INVALID")
        category = dim["category"]
        indexes = category.get("index")
        if isinstance(indexes, list):
            require(len(indexes) == size and all(isinstance(i, str) for i in indexes)
                    and set(indexes) == EXPECTED[identity], "CATEGORY_INDEX_INVALID")
            ordered = indexes
        else:
            require(isinstance(indexes, dict) and set(indexes) == EXPECTED[identity]
                    and all(type(i) is int for i in indexes.values())
                    and set(indexes.values()) == set(range(size)), "CATEGORY_INDEX_INVALID")
            ordered = [key for key, _ in sorted(indexes.items(), key=lambda pair: pair[1])]
        named = category.get("label")
        require(isinstance(named, dict) and set(named) == set(ordered)
                and all(isinstance(v, str) and 0 < len(v.strip()) <= 300 for v in named.values()),
                "CATEGORY_LABEL_INVALID")
        categories[identity], labels[identity] = ordered, named
    values = _cells(data.get("value"), 2)
    statuses = _cells(data.get("status"), 2, status=True)
    observations = []
    # Decode declared row-major positions, never assume dictionary insertion
    # order or that time is the last dimension.
    for position, (value, flag) in enumerate(zip(values, statuses)):
        coordinates, remainder = {}, position
        for identity, size in reversed(list(zip(ids, sizes))):
            remainder, offset = divmod(remainder, size)
            coordinates[identity] = categories[identity][offset]
        if value is not None:
            require(type(value) in (int, float), "VALUE_INVALID")
            try:
                finite = math.isfinite(value)
            except OverflowError:
                finite = False
            require(finite and value >= 0, "VALUE_INVALID")
        require(flag is None or (isinstance(flag, str) and 0 < len(flag) <= 32
                and re.fullmatch(r"[A-Za-z0-9 :]+", flag) is not None), "STATUS_INVALID")
        observations.append({"geo_code": coordinates["geo"], "geo_label": labels["geo"]["BE"],
            "geo_level": "COUNTRY", "time_period": int(coordinates["time"]),
            "value_thousand_tonnes": value, "missing": value is None, "status_flag": flag})
    return {"dataset_code": "tran_r_mago_nm", "dataset_title": label,
            "filters": {"frequency": "A", "transport_measure": "FR_LD_NLD", "unit": "THS_T"},
            "selected_geo_level": "COUNTRY", "grain": ["geo_code", "time_period"],
            "publisher_updated_raw": updated,
            "publisher_timezone": "EXPLICIT" if parsed_update.tzinfo else "UNSPECIFIED",
            "observations": sorted(observations, key=lambda row: row["time_period"]),
            "missing_value_count": sum(row["missing"] for row in observations)}


def inspect_statistics_candidate(quarantine, candidate_id, *, clock=time.time):
    start = int(clock())
    descriptor, content = quarantine.read(candidate_id, now=start, expected_recipe=STATISTICS_RECIPE)
    terms, terms_bytes = quarantine.read(descriptor["terms_candidate_id"], now=start,
                                         expected_recipe="EUROSTAT_REUSE_NOTICE")
    normalized = normalize_maritime_statistics(content)
    finish = int(clock())
    current, current_bytes = quarantine.read(candidate_id, now=finish, expected_recipe=STATISTICS_RECIPE)
    current_terms, current_terms_bytes = quarantine.read(descriptor["terms_candidate_id"], now=finish,
                                                         expected_recipe="EUROSTAT_REUSE_NOTICE")
    require(current == descriptor and current_bytes == content and current_terms == terms
            and current_terms_bytes == terms_bytes, "CHANGED_DURING_READ")
    report = {"version": "0.1.0", "source_id": "eurostat", "candidate_id": candidate_id,
        "source_url": descriptor["final_url"], "content_sha256": descriptor["content_sha256"],
        "acquired_at": descriptor["acquired_at"], "source_expires_at": descriptor["expires_at"],
        "terms_candidate_id": descriptor["terms_candidate_id"], "terms_content_sha256": terms["content_sha256"],
        "terms_expires_at": terms["expires_at"], "expires_at": min(descriptor["expires_at"], terms["expires_at"]),
        **normalized, "evidence_state": "QUARANTINED_NOT_ADMITTED", "resolution": "NOT_RESOLVED",
        "acceptance": "NOT_ACCEPTED", "runtime_effect": "NONE", "publication": "BLOCKED",
        "root_provenance": "UNCONFIRMED", "specific_change_cause": "UNCONFIRMED",
        "limitations": ["Same Eurostat root is not independent corroboration",
                        "Different years are not two releases of the same observation",
                        "No source admission, attestation, task or dossier mutation"]}
    report["fingerprint"] = sha256(canonical(report)).hexdigest()
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--candidate-id", required=True)
    args = parser.parse_args()
    print(json.dumps(inspect_statistics_candidate(ResearchQuarantine(args.root), args.candidate_id),
                     ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
