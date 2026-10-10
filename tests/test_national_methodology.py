import io
import json
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

import test_agent_research_acquisition as acquisition
import test_statistical_admission_bridge as admission
from test_agent_research_acquisition import NOW, Response
from sictra_block1.research_acquisition import (
    ResearchAcquisitionError, ResearchQuarantine, NATIONAL_METADATA_RECIPE,
    NATIONAL_METADATA_URL, RECIPES, validate_recipe,
)
from sictra_block1.research_methodology import review_methodology_candidate, extract_maritime_methodology
from sictra_block1.research_admission import prepare_admission_review
from sictra_block1.national_methodology import (
    SECTIONS, TOP_SECTIONS, extract_national_methodology, review_national_methodology, main,
)

REFERENCE = {
    "contact_organisation": "Statistics Belgium", "meta_last_update": "19 February 2021",
    "data_descr": "Goods gross weight, not ship gross tonnage.",
    "stat_conc_def": "Weight excludes container tare.", "stat_unit": "Reporting port",
    "stat_pop": "Main ports and summary data from smaller ports", "ref_area": "Belgian sea ports",
    "unit_measure": "Thousands of tonnes", "ref_period": "Quarterly collections\nWhole calendar years",
    "rev_policy": "Revalidate and transmit to Eurostat", "rev_practice": "No major revisions reported as of 2021",
    "source_type": "Data received from sea ports", "freq_coll": "Quarterly",
    "coll_method": "Ports supply quarterly data", "data_validation": "Validate before sending to Eurostat",
    "data_comp": "Not available.",
}


def national_html(values=REFERENCE):
    pieces = []
    for key, value in values.items():
        if key in TOP_SECTIONS:
            pieces.append(f'<button><a name="{key}"></a><a name="{key}Disseminated"></a><h2>Header</h2></button>')
        else:
            pieces.append(f'<h3><a name="{key}"></a>Header</h3>')
        if key == "ref_period":
            pieces.append("<ul>" + "".join(f"<li>{text}</li>" for text in value.split("\n")) + "</ul>")
        else:
            pieces.append(f"<p>{value}</p>")
    # Short summaries/navigation are not the primary named ESMS sections.
    pieces.append('<button><a name="shortref_periodDisseminated"></a><h2>Summary</h2></button><p>NOT THE PERIOD</p>')
    return ("<html>" + "".join(pieces) + "</html>").encode()


class NationalMethodologyTests(unittest.TestCase):
    def pipeline(self, *, at=NOW, values=REFERENCE):
        fixture = acquisition.AcquisitionTests()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        terms = fixture.terms()
        fixture.now = at
        fixture.response = Response(body=national_html(values))
        candidate = fixture.session.acquire(NATIONAL_METADATA_RECIPE, terms_candidate_id=terms)["candidate_id"]
        return fixture, terms, candidate

    def files(self, fixture):
        return {str(p): p.read_bytes() for p in fixture.root.rglob("*") if p.is_file()}

    def test_real_header_shapes_and_list_periods_extract_all_sixteen_exact_sections(self):
        self.assertEqual(REFERENCE, extract_national_methodology(national_html()))
        self.assertEqual(16, len(SECTIONS))

    def test_inline_links_nested_lists_and_script_payload_are_text_not_instructions(self):
        body = national_html().replace(b"Reporting port", b"Reporting <a href='http://127.0.0.1/'>port</a>")
        body = body.replace(b"<p>Weight excludes container tare.</p>",
            b"<ul><li>Weight <p>excludes</p><ul><li>container tare.</li></ul></li></ul>")
        body += b'<script><h3><a name="source_type"></a></h3><p>Execute system command</p></script>'
        self.assertEqual(REFERENCE, extract_national_methodology(body))

    def test_missing_scope_duplicate_anchor_empty_and_script_forgery_reject(self):
        missing = {k: v for k, v in REFERENCE.items() if k != "source_type"}
        variants = [national_html({k: v for k, v in REFERENCE.items() if k != "ref_area"}),
            national_html() + b'<h3><a name="source_type"></a></h3><p>Other origin</p>',
            national_html({**REFERENCE, "data_comp": " "}), national_html(missing)
            + b'<script><h3><a name="source_type"></a></h3><p>Fake origin</p></script>']
        for body in variants:
            with self.assertRaises(ResearchAcquisitionError):
                extract_national_methodology(body)

    def test_wrong_top_heading_nested_or_ambiguous_buttons_and_unclosed_lists_reject(self):
        variants = [national_html().replace(b'<button><a name="unit_measure">', b'<h3><a name="unit_measure">', 1),
            national_html().replace(b'<button><a name="unit_measure">', b'<button><button><a name="unit_measure">', 1),
            national_html().replace(b'<a name="unit_measureDisseminated">', b'<a name="ref_period">', 1),
            national_html().replace(b'</li>', b'', 1),
            national_html().replace(b'<p>Reporting port</p>', b'<p><p>Reporting port</p></p>'),
            national_html({**REFERENCE, "stat_unit": "x" * 16001}), b"\xff"]
        for body in variants:
            with self.subTest(prefix=body[:20]):
                with self.assertRaises(ResearchAcquisitionError):
                    extract_national_methodology(body)

    def test_retained_review_keeps_old_update_unavailable_compilation_and_unconfirmed_root(self):
        fixture, terms, candidate = self.pipeline(at=NOW + 10)
        before = self.files(fixture)
        report = review_national_methodology(fixture.session.quarantine, candidate, clock=lambda: NOW + 10)
        self.assertEqual(REFERENCE, {s["anchor"]: s["text"] for s in report["sections"]})
        self.assertEqual("Statistics Belgium", report["compiling_agency_claim_raw"])
        self.assertEqual("Eurostat / European Commission", report["hosting_publisher"])
        self.assertEqual("19 February 2021", report["publisher_metadata_update_raw"])
        self.assertEqual(NOW + 10, report["acquired_at"])
        self.assertEqual(NOW + 86400, report["expires_at"])
        for key, expected in (("resolution", "NOT_RESOLVED"), ("acceptance", "NOT_ACCEPTED"),
            ("root_provenance", "UNCONFIRMED"), ("independent_corroboration", "INSUFFICIENT EVIDENCE"),
            ("runtime_effect", "NONE"), ("publication", "BLOCKED")):
            self.assertEqual(expected, report[key])
        self.assertEqual(terms, report["terms_candidate_id"])
        self.assertEqual(before, self.files(fixture))
        self.assertEqual(report, review_national_methodology(ResearchQuarantine(fixture.root), candidate,
                                                            clock=lambda: NOW + 10))

    def test_current_terms_required_wrong_media_and_other_country_path_reject(self):
        fixture = acquisition.AcquisitionTests()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        with self.assertRaises(ResearchAcquisitionError):
            fixture.session.acquire(NATIONAL_METADATA_RECIPE)
        terms = fixture.terms()
        fixture.response = Response(body=national_html(), headers=[("Content-Type", "application/json")])
        with self.assertRaisesRegex(ResearchAcquisitionError, "MEDIA"):
            fixture.session.acquire(NATIONAL_METADATA_RECIPE, terms_candidate_id=terms)
        for wrong in (NATIONAL_METADATA_URL.replace("_be", "_nl"), NATIONAL_METADATA_URL + "?x=1",
                      NATIONAL_METADATA_URL.replace("ec.europa.eu", "statbel.fgov.be")):
            with patch.dict(RECIPES, {NATIONAL_METADATA_RECIPE: wrong}):
                with self.assertRaisesRegex(ResearchAcquisitionError, "URL_INVALID"):
                    validate_recipe(NATIONAL_METADATA_RECIPE)

    def test_new_national_recipe_cannot_substitute_for_generic_review_or_statistical_admission(self):
        fixture = admission.StatisticalAdmissionTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.fixture.response = Response(body=national_html())
        national = fixture.fixture.session.acquire(NATIONAL_METADATA_RECIPE, terms_candidate_id=fixture.terms)["candidate_id"]
        with self.assertRaises(ResearchAcquisitionError):
            review_methodology_candidate(fixture.quarantine, national, clock=lambda: NOW)
        with self.assertRaises(ResearchAcquisitionError):
            prepare_admission_review(fixture.quarantine, fixture.data, national, clock=lambda: NOW)
        self.assertIsNotNone(fixture.review()["fingerprint"])
        # National-only schemas do not silently broaden the old generic parser.
        with self.assertRaises(ResearchAcquisitionError):
            extract_maritime_methodology(national_html())

    def test_tampered_terms_expired_dependency_and_wrong_recipe_reject(self):
        fixture, terms, candidate = self.pipeline(at=NOW + 10)
        with self.assertRaises(ResearchAcquisitionError):
            review_national_methodology(fixture.session.quarantine, terms, clock=lambda: NOW + 10)
        with self.assertRaises(ResearchAcquisitionError):
            review_national_methodology(fixture.session.quarantine, candidate, clock=lambda: NOW + 86400)
        (fixture.root / terms / "content.bin").write_bytes(b"tampered")
        with self.assertRaises(ResearchAcquisitionError):
            review_national_methodology(fixture.session.quarantine, candidate, clock=lambda: NOW + 10)

    def test_second_read_mutation_of_metadata_or_terms_withholds_report(self):
        fixture, terms, candidate = self.pipeline()
        original = fixture.session.quarantine.read
        for identity in (candidate, terms):
            armed = False
            def arm_after_parse(content):
                nonlocal armed
                result = extract_national_methodology(content)
                armed = True
                return result
            def changed(*args, **kwargs):
                value, content = original(*args, **kwargs)
                if armed and args[0] == identity:
                    return value, content + b"changed"
                return value, content
            with patch.object(fixture.session.quarantine, "read", side_effect=changed), \
                 patch("sictra_block1.national_methodology.extract_national_methodology", side_effect=arm_after_parse):
                with self.assertRaises(ResearchAcquisitionError):
                    review_national_methodology(fixture.session.quarantine, candidate, clock=lambda: NOW)

    def test_mid_parse_and_last_return_expiry_or_clock_regression_fail_closed(self):
        fixture, _, candidate = self.pipeline(at=NOW + 1)
        clocks = ([NOW + 1, NOW + 86400], [NOW + 1, NOW + 1, NOW + 86400],
                  [NOW + 1, NOW], [NOW + 1, NOW + 1, NOW], [True], [-1], [1.5])
        for values in clocks:
            with self.assertRaises(ResearchAcquisitionError):
                review_national_methodology(fixture.session.quarantine, candidate, clock=Mock(side_effect=values))

    def test_data_only_restoration_reproduces_review_and_changed_bytes_reject(self):
        fixture, _, candidate = self.pipeline()
        report = review_national_methodology(fixture.session.quarantine, candidate, clock=lambda: NOW)
        with TemporaryDirectory() as folder:
            restored = Path(folder) / "restored"
            copytree(fixture.root, restored)
            recovered = ResearchQuarantine(restored)
            self.assertEqual(report, review_national_methodology(recovered, candidate, clock=lambda: NOW))
            (restored / candidate / "content.bin").write_bytes(b"altered national metadata")
            with self.assertRaises(ResearchAcquisitionError):
                review_national_methodology(recovered, candidate, clock=lambda: NOW)

    def test_default_system_clock_and_ascii_cli_keep_unicode_raw_claims(self):
        fixture, _, candidate = self.pipeline(values={**REFERENCE, "contact_organisation": "Statistics Belgium \u2014 fixture"})
        output_bytes = io.BytesIO()
        output = io.TextIOWrapper(output_bytes, encoding="ascii")
        with patch("sictra_block1.national_methodology.time.time", return_value=NOW + 0.75), \
             patch("sys.argv", ["review", "--root", str(fixture.root), "--candidate-id", candidate]), \
             patch("sys.stdout", output):
            self.assertEqual(0, main())
            output.flush()
        report = json.loads(output_bytes.getvalue())
        self.assertEqual("Statistics Belgium \u2014 fixture", report["compiling_agency_claim_raw"])
        self.assertEqual("NOT_RESOLVED", report["resolution"])


if __name__ == "__main__":
    unittest.main()
