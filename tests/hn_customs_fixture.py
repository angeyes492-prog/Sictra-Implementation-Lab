from html import escape
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile


SOURCE_URL = "https://www.aduanas.gob.hn/wp-content/uploads/2025/06/1_Boletin_Comercio_Exterior_1T_2025.pdf"
POINTS = (
    "Puerto Cortés", "Puesto de Control de Régimen Especial", "Puerto Henecán",
    "La Mesa", "Las Manos", "Resto de Aduanas",
)
HEADERS = (
    "record_id", "period_start", "period_end", "reporter", "customs_point",
    "metric", "value", "unit", "source_share_pct", "recalc_share_pct",
    "preliminary", "source_id", "root_source_identity", "evidence_class",
    "source_url", "version_id", "version_kind",
)


def _column(index):
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _cell(index, row, value):
    reference = f"{_column(index)}{row}"
    if value is None:
        return ""
    if type(value) is bool:
        return f'<c r="{reference}" t="b"><v>{1 if value else 0}</v></c>'
    if type(value) in (int, float):
        return f'<c r="{reference}"><v>{value}</v></c>'
    return f'<c r="{reference}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'


def _sheet(rows):
    material = []
    for row_number, row in enumerate(rows, 1):
        material.append(f'<row r="{row_number}">' + "".join(
            _cell(index, row_number, value) for index, value in enumerate(row, 1)
        ) + "</row>")
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheetData>' + "".join(material) + '</sheetData></worksheet>')


def workbook(year=2024, *, values=None, total=None, root="HN_SARAH", suffix=""):
    values = values or ((2213.6, 562.3, 387.4, 238.5, 282.1, 997.6) if year == 2024
                        else (2217.8, 647.8, 357.2, 350.3, 261.3, 1068.6))
    total = total if total is not None else (4681.5 if year == 2024 else 4903.7)
    version = f"{year}Q1_v{1 if year == 2024 else 2}"
    data = [HEADERS]
    for index, (point, value) in enumerate(zip(POINTS, values), 1):
        data.append((
            f"HN_IMP_{year}Q1_{index:02d}", f"{year}-01-01", f"{year}-03-31",
            "Honduras", point, "Importaciones CIF", value, "USD million",
            None if year == 2024 else round(value / total, 3), None, True,
            "HN_ADUANAS_BULLETINS", root, "OFFICIAL_ADMINISTRATIVE_DERIVED_TABLE",
            SOURCE_URL, version, "PERIOD_SNAPSHOT_NORMALIZED",
        ))
    provenance = [
        ("field", "value"),
        ("publisher", "Administración Aduanera de Honduras — Gerencia Nacional de Inteligencia"),
        ("source_document", "Boletín de Comercio Exterior 1T 2025"),
        ("source_table", "Tabla 2: Importaciones totales por aduana — Enero a Marzo de 2024-2025"),
        ("upstream_source", "SARAH (según nota del cuadro publicado)"),
        ("period_snapshot", f"{year}Q1"), ("version_id", version),
        ("published_total_usd_mn", total), ("retrieved_at", "2026-09-15"),
        ("version_kind", "PERIOD_SNAPSHOT_NORMALIZED"),
    ]
    checks = [
        ("check", "formula_or_value", "status", "note"),
        ("Published total", total, "REFERENCE", "Official table total."),
        ("Row count", 6, "EXPECTED", "Stable grain."),
        ("Root source", root, "IDENTITY", "Evidence independence."),
        ("Schema identity", "HN_CUSTOMS_Q1_V1", "EXPECTED", "Stable schema."),
    ]
    workbook_xml = ('<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
        '<sheet name="DATA" sheetId="1" r:id="rId1"/>'
        '<sheet name="PROVENANCE" sheetId="2" r:id="rId2"/>'
        '<sheet name="CHECKS" sheetId="3" r:id="rId3"/></sheets></workbook>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1, 4))
        + '</Relationships>')
    stream = BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>" + suffix)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", rels)
        for number, rows in enumerate((data, provenance, checks), 1):
            archive.writestr(f"xl/worksheets/sheet{number}.xml", _sheet(rows))
    return stream.getvalue()
