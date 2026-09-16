"""Governed local pipeline for normalized Honduras customs period snapshots.

This path is deliberately separate from the Eurostat contract. It accepts only
the owner-supplied HN_CUSTOMS_Q1_V1 workbook shape, retains the exact XLSX bytes,
recomputes reconciliation on every read, and emits a review dossier without
publication or causal interpretation authority.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from hashlib import sha256
import hmac
from io import BytesIO
import json
import math
import os
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from threading import Lock
import time
from typing import Any, Callable, Mapping
from urllib.parse import urlsplit
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from .common import ContractViolation
from .manual_source_preflight import ManualSourcePreflightViolation, preflight_manual_source_file


SOURCE_TYPE = "HN_CUSTOMS_Q1_V1"
SOURCE_ID = "HN_ADUANAS_BULLETINS"
ROOT_SOURCE = "HN_SARAH"
SCOPE = "BLOCK1_LOCAL_HN_CUSTOMS_PERIOD_PIPELINE"
MANIFEST = "manifest.json"
JOURNAL = "journal.json"
SOURCE_URL = "https://www.aduanas.gob.hn/wp-content/uploads/2025/06/1_Boletin_Comercio_Exterior_1T_2025.pdf"
EVIDENCE_MAX_AGE_SECONDS = 86_400
_VERSION = 1
_MAX_RECORDS = 32
_MAX_XLSX_BYTES = 8_388_608
_CELL = re.compile(r"([A-Z]+)([1-9][0-9]*)$")
_SHA = re.compile(r"[0-9a-f]{64}$")
_EXPECTED_SHEETS = frozenset(("DATA", "PROVENANCE", "CHECKS"))
_DATA_HEADER = (
    "record_id", "period_start", "period_end", "reporter", "customs_point",
    "metric", "value", "unit", "source_share_pct", "recalc_share_pct",
    "preliminary", "source_id", "root_source_identity", "evidence_class",
    "source_url", "version_id", "version_kind",
)
_CUSTOMS_POINTS = (
    "Puerto Cortés", "Puesto de Control de Régimen Especial", "Puerto Henecán",
    "La Mesa", "Las Manos", "Resto de Aduanas",
)


class HNCustomsPipelineViolation(ContractViolation):
    """The Honduras customs source cannot safely enter or leave the pipeline."""


def _encoded(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _fingerprint(value: object) -> str:
    return sha256(_encoded(value)).hexdigest()


def _column(reference: object) -> int:
    if not isinstance(reference, str) or (match := _CELL.fullmatch(reference)) is None:
        raise HNCustomsPipelineViolation("XLSX_CELL_REFERENCE_INVALID")
    result = 0
    for char in match.group(1):
        result = result * 26 + ord(char) - ord("A") + 1
    return result


def _local(element: ElementTree.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _shared_strings(archive: ZipFile) -> tuple[str, ...]:
    try:
        raw = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return ()
    if b"<!DOCTYPE" in raw.upper():
        raise HNCustomsPipelineViolation("XLSX_DTD_REJECTED")
    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError as error:
        raise HNCustomsPipelineViolation("XLSX_SHARED_STRINGS_INVALID") from error
    return tuple("".join(node.text or "" for node in item.iter() if _local(node) == "t")
                 for item in root if _local(item) == "si")


def _cell_value(cell: ElementTree.Element, shared: tuple[str, ...]) -> object:
    kind = cell.attrib.get("t")
    if kind == "inlineStr":
        return "".join(node.text or "" for node in cell.iter() if _local(node) == "t")
    raw = next((node.text for node in cell if _local(node) == "v"), None)
    if raw is None:
        return None
    if kind == "s":
        try:
            return shared[int(raw)]
        except (IndexError, ValueError) as error:
            raise HNCustomsPipelineViolation("XLSX_SHARED_STRING_REFERENCE_INVALID") from error
    if kind == "b":
        if raw not in {"0", "1"}:
            raise HNCustomsPipelineViolation("XLSX_BOOLEAN_INVALID")
        return raw == "1"
    if kind in {"str", "e"}:
        return raw
    try:
        number = float(raw)
    except ValueError:
        return raw
    return int(number) if number.is_integer() else number


def _sheet_paths(archive: ZipFile) -> dict[str, str]:
    try:
        workbook_raw = archive.read("xl/workbook.xml")
        relationships_raw = archive.read("xl/_rels/workbook.xml.rels")
    except KeyError as error:
        raise HNCustomsPipelineViolation("XLSX_WORKBOOK_STRUCTURE_MISSING") from error
    if b"<!DOCTYPE" in workbook_raw.upper() or b"<!DOCTYPE" in relationships_raw.upper():
        raise HNCustomsPipelineViolation("XLSX_DTD_REJECTED")
    try:
        workbook = ElementTree.fromstring(workbook_raw)
        relationships = ElementTree.fromstring(relationships_raw)
    except ElementTree.ParseError as error:
        raise HNCustomsPipelineViolation("XLSX_WORKBOOK_STRUCTURE_INVALID") from error
    targets = {item.attrib["Id"]: item.attrib["Target"] for item in relationships
               if "Id" in item.attrib and "Target" in item.attrib}
    result = {}
    for sheet in (node for node in workbook.iter() if _local(node) == "sheet"):
        name = sheet.attrib.get("name")
        relation = next((value for key, value in sheet.attrib.items() if key.endswith("}id") or key == "r:id"), None)
        if not name or relation not in targets:
            raise HNCustomsPipelineViolation("XLSX_SHEET_RELATION_INVALID")
        target = targets[relation].replace("\\", "/").lstrip("/")
        if target.startswith("../") or "/../" in target:
            raise HNCustomsPipelineViolation("XLSX_SHEET_PATH_INVALID")
        result[name] = target if target.startswith("xl/") else "xl/" + target
    return result


def _rows(archive: ZipFile, path: str, shared: tuple[str, ...]) -> tuple[dict[int, object], ...]:
    try:
        raw = archive.read(path)
    except KeyError as error:
        raise HNCustomsPipelineViolation("XLSX_SHEET_MISSING") from error
    if b"<!DOCTYPE" in raw.upper():
        raise HNCustomsPipelineViolation("XLSX_DTD_REJECTED")
    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError as error:
        raise HNCustomsPipelineViolation("XLSX_SHEET_INVALID") from error
    result = []
    for row in (node for node in root.iter() if _local(node) == "row"):
        mapped = {}
        for cell in (node for node in row if _local(node) == "c"):
            value = _cell_value(cell, shared)
            if value is not None:
                mapped[_column(cell.attrib.get("r"))] = value
        if mapped:
            result.append(mapped)
    return tuple(result)


def _text(value: object, label: str, maximum: int = 512) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise HNCustomsPipelineViolation(label + "_INVALID")
    return value.strip()


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise HNCustomsPipelineViolation(label + "_INVALID")
    return float(value)


def parse_hn_customs_workbook(file_name: object, payload: object) -> dict[str, Any]:
    """Parse and independently reconcile the exact normalized customs schema."""

    try:
        preflight = preflight_manual_source_file(file_name, payload)
    except ManualSourcePreflightViolation as error:
        raise HNCustomsPipelineViolation("PREFLIGHT_REJECTED") from error
    if preflight.get("status") != "READY_FOR_SCHEMA_REVIEW" or preflight.get("format") != "XLSX" or not isinstance(payload, bytes):
        raise HNCustomsPipelineViolation("PREFLIGHT_REJECTED")
    try:
        with ZipFile(BytesIO(payload)) as archive:
            shared = _shared_strings(archive)
            paths = _sheet_paths(archive)
            if frozenset(paths) != _EXPECTED_SHEETS:
                raise HNCustomsPipelineViolation("SHEET_INVENTORY_INVALID")
            sheets = {name: _rows(archive, path, shared) for name, path in paths.items()}
    except (BadZipFile, ValueError) as error:
        raise HNCustomsPipelineViolation("XLSX_ARCHIVE_INVALID") from error

    data_rows = sheets["DATA"]
    if (not data_rows or tuple(data_rows[0].get(index) for index in range(1, 18)) != _DATA_HEADER
            or any(any(column > 17 for column in row) for row in data_rows)):
        raise HNCustomsPipelineViolation("DATA_HEADER_INVALID")
    provenance_rows = sheets["PROVENANCE"]
    if not provenance_rows or (provenance_rows[0].get(1), provenance_rows[0].get(2)) != ("field", "value"):
        raise HNCustomsPipelineViolation("PROVENANCE_HEADER_INVALID")
    provenance = {_text(row.get(1), "PROVENANCE_FIELD"): row.get(2) for row in provenance_rows[1:] if row.get(1) is not None}
    required_provenance = {
        "publisher", "source_document", "source_table", "upstream_source", "period_snapshot",
        "version_id", "published_total_usd_mn", "retrieved_at", "version_kind",
    }
    if not required_provenance <= provenance.keys():
        raise HNCustomsPipelineViolation("PROVENANCE_FIELDS_MISSING")
    if (_text(provenance["version_kind"], "VERSION_KIND") != "PERIOD_SNAPSHOT_NORMALIZED"
            or _text(provenance["upstream_source"], "UPSTREAM_SOURCE").split()[0] != "SARAH"):
        raise HNCustomsPipelineViolation("PROVENANCE_SCOPE_INVALID")
    try:
        retrieved_at = date.fromisoformat(_text(provenance["retrieved_at"], "RETRIEVED_AT")).isoformat()
    except ValueError as error:
        raise HNCustomsPipelineViolation("RETRIEVED_AT_INVALID") from error
    published_total = _number(provenance["published_total_usd_mn"], "PUBLISHED_TOTAL")
    version_id = _text(provenance["version_id"], "VERSION_ID", 80)
    snapshot = _text(provenance["period_snapshot"], "PERIOD_SNAPSHOT", 40)

    checks = sheets["CHECKS"]
    check_values = {row.get(1): row.get(2) for row in checks[1:] if isinstance(row.get(1), str)}
    if check_values.get("Schema identity") != SOURCE_TYPE or check_values.get("Root source") != ROOT_SOURCE:
        raise HNCustomsPipelineViolation("CHECK_IDENTITY_INVALID")
    observations = []
    records = set()
    points = []
    periods = set()
    urls = set()
    for row in data_rows[1:]:
        record_id = _text(row.get(1), "RECORD_ID", 100)
        if record_id in records:
            raise HNCustomsPipelineViolation("RECORD_ID_DUPLICATED")
        records.add(record_id)
        period_start = _text(row.get(2), "PERIOD_START", 10)
        period_end = _text(row.get(3), "PERIOD_END", 10)
        try:
            start, end = date.fromisoformat(period_start), date.fromisoformat(period_end)
        except ValueError as error:
            raise HNCustomsPipelineViolation("PERIOD_INVALID") from error
        if start > end or start.year != end.year or (start.month, start.day, end.month, end.day) != (1, 1, 3, 31):
            raise HNCustomsPipelineViolation("PERIOD_SCOPE_INVALID")
        reporter = _text(row.get(4), "REPORTER")
        point = _text(row.get(5), "CUSTOMS_POINT")
        metric = _text(row.get(6), "METRIC")
        value = _number(row.get(7), "VALUE")
        unit = _text(row.get(8), "UNIT")
        preliminary = row.get(11)
        source_id = _text(row.get(12), "SOURCE_ID")
        root_source = _text(row.get(13), "ROOT_SOURCE")
        evidence_class = _text(row.get(14), "EVIDENCE_CLASS")
        source_url = _text(row.get(15), "SOURCE_URL", 1000)
        row_version = _text(row.get(16), "ROW_VERSION_ID")
        row_version_kind = _text(row.get(17), "ROW_VERSION_KIND")
        if (reporter != "Honduras" or metric != "Importaciones CIF" or unit != "USD million"
                or preliminary is not True or source_id != SOURCE_ID or root_source != ROOT_SOURCE
                or evidence_class != "OFFICIAL_ADMINISTRATIVE_DERIVED_TABLE" or row_version != version_id
                or row_version_kind != "PERIOD_SNAPSHOT_NORMALIZED"):
            raise HNCustomsPipelineViolation("OBSERVATION_SCOPE_INVALID")
        parsed = urlsplit(source_url)
        if (parsed.scheme != "https" or parsed.hostname != "www.aduanas.gob.hn" or parsed.username
                or parsed.password or parsed.port is not None or parsed.fragment or parsed.path != urlsplit(SOURCE_URL).path):
            raise HNCustomsPipelineViolation("SOURCE_URL_INVALID")
        share = row.get(9)
        if share is not None:
            share = _number(share, "SOURCE_SHARE")
            if share > 1 or abs(share - value / published_total) > 0.0015:
                raise HNCustomsPipelineViolation("SOURCE_SHARE_INCONSISTENT")
        points.append(point); periods.add((period_start, period_end)); urls.add(source_url)
        observations.append({
            "record_id": record_id, "customs_point": point, "value_usd_million": value,
            "source_share": share, "preliminary": True,
        })
    if (tuple(points) != _CUSTOMS_POINTS or len(periods) != 1 or len(urls) != 1
            or len(observations) != len(_CUSTOMS_POINTS)):
        raise HNCustomsPipelineViolation("OBSERVATION_GRAIN_INVALID")
    period_start, period_end = next(iter(periods))
    if snapshot != period_start[:4] + "Q1" or version_id.split("_", 1)[0] != snapshot:
        raise HNCustomsPipelineViolation("VERSION_PERIOD_MISMATCH")
    normalized_sum = sum(item["value_usd_million"] for item in observations)
    gap = published_total - normalized_sum
    if abs(gap) > 1.0:
        raise HNCustomsPipelineViolation("RECONCILIATION_FAILED")
    core = {
        "schema_version": 1, "source_type": SOURCE_TYPE, "source_id": SOURCE_ID,
        "root_source_identity": ROOT_SOURCE, "source_url": SOURCE_URL,
        "publisher": _text(provenance["publisher"], "PUBLISHER"),
        "source_document": _text(provenance["source_document"], "SOURCE_DOCUMENT"),
        "source_table": _text(provenance["source_table"], "SOURCE_TABLE"),
        "version_id": version_id, "version_kind": "PERIOD_SNAPSHOT_NORMALIZED",
        "period_start": period_start, "period_end": period_end, "retrieved_at": retrieved_at,
        "metric": "Importaciones CIF", "unit": "USD million", "preliminary": True,
        "published_total_usd_million": published_total,
        "normalized_sum_usd_million": normalized_sum, "reconciliation_gap_usd_million": gap,
        "observations": observations, "publication": "BLOCKED", "evidence_state": "MAPPED_NOT_EVIDENCE",
    }
    return {**core, "content_sha256": _fingerprint(core), "raw_sha256": preflight["content_sha256"]}


def _manifest(key: bytes, approved_at: int) -> dict[str, Any]:
    approval = {
        "source_type": SOURCE_TYPE, "source_id": SOURCE_ID, "root_source_identity": ROOT_SOURCE,
        "source_url": SOURCE_URL, "approved_by": "PROJECT_OWNER",
        "approved_at": approved_at, "binding_expires_at": approved_at + 15_552_000,
        "network_acquisition": "DISABLED", "publication": "BLOCKED",
        "approval_evidence": "OWNER_SUPPLIED_LOCAL_XLSX_2026-09-15",
    }
    return {"version": _VERSION, "scope": SCOPE, "approval": approval,
            "approval_fingerprint": _fingerprint(approval),
            "binding_fingerprint": hmac.new(key, b"hn-customs-binding-v1:" + _encoded(approval), sha256).hexdigest(),
            "key_check": hmac.new(key, b"hn-customs-key-v1", sha256).hexdigest()}


def initialize_hn_customs_pipeline(root: str | Path, *, key: bytes, clock: Callable[[], int] = lambda: int(time.time())) -> dict[str, Any]:
    if not isinstance(key, bytes) or len(key) != 32:
        raise HNCustomsPipelineViolation("KEY_INVALID")
    target = Path(root)
    if not target.name or target.is_symlink():
        raise HNCustomsPipelineViolation("STATE_PATH_INVALID")
    now = clock()
    if not isinstance(now, int) or isinstance(now, bool) or now < 0:
        raise HNCustomsPipelineViolation("CLOCK_INVALID")
    target.mkdir(parents=True, exist_ok=True)
    (target / "sources").mkdir(exist_ok=True)
    path = target / MANIFEST
    if path.exists():
        load_hn_customs_pipeline(target, key=key, clock=clock)
        return {"scope": SCOPE, "status": "READY", "reused": True}
    if any(item.name != "sources" for item in target.iterdir()) or any((target / "sources").iterdir()):
        raise HNCustomsPipelineViolation("UNINITIALIZED_STATE_NOT_EMPTY")
    value = _manifest(key, now)
    with path.open("xb") as stream:
        stream.write(_encoded(value))
    return {"scope": SCOPE, "status": "READY", "reused": False}


class HNCustomsPipeline:
    def __init__(self, root: Path, key: bytes, clock: Callable[[], int], manifest: dict[str, Any]) -> None:
        self.root, self.key, self.clock, self.manifest = root, key, clock, manifest
        self.lock = Lock()

    def _record_hash(self, record: Mapping[str, Any]) -> str:
        unsigned = {name: record[name] for name in record if name != "record_hash"}
        return hmac.new(self.key, b"hn-customs-record-v1:" + _encoded(unsigned), sha256).hexdigest()

    def _load(self) -> list[dict[str, Any]]:
        path = self.root / JOURNAL
        if not path.exists():
            return []
        if path.is_symlink():
            raise HNCustomsPipelineViolation("JOURNAL_PATH_INVALID")
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise HNCustomsPipelineViolation("JOURNAL_UNREADABLE") from error
        if not isinstance(document, dict) or set(document) != {"version", "records"} or document["version"] != 1 or not isinstance(document["records"], list) or len(document["records"]) > _MAX_RECORDS:
            raise HNCustomsPipelineViolation("JOURNAL_SCHEMA_INVALID")
        verified, previous_hash, previous_time, raw_hashes, content_hashes = [], "GENESIS", -1, set(), set()
        for record in document["records"]:
            if not isinstance(record, dict) or set(record) != {"observed_at", "raw_sha256", "content_sha256", "source_file", "normalized", "previous_hash", "record_hash"}:
                raise HNCustomsPipelineViolation("JOURNAL_RECORD_INVALID")
            raw_hash = record.get("raw_sha256")
            source = self.root / "sources" / str(record.get("source_file"))
            if (_SHA.fullmatch(str(raw_hash)) is None or record.get("source_file") != raw_hash + ".xlsx"
                    or source.is_symlink() or not source.is_file()):
                raise HNCustomsPipelineViolation("RETAINED_SOURCE_INVALID")
            raw = source.read_bytes()
            parsed = parse_hn_customs_workbook(source.name, raw)
            if (sha256(raw).hexdigest() != raw_hash or parsed != record.get("normalized")
                    or record.get("content_sha256") != parsed["content_sha256"]
                    or raw_hash in raw_hashes or parsed["content_sha256"] in content_hashes
                    or not isinstance(record.get("observed_at"), int) or isinstance(record.get("observed_at"), bool)
                    or record["observed_at"] < previous_time or record.get("previous_hash") != previous_hash
                    or not isinstance(record.get("record_hash"), str)
                    or not hmac.compare_digest(record["record_hash"], self._record_hash(record))):
                raise HNCustomsPipelineViolation("JOURNAL_INTEGRITY_FAILED")
            if verified and parsed["period_start"] <= verified[-1]["normalized"]["period_start"]:
                raise HNCustomsPipelineViolation("PERIOD_ORDER_INVALID")
            verified.append(deepcopy(record)); raw_hashes.add(raw_hash); content_hashes.add(parsed["content_sha256"])
            previous_hash, previous_time = record["record_hash"], record["observed_at"]
        return verified

    def _save(self, records: list[dict[str, Any]]) -> None:
        temporary_name = None
        try:
            with NamedTemporaryFile("wb", dir=self.root, delete=False) as temporary:
                temporary_name = temporary.name
                temporary.write(_encoded({"version": 1, "records": records})); temporary.flush(); os.fsync(temporary.fileno())
            os.replace(temporary_name, self.root / JOURNAL)
        except OSError as error:
            if temporary_name:
                Path(temporary_name).unlink(missing_ok=True)
            raise HNCustomsPipelineViolation("JOURNAL_WRITE_FAILED") from error

    def ingest(self, file_name: str, payload: bytes, *, observed_at: int | None = None) -> dict[str, Any]:
        now = int(self.clock()) if observed_at is None else observed_at
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise HNCustomsPipelineViolation("CLOCK_INVALID")
        approval = self.manifest["approval"]
        if now >= approval["binding_expires_at"]:
            raise HNCustomsPipelineViolation("SOURCE_BINDING_EXPIRED")
        normalized = parse_hn_customs_workbook(file_name, payload)
        raw_hash = sha256(payload).hexdigest()
        if normalized["raw_sha256"] != raw_hash:
            raise HNCustomsPipelineViolation("RAW_HASH_MISMATCH")
        with self.lock:
            records = self._load()
            for record in records:
                if record["raw_sha256"] == raw_hash:
                    return self._receipt(record, records.index(record), replay=True)
                if record["content_sha256"] == normalized["content_sha256"]:
                    raise HNCustomsPipelineViolation("NORMALIZED_CONTENT_REPLAY_DIFFERENT_BYTES")
            if len(records) >= _MAX_RECORDS or (records and now < records[-1]["observed_at"]):
                raise HNCustomsPipelineViolation("CAPACITY_OR_TIME_INVALID")
            if records and normalized["period_start"] <= records[-1]["normalized"]["period_start"]:
                raise HNCustomsPipelineViolation("PERIOD_ORDER_INVALID")
            source = self.root / "sources" / (raw_hash + ".xlsx")
            if source.exists() or source.is_symlink():
                raise HNCustomsPipelineViolation("RETAINED_SOURCE_COLLISION")
            with source.open("xb") as stream:
                stream.write(payload); stream.flush(); os.fsync(stream.fileno())
            record = {"observed_at": now, "raw_sha256": raw_hash,
                      "content_sha256": normalized["content_sha256"], "source_file": source.name,
                      "normalized": normalized, "previous_hash": "GENESIS" if not records else records[-1]["record_hash"],
                      "record_hash": ""}
            record["record_hash"] = self._record_hash(record)
            records.append(record)
            try:
                self._save(records)
            except Exception:
                source.unlink(missing_ok=True)
                raise
            return self._receipt(record, len(records) - 1, replay=False)

    def _receipt(self, record: Mapping[str, Any], index: int, *, replay: bool) -> dict[str, Any]:
        dossier = None if index == 0 else self._dossier_from_pair(self._load()[index - 1], record)
        return {"scope": SCOPE, "status": "BASELINE_ESTABLISHED_NOT_EVIDENCE" if index == 0 else "DELTA_DETECTED_NOT_EVIDENCE",
                "record_hash": record["record_hash"], "raw_sha256": record["raw_sha256"],
                "content_sha256": record["content_sha256"], "replay": replay,
                "dossier": None if dossier is None else {"dossier_id": dossier["dossier_id"],
                    "review_state": dossier["review_state"], "publication_state": dossier["publication_state"]},
                "publication_authority": "NONE"}

    def _dossier_from_pair(self, previous: Mapping[str, Any], current: Mapping[str, Any]) -> dict[str, Any]:
        before, after = previous["normalized"], current["normalized"]
        earlier = {item["customs_point"]: item for item in before["observations"]}
        later = {item["customs_point"]: item for item in after["observations"]}
        if set(earlier) != set(later):
            raise HNCustomsPipelineViolation("CUSTOMS_POINT_SET_CHANGED")
        facts = []
        for point in _CUSTOMS_POINTS:
            old, new = earlier[point]["value_usd_million"], later[point]["value_usd_million"]
            delta = new - old
            if delta == 0:
                continue
            facts.append({"fact_id": f"FACT-{len(facts)+1:03d}",
                "statement": f"Aduanas Honduras registra que las importaciones CIF por {point} cambiaron de {old:g} a {new:g} millones de US$ entre {before['period_start']}–{before['period_end']} y {after['period_start']}–{after['period_end']}.",
                "observed_change": {"customs_point": point, "before_period": before["period_start"][:4] + "Q1",
                    "after_period": after["period_start"][:4] + "Q1", "change_type": "VALUE_CHANGED",
                    "before_value_usd_million": old, "after_value_usd_million": new,
                    "absolute_delta_usd_million": delta,
                    "relative_delta": None if old == 0 else delta / old},
                "evidence_refs": {"source_id": SOURCE_ID, "root_source_identity": ROOT_SOURCE,
                    "previous_raw_sha256": previous["raw_sha256"], "current_raw_sha256": current["raw_sha256"],
                    "current_content_sha256": current["content_sha256"]},
                "certainty": "VERIFIED", "confidence": "B"})
        material = {"previous": previous["content_sha256"], "current": current["content_sha256"], "facts": facts}
        delta_hash = _fingerprint(material)
        return {"schema_version": "HN_CUSTOMS_DOSSIER_V1", "scope": SCOPE,
            "dossier_id": "hn-customs:" + delta_hash,
            "source": {"source_id": SOURCE_ID, "root_source_identity": ROOT_SOURCE,
                "observed_at": current["observed_at"], "content_sha256": current["content_sha256"],
                "raw_sha256": current["raw_sha256"], "previous_raw_sha256": previous["raw_sha256"],
                "delta_sha256": delta_hash, "approval_fingerprint": self.manifest["approval_fingerprint"],
                "binding_fingerprint": self.manifest["binding_fingerprint"]},
            "facts": facts, "interpretations": [], "hypotheses": [],
            "uncertainties": ["Los valores son preliminares y están sujetos a revisión.",
                "Los libros son snapshots normalizados de periodos distintos, no revisiones byte-a-byte del mismo archivo.",
                "No hay corroboración independiente adjunta para explicar causas o impacto comercial."],
            "contradictions": [],
            "limitations": [f"La tabla publicada totaliza {after['published_total_usd_million']:g} millones de US$; las seis filas normalizadas suman {after['normalized_sum_usd_million']:g}, con brecha de {after['reconciliation_gap_usd_million']:g}.",
                "Una diferencia entre periodos no demuestra causalidad ni una revisión de la fuente.",
                "Alcance limitado a importaciones CIF por seis aduanas o grupos en Honduras."],
            "affected_scope": {"customs_points": list(_CUSTOMS_POINTS),
                "periods": [before["period_start"][:4] + "Q1", after["period_start"][:4] + "Q1"]},
            "executive_questions": ["¿Qué parte del cambio corresponde a volumen, precio, tipo de cambio o cobertura administrativa?",
                "¿Qué fuente independiente permitiría corroborar el cambio antes de una decisión comercial?"],
            "next_data_needs": ["Detalle por producto, país de origen y régimen para los mismos periodos.",
                "Una fuente independiente o espejo bilateral con identidad de raíz distinta.",
                "Nota metodológica que explique revisiones y la brecha de reconciliación."],
            "certainty": "UNCONFIRMED", "confidence": "C",
            "review_state": "REQUIRES_HUMAN_INTERPRETATION", "publication_state": "BLOCKED"}

    def list_dossiers(self) -> list[dict[str, Any]]:
        with self.lock:
            records = self._load()
            return [self._dossier_from_pair(records[index - 1], records[index]) for index in range(1, len(records))]

    def export_package(self, dossier_id: str, *, package_key: bytes, now: int) -> dict[str, Any]:
        if not isinstance(package_key, bytes) or len(package_key) < 32:
            raise HNCustomsPipelineViolation("PACKAGE_KEY_INVALID")
        with self.lock:
            records = self._load()
            dossiers = [self._dossier_from_pair(records[index - 1], records[index]) for index in range(1, len(records))]
            matches = [item for item in dossiers if item["dossier_id"] == dossier_id]
            if len(matches) != 1 or not records or matches[0]["source"]["content_sha256"] != records[-1]["content_sha256"]:
                raise HNCustomsPipelineViolation("DOSSIER_NOT_CURRENT")
            dossier = matches[0]
            observed = dossier["source"]["observed_at"]
            expires = min(observed + EVIDENCE_MAX_AGE_SECONDS + 1, self.manifest["approval"]["binding_expires_at"] + 1)
            if now >= expires:
                raise HNCustomsPipelineViolation("DOSSIER_EVIDENCE_NOT_CURRENT")
            identity = sha256((dossier_id + "|" + records[-1]["record_hash"]).encode()).hexdigest()
            package = {"case_id": "CASE-" + identity[:24], "run_id": "RUN-" + identity[24:48],
                "message_id": "MSG-" + identity[8:32], "evidence_id": "hn-customs:" + records[-1]["record_hash"],
                "dossier_id": dossier_id, "producer": "BLOCK1", "contract_version": "0.1.0",
                "source_hash": dossier["source"]["content_sha256"], "provenance_root": ROOT_SOURCE,
                "observed_at": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(observed)),
                "expires_at": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(expires)),
                "currentness": "CURRENT", "certainty": dossier["certainty"],
                "uncertainty": list(dossier["uncertainties"]), "disposition": "REVIEW_REQUIRED",
                "lineage": ["BLOCK1"],
                "payload": {"summary": " ".join(fact["statement"] for fact in dossier["facts"][:3]),
                    "limitations": list(dossier["limitations"]) + ["NO_INTERPRETATION_ADDED"]}}
            package["signature"] = hmac.new(package_key, _encoded(package), sha256).hexdigest()
            return package

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            records = self._load()
            dossiers = [self._dossier_from_pair(records[index - 1], records[index]) for index in range(1, len(records))]
            return {"scope": SCOPE, "status": "READY", "source_id": SOURCE_ID,
                "retained_versions": len(records), "dossier_count": len(dossiers),
                "latest_period": None if not records else records[-1]["normalized"]["period_start"][:4] + "Q1",
                "network_acquisition": "DISABLED", "publication_authority": "NONE"}


def load_hn_customs_pipeline(root: str | Path, *, key: bytes, clock: Callable[[], int] = lambda: int(time.time())) -> HNCustomsPipeline:
    if not isinstance(key, bytes) or len(key) != 32:
        raise HNCustomsPipelineViolation("KEY_INVALID")
    target = Path(root)
    path = target / MANIFEST
    if target.is_symlink() or not target.is_dir() or path.is_symlink() or not path.is_file() or (target / "sources").is_symlink() or not (target / "sources").is_dir():
        raise HNCustomsPipelineViolation("STATE_UNAVAILABLE")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HNCustomsPipelineViolation("MANIFEST_UNREADABLE") from error
    if (not isinstance(manifest, dict) or set(manifest) != {"version", "scope", "approval", "approval_fingerprint", "binding_fingerprint", "key_check"}
            or manifest.get("version") != _VERSION or manifest.get("scope") != SCOPE
            or manifest.get("approval_fingerprint") != _fingerprint(manifest.get("approval"))
            or not hmac.compare_digest(str(manifest.get("key_check")), hmac.new(key, b"hn-customs-key-v1", sha256).hexdigest())
            or not hmac.compare_digest(str(manifest.get("binding_fingerprint")), hmac.new(key, b"hn-customs-binding-v1:" + _encoded(manifest.get("approval")), sha256).hexdigest())):
        raise HNCustomsPipelineViolation("MANIFEST_INTEGRITY_FAILED")
    pipeline = HNCustomsPipeline(target, bytes(key), clock, manifest)
    pipeline._load()
    return pipeline


def ingest_hn_customs_workbook(
    root: str | Path,
    workbook: str | Path,
    *,
    key: bytes,
    clock: Callable[[], int] = lambda: int(time.time()),
) -> dict[str, Any]:
    """Ingest one exact, local, operator-supplied HN customs workbook.

    The wrapper deliberately accepts no URL and performs no network access. It
    rejects links and non-regular paths before the governed parser sees bytes.
    """
    source = Path(workbook)
    if source.is_symlink() or not source.is_file() or source.suffix.lower() != ".xlsx":
        raise HNCustomsPipelineViolation("SOURCE_PATH_INVALID")
    try:
        with source.open("rb") as stream:
            payload = stream.read(_MAX_XLSX_BYTES + 1)
    except OSError as error:
        raise HNCustomsPipelineViolation("SOURCE_UNREADABLE") from error
    if len(payload) > _MAX_XLSX_BYTES:
        raise HNCustomsPipelineViolation("SOURCE_SIZE_EXCEEDED")
    pipeline = load_hn_customs_pipeline(root, key=key, clock=clock)
    return pipeline.ingest(source.name, payload)
