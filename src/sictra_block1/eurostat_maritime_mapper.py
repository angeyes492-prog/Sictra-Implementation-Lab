"""Schema mapper for one approved Eurostat maritime workbook shape.

The mapper accepts only a locally supplied ``tran_r_mago_nm`` workbook after
manual-file preflight.  Its output is structured data for later review, never
evidence, a source binding, or an insight.
"""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
import math
import re
from typing import Any
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from .common import ContractViolation
from .manual_source_preflight import preflight_manual_source_file


_CELL_REF = re.compile(r"([A-Z]+)([1-9][0-9]*)$")
_GEO_CODE = re.compile(r"[A-Z0-9_]{2,15}$")
_YEAR = re.compile(r"[12][0-9]{3}$")
_DATASET = re.compile(r"\[tran_r_mago_nm(?:\$[^\]]+)?\]")
_REQUIRED_METADATA = {
    "Time frequency [FREQ]": "Annual [A]",
    "Traffic and transport measurement [TRA_MEAS]": "Freight loaded and unloaded [FR_LD_NLD]",
    "Unit of measure [UNIT]": "Thousand tonnes [THS_T]",
}
_MISSING_VALUES = frozenset((":",))


class EurostatMaritimeMappingViolation(ContractViolation):
    """The supplied workbook cannot be safely mapped to the declared schema."""


def _local_name(element: ElementTree.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _column_index(reference: object) -> int:
    if not isinstance(reference, str):
        raise EurostatMaritimeMappingViolation("XLSX cell reference is missing")
    match = _CELL_REF.fullmatch(reference)
    if match is None:
        raise EurostatMaritimeMappingViolation("XLSX cell reference is invalid")
    number = 0
    for char in match.group(1):
        number = number * 26 + ord(char) - ord("A") + 1
    return number


def _shared_strings(archive: ZipFile) -> tuple[str, ...]:
    try:
        raw = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return ()
    if b"<!DOCTYPE" in raw.upper():
        raise EurostatMaritimeMappingViolation("XLSX shared strings contain a DTD")
    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError as error:
        raise EurostatMaritimeMappingViolation("XLSX shared strings are malformed") from error
    values = []
    for item in (node for node in root if _local_name(node) == "si"):
        values.append("".join(node.text or "" for node in item.iter() if _local_name(node) == "t"))
    return tuple(values)


def _cell_value(cell: ElementTree.Element, shared: tuple[str, ...]) -> str | None:
    kind = cell.attrib.get("t")
    if kind == "inlineStr":
        value = "".join(node.text or "" for node in cell.iter() if _local_name(node) == "t")
        return value.strip() or None
    raw = next((node.text for node in cell if _local_name(node) == "v"), None)
    if raw is None or not raw.strip():
        return None
    if kind == "s":
        try:
            return shared[int(raw)].strip() or None
        except (IndexError, ValueError) as error:
            raise EurostatMaritimeMappingViolation("XLSX shared-string reference is invalid") from error
    return raw.strip()


def _sheet_rows(archive: ZipFile, shared: tuple[str, ...]) -> tuple[dict[int, str], ...]:
    sheets = [
        item for item in archive.infolist()
        if item.filename.startswith("xl/worksheets/")
        and "/" not in item.filename.removeprefix("xl/worksheets/")
        and item.filename.endswith(".xml")
    ]
    if not sheets:
        raise EurostatMaritimeMappingViolation("XLSX has no worksheet")
    rows: list[dict[int, str]] = []
    for sheet in sheets:
        raw = archive.read(sheet)
        if b"<!DOCTYPE" in raw.upper():
            raise EurostatMaritimeMappingViolation("XLSX worksheet contains a DTD")
        try:
            root = ElementTree.fromstring(raw)
        except ElementTree.ParseError as error:
            raise EurostatMaritimeMappingViolation("XLSX worksheet is malformed") from error
        for row in (node for node in root.iter() if _local_name(node) == "row"):
            mapped = {
                _column_index(cell.attrib.get("r")): value
                for cell in row
                if _local_name(cell) == "c"
                for value in (_cell_value(cell, shared),)
                if value is not None
            }
            rows.append(mapped)
    return tuple(rows)


def _metadata(rows: tuple[dict[int, str], ...]) -> dict[str, str]:
    result: dict[str, str] = {}
    labels = {"Dataset:", "Last updated:", *_REQUIRED_METADATA}
    for row in rows:
        for column, value in row.items():
            if value in labels:
                candidate = next((item for index, item in sorted(row.items()) if index > column and item), None)
                if candidate is not None:
                    result[value] = candidate
    return result


def _time_columns(rows: tuple[dict[int, str], ...]) -> tuple[int, dict[int, int]]:
    for index, row in enumerate(rows):
        years = {column: int(value) for column, value in row.items() if _YEAR.fullmatch(value)}
        if years and any(value == "TIME" for value in row.values()):
            return index, years
    raise EurostatMaritimeMappingViolation("Eurostat TIME header is missing")


def _geo_columns(rows: tuple[dict[int, str], ...], start: int) -> tuple[int, int, int]:
    for index in range(start + 1, len(rows)):
        row = rows[index]
        codes = next((column for column, value in row.items() if value == "GEO (Codes)"), None)
        labels = next((column for column, value in row.items() if value == "GEO (Labels)"), None)
        if codes is not None and labels is not None:
            return index, codes, labels
    raise EurostatMaritimeMappingViolation("Eurostat GEO header is missing")


def _require_metadata(metadata: dict[str, str]) -> tuple[str, str]:
    dataset = metadata.get("Dataset:", "")
    if _DATASET.search(dataset) is None:
        raise EurostatMaritimeMappingViolation("workbook is not the approved tran_r_mago_nm dataset")
    for label, expected in _REQUIRED_METADATA.items():
        if metadata.get(label) != expected:
            raise EurostatMaritimeMappingViolation(f"Eurostat metadata does not match {label}")
    last_updated = metadata.get("Last updated:")
    if last_updated is None:
        raise EurostatMaritimeMappingViolation("Eurostat last-updated metadata is missing")
    try:
        last_updated_iso = datetime.strptime(last_updated, "%d/%m/%Y %H:%M").isoformat(timespec="minutes")
    except ValueError as error:
        raise EurostatMaritimeMappingViolation("Eurostat last-updated metadata is invalid") from error
    return dataset, last_updated_iso


def _geo_level(code: str) -> str:
    if len(code) == 2:
        return "COUNTRY"
    if len(code) == 3:
        return "NUTS1"
    if len(code) == 4:
        return "NUTS2"
    return "AGGREGATE_OR_OTHER"


def map_eurostat_maritime_workbook(file_name: object, payload: object) -> dict[str, Any]:
    """Map the approved annual freight workbook while preserving its boundaries."""

    preflight = preflight_manual_source_file(file_name, payload)
    if preflight["status"] != "READY_FOR_SCHEMA_REVIEW" or preflight["format"] != "XLSX":
        raise EurostatMaritimeMappingViolation("workbook did not pass manual-source preflight")
    if not isinstance(payload, bytes):
        raise EurostatMaritimeMappingViolation("workbook payload is invalid")
    try:
        with ZipFile(BytesIO(payload)) as archive:
            rows = _sheet_rows(archive, _shared_strings(archive))
    except (BadZipFile, ValueError) as error:
        raise EurostatMaritimeMappingViolation("workbook archive is invalid") from error
    metadata = _metadata(rows)
    dataset_title, last_updated = _require_metadata(metadata)
    time_header, years = _time_columns(rows)
    geo_header, geo_column, label_column = _geo_columns(rows, time_header)
    observations: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    declared_geographies: dict[str, dict[str, str]] = {}
    missing_values = 0
    flagged_observations = 0
    legend_rows = 0
    legend_started = False
    for row in rows[geo_header + 1:]:
        geo, label = row.get(geo_column), row.get(label_column)
        if geo is None and label is None:
            continue
        no_measurements = all(row.get(column) is None for column in years)
        if geo == "Special value" and label is None and no_measurements:
            legend_started = True
            legend_rows += 1
            continue
        if legend_started and geo == ":" and label == "not available" and no_measurements:
            legend_rows += 1
            continue
        if legend_started:
            raise EurostatMaritimeMappingViolation("Eurostat end-of-table legend is invalid")
        if geo is None or label is None or _GEO_CODE.fullmatch(geo) is None:
            raise EurostatMaritimeMappingViolation("Eurostat geography row is invalid")
        if geo in declared_geographies:
            raise EurostatMaritimeMappingViolation("Eurostat geography row is duplicated")
        declared_geographies[geo] = {"geo_label": label, "geo_level": _geo_level(geo)}
        for column, year in years.items():
            raw = row.get(column)
            if raw is None or raw in _MISSING_VALUES:
                missing_values += 1
                continue
            try:
                value = float(raw)
            except ValueError as error:
                raise EurostatMaritimeMappingViolation("Eurostat freight value is not numeric") from error
            if not math.isfinite(value) or value < 0:
                raise EurostatMaritimeMappingViolation("Eurostat freight value is outside the allowed range")
            key = (geo, year)
            if key in seen:
                raise EurostatMaritimeMappingViolation("Eurostat geography-time grain is not unique")
            seen.add(key)
            flag = row.get(column + 1)
            if flag is not None:
                flagged_observations += 1
            observations.append({
                "geo_code": geo,
                "geo_label": label,
                "geo_level": declared_geographies[geo]["geo_level"],
                "time_period": year,
                "value_thousand_tonnes": value,
                "status_flag": flag,
            })
    if not observations:
        raise EurostatMaritimeMappingViolation("Eurostat workbook has no freight observations")
    observed_geographies = {item["geo_code"] for item in observations}
    geo_level_counts = {
        level: sum(item["geo_level"] == level for item in declared_geographies.values())
        for level in sorted({item["geo_level"] for item in declared_geographies.values()})
    }
    return {
        "scope": "BLOCK1_EUROSTAT_MARITIME_SCHEMA_MAPPING",
        "source_id": "eurostat",
        "dataset_code": "tran_r_mago_nm",
        "dataset_title": dataset_title,
        "filters": {
            "frequency": "A",
            "transport_measure": "FR_LD_NLD",
            "unit": "THS_T",
        },
        "last_updated": last_updated,
        "grain": ["geo_code", "time_period"],
        "quality": {
            "observation_count": len(observations),
            "declared_geography_count": len(declared_geographies),
            "observed_geography_count": len(observed_geographies),
            "all_missing_geography_count": len(set(declared_geographies) - observed_geographies),
            "geography_level_counts": geo_level_counts,
            "years": sorted(set(years.values())),
            "missing_value_count": missing_values,
            "flagged_observation_count": flagged_observations,
            "duplicate_geo_time_count": 0,
            "legend_row_count": legend_rows,
        },
        "content_sha256": preflight["content_sha256"],
        "geographies": [
            {"geo_code": code, **details}
            for code, details in sorted(declared_geographies.items())
        ],
        "observations": observations,
        "status": "MAPPED_NOT_EVIDENCE",
        "analysis_state": "REQUIRES_GEO_LEVEL_SELECTION",
        "evidence_state": "NOT_EVIDENCE",
    }


def select_eurostat_geography_level(file_name: object, payload: object, geo_level: object) -> dict[str, Any]:
    """Select one declared geography level without cross-level aggregation."""

    if not isinstance(geo_level, str) or geo_level not in {"COUNTRY", "NUTS1", "NUTS2"}:
        raise EurostatMaritimeMappingViolation("Eurostat geography level is unsupported")
    mapped = map_eurostat_maritime_workbook(file_name, payload)
    geographies = [item for item in mapped["geographies"] if item["geo_level"] == geo_level]
    observations = [item for item in mapped["observations"] if item["geo_level"] == geo_level]
    observed_codes = {item["geo_code"] for item in observations}
    years = mapped["quality"]["years"]
    return {
        "scope": "BLOCK1_EUROSTAT_MARITIME_GEO_LEVEL_SELECTION",
        "source_id": mapped["source_id"],
        "dataset_code": mapped["dataset_code"],
        "filters": mapped["filters"],
        "content_sha256": mapped["content_sha256"],
        "selected_geo_level": geo_level,
        "grain": mapped["grain"],
        "years": years,
        "coverage": {
            "declared_geography_count": len(geographies),
            "observed_geography_count": len(observed_codes),
            "all_missing_geography_count": len({item["geo_code"] for item in geographies} - observed_codes),
            "expected_geo_time_cells": len(geographies) * len(years),
            "observation_count": len(observations),
            "missing_value_count": len(geographies) * len(years) - len(observations),
        },
        "observations": observations,
        "status": "SELECTED_NOT_EVIDENCE",
        "analysis_state": "READY_FOR_COVERAGE_REVIEW",
        "evidence_state": "NOT_EVIDENCE",
    }
