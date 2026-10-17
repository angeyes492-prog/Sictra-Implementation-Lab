import json
import unittest
from unittest.mock import Mock, patch

import test_agent_research_acquisition as acquisition
from test_agent_research_acquisition import Response, NOW
from sictra_block1.research_acquisition import (
    ResearchAcquisitionError, ResearchQuarantine, RECIPES, STATISTICS_RECIPE, STATISTICS_URL,
)
from sictra_block1.research_methodology import review_methodology_candidate
from sictra_block1.research_statistics import normalize_maritime_statistics, inspect_statistics_candidate


def dataset():
    # Independently stated row-major reference: 2024 at position 0 = 12.5;
    # 2023 at position 1 = 10.0. Dict order deliberately opposes positions.
    codes = {"freq": {"A": 0}, "tra_meas": {"FR_LD_NLD": 0}, "unit": {"THS_T": 0},
             "geo": {"BE": 0}, "time": {"2023": 1, "2024": 0}}
    return {"version": "2.0", "class": "dataset", "source": "ESTAT", "label": "Freight reference",
            "updated": "2025-01-15T12:00:00Z", "extension": {"id": "TRAN_R_MAGO_NM"},
            "id": ["freq", "tra_meas", "unit", "geo", "time"], "size": [1, 1, 1, 1, 2],
            "dimension": {key: {"category": {"index": value, "label": {
                code: "Belgium" if code == "BE" else code for code in value}}}
                          for key, value in codes.items()},
            "value": [12.5, 10.0], "status": {"0": "p"}}


def raw(data):
    return json.dumps(data, allow_nan=False).encode()


class StatisticsResearchTests(unittest.TestCase):
    def pipeline(self, data=None, *, delay=0):
        fixture = acquisition.AcquisitionTests()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        terms = fixture.terms()
        fixture.now = NOW + delay
        body = raw(dataset() if data is None else data)
        fixture.response = Response(body=body, headers=[("Content-Type", "application/json"),
                                                        ("Content-Length", str(len(body)))])
        receipt = fixture.session.acquire(STATISTICS_RECIPE, terms_candidate_id=terms)
        return fixture, terms, receipt["candidate_id"]

    def test_dense_reference_uses_category_positions_not_json_key_order(self):
        result = normalize_maritime_statistics(raw(dataset()))
        self.assertEqual([(2023, 10.0, None), (2024, 12.5, "p")], [
            (r["time_period"], r["value_thousand_tonnes"], r["status_flag"]) for r in result["observations"]])
        self.assertEqual("THS_T", result["filters"]["unit"])
        self.assertEqual("BE", result["observations"][0]["geo_code"])
        self.assertEqual("EXPLICIT", result["publisher_timezone"])

    def test_retained_publisher_compact_timezone_and_sparse_actual_cells(self):
        # From the retained 2026-10-03 official response (hash in evidence),
        # not inferred from the parser or a copied normalization conclusion.
        data = dataset()
        data["updated"] = "2026-03-17T23:00:00+0100"
        data["dimension"]["time"]["category"]["index"] = {"2023": 0, "2024": 1}
        data["value"], data["status"] = {"0": 272698.25, "1": 274369.05}, {}
        result = normalize_maritime_statistics(raw(data))
        self.assertEqual("2026-03-17T23:00:00+0100", result["publisher_updated_raw"])
        self.assertEqual("EXPLICIT", result["publisher_timezone"])
        self.assertEqual([(2023, 272698.25), (2024, 274369.05)], [
            (r["time_period"], r["value_thousand_tonnes"]) for r in result["observations"]])
        for invalid in ("2026-03-17T23:00:00+2500", "2026-03-17T23:00:00+0160",
                        "2026-03-17T23:00:00+0100junk"):
            with self.assertRaises(ResearchAcquisitionError):
                normalize_maritime_statistics(raw({**data, "updated": invalid}))

    def test_sparse_missing_is_not_zero_and_flags_can_mark_missing_cells(self):
        data = dataset()
        data["value"], data["status"] = {"0": 0}, ["p", ":"]
        result = normalize_maritime_statistics(raw(data))
        self.assertEqual(1, result["missing_value_count"])
        self.assertEqual([(2023, None, True, ":"), (2024, 0, False, "p")], [
            (r["time_period"], r["value_thousand_tonnes"], r["missing"], r["status_flag"])
            for r in result["observations"]])

    def test_time_first_array_category_and_global_status_preserve_identity(self):
        data = dataset()
        data["id"], data["size"] = ["time", "geo", "freq", "unit", "tra_meas"], [2, 1, 1, 1, 1]
        data["dimension"]["time"]["category"]["index"] = ["2024", "2023"]
        data["status"] = "e"
        data["updated"] = "2025-01-15T12:00:00"
        result = normalize_maritime_statistics(raw(data))
        self.assertEqual([10.0, 12.5], [r["value_thousand_tonnes"] for r in result["observations"]])
        self.assertEqual(["e", "e"], [r["status_flag"] for r in result["observations"]])
        self.assertEqual("UNSPECIFIED", result["publisher_timezone"])

    def test_wrong_source_dataset_unit_geography_period_and_size_reject(self):
        variants = []
        for key, value in (("version", "1.0"), ("class", "collection"), ("source", "UNKNOWN"),
                           ("size", [1, 1, 1, 1, True]), ("id", ["freq"] * 5),
                           ("updated", "2025-02-31"), ("extension", {"id": "OTHER"})):
            variants.append({**dataset(), key: value})
        for dim, code in (("geo", "HN"), ("unit", "EUR"), ("time", "2025"), ("tra_meas", "OTHER")):
            data = dataset()
            data["dimension"][dim]["category"]["index"] = {code: 0}
            variants.append(data)
        for data in variants:
            with self.subTest(data=data.get("size")):
                with self.assertRaises(ResearchAcquisitionError):
                    normalize_maritime_statistics(raw(data))

    def test_duplicate_nonbijective_index_labels_and_cell_indexes_reject(self):
        variants = []
        for indexes in ({"2023": 0, "2024": 0}, {"2023": False, "2024": 1},
                        ["2023", "2023"], {"2023": 0, "2024": 2}):
            data = dataset()
            data["dimension"]["time"]["category"]["index"] = indexes
            variants.append(data)
        data = dataset()
        data["dimension"]["geo"]["category"]["label"] = {"HN": "Belgium"}
        variants.append(data)
        for cells in ({"01": 1}, {"2": 1}, {"-1": 1}, [1], "12.5"):
            variants.append({**dataset(), "value": cells})
        for data in variants:
            with self.assertRaises(ResearchAcquisitionError):
                normalize_maritime_statistics(raw(data))

    def test_bool_negative_nonfinite_and_malformed_flags_reject(self):
        for value in (True, -1, "12.5", [], {}):
            with self.assertRaises(ResearchAcquisitionError):
                normalize_maritime_statistics(raw({**dataset(), "value": [value, 1]}))
        for status in (False, ["p"], {"2": "p"}, [1, "p"], ["<script>", None], ["x" * 33, None]):
            with self.assertRaises(ResearchAcquisitionError):
                normalize_maritime_statistics(raw({**dataset(), "status": status}))
        for number in (b"NaN", b"Infinity", b"1e9999"):
            body = raw(dataset()).replace(b"12.5", number)
            with self.assertRaises(ResearchAcquisitionError):
                normalize_maritime_statistics(body)

    def test_duplicate_json_encoding_size_error_and_async_warning_fail_closed(self):
        variants = [b'\xff', b"{" * 2000, b"x" * (1024 * 1024 + 1),
                    raw(dataset())[:-1] + b',"value":[999,999]}',
                    raw({"warning": {"status": 413}}), raw({"error": {"status": "400"}}),
                    raw({**dataset(), "warning": {"status": 413}})]
        for body in variants:
            with self.assertRaises(ResearchAcquisitionError):
                normalize_maritime_statistics(body)

    def test_statistical_acquisition_pins_exact_query_mime_terms_and_bytes(self):
        fixture, terms, identity = self.pipeline()
        descriptor, body = ResearchQuarantine(fixture.root).read(identity, now=NOW)
        self.assertEqual(raw(dataset()), body)
        self.assertEqual(STATISTICS_URL, descriptor["final_url"])
        self.assertEqual(STATISTICS_URL.split("ec.europa.eu", 1)[1], fixture.connections[-1][2])
        self.assertEqual("application/json", descriptor["media_type"])
        self.assertEqual(terms, descriptor["terms_candidate_id"])
        self.assertEqual("NOT_ADMITTED", descriptor["admission"])
        with self.assertRaises(ResearchAcquisitionError):
            review_methodology_candidate(fixture.session.quarantine, identity, clock=lambda: NOW)

    def test_arbitrary_query_and_wrong_recipe_media_do_not_retain(self):
        fixture, terms, _ = self.pipeline()
        before = set(fixture.root.iterdir())
        for url in (STATISTICS_URL + "&geo=HN", STATISTICS_URL.split("?", 1)[0],
                    STATISTICS_URL.replace("tran_r_mago_nm?", "OTHER?")):
            with patch.dict(RECIPES, {STATISTICS_RECIPE: url}):
                with self.assertRaisesRegex(ResearchAcquisitionError, "URL_INVALID"):
                    fixture.session.acquire(STATISTICS_RECIPE, terms_candidate_id=terms)
        fixture.response = Response()
        with self.assertRaisesRegex(ResearchAcquisitionError, "MEDIA_REJECTED"):
            fixture.session.acquire(STATISTICS_RECIPE, terms_candidate_id=terms)
        fixture.response = Response(headers=[("Content-Type", "application/json")])
        with self.assertRaisesRegex(ResearchAcquisitionError, "MEDIA_REJECTED"):
            fixture.session.acquire("EUROSTAT_MAR_METADATA", terms_candidate_id=terms)
        self.assertEqual(before, set(fixture.root.iterdir()))

    def test_retained_inspection_reopens_without_mutation_and_uses_earliest_expiry(self):
        fixture, terms, identity = self.pipeline(delay=100)
        before = {str(p): p.read_bytes() for p in fixture.root.rglob("*") if p.is_file()}
        result = inspect_statistics_candidate(fixture.session.quarantine, identity, clock=lambda: NOW + 100)
        self.assertEqual([10.0, 12.5], [r["value_thousand_tonnes"] for r in result["observations"]])
        self.assertEqual(NOW + 86400, result["expires_at"])
        self.assertEqual(NOW + 86500, result["source_expires_at"])
        self.assertEqual(terms, result["terms_candidate_id"])
        for key, expected in (("runtime_effect", "NONE"), ("resolution", "NOT_RESOLVED"),
                              ("acceptance", "NOT_ACCEPTED"), ("root_provenance", "UNCONFIRMED")):
            self.assertEqual(expected, result[key])
        self.assertEqual(result, inspect_statistics_candidate(ResearchQuarantine(fixture.root), identity,
                                                              clock=lambda: NOW + 100))
        self.assertEqual(before, {str(p): p.read_bytes() for p in fixture.root.rglob("*") if p.is_file()})

    def test_foreign_receipt_expiry_and_tamper_reject(self):
        fixture, terms, identity = self.pipeline()
        for candidate, now in ((terms, NOW), (identity, NOW + 86400), (identity, NOW - 1)):
            with self.assertRaises(ResearchAcquisitionError):
                inspect_statistics_candidate(fixture.session.quarantine, candidate, clock=lambda: now)
        (fixture.root / identity / "content.bin").write_bytes(raw({**dataset(), "value": [999, 999]}))
        with self.assertRaises(ResearchAcquisitionError):
            inspect_statistics_candidate(fixture.session.quarantine, identity, clock=lambda: NOW)

    def test_slow_parse_expiry_and_changed_second_read_cannot_emit_report(self):
        fixture, _, identity = self.pipeline()
        with self.assertRaisesRegex(ResearchAcquisitionError, "NOT_CURRENT"):
            inspect_statistics_candidate(fixture.session.quarantine, identity,
                                         clock=Mock(side_effect=[NOW, NOW + 86400]))
        original, calls = fixture.session.quarantine.read, 0
        def changed(*args, **kwargs):
            nonlocal calls
            descriptor, body = original(*args, **kwargs)
            if args[0] == identity:
                calls += 1
                if calls == 2:
                    return descriptor, body + b"changed"
            return descriptor, body
        with patch.object(fixture.session.quarantine, "read", side_effect=changed):
            with self.assertRaisesRegex(ResearchAcquisitionError, "CHANGED_DURING_READ"):
                inspect_statistics_candidate(fixture.session.quarantine, identity, clock=lambda: NOW)
