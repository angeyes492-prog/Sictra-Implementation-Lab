"""Agent-only Statbel quarantine: exact recipe, lineage and rejection vectors."""
from contextlib import contextmanager
from hashlib import sha256
import io
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from sictra_block1.research_acquisition import ResearchAcquisitionError, MAX_FILE
from sictra_block1.research_statbel import (
    DATA_RECIPE, TERMS_RECIPE, STATBEL_DATA_URL, STATBEL_TERMS_URL,
    STATBEL_RECIPES, StatbelResearchAcquirer, StatbelResearchQuarantine,
    extract_maritime_table,
)


NOW = 1791000000
TERMS = b"<html><title>CC BY 4.0 | Statbel</title><body>Statbel General terms of use CC BY 4.0 Attribution of source</body></html>"
DATA = (b"<html><title>Sea transport | Statbel</title><body>Sea transport Belgian sea ports "
        b"2023 2024 Cargo loaded Cargo unloaded Source: Statbel</body></html>")
TABLE = (b"<html><body>Sea transport Belgian sea ports Source: Statbel"
         b"<table><tr><th>Sea transport (1997-2025)</th><th>2024</th><th>2023</th></tr>"
         b"<tr><th>Cargo loaded (x 1,000 t)</th><td>128,118</td><td>126,590</td></tr>"
         b"<tr><th>Cargo unloaded (x 1,000 t)</th><td>146,776</td><td>146,397</td></tr>"
         b"</table></body></html>")


def dns(_host, _port, **_kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]


class Response:
    def __init__(self, body=DATA, status=200, headers=None):
        self.status = status
        self.headers = headers if headers is not None else [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Last-Modified", "Wed, 07 Oct 2026 00:00:00 GMT")]
        self.stream = io.BytesIO(body)

    def getheaders(self):
        return self.headers

    def read1(self, amount):
        return self.stream.read(amount)


class StatbelAcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "statbel-quarantine"
        self.now = NOW
        self.response = Response(TERMS)
        self.connections = []

        @contextmanager
        def transport(host, address, path):
            self.connections.append((host, address, path))
            yield self.response

        self.session = StatbelResearchAcquirer(
            self.root, clock=lambda: self.now, resolver=dns, transport=transport)

    def tearDown(self):
        self.temp.cleanup()

    def terms(self):
        self.response = Response(TERMS)
        return self.session.acquire(TERMS_RECIPE)["candidate_id"]

    def test_exact_official_bytes_reopen_rights_and_no_effects(self):
        terms_id = self.terms()
        self.response = Response(DATA)
        receipt = self.session.acquire(DATA_RECIPE, terms_candidate_id=terms_id)
        descriptor, raw = StatbelResearchQuarantine(self.root).read(
            receipt["candidate_id"], now=NOW)
        self.assertEqual(DATA, raw)
        self.assertEqual(sha256(DATA).hexdigest(), descriptor["content_sha256"])
        self.assertEqual(STATBEL_DATA_URL, descriptor["original_url"])
        self.assertEqual(STATBEL_DATA_URL, descriptor["final_url"])
        self.assertEqual(STATBEL_TERMS_URL, descriptor["rights_url"])
        self.assertEqual(terms_id, descriptor["terms_candidate_id"])
        self.assertEqual("UNAVAILABLE", descriptor["publisher_release_extracted"])
        self.assertEqual("UNCONFIRMED", descriptor["root_provenance"])
        self.assertEqual("NOT_ADMITTED", descriptor["admission"])
        self.assertEqual("NONE", descriptor["runtime_effect"])
        self.assertEqual("BLOCKED", descriptor["publication"])
        self.assertEqual(("statbel.fgov.be", "93.184.216.34",
                          "/en/themes/mobility/transport/sea-transport"),
                         self.connections[-1])
        self.assertEqual(2, self.session.budget.attempts)

    def test_distinct_html_versions_retained_without_promotion(self):
        terms_id = self.terms()
        self.response = Response(DATA)
        first = self.session.acquire(DATA_RECIPE, terms_candidate_id=terms_id)
        changed = DATA.replace(b"2024", b"2024 2025")
        self.response = Response(changed)
        second = self.session.acquire(DATA_RECIPE, terms_candidate_id=terms_id)
        self.assertNotEqual(first["candidate_id"], second["candidate_id"])
        self.assertEqual(DATA, self.session.quarantine.read(first["candidate_id"], now=NOW)[1])
        self.assertEqual(changed, self.session.quarantine.read(second["candidate_id"], now=NOW)[1])
        self.assertEqual("NOT_ADMITTED", second["admission"])

    def test_fixed_table_decodes_year_position_and_keeps_observation_literal(self):
        self.assertEqual([
            {"year": 2023, "loaded_thousand_tonnes": 126590,
             "unloaded_thousand_tonnes": 146397, "sum_thousand_tonnes": 272987},
            {"year": 2024, "loaded_thousand_tonnes": 128118,
             "unloaded_thousand_tonnes": 146776, "sum_thousand_tonnes": 274894},
        ], extract_maritime_table(TABLE))

    def test_fixed_table_rejects_duplicate_year_and_duplicate_measurement(self):
        duplicate_year = TABLE.replace(b"<th>2023</th>", b"<th>2023</th><th>2023</th>")
        with self.assertRaisesRegex(ResearchAcquisitionError, "YEAR_COLUMNS_INVALID"):
            extract_maritime_table(duplicate_year)
        duplicate_row = TABLE.replace(b"</table>",
                                      b"<tr><th>Cargo loaded (x 1,000 t)</th>"
                                      b"<td>128,118</td><td>126,590</td></tr></table>")
        with self.assertRaisesRegex(ResearchAcquisitionError, "MEASUREMENT_AMBIGUOUS"):
            extract_maritime_table(duplicate_row)

    def test_fixed_table_rejects_malformed_number_and_mislabelled_unit(self):
        with self.assertRaisesRegex(ResearchAcquisitionError, "VALUE_INVALID"):
            extract_maritime_table(TABLE.replace(b"126,590", b"126,590<script>1</script>"))
        with self.assertRaisesRegex(ResearchAcquisitionError, "MEASUREMENT_MISSING"):
            extract_maritime_table(TABLE.replace(b"Cargo unloaded (x 1,000 t)",
                                            b"Cargo unloaded (tonnes)"))

    def test_terms_identity_and_expiry_reject_before_data_request(self):
        with self.assertRaisesRegex(ResearchAcquisitionError, "ID_INVALID"):
            self.session.acquire(DATA_RECIPE)
        terms_id = self.terms()
        before = len(self.connections)
        with self.assertRaisesRegex(ResearchAcquisitionError, "READ_INVALID"):
            self.session.acquire(DATA_RECIPE, terms_candidate_id="a" * 64)
        self.assertEqual(before, len(self.connections))
        self.now += 86400
        with self.assertRaisesRegex(ResearchAcquisitionError, "CURRENT"):
            self.session.acquire(DATA_RECIPE, terms_candidate_id=terms_id)

    def test_redirect_wrong_media_and_oversize_never_retain(self):
        self.response = Response(TERMS, status=302, headers=[("Location", "http://127.0.0.1/")])
        with self.assertRaisesRegex(ResearchAcquisitionError, "STATUS_REJECTED"):
            self.session.acquire(TERMS_RECIPE)
        self.response = Response(TERMS, headers=[("Content-Type", "application/json")])
        with self.assertRaisesRegex(ResearchAcquisitionError, "MEDIA_REJECTED"):
            self.session.acquire(TERMS_RECIPE)
        self.response = Response(TERMS, headers=[("Content-Type", "text/html"),
                                               ("Content-Length", str(MAX_FILE + 1))])
        with self.assertRaisesRegex(ResearchAcquisitionError, "SIZE_REJECTED"):
            self.session.acquire(TERMS_RECIPE)
        self.assertEqual(3, self.session.budget.attempts)
        self.assertFalse(list(self.root.iterdir()))

    def test_only_fixed_host_paths_public_dns_and_visible_identity(self):
        for forged in ("http://statbel.fgov.be/en/cc-40",
                       "https://statbel.fgov.be.evil.example/en/cc-40",
                       "https://statbel.fgov.be:443/en/cc-40",
                       "https://statbel.fgov.be/en/cc-40#fragment"):
            with self.subTest(forged=forged), patch.dict(STATBEL_RECIPES, {TERMS_RECIPE: forged}):
                with self.assertRaisesRegex(ResearchAcquisitionError, "URL_INVALID"):
                    self.session.acquire(TERMS_RECIPE)
        self.session.resolver = lambda *_args, **_kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]
        with self.assertRaisesRegex(ResearchAcquisitionError, "DNS_NON_PUBLIC"):
            self.session.acquire(TERMS_RECIPE)
        self.session.resolver = dns
        self.response = Response(b"<html><body>Verify you are human</body></html>")
        with self.assertRaisesRegex(ResearchAcquisitionError, "CONTENT_IDENTITY_INVALID"):
            self.session.acquire(TERMS_RECIPE)
        self.assertFalse(list(self.root.iterdir()))

    def test_replay_tamper_and_expired_rights_reject(self):
        terms_id = self.terms()
        self.response = Response(DATA)
        first = self.session.acquire(DATA_RECIPE, terms_candidate_id=terms_id)
        self.response = Response(DATA)
        second = self.session.acquire(DATA_RECIPE, terms_candidate_id=terms_id)
        self.assertEqual(first["candidate_id"], second["candidate_id"])
        self.assertEqual(2, len(list(self.root.iterdir())))
        content = self.root / first["candidate_id"] / "content.bin"
        content.write_bytes(b"altered")
        with self.assertRaisesRegex(ResearchAcquisitionError, "INTEGRITY"):
            self.session.quarantine.read(first["candidate_id"], now=NOW)
        self.now += 86400
        with self.assertRaisesRegex(ResearchAcquisitionError, "CURRENT"):
            self.session.quarantine.read(terms_id, now=self.now)


if __name__ == "__main__":
    unittest.main()
