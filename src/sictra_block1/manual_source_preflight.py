"""Fail-closed preflight for operator-supplied source files.

This module classifies a local CSV/XLSX payload before schema mapping or source
attestation.  It does not read from the network, persist content, issue
evidence, or bind a source.
"""

from __future__ import annotations

import csv
from hashlib import sha256
from io import BytesIO, StringIO
from pathlib import PurePath
from typing import Any
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from .common import ContractViolation


MAX_MANUAL_SOURCE_BYTES = 131_072
MAX_XLSX_ENTRIES = 64
MAX_XLSX_EXPANDED_BYTES = 1_048_576
_SUPPORTED_EXTENSIONS = frozenset((".csv", ".xlsx"))


class ManualSourcePreflightViolation(ContractViolation):
    """The supplied file cannot enter the bounded preflight boundary."""


def _file_name(value: object) -> tuple[str, str]:
    if not isinstance(value, str) or not value.strip():
        raise ManualSourcePreflightViolation("source file name must be non-empty text")
    name = value.strip()
    path = PurePath(name)
    if "/" in name or "\\" in name or not path.stem or path.suffix.lower() not in _SUPPORTED_EXTENSIONS:
        raise ManualSourcePreflightViolation("source file name or extension is not allowed")
    return name, path.suffix.lower()


def _rejected(*, name: str, extension: str, digest: str, reason: str) -> dict[str, Any]:
    return {
        "scope": "BLOCK1_MANUAL_SOURCE_PREFLIGHT",
        "file_name": name,
        "format": extension[1:].upper(),
        "content_sha256": digest,
        "status": "REJECTED_NOT_EVIDENCE",
        "reason": reason,
        "detected_table_rows": 0,
        "evidence_state": "NOT_EVIDENCE",
    }


def _csv_preflight(*, name: str, extension: str, digest: str, payload: bytes) -> dict[str, Any]:
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        return _rejected(name=name, extension=extension, digest=digest, reason="CSV_MUST_BE_UTF8")
    if "\x00" in text:
        return _rejected(name=name, extension=extension, digest=digest, reason="CSV_CONTAINS_NUL")
    try:
        rows = [
            [cell.strip() for cell in row]
            for row in csv.reader(StringIO(text))
            if any(cell.strip() for cell in row)
        ]
    except csv.Error:
        return _rejected(name=name, extension=extension, digest=digest, reason="CSV_IS_MALFORMED")
    if len(rows) < 2 or len([cell for cell in rows[0] if cell]) < 2:
        return _rejected(name=name, extension=extension, digest=digest, reason="CSV_HAS_NO_TABULAR_DATA")
    width = len(rows[0])
    if any(len(row) != width for row in rows[1:]):
        return _rejected(name=name, extension=extension, digest=digest, reason="CSV_ROWS_HAVE_INCONSISTENT_WIDTH")
    return {
        "scope": "BLOCK1_MANUAL_SOURCE_PREFLIGHT",
        "file_name": name,
        "format": "CSV",
        "content_sha256": digest,
        "status": "READY_FOR_SCHEMA_REVIEW",
        "reason": "TABULAR_CONTENT_PRESENT",
        "detected_table_rows": len(rows),
        "detected_data_rows": len(rows) - 1,
        "header": rows[0],
        "evidence_state": "NOT_EVIDENCE",
    }


def _has_nonempty_value(cell: ElementTree.Element) -> bool:
    return any(node.tag.rsplit("}", 1)[-1] in {"v", "t"} and (node.text or "").strip() for node in cell.iter())


def _xlsx_preflight(*, name: str, extension: str, digest: str, payload: bytes) -> dict[str, Any]:
    try:
        with ZipFile(BytesIO(payload)) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_XLSX_ENTRIES or sum(item.file_size for item in entries) > MAX_XLSX_EXPANDED_BYTES:
                return _rejected(name=name, extension=extension, digest=digest, reason="XLSX_ARCHIVE_LIMIT_EXCEEDED")
            sheets = [item for item in entries if item.filename.startswith("xl/worksheets/") and item.filename.endswith(".xml")]
            if not sheets:
                return _rejected(name=name, extension=extension, digest=digest, reason="XLSX_HAS_NO_WORKSHEET")
            tabular_rows = 0
            for sheet in sheets:
                raw = archive.read(sheet)
                if b"<!DOCTYPE" in raw.upper():
                    return _rejected(name=name, extension=extension, digest=digest, reason="XLSX_XML_DTD_REJECTED")
                root = ElementTree.fromstring(raw)
                for row in (node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "row"):
                    cells = [node for node in row if node.tag.rsplit("}", 1)[-1] == "c"]
                    if sum(_has_nonempty_value(cell) for cell in cells) >= 2:
                        tabular_rows += 1
    except (BadZipFile, ElementTree.ParseError, KeyError, ValueError):
        return _rejected(name=name, extension=extension, digest=digest, reason="XLSX_IS_MALFORMED")
    if tabular_rows < 2:
        return _rejected(name=name, extension=extension, digest=digest, reason="XLSX_HAS_NO_TABULAR_DATA")
    return {
        "scope": "BLOCK1_MANUAL_SOURCE_PREFLIGHT",
        "file_name": name,
        "format": "XLSX",
        "content_sha256": digest,
        "status": "READY_FOR_SCHEMA_REVIEW",
        "reason": "TABULAR_CONTENT_PRESENT",
        "detected_table_rows": tabular_rows,
        "evidence_state": "NOT_EVIDENCE",
    }


def preflight_manual_source_file(file_name: object, payload: object) -> dict[str, Any]:
    """Return a bounded format decision; never a source or evidence decision."""

    name, extension = _file_name(file_name)
    if not isinstance(payload, bytes) or isinstance(payload, bool) or not payload or len(payload) > MAX_MANUAL_SOURCE_BYTES:
        raise ManualSourcePreflightViolation("source file payload is invalid or exceeds the limit")
    digest = sha256(payload).hexdigest()
    if extension == ".csv":
        return _csv_preflight(name=name, extension=extension, digest=digest, payload=payload)
    return _xlsx_preflight(name=name, extension=extension, digest=digest, payload=payload)
