from html import escape
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile
import unittest

from sictra_block3_precision.excel_account_import import (
    ExcelAccountImportPolicy,
    ExcelAccountSeedImporter,
)
from sictra_block3_precision.contracts import PrecisionContractViolation


NOW = 2_000_000_000
POLICY = ExcelAccountImportPolicy("excel-seed-v1", "authority:excel-import")


def _cell(column, row, value, *, formula=False):
    reference = f"{column}{row}"
    if formula:
        return f'<c r="{reference}"><f>{escape(value)}</f><v>cached</v></c>'
    return f'<c r="{reference}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'


def workbook_bytes(headers, rows, *, malicious_workbook_xml=None, extra_entries=(), row_numbers=None, shared_strings=False):
    shared = []

    def cell(column, row, value, *, formula=False):
        if formula or not shared_strings:
            return _cell(column, row, value, formula=formula)
        try:
            index = shared.index(value)
        except ValueError:
            shared.append(value)
            index = len(shared) - 1
        return f'<c r="{column}{row}" t="s"><v>{index}</v></c>'

    row_xml = ["<row r=\"1\">" + "".join(cell(chr(65 + index), 1, value) for index, value in enumerate(headers)) + "</row>"]
    for position, values in enumerate(rows, start=2):
        row_number = row_numbers[position - 2] if row_numbers else position
        row_xml.append("<row r=\"%s\">%s</row>" % (
            row_number,
            "".join(cell(chr(65 + index), row_number, value[0] if isinstance(value, tuple) else value, formula=isinstance(value, tuple)) for index, value in enumerate(values)),
        ))
    worksheet = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
    <worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"><sheetData>%s</sheetData></worksheet>""" % "".join(row_xml)
    workbook = malicious_workbook_xml or """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
    <workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\"><sheets><sheet name=\"Accounts\" sheetId=\"1\" r:id=\"rId1\"/></sheets></workbook>"""
    relationships = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
    <Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\"><Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet1.xml\"/></Relationships>"""
    stream = BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", relationships)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)
        if shared_strings:
            archive.writestr("xl/sharedStrings.xml", "<sst xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">" + "".join(f"<si><t>{escape(value)}</t></si>" for value in shared) + "</sst>")
        for name, content in extra_entries:
            archive.writestr(name, content)
    return stream.getvalue()


class ExcelAccountImportTests(unittest.TestCase):
    def setUp(self):
        self.importer = ExcelAccountSeedImporter(policy=POLICY)

    def import_file(self, workbook):
        return self.importer.import_workbook(
            tenant_id="tenant-a", authorized_purpose="ACCOUNT_RESEARCH", workbook=workbook,
            source_filename="target-accounts.xlsx", now=NOW,
        )

    def test_imports_governed_seeds_with_unconfirmed_workbook_lineage(self):
        result = self.import_file(workbook_bytes(
            ["Account ID", "Official Website", "Company Name", "Source Reference"],
            [["ACME-01", "https://acme.example/", "ACME Logistics", "sales-list-2026"]],
            shared_strings=True,
        ))
        self.assertEqual(1, len(result.accepted))
        imported = result.accepted[0]
        self.assertEqual("tenant-a", imported.seed.tenant_id)
        self.assertEqual("ACCOUNT_RESEARCH", imported.seed.authorized_purpose)
        self.assertEqual("https://acme.example/", imported.seed.official_url)
        self.assertEqual("UNCONFIRMED", imported.evidence.epistemic_state)
        self.assertIn("NO_CRAWL_EXECUTED", result.restrictions)
        self.assertIn("WORKBOOK_DECLARATION_NOT_FACT", imported.restrictions)

    def test_tenant_and_purpose_cannot_be_supplied_by_workbook_columns(self):
        with self.assertRaises(PrecisionContractViolation):
            self.import_file(workbook_bytes(
                ["Account ID", "Official Website", "tenant_id"],
                [["ACME-01", "https://acme.example/", "tenant-b"]],
            ))

    def test_formula_and_invalid_urls_are_row_rejections_not_silent_imports(self):
        result = self.import_file(workbook_bytes(
            ["Account ID", "Official Website"],
            [[("A1&\"-01\"",), "https://acme.example/"], ["bad-url", "mailto:x@example.test"]],
        ))
        self.assertEqual((), result.accepted)
        self.assertEqual(["FORMULA_NOT_ALLOWED", "UNSAFE_OFFICIAL_URL"], [item.reason for item in result.rejected])

    def test_http_query_and_fragment_urls_are_rejected_before_seed_normalization(self):
        result = self.import_file(workbook_bytes(
            ["Account ID", "Official Website"],
            [["A", "http://a.example/"], ["B", "https://b.example/?token=not-allowed"], ["C", "https://c.example/#fragment"]],
        ))
        self.assertEqual(["UNSAFE_OFFICIAL_URL"] * 3, [item.reason for item in result.rejected])

    def test_filename_is_metadata_not_a_path(self):
        with self.assertRaises(PrecisionContractViolation):
            self.importer.import_workbook(
                tenant_id="tenant-a", authorized_purpose="ACCOUNT_RESEARCH", now=NOW,
                source_filename="folder/accounts.xlsx", workbook=workbook_bytes(["Account ID", "Official Website"], [["A", "https://a.example/"]]),
            )

    def test_duplicate_identity_or_url_is_rejected_deterministically(self):
        result = self.import_file(workbook_bytes(
            ["Account ID", "Official Website"],
            [
                ["Acme-01", "https://acme.example/"],
                ["acme-01", "https://acme-two.example/"],
                ["BETA-01", "https://acme.example/"],
            ],
        ))
        self.assertEqual(1, len(result.accepted))
        self.assertEqual(["DUPLICATE_ACCOUNT_ID", "DUPLICATE_OFFICIAL_URL"], [item.reason for item in result.rejected])

    def test_unknown_or_missing_headers_fail_closed(self):
        with self.assertRaises(PrecisionContractViolation):
            self.import_file(workbook_bytes(["Account ID", "Website", "Contact Email"], [["A", "https://a.example/", "x@a.example"]]))
        with self.assertRaises(PrecisionContractViolation):
            self.import_file(workbook_bytes(["Account ID"], [["A"]]))

    def test_unmapped_cells_are_rejected_and_original_excel_row_is_preserved(self):
        result = self.import_file(workbook_bytes(
            ["Account ID", "Official Website"],
            [["A", "https://a.example/", "hidden@example.test"], ["B", "https://b.example/"]],
            row_numbers=[4, 7],
        ))
        self.assertEqual(["UNMAPPED_COLUMN_VALUE"], [item.reason for item in result.rejected])
        self.assertEqual(7, result.accepted[0].row_number)

    def test_macro_content_and_zip_bombs_are_rejected_before_sheet_read(self):
        with self.assertRaises(PrecisionContractViolation):
            self.import_file(workbook_bytes(
                ["Account ID", "Official Website"], [["A", "https://a.example/"]],
                extra_entries=(("xl/vbaProject.bin", b"macro"),),
            ))
        strict = ExcelAccountSeedImporter(policy=ExcelAccountImportPolicy(
            "excel-seed-strict", "authority:excel-import", max_compression_ratio=2,
        ))
        with self.assertRaises(PrecisionContractViolation):
            strict.import_workbook(
                tenant_id="tenant-a", authorized_purpose="ACCOUNT_RESEARCH", source_filename="accounts.xlsx", now=NOW,
                workbook=workbook_bytes(["Account ID", "Official Website"], [["A", "https://a.example/"]], extra_entries=(("padding.txt", b"x" * 50_000),)),
            )

    def test_xml_declarations_are_rejected_before_parser_expansion(self):
        malicious = """<!DOCTYPE workbook [<!ENTITY xxe SYSTEM \"file:///etc/passwd\">]>
        <workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"/>"""
        with self.assertRaises(PrecisionContractViolation):
            self.import_file(workbook_bytes(["Account ID", "Official Website"], [["A", "https://a.example/"]], malicious_workbook_xml=malicious))


if __name__ == "__main__":
    unittest.main()


