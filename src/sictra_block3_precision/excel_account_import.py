"""Strict, read-only ingestion of account seeds from an XLSX workbook.

An XLSX file is untrusted input.  This adapter extracts a narrow account-seed
schema, preserves source lineage, and returns declarations for review.  It
does not crawl, persist, contact, or promote workbook values to facts.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import posixpath
import re
from typing import Literal
from urllib.parse import urlsplit
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from .account_knowledge import AccountSeed
from .contracts import EvidenceRef, PrecisionContractViolation, fingerprint, require_text


_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_CELL_REF = re.compile(r"^([A-Z]+)([1-9][0-9]*)$")
_HEADER_ALIASES = {
    "account_id": "account_id", "account id": "account_id", "id cuenta": "account_id",
    "id de cuenta": "account_id",
    "official_url": "official_url", "official url": "official_url", "official website": "official_url",
    "website": "official_url", "url oficial": "official_url", "sitio web oficial": "official_url",
    "pagina web oficial": "official_url", "página web oficial": "official_url",
    "company_name": "company_name", "company name": "company_name", "nombre empresa": "company_name",
    "nombre de empresa": "company_name",
    "source_reference": "source_reference", "source reference": "source_reference",
    "referencia fuente": "source_reference", "referencia de fuente": "source_reference",
}
_REQUIRED_COLUMNS = frozenset(("account_id", "official_url"))
_OPTIONAL_COLUMNS = frozenset(("company_name", "source_reference"))
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _xml_root(raw: bytes, *, label: str) -> ElementTree.Element:
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise PrecisionContractViolation(f"{label} contains prohibited XML declarations")
    try:
        return ElementTree.fromstring(raw)
    except ElementTree.ParseError as error:
        raise PrecisionContractViolation(f"{label} is invalid XML") from error


def _column_index(reference: str) -> int:
    match = _CELL_REF.fullmatch(reference)
    if match is None:
        raise PrecisionContractViolation("worksheet cell reference is invalid")
    number = 0
    for character in match.group(1):
        number = number * 26 + ord(character) - ord("A") + 1
    return number - 1


def _header(value: str) -> str | None:
    normalized = " ".join(value.casefold().replace("_", " ").replace("-", " ").split())
    return _HEADER_ALIASES.get(normalized)


def _cell_text(value: str, *, policy: "ExcelAccountImportPolicy") -> str:
    value = " ".join(value.split()).strip()
    if _CONTROL.search(value) or len(value) > policy.max_cell_characters:
        raise PrecisionContractViolation("workbook cell exceeds safe text policy")
    return value


@dataclass(frozen=True, slots=True)
class ExcelAccountImportPolicy:
    policy_id: str
    authority_reference: str
    sheet_name: str = "Accounts"
    max_workbook_bytes: int = 5_000_000
    max_zip_entries: int = 80
    max_uncompressed_bytes: int = 20_000_000
    max_compression_ratio: int = 100
    max_rows: int = 2_000
    max_columns: int = 4
    max_cell_characters: int = 2_048

    def __post_init__(self) -> None:
        for name in ("policy_id", "authority_reference", "sheet_name"):
            require_text(name, getattr(self, name))
        for name in (
            "max_workbook_bytes", "max_zip_entries", "max_uncompressed_bytes",
            "max_compression_ratio", "max_rows", "max_columns", "max_cell_characters",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise PrecisionContractViolation(f"{name} must be a positive integer")
        if self.max_rows > 10_000 or self.max_columns > 12 or self.max_workbook_bytes > 20_000_000:
            raise PrecisionContractViolation("Excel import policy exceeds bounded shadow limits")


@dataclass(frozen=True, slots=True)
class ImportedAccountSeed:
    seed: AccountSeed
    row_number: int
    company_name: str | None
    source_reference: str | None
    evidence: EvidenceRef
    restrictions: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.row_number, int) or self.row_number < 2:
            raise PrecisionContractViolation("imported seed must identify a data row")
        for name in ("company_name", "source_reference"):
            value = getattr(self, name)
            if value is not None:
                require_text(name, value)
        if self.evidence.epistemic_state != "UNCONFIRMED":
            raise PrecisionContractViolation("workbook declarations cannot be elevated to facts")
        object.__setattr__(self, "restrictions", tuple(self.restrictions))


@dataclass(frozen=True, slots=True)
class ExcelImportRejection:
    row_number: int
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.row_number, int) or self.row_number < 1:
            raise PrecisionContractViolation("rejection must identify a workbook row")
        require_text("reason", self.reason)


@dataclass(frozen=True, slots=True)
class ExcelAccountImportBatch:
    import_id: str
    tenant_id: str
    policy_id: str
    source_filename: str
    source_content_hash: str
    imported_at: int
    accepted: tuple[ImportedAccountSeed, ...]
    rejected: tuple[ExcelImportRejection, ...]
    restrictions: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("import_id", "tenant_id", "policy_id", "source_filename", "source_content_hash"):
            require_text(name, getattr(self, name))
        if not isinstance(self.imported_at, int) or self.imported_at < 0:
            raise PrecisionContractViolation("import timestamp is invalid")
        if any(item.seed.tenant_id != self.tenant_id for item in self.accepted):
            raise PrecisionContractViolation("import batch cannot mix tenants")
        object.__setattr__(self, "accepted", tuple(self.accepted))
        object.__setattr__(self, "rejected", tuple(self.rejected))
        object.__setattr__(self, "restrictions", tuple(self.restrictions))

    @property
    def output_fingerprint(self) -> str:
        return fingerprint(self)


class ExcelAccountSeedImporter:
    """Reads a constrained XLSX account sheet without side effects."""

    def __init__(self, *, policy: ExcelAccountImportPolicy) -> None:
        self._policy = policy

    def _open(self, workbook: bytes) -> ZipFile:
        if not isinstance(workbook, bytes) or not workbook:
            raise PrecisionContractViolation("workbook must be non-empty bytes")
        if len(workbook) > self._policy.max_workbook_bytes:
            raise PrecisionContractViolation("workbook exceeds byte policy")
        try:
            archive = ZipFile(BytesIO(workbook))
        except BadZipFile as error:
            raise PrecisionContractViolation("workbook is not a valid XLSX archive") from error
        infos = archive.infolist()
        if "[Content_Types].xml" not in archive.namelist():
            archive.close()
            raise PrecisionContractViolation("workbook lacks XLSX content-type manifest")
        if len(infos) > self._policy.max_zip_entries:
            archive.close()
            raise PrecisionContractViolation("workbook has too many archive entries")
        total_uncompressed = sum(item.file_size for item in infos)
        if total_uncompressed > self._policy.max_uncompressed_bytes:
            archive.close()
            raise PrecisionContractViolation("workbook uncompressed content exceeds policy")
        for item in infos:
            if item.filename.startswith(("/", "\\")) or ".." in item.filename.split("/"):
                archive.close()
                raise PrecisionContractViolation("workbook archive has unsafe path")
            if item.filename.casefold().endswith("vbaProject.bin".casefold()):
                archive.close()
                raise PrecisionContractViolation("macro-enabled workbook content is prohibited")
            if item.file_size and item.compress_size and item.file_size / item.compress_size > self._policy.max_compression_ratio:
                archive.close()
                raise PrecisionContractViolation("workbook compression ratio exceeds policy")
        return archive

    @staticmethod
    def _read(archive: ZipFile, path: str) -> bytes:
        try:
            return archive.read(path)
        except KeyError as error:
            raise PrecisionContractViolation(f"workbook is missing required part {path}") from error

    def _worksheet_path(self, archive: ZipFile) -> str:
        workbook = _xml_root(self._read(archive, "xl/workbook.xml"), label="workbook manifest")
        relationships = _xml_root(self._read(archive, "xl/_rels/workbook.xml.rels"), label="workbook relationships")
        sheet_id = None
        for sheet in workbook.findall(f".//{{{_MAIN_NS}}}sheet"):
            if sheet.attrib.get("name", "").casefold() == self._policy.sheet_name.casefold():
                sheet_id = sheet.attrib.get(f"{{{_REL_NS}}}id")
                break
        if not sheet_id:
            raise PrecisionContractViolation("workbook lacks required Accounts sheet")
        targets = {item.attrib.get("Id"): item.attrib.get("Target", "") for item in relationships.findall(f"{{{_PKG_REL_NS}}}Relationship")}
        target = targets.get(sheet_id)
        if not target:
            raise PrecisionContractViolation("Accounts sheet relationship is missing")
        path = posixpath.normpath(posixpath.join("xl", target.lstrip("/")))
        if not path.startswith("xl/") or ".." in path.split("/"):
            raise PrecisionContractViolation("Accounts sheet relationship is unsafe")
        return path

    def _shared_strings(self, archive: ZipFile) -> tuple[str, ...]:
        if "xl/sharedStrings.xml" not in archive.namelist():
            return ()
        root = _xml_root(self._read(archive, "xl/sharedStrings.xml"), label="shared strings")
        values = []
        for item in root.findall(f"{{{_MAIN_NS}}}si"):
            values.append(_cell_text("".join(item.itertext()), policy=self._policy))
            if len(values) > self._policy.max_rows * self._policy.max_columns:
                raise PrecisionContractViolation("shared string table exceeds bounded import policy")
        return tuple(values)

    def _rows(self, archive: ZipFile) -> tuple[tuple[int, dict[int, tuple[str, bool]]], ...]:
        shared = self._shared_strings(archive)
        root = _xml_root(self._read(archive, self._worksheet_path(archive)), label="Accounts worksheet")
        rows: list[tuple[int, dict[int, tuple[str, bool]]]] = []
        seen_row_numbers: set[int] = set()
        for row in root.findall(f".//{{{_MAIN_NS}}}sheetData/{{{_MAIN_NS}}}row"):
            try:
                number = int(row.attrib.get("r", "0"))
            except ValueError as error:
                raise PrecisionContractViolation("worksheet row reference is invalid") from error
            if number < 1 or number > self._policy.max_rows + 1:
                raise PrecisionContractViolation("worksheet row exceeds bounded import policy")
            if number in seen_row_numbers:
                raise PrecisionContractViolation("worksheet contains duplicate row reference")
            seen_row_numbers.add(number)
            values: dict[int, tuple[str, bool]] = {}
            for cell in row.findall(f"{{{_MAIN_NS}}}c"):
                index = _column_index(cell.attrib.get("r", ""))
                if index >= self._policy.max_columns:
                    raise PrecisionContractViolation("worksheet column exceeds bounded import policy")
                if index in values:
                    raise PrecisionContractViolation("worksheet contains duplicate cell reference")
                formula = cell.find(f"{{{_MAIN_NS}}}f") is not None
                cell_type = cell.attrib.get("t")
                if cell_type == "inlineStr":
                    text = "".join(cell.find(f"{{{_MAIN_NS}}}is").itertext()) if cell.find(f"{{{_MAIN_NS}}}is") is not None else ""
                else:
                    node = cell.find(f"{{{_MAIN_NS}}}v")
                    text = node.text if node is not None and node.text is not None else ""
                    if cell_type == "s" and text:
                        try:
                            text = shared[int(text)]
                        except (ValueError, IndexError) as error:
                            raise PrecisionContractViolation("shared string index is invalid") from error
                values[index] = (_cell_text(text, policy=self._policy), formula)
            rows.append((number, values))
        return tuple(sorted(rows))

    def import_workbook(
        self,
        *,
        tenant_id: str,
        authorized_purpose: str,
        workbook: bytes,
        source_filename: str,
        now: int,
    ) -> ExcelAccountImportBatch:
        require_text("tenant_id", tenant_id)
        require_text("authorized_purpose", authorized_purpose)
        require_text("source_filename", source_filename)
        if "/" in source_filename or "\\" in source_filename or _CONTROL.search(source_filename):
            raise PrecisionContractViolation("source_filename must be a safe basename")
        if not source_filename.casefold().endswith(".xlsx") or source_filename.casefold().endswith(".xlsm"):
            raise PrecisionContractViolation("only non-macro .xlsx workbooks are accepted")
        if not isinstance(now, int) or now < 0:
            raise PrecisionContractViolation("import requires non-negative logical time")
        archive = self._open(workbook)
        try:
            rows = self._rows(archive)
        finally:
            archive.close()
        if not rows or rows[0][0] != 1 or not rows[0][1]:
            raise PrecisionContractViolation("Accounts sheet requires a header row at row 1")
        headers: dict[int, str] = {}
        for index, (value, formula) in rows[0][1].items():
            if formula:
                raise PrecisionContractViolation("header formulas are prohibited")
            canonical = _header(value)
            if canonical is None or canonical in headers.values():
                raise PrecisionContractViolation("Accounts sheet has unsupported or duplicate header")
            headers[index] = canonical
        if _REQUIRED_COLUMNS - set(headers.values()):
            raise PrecisionContractViolation("Accounts sheet is missing required account_id or official_url")
        content_hash = sha256(workbook).hexdigest()
        root = f"excel-workbook:{content_hash}"
        accepted: list[ImportedAccountSeed] = []
        rejected: list[ExcelImportRejection] = []
        seen_accounts: set[str] = set()
        seen_urls: set[str] = set()
        for row_number, row in rows[1:]:
            if not row:
                continue
            unmapped = set(row) - set(headers)
            if any(row[index][0] or row[index][1] for index in unmapped):
                rejected.append(ExcelImportRejection(row_number, "UNMAPPED_COLUMN_VALUE"))
                continue
            values = {name: row.get(index, ("", False)) for index, name in headers.items()}
            if all(not value for value, _ in values.values()):
                continue
            if any(formula for _, formula in values.values()):
                rejected.append(ExcelImportRejection(row_number, "FORMULA_NOT_ALLOWED"))
                continue
            if any(not values[name][0] for name in _REQUIRED_COLUMNS):
                rejected.append(ExcelImportRejection(row_number, "MISSING_REQUIRED_VALUE"))
                continue
            parsed_url = urlsplit(values["official_url"][0])
            if parsed_url.scheme.casefold() != "https" or parsed_url.query or parsed_url.fragment:
                rejected.append(ExcelImportRejection(row_number, "UNSAFE_OFFICIAL_URL"))
                continue
            try:
                seed = AccountSeed(tenant_id, values["account_id"][0], values["official_url"][0], authorized_purpose)
            except PrecisionContractViolation:
                rejected.append(ExcelImportRejection(row_number, "INVALID_ACCOUNT_SEED"))
                continue
            account_key = seed.account_id.casefold()
            if account_key in seen_accounts:
                rejected.append(ExcelImportRejection(row_number, "DUPLICATE_ACCOUNT_ID"))
                continue
            if seed.official_url in seen_urls:
                rejected.append(ExcelImportRejection(row_number, "DUPLICATE_OFFICIAL_URL"))
                continue
            seen_accounts.add(account_key)
            seen_urls.add(seed.official_url)
            identity = sha256(f"{content_hash}:{row_number}:{seed.account_id}:{seed.official_url}".encode("utf-8")).hexdigest()
            evidence = EvidenceRef(
                evidence_id=f"excel-account-seed:{identity}", source_identity=f"EXCEL_WORKBOOK:{source_filename}",
                root_provenance=root, observed_at=now, temporal_state="CURRENT", epistemic_state="UNCONFIRMED",
                confidence="C", provenance_refs=(root, f"row:{row_number}"),
            )
            accepted.append(ImportedAccountSeed(
                seed=seed, row_number=row_number, company_name=values.get("company_name", ("", False))[0] or None,
                source_reference=values.get("source_reference", ("", False))[0] or None, evidence=evidence,
                restrictions=(
                    "READ_ONLY_IMPORT", "WORKBOOK_DECLARATION_NOT_FACT", "NO_CRAWL_EXECUTED",
                    "NO_PERSISTENCE", "NO_CRM_WRITE", "NO_DELIVERY", "TENANT_BOUND_OUTSIDE_WORKBOOK",
                ),
            ))
        return ExcelAccountImportBatch(
            import_id=f"excel-import:{fingerprint((tenant_id, authorized_purpose, self._policy.policy_id, content_hash, accepted, rejected))}",
            tenant_id=tenant_id, policy_id=self._policy.policy_id, source_filename=source_filename,
            source_content_hash=content_hash, imported_at=now, accepted=tuple(accepted), rejected=tuple(rejected),
            restrictions=(
                "SHADOW_IMPORT_ONLY", "NO_CRAWL_EXECUTED", "NO_FACT_PROMOTION", "NO_PERSISTENCE",
                "NO_CRM_WRITE", "NO_DELIVERY", "TENANT_BOUND_OUTSIDE_WORKBOOK",
            ),
        )


