"""Controlled assembly of an un-attested Eurostat manual source bundle."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlsplit

from .common import ContractViolation
from .eurostat_maritime_mapper import (
    EurostatMaritimeMappingViolation,
    map_eurostat_maritime_workbook,
    select_eurostat_geography_level,
)


_MAX_CONTENT_BYTES = 131_072
_CORRELATION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_DATASET_TOKEN = "tran_r_mago_nm"


class EurostatManualBundleViolation(ContractViolation):
    """A local mapping cannot become a safe gateway bundle."""


def _source_url(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EurostatManualBundleViolation("Eurostat source URL is required")
    try:
        parsed = urlsplit(value.strip())
        port = parsed.port
    except ValueError as error:
        raise EurostatManualBundleViolation("Eurostat source URL is invalid") from error
    if (
        parsed.scheme.lower() != "https"
        or parsed.hostname != "ec.europa.eu"
        or parsed.username
        or parsed.password
        or port is not None
        or parsed.fragment
        or _DATASET_TOKEN not in parsed.path.lower()
    ):
        raise EurostatManualBundleViolation("Eurostat source URL is outside the approved dataset")
    return value.strip()


def _observed_at(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise EurostatManualBundleViolation("observed_at must be a non-negative integer")
    return value


def _correlation_id(value: object) -> str:
    if not isinstance(value, str) or _CORRELATION.fullmatch(value) is None:
        raise EurostatManualBundleViolation("correlation identifier is invalid")
    return value


def build_eurostat_manual_bundle(
    file_name: object,
    payload: object,
    geo_level: object,
    *,
    source_url: object,
    observed_at: object,
    correlation_id: object,
) -> dict[str, Any]:
    """Serialize one explicit level for a later, separately governed attestation."""

    url = _source_url(source_url)
    observed = _observed_at(observed_at)
    correlation = _correlation_id(correlation_id)
    if not isinstance(geo_level, str) or geo_level not in {"COUNTRY", "NUTS1", "NUTS2"}:
        raise EurostatManualBundleViolation("Eurostat geography level is unsupported")
    try:
        mapped = map_eurostat_maritime_workbook(file_name, payload)
        selected = select_eurostat_geography_level(file_name, payload, geo_level)
    except EurostatMaritimeMappingViolation as error:
        raise EurostatManualBundleViolation("Eurostat workbook cannot be assembled") from error
    content = json.dumps(
        {
            "schema_version": "0.1.0",
            "content_type": "application/vnd.sictra.eurostat-maritime-selection+json",
            "bundle_state": "UNATTESTED_MANUAL_BUNDLE",
            "provenance": {
                "source_file_sha256": mapped["content_sha256"],
                "dataset_code": mapped["dataset_code"],
                "dataset_title": mapped["dataset_title"],
                "dataset_last_updated": mapped["last_updated"],
                "mapping_scope": mapped["scope"],
                "mapping_status": mapped["status"],
                "mapping_evidence_state": mapped["evidence_state"],
            },
            "filters": selected["filters"],
            "selection": {
                "geo_level": selected["selected_geo_level"],
                "grain": selected["grain"],
                "years": selected["years"],
                "coverage": selected["coverage"],
                "selection_scope": selected["scope"],
                "selection_status": selected["status"],
                "selection_evidence_state": selected["evidence_state"],
            },
            "observations": selected["observations"],
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    if len(content.encode("utf-8")) > _MAX_CONTENT_BYTES:
        raise EurostatManualBundleViolation("Eurostat bundle exceeds the governed content limit")
    return {
        "source_id": "eurostat",
        "source_url": url,
        "content": content,
        "observed_at": observed,
        "claim_key": "maritime_freight_weight_thousand_tonnes",
        "polarity": 1,
        "correlation_id": correlation,
    }
