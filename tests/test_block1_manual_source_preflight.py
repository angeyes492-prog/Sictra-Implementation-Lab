from io import BytesIO
import unittest
from zipfile import ZIP_DEFLATED, ZipFile

from sictra_block1 import (
    ManualSourcePreflightViolation,
    preflight_manual_source_file,
)


def workbook(rows: tuple[tuple[str, ...], ...]) -> bytes:
    xml_rows = []
    for row_index, row in enumerate(rows, start=1):
        cells = "".join(
            f'<c r="{chr(64 + column)}{row_index}" t="inlineStr"><is><t>{value}</t></is></c>'
            for column, value in enumerate(row, start=1)
        )
        xml_rows.append(f'<row r="{row_index}">{cells}</row>')
    sheet = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(xml_rows)}</sheetData></worksheet>'
    ).encode()
    stream = BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as archive:
        archive.writestr("xl/worksheets/sheet1.xml", sheet)
    return stream.getvalue()


class ManualSourcePreflightTests(unittest.TestCase):
    def test_csv_with_header_and_rows_is_ready_but_not_evidence(self):
        result = preflight_manual_source_file(
            "eurostat.csv", b"freq,unit,geo\nA,THS_T,ES51\n"
        )
        self.assertEqual(result["status"], "READY_FOR_SCHEMA_REVIEW")
        self.assertEqual(result["header"], ["freq", "unit", "geo"])
        self.assertEqual(result["detected_table_rows"], 2)
        self.assertEqual(result["detected_data_rows"], 1)
        self.assertEqual(result["evidence_state"], "NOT_EVIDENCE")

    def test_xlsx_requires_a_header_and_data_row(self):
        empty = preflight_manual_source_file(
            "eurostat.xlsx", workbook((("Data extracted from ESTAT",),))
        )
        ready = preflight_manual_source_file(
            "eurostat.xlsx", workbook((("freq", "unit"), ("A", "THS_T")))
        )
        self.assertEqual(empty["status"], "REJECTED_NOT_EVIDENCE")
        self.assertEqual(empty["reason"], "XLSX_HAS_NO_TABULAR_DATA")
        self.assertEqual(ready["status"], "READY_FOR_SCHEMA_REVIEW")
        self.assertEqual(ready["detected_table_rows"], 2)

    def test_unsafe_and_inconsistent_payloads_fail_closed(self):
        with self.assertRaises(ManualSourcePreflightViolation):
            preflight_manual_source_file("..\\eurostat.csv", b"a,b\n1,2\n")
        with self.assertRaises(ManualSourcePreflightViolation):
            preflight_manual_source_file("../eurostat.csv", b"a,b\n1,2\n")
        inconsistent = preflight_manual_source_file("eurostat.csv", b"a,b\n1,2,3\n")
        self.assertEqual(inconsistent["reason"], "CSV_ROWS_HAVE_INCONSISTENT_WIDTH")
        bomb = BytesIO()
        with ZipFile(bomb, "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/worksheets/sheet1.xml", b"x" * 1_100_000)
        expanded = preflight_manual_source_file("eurostat.xlsx", bomb.getvalue())
        self.assertEqual(expanded["reason"], "XLSX_ARCHIVE_LIMIT_EXCEEDED")


if __name__ == "__main__":
    unittest.main()
