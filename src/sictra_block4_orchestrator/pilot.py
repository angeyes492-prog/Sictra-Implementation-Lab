"""Create a fresh labelled local pilot and retain the generated design artifacts."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import argparse
import json
import time
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZIP_DEFLATED

from .operations import initialize
from .operations_store import OperationsError


def pilot_workbook(*, changed=False):
    rows = [
        ("Data extracted on 05/09/2026 06:14:51 from [ESTAT]",),
        ("Dataset:", "Maritime transport of freight by NUTS 2 region [tran_r_mago_nm$defaultview]"),
        ("Last updated:", "07/09/2026 06:14" if changed else "05/09/2026 06:14"), (),
        ("Time frequency [FREQ]", None, "Annual [A]"),
        ("Traffic and transport measurement [TRA_MEAS]", None, "Freight loaded and unloaded [FR_LD_NLD]"),
        ("Unit of measure [UNIT]", None, "Thousand tonnes [THS_T]"), (),
        ("TIME", "TIME", "2020", None, "2021"), ("GEO (Codes)", "GEO (Labels)"),
        ("BE", "Belgium", "14" if changed else "12.5", None, "15.5" if changed else "13.5")]
    xml = []
    for i, row in enumerate(rows, 1):
        cells = ''.join(f'<c r="{chr(64+j)}{i}" t="inlineStr"><is><t>{escape(str(v))}</t></is></c>'
                        for j, v in enumerate(row, 1) if v is not None)
        xml.append(f'<row r="{i}">{cells}</row>')
    data = '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + ''.join(xml) + '</sheetData></worksheet>'
    output = BytesIO()
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        archive.writestr('xl/worksheets/sheet1.xml', data)
    return output.getvalue()


def run_pilot(root):
    root = Path(root)
    if root.exists():
        raise OperationsError("PILOT_REQUIRES_FRESH_PATH")
    service = initialize(root)
    service.store.put("ENV", "data", {"class": "SYNTHETIC_PILOT"}, immutable=True)
    profile = service.store.latest("PROFILE")["logistics-general"]
    service.add_profile({**profile, "id": "pilot-executive", "label": "Dirección · perfil de prueba",
                         "role": "Lectura ejecutiva", "tone": "EXECUTIVE", "depth": "BRIEF"})
    results = []
    for changed in (False, True):
        source = root / ("pilot-change.xlsx" if changed else "pilot-baseline.xlsx")
        data = pilot_workbook(changed=changed)
        source.write_bytes(data)
        service.register_file(source, expected_sha256=sha256(data).hexdigest())
        results.append(service.tick())
    outputs = service.store.latest("OUTPUT")
    if len(outputs) != 2 or any("12.5" not in x["plain_text"] or "14 miles de toneladas" not in x["plain_text"] for x in outputs.values()):
        raise OperationsError("PILOT_OUTPUT_EXPECTATION_FAILED")
    backup = root / "backups" / "pilot-proof"
    service.store.backup(backup)
    restored = service.store.restore(backup, root / "recovery-proof.sqlite")
    if restored.latest("OUTPUT") != outputs:
        raise OperationsError("PILOT_RESTORE_FAILED")
    report = {"scope": "SYNTHETIC_LOCAL_PILOT", "at": int(time.time()), "cycles": results,
              "outputs": [{"id": x["id"], "title": x["adaptation"]["heading"], "html_sha256": x["html_sha256"]} for x in outputs.values()],
              "restore": "VERIFIED", "publication": "BLOCKED", "delivery": "NONE"}
    (root / "pilot-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", required=True, type=Path)
    print(json.dumps(run_pilot(parser.parse_args().state), ensure_ascii=False, indent=2))
