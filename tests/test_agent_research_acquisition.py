from contextlib import contextmanager
from hashlib import sha256
import io
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import Mock, patch

from sictra_block1.research_acquisition import (
    ResearchAcquirer, ResearchQuarantine, ResearchAcquisitionError,
    PinnedHTTPSConnection, public_addresses, RECIPES, MAX_FILE, MAX_SESSION,
    canonical,
)

NOW = 1791000000
BODY = b"<html>Official public metadata fixture, not independent evidence.</html>"


def dns(_host, _port, **_kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]


class Response:
    def __init__(self, body=BODY, status=200, headers=None):
        self.status = status
        self.headers = headers if headers is not None else [
            ("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(body)))]
        self.stream = io.BytesIO(body)

    def getheaders(self):
        return self.headers

    def read1(self, amount):
        return self.stream.read(amount)


class AcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "quarantine"
        self.now = NOW
        self.response = Response()
        self.connections = []
        @contextmanager
        def transport(host, address, path):
            self.connections.append((host, address, path))
            yield self.response
        self.transport = transport
        self.session = ResearchAcquirer(self.root, resolver=dns, transport=transport,
                                        clock=lambda: self.now)

    def tearDown(self):
        self.temp.cleanup()

    def terms(self):
        self.response = Response()
        return self.session.acquire("EUROSTAT_REUSE_NOTICE")["candidate_id"]

    def test_exact_bytes_terms_lineage_reopen_and_no_runtime_authority(self):
        terms = self.terms()
        self.response = Response()
        receipt = self.session.acquire("EUROSTAT_MAR_METADATA", terms_candidate_id=terms)
        descriptor, content = ResearchQuarantine(self.root).read(receipt["candidate_id"], now=NOW)
        self.assertEqual(BODY, content)
        self.assertEqual(sha256(BODY).hexdigest(), descriptor["content_sha256"])
        self.assertEqual("SOURCE_METHODOLOGY", descriptor["need_type"])
        self.assertEqual(terms, descriptor["terms_candidate_id"])
        for key, expected in (("admission", "NOT_ADMITTED"), ("runtime_effect", "NONE"),
                              ("publication", "BLOCKED"), ("root_provenance", "UNCONFIRMED")):
            self.assertEqual(expected, descriptor[key])
        self.assertEqual(["content.bin", "manifest.json"],
                         sorted(p.name for p in (self.root / receipt["candidate_id"]).iterdir()))
        self.assertEqual(("ec.europa.eu", "93.184.216.34", "/eurostat/cache/metadata/EN/mar_esms.htm"),
                         self.connections[-1])

    def test_regional_methodology_uses_exact_official_path_and_current_rights(self):
        terms = self.terms()
        body = b"<html>regional method source bytes</html>"
        self.response = Response(body)
        receipt = self.session.acquire("EUROSTAT_REGIONAL_MAR_METADATA", terms_candidate_id=terms)
        descriptor, reopened = self.session.quarantine.read(receipt["candidate_id"], now=NOW,
            expected_recipe="EUROSTAT_REGIONAL_MAR_METADATA")
        self.assertEqual(body, reopened)
        self.assertEqual(terms, descriptor["terms_candidate_id"])
        self.assertEqual("NOT_ADMITTED", descriptor["admission"])
        self.assertEqual("NONE", descriptor["runtime_effect"])
        self.assertEqual(("ec.europa.eu", "93.184.216.34",
            "/eurostat/cache/metadata/en/tran_r_esms.htm"), self.connections[-1])
        before = len(self.connections)
        self.now = NOW + 86400
        with self.assertRaisesRegex(ResearchAcquisitionError, "NOT_CURRENT"):
            self.session.acquire("EUROSTAT_REGIONAL_MAR_METADATA", terms_candidate_id=terms)
        self.assertEqual(before, len(self.connections))

    def test_replay_same_bytes_same_time_is_idempotent(self):
        original = self.terms()
        self.assertEqual(original, self.terms())
        self.assertEqual(1, len(list(self.root.iterdir())))
        self.assertEqual(2, self.session.budget.attempts)
        self.assertEqual(2 * len(BODY), self.session.budget.received_bytes)

    def test_metadata_requires_current_notice_not_a_metadata_receipt(self):
        with self.assertRaises(ResearchAcquisitionError):
            self.session.acquire("EUROSTAT_MAR_METADATA")
        terms = self.terms()
        self.response = Response()
        metadata = self.session.acquire("EUROSTAT_MAR_METADATA", terms_candidate_id=terms)["candidate_id"]
        before = self.session.budget.attempts
        with self.assertRaisesRegex(ResearchAcquisitionError, "CANDIDATE_TERMS_INVALID"):
            self.session.acquire("EUROSTAT_MAR_METADATA", terms_candidate_id=metadata)
        self.assertEqual(before, self.session.budget.attempts)
        self.now += 86400
        with self.assertRaisesRegex(ResearchAcquisitionError, "NOT_CURRENT"):
            self.session.acquire("EUROSTAT_MAR_METADATA", terms_candidate_id=terms)

    def test_tamper_future_expiry_and_path_rejection(self):
        identity = self.terms()
        for now in (NOW - 1, NOW + 86400):
            with self.assertRaisesRegex(ResearchAcquisitionError, "NOT_CURRENT"):
                self.session.quarantine.read(identity, now=now)
        for bad in ("../escape", "A" * 64, None):
            with self.assertRaisesRegex(ResearchAcquisitionError, "ID_INVALID"):
                self.session.quarantine.read(bad, now=NOW)
        (self.root / identity / "content.bin").write_bytes(b"altered")
        with self.assertRaisesRegex(ResearchAcquisitionError, "INTEGRITY"):
            self.session.quarantine.read(identity, now=NOW)

    def test_self_sealed_admitted_descriptor_cannot_be_retained(self):
        identity = self.terms()
        descriptor, data = self.session.quarantine.read(identity, now=NOW)
        for key, value in (("admission", "APPROVED"), ("runtime_effect", "ATTESTED"),
                           ("root_provenance", "independent"), ("source_id", "new-source")):
            altered = {**descriptor, key: value}
            with self.assertRaisesRegex(ResearchAcquisitionError, "INTEGRITY"):
                self.session.quarantine.retain(altered, data)
        self.assertEqual(1, len(list(self.root.iterdir())))

    def test_manifest_mutation_and_duplicate_fields_are_rejected(self):
        identity = self.terms()
        path = self.root / identity / "manifest.json"
        descriptor = json.loads(path.read_bytes())
        altered = {**descriptor, "expires_at": NOW + 999999}
        path.write_bytes(canonical(altered))
        with self.assertRaisesRegex(ResearchAcquisitionError, "INTEGRITY"):
            self.session.quarantine.read(identity, now=NOW)
        path.write_bytes(canonical(descriptor)[:-1] + b',"version":"0.1.0"}')
        with self.assertRaisesRegex(ResearchAcquisitionError, "READ_INVALID"):
            self.session.quarantine.read(identity, now=NOW)

    def test_private_mixed_reserved_multicast_and_mapped_dns_fail_before_transport(self):
        for ip in ("127.0.0.1", "10.0.0.1", "169.254.169.254", "::1", "::ffff:127.0.0.1", "224.0.0.1", "192.0.2.1"):
            with self.subTest(ip=ip):
                self.session.resolver = lambda *a, **kw: dns(*a, **kw) + [(2, 1, 6, "", (ip, 443))]
                with self.assertRaisesRegex(ResearchAcquisitionError, "DNS_NON_PUBLIC"):
                    self.session.acquire("EUROSTAT_REUSE_NOTICE")
        self.assertFalse(self.connections)
        self.assertFalse(list(self.root.iterdir()))
        self.assertEqual(7, self.session.budget.attempts)

    def test_unknown_recipe_and_changed_host_never_resolve(self):
        self.session.resolver = Mock(side_effect=AssertionError("DNS must not run"))
        with self.assertRaisesRegex(ResearchAcquisitionError, "RECIPE_UNSUPPORTED"):
            self.session.acquire("https://ec.europa.eu/arbitrary")
        for url in ("http://ec.europa.eu/", "https://ec.europa.eu:443/", "https://user@ec.europa.eu/",
                    "https://ec.europa.eu.evil.example/", "https://ec.europa.eu/x#fragment"):
            with patch.dict(RECIPES, {"EUROSTAT_REUSE_NOTICE": url}):
                with self.assertRaisesRegex(ResearchAcquisitionError, "URL_INVALID"):
                    self.session.acquire("EUROSTAT_REUSE_NOTICE")
        self.session.resolver.assert_not_called()

    def test_pinned_connection_uses_numeric_address_and_original_tls_hostname(self):
        connection = PinnedHTTPSConnection("ec.europa.eu", "93.184.216.34")
        raw, wrapped = Mock(), Mock()
        context = Mock()
        context.wrap_socket.return_value = wrapped
        connection._context = context
        with patch("socket.create_connection", return_value=raw) as create:
            connection.connect()
        create.assert_called_once_with(("93.184.216.34", 443), timeout=30)
        context.wrap_socket.assert_called_once_with(raw, server_hostname="ec.europa.eu")
        self.assertIs(wrapped, connection.sock)
        connection.close()

    def test_redirect_denial_and_server_error_are_not_retried_or_retained(self):
        for status in (301, 302, 401, 403, 429, 500):
            self.response = Response(status=status, headers=[("Location", "http://127.0.0.1/")])
            with self.assertRaisesRegex(ResearchAcquisitionError, "STATUS_REJECTED"):
                self.session.acquire("EUROSTAT_REUSE_NOTICE")
        self.assertEqual(6, len(self.connections))
        self.assertEqual(6, self.session.budget.attempts)
        self.assertFalse(list(self.root.iterdir()))

    def test_ambiguous_framing_encoding_media_and_oversize_length_reject(self):
        variants = [
            [("Content-Type", "text/html"), ("Content-Length", "2"), ("content-length", "2")],
            [("Content-Type", "text/html"), ("Content-Encoding", "gzip")],
            [("Content-Type", "application/octet-stream")],
            [("Content-Type", "text/html"), ("Transfer-Encoding", "chunked"), ("Content-Length", "2")],
            [("Content-Type", "text/html"), ("Transfer-Encoding", "gzip")],
            [("Content-Type", "text/html"), ("Content-Length", str(MAX_FILE + 1))],
            [("Content-Type", "text/html"), ("Content-Length", "-2")],
        ]
        for headers in variants:
            with self.subTest(headers=headers):
                self.response = Response(headers=headers)
                with self.assertRaises(ResearchAcquisitionError):
                    self.session.acquire("EUROSTAT_REUSE_NOTICE")
        self.assertFalse(list(self.root.iterdir()))
        self.assertEqual(0, self.session.budget.received_bytes)

    def test_chunked_body_retains_exact_decoded_bytes_and_truncation_spends_budget(self):
        self.response = Response(headers=[("Content-Type", "text/html"), ("Transfer-Encoding", "chunked")])
        receipt = self.session.acquire("EUROSTAT_REUSE_NOTICE")
        self.assertEqual(BODY, self.session.quarantine.read(receipt["candidate_id"], now=NOW)[1])
        before = self.session.budget.received_bytes
        self.response = Response(body=b"short", headers=[("Content-Type", "text/html"), ("Content-Length", "99")])
        with self.assertRaisesRegex(ResearchAcquisitionError, "TRUNCATED"):
            self.session.acquire("EUROSTAT_REUSE_NOTICE")
        self.assertEqual(before + 5, self.session.budget.received_bytes)
        self.assertEqual(1, len(list(self.root.iterdir())))

    def test_stream_limits_and_exhausted_sessions_do_not_create_candidate(self):
        self.response = Response(body=b"x" * (MAX_FILE + 1), headers=[("Content-Type", "text/html")])
        with self.assertRaisesRegex(ResearchAcquisitionError, "SIZE_REJECTED"):
            self.session.acquire("EUROSTAT_REUSE_NOTICE")
        self.assertEqual(MAX_FILE + 1, self.session.budget.received_bytes)
        self.session.budget.received_bytes = MAX_SESSION - 1
        self.response = Response(body=b"ab", headers=[("Content-Type", "text/html")])
        with self.assertRaisesRegex(ResearchAcquisitionError, "SIZE_REJECTED"):
            self.session.acquire("EUROSTAT_REUSE_NOTICE")
        attempts = self.session.budget.attempts
        with self.assertRaisesRegex(ResearchAcquisitionError, "BUDGET_EXHAUSTED"):
            self.session.acquire("EUROSTAT_REUSE_NOTICE")
        self.assertEqual(attempts, self.session.budget.attempts)
        self.assertFalse(list(self.root.iterdir()))

    def test_deadline_terms_expiring_inflight_and_clock_rollback_prevent_persistence(self):
        self.session.monotonic = Mock(side_effect=[0, 30])
        with self.assertRaisesRegex(ResearchAcquisitionError, "DEADLINE"):
            self.session.acquire("EUROSTAT_REUSE_NOTICE")
        self.session.monotonic = __import__("time").monotonic
        terms = self.terms()
        self.now = NOW + 86399
        self.response = Response()
        original_read = self.response.read1
        def advance(amount):
            self.now = NOW + 86400
            return original_read(amount)
        self.response.read1 = advance
        with self.assertRaisesRegex(ResearchAcquisitionError, "NOT_CURRENT"):
            self.session.acquire("EUROSTAT_MAR_METADATA", terms_candidate_id=terms)
        self.now = NOW
        self.response = Response()
        self.session.clock = Mock(side_effect=[NOW, NOW - 1])
        with self.assertRaisesRegex(ResearchAcquisitionError, "CLOCK_OR_DEADLINE"):
            self.session.acquire("EUROSTAT_REUSE_NOTICE")
        self.assertEqual(1, len(list(self.root.iterdir())))

    def test_atomic_failure_leaves_no_selected_candidate_and_retry_recovers(self):
        with patch("sictra_block1.research_acquisition.os.rename", side_effect=OSError("injected interrupted commit")):
            with self.assertRaises(OSError):
                self.terms()
        self.assertFalse(list(self.root.iterdir()))
        identity = self.terms()
        self.assertEqual(BODY, self.session.quarantine.read(identity, now=NOW)[1])

    def test_final_eof_cannot_hide_deadline(self):
        self.session.monotonic = Mock(side_effect=[0, 0, 0, 31])
        with self.assertRaisesRegex(ResearchAcquisitionError, "DEADLINE"):
            self.session.acquire("EUROSTAT_REUSE_NOTICE")
        self.assertFalse(list(self.root.iterdir()))

    def test_symlink_rejects_before_storage_or_read(self):
        with patch("sictra_block1.research_acquisition.Path.is_symlink", return_value=True):
            with self.assertRaisesRegex(ResearchAcquisitionError, "SYMLINK"):
                ResearchQuarantine(Path(self.temp.name) / "linked")
        identity = self.terms()
        with patch("sictra_block1.research_acquisition.Path.is_symlink", return_value=True):
            with self.assertRaisesRegex(ResearchAcquisitionError, "SYMLINK"):
                self.session.quarantine.read(identity, now=NOW)
