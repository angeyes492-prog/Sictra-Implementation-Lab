"""Retained regional scope evidence, with fixed independent expectations."""
import unittest
from contextlib import contextmanager
from pathlib import Path
import tempfile
from unittest.mock import patch

from sictra_block1.research_acquisition import (
    ResearchAcquirer, ResearchAcquisitionError, ResearchQuarantine,
)
from sictra_block1.regional_methodology import (
    review_regional_methodology, verify_regional_methodology_current,
)
from test_agent_research_acquisition import NOW, Response, dns


SCOPE = ("For the tables presenting maritime data at regional level the same "
         "aggregation method (exclusion of double counting) is applied taking "
         "into account main ports only. Only for these ports (handling more "
         "than one million tonnes of goods or recording more than 200 000 "
         "passenger movements annually) the detailed statistics allow such aggregation.")


def page(text=SCOPE):
    return ('<html><h3><a name="data_descr"></a>Data description</h3><p>'
            + text + '</p></html>').encode()


class RegionalMethodologyTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / "quarantine"
        self.response = Response()
        @contextmanager
        def transport(_host, _address, _path):
            yield self.response
        self.session = ResearchAcquirer(self.root, clock=lambda: NOW,
                                        resolver=dns, transport=transport)
        self.terms = self.session.acquire("EUROSTAT_REUSE_NOTICE")["candidate_id"]
        self.response = Response(page())
        self.candidate = self.session.acquire(
            "EUROSTAT_REGIONAL_MAR_METADATA", terms_candidate_id=self.terms)["candidate_id"]
        self.quarantine = ResearchQuarantine(self.root)

    def test_reopen_reports_literal_main_ports_scope_without_gap_cause_or_effect(self):
        report = review_regional_methodology(self.quarantine, self.candidate, clock=lambda: NOW)
        self.assertEqual(SCOPE, report["section_text"])
        self.assertEqual("data_descr", report["section_anchor"])
        self.assertEqual("EXPLICIT_MAIN_PORTS_ONLY", report["regional_scope_label"])
        self.assertEqual("UNCONFIRMED", report["statbel_scope_equivalence"])
        self.assertEqual("UNCONFIRMED", report["specific_gap_cause"])
        self.assertEqual(self.terms, report["terms_candidate_id"])
        self.assertEqual("NOT_ADMITTED", report["admission"])
        self.assertEqual("NOT_RESOLVED", report["resolution"])
        self.assertEqual("NONE", report["runtime_effect"])
        self.assertEqual(report, review_regional_methodology(
            ResearchQuarantine(self.root), self.candidate, clock=lambda: NOW))
        verify_regional_methodology_current(self.quarantine, self.candidate, report, clock=lambda: NOW)

    def test_missing_duplicate_and_changed_wording_do_not_fabricate_scope(self):
        for body in (b"<html><p>main ports only</p></html>",
                     page() + b'<h3><a name="data_descr"></a></h3><p>again</p>'):
            with self.subTest(body=body[-40:]):
                self.response = Response(body)
                candidate = self.session.acquire(
                    "EUROSTAT_REGIONAL_MAR_METADATA", terms_candidate_id=self.terms)["candidate_id"]
                with self.assertRaises(ResearchAcquisitionError):
                    review_regional_methodology(self.quarantine, candidate, clock=lambda: NOW)
        self.response = Response(page("Maritime regional statistics use ports selected by the source."))
        changed = self.session.acquire(
            "EUROSTAT_REGIONAL_MAR_METADATA", terms_candidate_id=self.terms)["candidate_id"]
        report = review_regional_methodology(self.quarantine, changed, clock=lambda: NOW)
        self.assertEqual("UNCONFIRMED", report["regional_scope_label"])

    def test_negated_scope_sentence_cannot_produce_explicit_main_ports_label(self):
        negated = SCOPE.replace("taking into account main ports only",
                                "not taking into account main ports only")
        self.response = Response(page(negated))
        candidate = self.session.acquire(
            "EUROSTAT_REGIONAL_MAR_METADATA", terms_candidate_id=self.terms)["candidate_id"]
        report = review_regional_methodology(self.quarantine, candidate, clock=lambda: NOW)
        self.assertEqual("UNCONFIRMED", report["regional_scope_label"])

    def test_prefixed_denial_or_struck_statement_cannot_confirm_scope(self):
        variants = (page("It is not true that " + SCOPE),
                    page("<del>" + SCOPE + "</del>"),
                    page().replace(b"</html>",
                        b"<p>This rule no longer applies.</p></html>"))
        for body in variants:
            with self.subTest(body=body[:65]):
                self.response = Response(body)
                candidate = self.session.acquire(
                    "EUROSTAT_REGIONAL_MAR_METADATA", terms_candidate_id=self.terms)["candidate_id"]
                report = review_regional_methodology(self.quarantine, candidate, clock=lambda: NOW)
                self.assertEqual("UNCONFIRMED", report["regional_scope_label"])

    def test_wrong_recipe_expired_rights_and_changed_bytes_reject(self):
        with self.assertRaises(ResearchAcquisitionError):
            review_regional_methodology(self.quarantine, self.terms, clock=lambda: NOW)
        with self.assertRaisesRegex(ResearchAcquisitionError, "NOT_CURRENT"):
            review_regional_methodology(self.quarantine, self.candidate, clock=lambda: NOW + 86400)
        report = review_regional_methodology(self.quarantine, self.candidate, clock=lambda: NOW)
        (self.root / self.terms / "content.bin").write_bytes(b"altered rights")
        with self.assertRaisesRegex(ResearchAcquisitionError, "INTEGRITY"):
            verify_regional_methodology_current(self.quarantine, self.candidate, report, clock=lambda: NOW)

    def test_changed_second_read_and_clock_crossing_expiry_reject(self):
        original = self.quarantine.read
        seen = 0
        def changed(*args, **kwargs):
            nonlocal seen
            descriptor, body = original(*args, **kwargs)
            if args[0] == self.candidate:
                seen += 1
                if seen == 2:
                    return descriptor, body + b"mutation"
            return descriptor, body
        with patch.object(self.quarantine, "read", side_effect=changed):
            with self.assertRaisesRegex(ResearchAcquisitionError, "CHANGED_DURING_READ"):
                review_regional_methodology(self.quarantine, self.candidate, clock=lambda: NOW)
        clock = iter((NOW, NOW, NOW + 86400))
        with self.assertRaises(ResearchAcquisitionError):
            review_regional_methodology(self.quarantine, self.candidate, clock=lambda: next(clock))

    def test_self_sealed_report_cannot_claim_admission(self):
        report = review_regional_methodology(self.quarantine, self.candidate, clock=lambda: NOW)
        forged = {**report, "admission": "APPROVED"}
        with self.assertRaises(ResearchAcquisitionError):
            verify_regional_methodology_current(self.quarantine, self.candidate, forged, clock=lambda: NOW)


if __name__ == "__main__":
    unittest.main()
