"""Local-only web interface for the bounded Block 1 test laboratory."""

from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import webbrowser
from typing import Any

from .lab import LAB_SCOPE, SCENARIOS, execute_scenario

UI_SCOPE = "BLOCK1_LOCAL_INTERACTIVE_LAB_UI"

_PAGE = """<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Telecare OS · Laboratorio interno</title><style>
:root{--ink:#173042;--muted:#607381;--paper:#f3f7f8;--panel:#fff;--line:#d3e0e4;--safe:#1c7754;--block:#a85520;--alert:#ad3333;--blue:#0f607b}*{box-sizing:border-box}body{margin:0;font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--paper);color:var(--ink)}main{max-width:880px;margin:0 auto;padding:42px 22px 72px}h1{font-size:clamp(1.7rem,4vw,2.6rem);margin:0 0 4px}h2{margin-top:0;font-size:1.15rem}.eyebrow{color:var(--blue);font-weight:700;letter-spacing:.08em;text-transform:uppercase;font-size:.75rem}.notice,.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:20px;margin-top:20px}.notice{border-left:5px solid var(--blue)}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}button{font:inherit;text-align:left;border:1px solid #9fb7c0;border-radius:8px;background:#fff;color:var(--ink);cursor:pointer;padding:15px;min-height:70px}button:hover{border-color:var(--blue);background:#f5fbfd}button:focus-visible{outline:3px solid #64b8d7;outline-offset:2px}button:disabled{opacity:.6;cursor:wait}.label{display:block;color:var(--muted);font-size:.82rem;margin-top:3px}#result[hidden]{display:none}.status{border-left:5px solid var(--blue)}.status.good{border-color:var(--safe)}.status.blocked{border-color:var(--block)}.status.unexpected{border-color:var(--alert)}.status p{margin-bottom:0}details{margin-top:16px}pre{overflow:auto;white-space:pre-wrap;font-size:.8rem;background:#edf3f5;padding:14px;border-radius:6px}.actions{margin-top:16px}.actions button{min-height:auto;padding:9px 13px}@media(max-width:600px){.grid{grid-template-columns:1fr}main{padding-top:26px}}
</style></head><body><main><div class="eyebrow">Entorno local de pruebas</div><h1>Telecare OS · Laboratorio interno</h1><p>Bloque 1 · Intelligence</p><aside class="notice"><strong>Sin datos reales ni acciones externas.</strong> Esta pantalla ejecuta casos de prueba locales; no envía mensajes, no consulta fuentes externas y no cambia ningún gate.</aside><section class="card"><h2>Elige una prueba</h2><div class="grid"><button data-scenario="valid">Ejecutar prueba válida<span class="label">Debe registrar un efecto controlado.</span></button><button data-scenario="stale-evidence">Probar evidencia vencida<span class="label">Debe bloquearse sin registrar efecto.</span></button><button data-scenario="missing-authority">Probar falta de autorización<span class="label">Debe bloquearse sin registrar efecto.</span></button><button data-scenario="wrong-scope">Probar alcance incorrecto<span class="label">Debe bloquearse sin registrar efecto.</span></button></div></section><section id="result" class="card status" aria-live="polite" hidden><h2 id="result-title">Resultado</h2><p id="result-message"></p><details><summary>Ver detalle técnico</summary><pre id="detail"></pre></details><div class="actions"><button id="clear" type="button">Limpiar resultado</button></div></section></main><script>
const buttons=[...document.querySelectorAll('[data-scenario]')],result=document.querySelector('#result'),title=document.querySelector('#result-title'),message=document.querySelector('#result-message'),detail=document.querySelector('#detail');function show(kind,heading,text,data){result.hidden=false;result.className='card status '+kind;title.textContent=heading;message.textContent=text;detail.textContent=JSON.stringify(data,null,2);result.scrollIntoView({behavior:'smooth',block:'nearest'})}buttons.forEach(button=>button.addEventListener('click',async()=>{buttons.forEach(item=>item.disabled=true);try{const response=await fetch('/api/scenarios/'+button.dataset.scenario,{method:'POST'});const data=await response.json();if(!response.ok)throw new Error(data.error||'No se pudo ejecutar la prueba.');const summary=data.summary;const kind=summary.status==='COMMITTED'?'good':summary.status==='BLOCKED_CORRECTLY'?'blocked':'unexpected';show(kind,summary.title,summary.message,data)}catch(error){show('unexpected','Resultado inesperado','La prueba no pudo completarse. Revisa el detalle técnico.',{error:String(error)})}finally{buttons.forEach(item=>item.disabled=false)}}));document.querySelector('#clear').addEventListener('click',()=>{result.hidden=true;detail.textContent=''})
</script></body></html>"""


def _summary(report: dict[str, Any]) -> dict[str, str]:
    enforcement = report["result"]["enforcement"]["status"]
    records = report["memory_record_count"]
    scenario = report["scenario"]
    if scenario == "valid" and enforcement == "COMMITTED" and records == 1:
        return {"status": "COMMITTED", "title": "Efecto controlado registrado", "message": "La prueba válida completó un único efecto local y controlado."}
    if scenario != "valid" and enforcement == "NOT_EXECUTED" and records == 0:
        return {"status": "BLOCKED_CORRECTLY", "title": "Bloqueado correctamente", "message": "El sistema no registró ningún efecto ante esta condición de prueba."}
    return {"status": "UNEXPECTED", "title": "Resultado inesperado", "message": "El resultado no cumple el patrón esperado; revisa el detalle técnico."}


class LabWebHandler(BaseHTTPRequestHandler):
    server_version = "SICTrALabWeb/0.1"

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json(HTTPStatus.OK, {"status": "ok", "scope": UI_SCOPE})
            return
        if self.path != "/":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Ruta no disponible."})
            return
        encoded = _PAGE.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self) -> None:
        prefix = "/api/scenarios/"
        if not self.path.startswith(prefix):
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Ruta no disponible."})
            return
        scenario = self.path[len(prefix):]
        if scenario not in SCENARIOS or "/" in scenario:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Escenario no disponible."})
            return
        try:
            report = dict(execute_scenario(scenario, store_path=":memory:"))
            self._send_json(HTTPStatus.OK, {"scope": UI_SCOPE, "lab_scope": LAB_SCOPE, "scenario": scenario, "summary": _summary(report), "report": report})
        except Exception as error:
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Error local del laboratorio: {type(error).__name__}"})


def create_server(*, host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    if host != "127.0.0.1":
        raise ValueError("the internal lab UI may only bind to 127.0.0.1")
    return ThreadingHTTPServer((host, port), LabWebHandler)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true", help="Open the local page in the default browser.")
    args = parser.parse_args()
    server = create_server(port=args.port)
    address = f"http://127.0.0.1:{server.server_port}/"
    print(f"Laboratorio interno disponible en {address}")
    if args.open:
        webbrowser.open(address)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
