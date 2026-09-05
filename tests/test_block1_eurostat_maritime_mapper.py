from io import BytesIO
from xml.sax.saxutils import escape
import unittest
from zipfile import ZIP_DEFLATED, ZipFile

from sictra_block1 import (
    EurostatMaritimeMappingViolation,
    map_eurostat_maritime_workbook,
    select_eurostat_geography_level,
)


def workbook(*, unit="Thousand tonnes [THS_T]", rows=(("BE", "Belgium", "12.5", None, "13.5"),)) -> bytes:
    content = [
        ("Data extracted on 05/09/2026 06:14:51 from [ESTAT]",),
        ("Dataset:", "Maritime transport of freight by NUTS 2 region [tran_r_mago_nm$defaultview]"),
        ("Last updated:", "05/09/2026 06:14"),
        (),
        ("Time frequency [FREQ]", None, "Annual [A]"),
        ("Traffic and transport measurement [TRA_MEAS]", None, "Freight loaded and unloaded [FR_LD_NLD]"),
        ("Unit of measure [UNIT]", None, unit),
        (),
        ("TIME", "TIME", "2020", None, "2021"),
        ("GEO (Codes)", "GEO (Labels)"),
        *rows,
    ]
    xml_rows = []
    for row_number, row in enumerate(content, start=1):
        cells = "".join(
            f'<c r="{chr(64 + column)}{row_number}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'
            for column, value in enumerate(row, start=1) if value is not None
        )
        xml_rows.append(f'<row r="{row_number}">{cells}</row>')
    sheet = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(xml_rows)}</sheetData></worksheet>'
    ).encode()
    stream = BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as archive:
        archive.writestr("xl/worksheets/sheet1.xml", sheet)
    return stream.getvalue()


class EurostatMaritimeMapperTests(unittest.TestCase):
    def test_maps_declared_grain_but_never_declares_evidence(self):
        result = map_eurostat_maritime_workbook("eurostat.xlsx", workbook())
        self.assertEqual(result["dataset_code"], "tran_r_mago_nm")
        self.assertEqual(result["filters"], {"frequency": "A", "transport_measure": "FR_LD_NLD", "unit": "THS_T"})
        self.assertEqual(result["grain"], ["geo_code", "time_period"])
        self.assertEqual(result["quality"]["observation_count"], 2)
        self.assertEqual(result["quality"]["declared_geography_count"], 1)
        self.assertEqual(result["quality"]["observed_geography_count"], 1)
        self.assertEqual(result["quality"]["all_missing_geography_count"], 0)
        self.assertEqual(result["quality"]["geography_level_counts"], {"COUNTRY": 1})
        self.assertEqual(result["observations"][0]["geo_level"], "COUNTRY")
        self.assertEqual(result["observations"][0]["value_thousand_tonnes"], 12.5)
        self.assertEqual(result["status"], "MAPPED_NOT_EVIDENCE")
        self.assertEqual(result["analysis_state"], "REQUIRES_GEO_LEVEL_SELECTION")
        self.assertEqual(result["evidence_state"], "NOT_EVIDENCE")

    def test_eurostat_colon_is_an_explicit_missing_value_not_zero(self):
        result = map_eurostat_maritime_workbook(
            "eurostat.xlsx", workbook(rows=(("BE", "Belgium", ":", None, "13.5"),))
        )
        self.assertEqual(result["quality"]["missing_value_count"], 1)
        self.assertEqual(result["quality"]["observation_count"], 1)
        self.assertEqual(result["observations"][0]["value_thousand_tonnes"], 13.5)

    def test_geographies_missing_every_period_remain_visible_in_quality(self):
        result = map_eurostat_maritime_workbook(
            "eurostat.xlsx", workbook(rows=(
                ("BE", "Belgium", "12.5", None, "13.5"),
                ("NL", "Netherlands", ":", None, ":"),
            ))
        )
        self.assertEqual(result["quality"]["declared_geography_count"], 2)
        self.assertEqual(result["quality"]["observed_geography_count"], 1)
        self.assertEqual(result["quality"]["all_missing_geography_count"], 1)

    def test_explicit_level_selection_reports_coverage_without_aggregating(self):
        result = select_eurostat_geography_level(
            "eurostat.xlsx", workbook(rows=(
                ("BE", "Belgium", "12.5", None, "13.5"),
                ("BE2", "Vlaams Gewest", "10", None, "11"),
                ("NL", "Netherlands", ":", None, ":"),
            )), "COUNTRY"
        )
        self.assertEqual(result["coverage"], {
            "declared_geography_count": 2,
            "observed_geography_count": 1,
            "all_missing_geography_count": 1,
            "expected_geo_time_cells": 4,
            "observation_count": 2,
            "missing_value_count": 2,
        })
        self.assertTrue(all(item["geo_level"] == "COUNTRY" for item in result["observations"]))
        self.assertEqual(result["status"], "SELECTED_NOT_EVIDENCE")
        with self.assertRaises(EurostatMaritimeMappingViolation):
            select_eurostat_geography_level("eurostat.xlsx", workbook(), "ALL")

    def test_end_of_table_legend_is_not_mapped_as_a_geography(self):
        result = map_eurostat_maritime_workbook(
            "eurostat.xlsx",
            workbook(rows=(
                ("BE", "Belgium", "12.5", None, "13.5"),
                ("Special value",),
                (":", "not available"),
            )),
        )
        self.assertEqual(result["quality"]["legend_row_count"], 2)
        self.assertEqual(result["quality"]["declared_geography_count"], 1)

    def test_unexpected_row_after_legend_fails_closed(self):
        with self.assertRaises(EurostatMaritimeMappingViolation):
            map_eurostat_maritime_workbook(
                "eurostat.xlsx",
                workbook(rows=(
                    ("BE", "Belgium", "12.5", None, "13.5"),
                    ("Special value",),
                    ("unexpected", "row"),
                )),
            )

    def test_wrong_metadata_duplicate_grain_and_invalid_values_fail_closed(self):
        with self.assertRaises(EurostatMaritimeMappingViolation):
            map_eurostat_maritime_workbook("eurostat.xlsx", workbook(unit="Tonnes [T]"))
        with self.assertRaises(EurostatMaritimeMappingViolation):
            map_eurostat_maritime_workbook(
                "eurostat.xlsx", workbook(rows=(("BE", "Belgium", "12", None, "13"), ("BE", "Belgium", "14", None, "15")))
            )
        with self.assertRaises(EurostatMaritimeMappingViolation):
            map_eurostat_maritime_workbook("eurostat.xlsx", workbook(rows=(("BE", "Belgium", "-1", None, "13"),)))


if __name__ == "__main__":
    unittest.main()
