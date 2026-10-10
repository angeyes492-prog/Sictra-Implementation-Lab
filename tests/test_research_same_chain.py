"""Independent expected values and hostile mutation for same-chain review."""
import unittest
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from sictra_block1.research_acquisition import ResearchAcquisitionError, ResearchQuarantine, STATISTICS_RECIPE
from sictra_block1.research_same_chain import SameChainReview, main
from sictra_block1.research_statbel import DATA_RECIPE, StatbelResearchQuarantine
import test_agent_research_acquisition as euro_fixture
import test_research_statbel as statbel_fixture
from test_research_statistics import dataset, raw


class SameChainReviewTests(unittest.TestCase):
    def setUp(self):
        self.euro = euro_fixture.AcquisitionTests(); self.euro.setUp(); self.addCleanup(self.euro.tearDown)
        self.statbel = statbel_fixture.StatbelAcquisitionTests(); self.statbel.setUp(); self.addCleanup(self.statbel.tearDown)
        self.now = euro_fixture.NOW
        euro_terms = self.euro.terms()
        self.euro_terms = euro_terms
        data = dataset()
        data["dimension"]["time"]["category"]["index"] = {"2023": 0, "2024": 1}
        data["value"], data["status"] = [272698.25, 274369.05], [None, None]
        euro_body = raw(data)
        self.euro.response = euro_fixture.Response(euro_body, headers=[
            ("Content-Type", "application/json"), ("Content-Length", str(len(euro_body)))])
        self.euro_id = self.euro.session.acquire(STATISTICS_RECIPE, terms_candidate_id=euro_terms)["candidate_id"]
        statbel_terms = self.statbel.terms()
        self.statbel.response = statbel_fixture.Response(statbel_fixture.TABLE)
        self.statbel_id = self.statbel.session.acquire(DATA_RECIPE, terms_candidate_id=statbel_terms)["candidate_id"]
        self.review = SameChainReview(ResearchQuarantine(self.euro.root), self.euro_id,
            StatbelResearchQuarantine(self.statbel.root), self.statbel_id, clock=lambda: self.now)

    def test_reopen_exact_values_decimal_gaps_and_no_authority(self):
        report = self.review.read()
        self.assertEqual([("2023", "272987", "272698.25", "288.75"),
                          ("2024", "274894", "274369.05", "524.95")],
            [(str(row["year"]), row["statbel_sum_thousand_tonnes"],
              row["eurostat_thousand_tonnes"], row["numeric_gap_thousand_tonnes"])
             for row in report["rows"]])
        self.assertEqual("NOT_ESTABLISHED", report["independent_root"])
        self.assertEqual("UNCONFIRMED", report["comparability"])
        self.assertEqual("NOT_ADMITTED", report["admission"])
        self.assertEqual("NOT_RESOLVED", report["resolution"])
        self.assertEqual("NONE", report["runtime_effect"])
        self.assertEqual(self.euro_id, report["eurostat"]["candidate_id"])
        self.assertEqual(self.statbel_id, report["statbel"]["candidate_id"])
        reopened = SameChainReview(ResearchQuarantine(self.euro.root), self.euro_id,
            StatbelResearchQuarantine(self.statbel.root), self.statbel_id, clock=lambda: self.now)
        self.assertEqual(report, reopened.read())
        reopened.verify_current(report)

    def test_expiry_and_raw_byte_tamper_withdraw_all_measurements(self):
        report = self.review.read()
        self.now = report["expires_at"]
        with self.assertRaises(ResearchAcquisitionError): self.review.read()
        with self.assertRaises(ResearchAcquisitionError): self.review.verify_current(report)
        self.now = euro_fixture.NOW
        (Path(self.statbel.root) / self.statbel_id / "content.bin").write_bytes(statbel_fixture.TABLE + b"changed")
        with self.assertRaises(ResearchAcquisitionError): self.review.read()
        with self.assertRaises(ResearchAcquisitionError): self.review.verify_current(report)

    def test_substituted_terms_wrong_ids_and_report_forgery_reject(self):
        report = self.review.read()
        with self.assertRaises(ResearchAcquisitionError):
            SameChainReview(ResearchQuarantine(self.euro.root), self.statbel_id,
                StatbelResearchQuarantine(self.statbel.root), self.euro_id, clock=lambda: self.now).read()
        forged = dict(report); forged["independent_root"] = "ESTABLISHED"
        with self.assertRaises(ResearchAcquisitionError): self.review.verify_current(forged)
        (Path(self.euro.root) / report["eurostat"]["terms_candidate_id"] / "content.bin").write_bytes(b"forged")
        with self.assertRaises(ResearchAcquisitionError): self.review.read()

    def test_clock_crosses_expiry_during_read(self):
        clock = iter([euro_fixture.NOW, euro_fixture.NOW + 86400])
        review = SameChainReview(ResearchQuarantine(self.euro.root), self.euro_id,
            StatbelResearchQuarantine(self.statbel.root), self.statbel_id, clock=lambda: next(clock))
        with self.assertRaises(ResearchAcquisitionError): review.read()

    def test_missing_eurostat_measurement_cannot_be_compared_as_zero(self):
        data = dataset()
        data["dimension"]["time"]["category"]["index"] = {"2023": 0, "2024": 1}
        data["value"], data["status"] = [272698.25, None], [None, ":"]
        body = raw(data)
        self.euro.response = euro_fixture.Response(body, headers=[
            ("Content-Type", "application/json"), ("Content-Length", str(len(body)))])
        missing_id = self.euro.session.acquire(
            STATISTICS_RECIPE, terms_candidate_id=self.euro_terms)["candidate_id"]
        review = SameChainReview(ResearchQuarantine(self.euro.root), missing_id,
            StatbelResearchQuarantine(self.statbel.root), self.statbel_id, clock=lambda: self.now)
        with self.assertRaisesRegex(ResearchAcquisitionError, "MEASUREMENT_MISSING"):
            review.read()

    def test_publisher_numeric_lexeme_is_not_rounded_through_binary_float(self):
        data = dataset()
        data["dimension"]["time"]["category"]["index"] = {"2023": 0, "2024": 1}
        data["value"], data["status"] = ["EXACT_2023", 274369.05], [None, None]
        body = json.dumps(data).encode().replace(b'"EXACT_2023"', b'272698.24999999999')
        self.euro.response = euro_fixture.Response(body, headers=[
            ("Content-Type", "application/json"), ("Content-Length", str(len(body)))])
        exact_id = self.euro.session.acquire(
            STATISTICS_RECIPE, terms_candidate_id=self.euro_terms)["candidate_id"]
        review = SameChainReview(ResearchQuarantine(self.euro.root), exact_id,
            StatbelResearchQuarantine(self.statbel.root), self.statbel_id, clock=lambda: self.now)
        row = review.read()["rows"][0]
        self.assertEqual("272698.24999999999", row["eurostat_thousand_tonnes"])
        self.assertEqual("288.75000000001", row["numeric_gap_thousand_tonnes"])

    def test_cli_missing_quarantine_root_does_not_create_directory(self):
        with tempfile.TemporaryDirectory() as parent:
            missing = Path(parent) / "missing-eurostat"
            argv = ["research_same_chain", "--eurostat-root", str(missing),
                    "--eurostat-id", self.euro_id, "--statbel-root", str(self.statbel.root),
                    "--statbel-id", self.statbel_id]
            with patch.object(sys, "argv", argv):
                with self.assertRaisesRegex(ResearchAcquisitionError, "ROOT_MISSING"):
                    main()
            self.assertFalse(missing.exists())

    def test_gap_subtraction_preserves_more_than_default_decimal_precision(self):
        data = dataset()
        data["dimension"]["time"]["category"]["index"] = {"2023": 0, "2024": 1}
        data["value"], data["status"] = ["EXACT_2023", 274369.05], [None, None]
        literal = b"272698.249999999999999999999999999"
        body = json.dumps(data).encode().replace(b'"EXACT_2023"', literal)
        self.euro.response = euro_fixture.Response(body, headers=[
            ("Content-Type", "application/json"), ("Content-Length", str(len(body)))])
        exact_id = self.euro.session.acquire(
            STATISTICS_RECIPE, terms_candidate_id=self.euro_terms)["candidate_id"]
        review = SameChainReview(ResearchQuarantine(self.euro.root), exact_id,
            StatbelResearchQuarantine(self.statbel.root), self.statbel_id, clock=lambda: self.now)
        row = review.read()["rows"][0]
        fraction = literal.split(b".")[1]
        scale = 10 ** len(fraction)
        expected = 272987 * scale - (272698 * scale + int(fraction))
        expected_gap = f"{expected // scale}.{expected % scale:0{len(fraction)}d}"
        self.assertEqual(literal.decode(), row["eurostat_thousand_tonnes"])
        self.assertEqual(expected_gap, row["numeric_gap_thousand_tonnes"])

    def test_extreme_underflowing_publisher_exponent_is_rejected(self):
        data = dataset()
        data["dimension"]["time"]["category"]["index"] = {"2023": 0, "2024": 1}
        data["value"], data["status"] = ["EXACT_2023", 274369.05], [None, None]
        body = json.dumps(data).encode().replace(b'"EXACT_2023"', b'1e-999999999')
        self.euro.response = euro_fixture.Response(body, headers=[
            ("Content-Type", "application/json"), ("Content-Length", str(len(body)))])
        extreme_id = self.euro.session.acquire(
            STATISTICS_RECIPE, terms_candidate_id=self.euro_terms)["candidate_id"]
        review = SameChainReview(ResearchQuarantine(self.euro.root), extreme_id,
            StatbelResearchQuarantine(self.statbel.root), self.statbel_id, clock=lambda: self.now)
        with self.assertRaisesRegex(ResearchAcquisitionError, "EXACT_VALUE_INVALID"):
            review.read()
