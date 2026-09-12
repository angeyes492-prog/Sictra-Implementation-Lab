import http.client
from html.parser import HTMLParser
import json
from pathlib import Path
import threading
import unittest

from sictra_block3_precision.precision_console_web import create_server, synthetic_workspace


class _Parser(HTMLParser):
    def __init__(self): super().__init__(); self.tags=[]; self.attrs=[]
    def handle_starttag(self, tag, attrs): self.tags.append(tag); self.attrs.append((tag, dict(attrs)))


class PrecisionConsoleTests(unittest.TestCase):
    def setUp(self):
        self.server=create_server(port=0); self.thread=threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start()
    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2)
    def request(self, method, path, headers=None):
        c=http.client.HTTPConnection("127.0.0.1",self.server.server_port,timeout=2); c.request(method,path,headers=headers or {}); r=c.getresponse(); result=(r.status,dict(r.getheaders()),r.read()); c.close(); return result

    def test_workspace_is_explicit_synthetic_non_authority(self):
        status,headers,body=self.request("GET","/api/workspace"); payload=json.loads(body)
        self.assertEqual(200,status); self.assertEqual("no-store",headers["Cache-Control"])
        self.assertEqual("SYNTHETIC_DETERMINISTIC_NOT_EVIDENCE",payload["fixture"])
        self.assertEqual("NOT_ACCEPTED",payload["authority"]["acceptance"])
        self.assertEqual("PROHIBITED",payload["authority"]["delivery"])
        self.assertEqual("REVIEW_REQUIRED",payload["signals"][0]["state"])

    def test_static_security_and_loopback_binding(self):
        status,headers,_=self.request("GET","/"); self.assertEqual(200,status)
        self.assertIn("frame-ancestors 'none'",headers["Content-Security-Policy"])
        status,headers,body=self.request("GET","/favicon.svg"); self.assertEqual(200,status)
        self.assertEqual("image/svg+xml",headers["Content-Type"]); self.assertIn(b"SICTrA Precision",body)
        with self.assertRaisesRegex(ValueError,"127.0.0.1"): create_server(host="0.0.0.0",port=0)

    def test_host_origin_cross_site_and_mutations_fail_closed(self):
        self.assertEqual(403,self.request("GET","/health",{"Host":"attacker.invalid"})[0])
        self.assertEqual(403,self.request("GET","/health",{"Origin":"https://attacker.invalid"})[0])
        self.assertEqual(403,self.request("GET","/health",{"Sec-Fetch-Site":"cross-site"})[0])
        status,_,body=self.request("POST","/api/workspace"); self.assertEqual(405,status); self.assertIn("sólo lectura",json.loads(body)["error"])

    def test_loader_failure_does_not_become_empty_success(self):
        other=create_server(port=0,workspace_loader=lambda: (_ for _ in ()).throw(RuntimeError("secret path")))
        thread=threading.Thread(target=other.serve_forever,daemon=True); thread.start()
        try:
            c=http.client.HTTPConnection("127.0.0.1",other.server_port,timeout=2); c.request("GET","/api/workspace"); r=c.getresponse(); body=r.read(); c.close()
            self.assertEqual(409,r.status); self.assertNotIn(b"secret path",body); self.assertIn("verificarse",json.loads(body)["error"])
        finally: other.shutdown(); other.server_close(); thread.join(timeout=2)

    def test_markup_exposes_four_views_suite_links_and_accessibility(self):
        root=Path(__file__).parents[1]/"src"/"sictra_block3_precision"/"precision_console"; html=(root/"index.html").read_text(encoding="utf-8"); parser=_Parser(); parser.feed(html)
        self.assertIn("main",parser.tags); self.assertIn("nav",parser.tags); self.assertEqual(4,html.count('data-view="'))
        self.assertIn("http://127.0.0.1:8765/",html); self.assertIn("http://127.0.0.1:8766/",html)
        self.assertTrue(any(a.get("role")=="alert" for _,a in parser.attrs)); self.assertFalse(any(t=="style" for t in parser.tags))
        self.assertTrue(all(a.get("type") in {"button","submit"} for t,a in parser.attrs if t=="button"))

    def test_css_and_js_preserve_accessibility_and_escape_untrusted_values(self):
        root=Path(__file__).parents[1]/"src"/"sictra_block3_precision"/"precision_console"; css=(root/"app.css").read_text(); js=(root/"app.js").read_text()
        for token in (":focus-visible","prefers-reduced-motion:reduce","forced-colors:active","min-height:44px","[hidden]{display:none!important}"): self.assertIn(token,css)
        self.assertIn("replace(/[&<>'\"]",js)
        for unsafe_interpolation in ("${a.account_id}", "${s.value}", "${v}"):
            self.assertNotIn(unsafe_interpolation, js)
        self.assertEqual("BLOCK3_LOCAL_PRECISION_CONSOLE_READ_MODEL",synthetic_workspace()["scope"])

    def test_polish_exposes_account_context_guidance_and_refresh_recovery(self):
        root=Path(__file__).parents[1]/"src"/"sictra_block3_precision"/"precision_console"
        html=(root/"index.html").read_text(encoding="utf-8")
        css=(root/"app.css").read_text(encoding="utf-8")
        js=(root/"app.js").read_text(encoding="utf-8")

        self.assertIn('id="account-context"',html)
        for element_id in ("context-tenant","context-account","context-evidence","context-disposition"):
            self.assertIn(f'id="{element_id}"',html)
        self.assertIn('id="view-guidance"',html)
        self.assertIn('id="view-next-step"',html)
        self.assertIn('id="refresh-status" class="sr-only" role="status" aria-live="polite" aria-atomic="true"',html)
        self.assertIn('id="retry"',html)
        self.assertIn('aria-busy="false"',html)
        self.assertIn("Evidencia actualizada; ninguna señal fue aceptada.",js)
        self.assertIn("No se realizó contacto, delivery ni escritura en CRM.",js)
        self.assertIn("Sin señales gobernadas",js)
        self.assertIn("Sin controles declarados",js)
        self.assertIn("clearWorkspace",js)
        self.assertIn('[data-evidence-state="stale"]',css)
        self.assertIn(".route-step.current",css)

    def test_empty_collections_remain_explicit_non_authority(self):
        payload=synthetic_workspace(); payload["signals"]=[]; payload["controls"]=[]
        other=create_server(port=0,workspace_loader=lambda: payload)
        thread=threading.Thread(target=other.serve_forever,daemon=True); thread.start()
        try:
            c=http.client.HTTPConnection("127.0.0.1",other.server_port,timeout=2)
            c.request("GET","/api/workspace"); r=c.getresponse(); body=json.loads(r.read()); c.close()
            self.assertEqual(200,r.status)
            self.assertEqual([],body["signals"])
            self.assertEqual([],body["controls"])
            self.assertEqual("NOT_ACCEPTED",body["authority"]["acceptance"])
        finally: other.shutdown(); other.server_close(); thread.join(timeout=2)


if __name__ == "__main__": unittest.main()
