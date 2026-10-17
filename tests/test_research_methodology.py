from unittest.mock import Mock, patch
import io
import json
import unittest

from sictra_block1.research_acquisition import ResearchAcquisitionError, ResearchQuarantine
from sictra_block1.research_methodology import (
    extract_maritime_methodology, review_methodology_candidate, main,
)
import test_agent_research_acquisition as acquisition
from test_agent_research_acquisition import Response, NOW

PARAGRAPHS = {
    "meta_last_update": "15 January 2025", "data_descr": "Gross weight, not monetary imports.",
    "coverage_sector": "Goods at reporting ports.", "coverage_time": "Annual and quarterly series.",
    "rev_policy": "National competent authorities provide revisions.",
    "rev_practice": "Validated reported errors are corrected.",
    "source_type": "National port and administrative sources.", "freq_coll": "Quarterly and annual.",
}


def html_sections(values=PARAGRAPHS):
    return ("<html>" + "".join(f'<h3><a name="{key}"></a>Section</h3><p>{value}</p>'
                               for key, value in values.items()) + "</html>").encode()


class MethodologyTests(unittest.TestCase):
    def test_exact_sections_update_date_and_no_link_follow_or_script_content(self):
        body = html_sections().replace(b"reporting ports", b"reporting <a href='http://127.0.0.1/'>ports</a>")
        body = body.replace(b"</html>", b"<script>execute evil</script><style>hidden</style></html>")
        self.assertEqual(PARAGRAPHS, extract_maritime_methodology(body))

    def test_missing_duplicate_empty_and_script_forged_sections_reject(self):
        variants = [html_sections({key: value for key, value in PARAGRAPHS.items() if key != "rev_policy"}),
                    html_sections() + b'<h3><a name="rev_policy"></a></h3><p>fake duplicate</p>',
                    html_sections({**PARAGRAPHS, "rev_practice": " "}),
                    html_sections({key: value for key, value in PARAGRAPHS.items() if key != "source_type"})
                    + b'<script><h3><a name="source_type"></a></h3><p>fake</p></script>']
        for body in variants:
            with self.subTest(body=body[:30]):
                with self.assertRaises(ResearchAcquisitionError):
                    extract_maritime_methodology(body)

    def test_heading_and_paragraph_shape_size_encoding_are_not_guessed(self):
        variants = [b'\xff', b"x" * (1024 * 1024 + 1), html_sections().replace(b"</p>", b"", 1),
                    html_sections({**PARAGRAPHS, "rev_policy": "x" * 16001}),
                    html_sections().replace(b'<a name="rev_policy">', b'<a name="rev_policy" name="source_type">')]
        for body in variants:
            with self.assertRaises(ResearchAcquisitionError):
                extract_maritime_methodology(body)

    def pipeline(self, values=PARAGRAPHS):
        # Reuse retained-source setup, not the acquisition tests as an oracle.
        fixture = acquisition.AcquisitionTests()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        terms = fixture.terms()
        fixture.response = Response(body=html_sections(values))
        candidate = fixture.session.acquire("EUROSTAT_MAR_METADATA", terms_candidate_id=terms)["candidate_id"]
        return fixture, terms, candidate

    def test_retained_pipeline_review_replays_and_remains_unresolved(self):
        fixture, terms, candidate = self.pipeline()
        before = {str(path): path.read_bytes() for path in fixture.root.rglob("*") if path.is_file()}
        report = review_methodology_candidate(fixture.session.quarantine, candidate, clock=lambda: NOW)
        self.assertEqual(PARAGRAPHS, {section["anchor"]: section["text"] for section in report["sections"]})
        self.assertEqual("15 January 2025", report["publisher_metadata_update_raw"])
        self.assertEqual(NOW, report["acquired_at"])
        self.assertEqual("NOT_RESOLVED", report["resolution"])
        self.assertEqual("NOT_ACCEPTED", report["acceptance"])
        self.assertEqual("UNCONFIRMED", report["specific_change_cause"])
        self.assertEqual("NONE", report["runtime_effect"])
        self.assertEqual(terms, report["terms_candidate_id"])
        self.assertEqual(report, review_methodology_candidate(ResearchQuarantine(fixture.root), candidate, clock=lambda: NOW))
        self.assertEqual(before, {str(path): path.read_bytes() for path in fixture.root.rglob("*") if path.is_file()})

    def test_tampered_stale_foreign_recipe_and_mid_parse_expiry_reject(self):
        fixture, terms, candidate = self.pipeline()
        with self.assertRaises(ResearchAcquisitionError):
            review_methodology_candidate(fixture.session.quarantine, terms, clock=lambda: NOW)
        with self.assertRaises(ResearchAcquisitionError):
            review_methodology_candidate(fixture.session.quarantine, candidate, clock=lambda: NOW + 86400)
        with self.assertRaisesRegex(ResearchAcquisitionError, "NOT_CURRENT"):
            review_methodology_candidate(fixture.session.quarantine, candidate,
                                         clock=Mock(side_effect=[NOW, NOW + 86400]))
        (fixture.root / terms / "content.bin").write_bytes(b"tampered notice")
        with self.assertRaisesRegex(ResearchAcquisitionError, "INTEGRITY"):
            review_methodology_candidate(fixture.session.quarantine, candidate, clock=lambda: NOW)

    def test_changed_second_read_is_rejected_without_result(self):
        fixture, _, candidate = self.pipeline()
        original = fixture.session.quarantine.read
        calls = 0
        def changed(*args, **kwargs):
            nonlocal calls
            value, body = original(*args, **kwargs)
            if args[0] == candidate:
                calls += 1
                if calls == 2:
                    return value, body + b"changed"
            return value, body
        with patch.object(fixture.session.quarantine, "read", side_effect=changed):
            with self.assertRaisesRegex(ResearchAcquisitionError, "CHANGED_DURING_READ"):
                review_methodology_candidate(fixture.session.quarantine, candidate, clock=lambda: NOW)

    def test_cli_preserves_unicode_on_ascii_windows_style_stdout(self):
        fixture, _, candidate = self.pipeline({**PARAGRAPHS, "rev_policy": "Non\u2011breaking policy"})
        raw = io.BytesIO()
        output = io.TextIOWrapper(raw, encoding="ascii")
        with patch("sys.argv", ["review", "--root", str(fixture.root), "--candidate-id", candidate]), \
             patch("sys.stdout", output), \
             patch("sictra_block1.research_methodology.review_methodology_candidate",
                   side_effect=lambda store, identity: review_methodology_candidate(store, identity, clock=lambda: NOW)):
            self.assertEqual(0, main())
            output.flush()
        report = json.loads(raw.getvalue())
        self.assertEqual("Non\u2011breaking policy", next(s["text"] for s in report["sections"] if s["anchor"] == "rev_policy"))
        self.assertEqual("NOT_RESOLVED", report["resolution"])

    def test_report_expires_with_earlier_linked_terms_not_later_metadata(self):
        fixture = acquisition.AcquisitionTests()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        terms = fixture.terms()
        fixture.now = NOW + 100
        fixture.response = Response(body=html_sections())
        candidate = fixture.session.acquire("EUROSTAT_MAR_METADATA", terms_candidate_id=terms)["candidate_id"]
        report = review_methodology_candidate(fixture.session.quarantine, candidate, clock=lambda: NOW + 100)
        self.assertEqual(NOW + 86400, report["expires_at"])
