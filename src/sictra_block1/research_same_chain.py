"""Read-only numeric comparison of two quarantined Belgian maritime pages.

This is an agent research diagnostic, not independent corroboration or an
installed Telecare source adapter.
"""
from decimal import Decimal, localcontext
from hashlib import sha256
import json
import re
import time

from .research_acquisition import (
    ResearchAcquisitionError, ResearchQuarantine, STATISTICS_RECIPE, canonical,
)
from .research_statistics import inspect_statistics_candidate, unique
from .research_statbel import (
    DATA_RECIPE, TERMS_RECIPE, StatbelResearchQuarantine, extract_maritime_table,
)


class SameChainReview:
    def __init__(self, eurostat_quarantine, eurostat_id, statbel_quarantine, statbel_id,
                 *, clock=lambda: int(time.time())):
        if (not isinstance(eurostat_quarantine, ResearchQuarantine)
                or not isinstance(statbel_quarantine, StatbelResearchQuarantine)
                or not callable(clock)
                or any(not isinstance(identity, str)
                       or re.fullmatch(r"[0-9a-f]{64}", identity) is None
                       for identity in (eurostat_id, statbel_id))):
            raise ResearchAcquisitionError("SAME_CHAIN_CONFIGURATION_INVALID")
        self.eurostat_quarantine = eurostat_quarantine
        self.statbel_quarantine = statbel_quarantine
        self.eurostat_id, self.statbel_id = eurostat_id, statbel_id
        self.clock = clock

    def _time(self):
        now = self.clock()
        if type(now) is not int or now < 0:
            raise ResearchAcquisitionError("SAME_CHAIN_CLOCK_INVALID")
        return now

    def _inputs(self, now):
        euro = inspect_statistics_candidate(self.eurostat_quarantine, self.eurostat_id,
                                             clock=lambda: now)
        euro_descriptor, euro_original = self.eurostat_quarantine.read(
            self.eurostat_id, now=now, expected_recipe=STATISTICS_RECIPE)
        if euro_descriptor["content_sha256"] != euro["content_sha256"]:
            raise ResearchAcquisitionError("SAME_CHAIN_EUROSTAT_CHANGED_DURING_READ")
        exact_euro = self._exact_eurostat_values(euro_original)
        statbel, original = self.statbel_quarantine.read(
            self.statbel_id, now=now, expected_recipe=DATA_RECIPE)
        terms, terms_bytes = self.statbel_quarantine.read(
            statbel["terms_candidate_id"], now=now, expected_recipe=TERMS_RECIPE)
        rows = extract_maritime_table(original)
        # The terms descriptor and bytes are both retained in the comparison
        # snapshot; a changed rights document cannot silently keep old data.
        return euro, euro_original, exact_euro, statbel, original, terms, terms_bytes, rows

    @staticmethod
    def _exact_eurostat_values(original):
        # The upstream inspector validates the fixed JSON-stat schema and
        # coordinates. Reparse the same hash-bound raw bytes before binary
        # floats can erase the publisher's decimal digits.
        try:
            parsed = json.loads(original.decode("utf-8-sig", errors="strict"),
                                object_pairs_hook=unique, parse_float=Decimal)
            values = parsed["value"]
            cells = values if isinstance(values, list) else [values.get("0"), values.get("1")]
            indexes = parsed["dimension"]["time"]["category"]["index"]
            years = indexes if isinstance(indexes, list) else [
                key for key, _ in sorted(indexes.items(), key=lambda pair: pair[1])]
            if len(cells) != 2 or len(years) != 2:
                raise ValueError("cell count")
            exact = {}
            for position, year in enumerate(years):
                cell = cells[position]
                value = None if cell is None else Decimal(cell)
                if value is not None:
                    digits, exponent = value.as_tuple().digits, value.as_tuple().exponent
                    if (not value.is_finite() or value < 0 or len(digits) > 64
                            or not -64 <= exponent <= 64):
                        raise ValueError("exact numeric bound")
                exact[int(year)] = value
            return exact
        except (ValueError, KeyError, TypeError, UnicodeError) as error:
            raise ResearchAcquisitionError("SAME_CHAIN_EXACT_VALUE_INVALID") from error

    @staticmethod
    def _input_identity(inputs):
        euro, euro_original, exact_euro, statbel, original, terms, terms_bytes, rows = inputs
        return (euro, sha256(euro_original).hexdigest(),
                {year: str(value) for year, value in exact_euro.items()},
                statbel, sha256(original).hexdigest(), terms,
                sha256(terms_bytes).hexdigest(), rows)

    def read(self):
        started = self._time()
        initial = self._inputs(started)
        euro, _, exact_euro, statbel, _, terms, _, statbel_rows = initial
        finished = self._time()
        if finished < started:
            raise ResearchAcquisitionError("SAME_CHAIN_CLOCK_REGRESSED")
        if canonical(self._input_identity(initial)) != canonical(
                self._input_identity(self._inputs(finished))):
            raise ResearchAcquisitionError("SAME_CHAIN_INPUT_CHANGED")
        expires = min(euro["expires_at"], statbel["expires_at"], terms["expires_at"])
        checked = self._time()
        if checked < finished or checked >= expires:
            raise ResearchAcquisitionError("SAME_CHAIN_NOT_CURRENT")
        euros = {row["time_period"]: row for row in euro["observations"]}
        if set(euros) != {2023, 2024} or {row["year"] for row in statbel_rows} != {2023, 2024}:
            raise ResearchAcquisitionError("SAME_CHAIN_SCOPE_INVALID")
        rows = []
        for stat in statbel_rows:
            year = stat["year"]
            observation = euros[year]
            if observation["missing"] or observation["value_thousand_tonnes"] is None:
                raise ResearchAcquisitionError("SAME_CHAIN_MEASUREMENT_MISSING")
            euro_value = exact_euro[year]
            if euro_value is None:
                raise ResearchAcquisitionError("SAME_CHAIN_MEASUREMENT_MISSING")
            statbel_sum = Decimal(stat["sum_thousand_tonnes"])
            with localcontext() as context:
                # Fixed source numeric bounds above keep this well below the
                # 256-digit ceiling; no default-context rounding is allowed.
                context.prec = 256
                gap = statbel_sum - euro_value
            rows.append({"year": year,
                "statbel_loaded_thousand_tonnes": str(stat["loaded_thousand_tonnes"]),
                "statbel_unloaded_thousand_tonnes": str(stat["unloaded_thousand_tonnes"]),
                "statbel_sum_thousand_tonnes": str(statbel_sum),
                "eurostat_thousand_tonnes": str(euro_value),
                "eurostat_status_flag": observation["status_flag"],
                "numeric_gap_thousand_tonnes": str(gap)})
        report = {"version": "0.1.0", "scope": "LABORATORY_INTERNAL_SUPERVISED",
            "checked_at": checked, "expires_at": expires,
            "eurostat": {"candidate_id": self.eurostat_id,
                         "content_sha256": euro["content_sha256"],
                         "terms_candidate_id": euro["terms_candidate_id"],
                         "terms_content_sha256": euro["terms_content_sha256"],
                         "source_url": euro["source_url"],
                         "publisher_updated_raw": euro["publisher_updated_raw"]},
            "statbel": {"candidate_id": self.statbel_id,
                        "content_sha256": statbel["content_sha256"],
                        "terms_candidate_id": statbel["terms_candidate_id"],
                        "terms_content_sha256": terms["content_sha256"],
                        "source_url": statbel["final_url"],
                        "publisher_release_extracted": statbel["publisher_release_extracted"]},
            "rows": rows, "independent_root": "NOT_ESTABLISHED",
            "comparability": "UNCONFIRMED", "gap_cause": "UNCONFIRMED",
            "revision_explanation": "INSUFFICIENT EVIDENCE",
            "admission": "NOT_ADMITTED", "resolution": "NOT_RESOLVED",
            "acceptance": "NOT_ACCEPTED", "runtime_effect": "NONE",
            "publication": "BLOCKED"}
        report["fingerprint"] = sha256(canonical(report)).hexdigest()
        return report

    def verify_current(self, report):
        if (not isinstance(report, dict) or report.get("fingerprint") != sha256(canonical(
                {key: value for key, value in report.items() if key != "fingerprint"})).hexdigest()):
            raise ResearchAcquisitionError("SAME_CHAIN_REPORT_INVALID")
        now = self._time()
        if (type(report.get("checked_at")) is not int
                or type(report.get("expires_at")) is not int
                or not report["checked_at"] <= now < report["expires_at"]):
            raise ResearchAcquisitionError("SAME_CHAIN_NOT_CURRENT")
        fresh = self.read()
        final = self._time()
        if not now <= fresh["checked_at"] <= final < fresh["expires_at"]:
            raise ResearchAcquisitionError("SAME_CHAIN_CLOCK_REGRESSED_OR_EXPIRED")
        stable = lambda value: {key: item for key, item in value.items()
                                if key not in {"checked_at", "fingerprint"}}
        if canonical(stable(fresh)) != canonical(stable(report)):
            raise ResearchAcquisitionError("SAME_CHAIN_INPUT_CHANGED")


def main():
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eurostat-root", required=True)
    parser.add_argument("--eurostat-id", required=True)
    parser.add_argument("--statbel-root", required=True)
    parser.add_argument("--statbel-id", required=True)
    args = parser.parse_args()
    if not Path(args.eurostat_root).is_dir() or not Path(args.statbel_root).is_dir():
        raise ResearchAcquisitionError("SAME_CHAIN_QUARANTINE_ROOT_MISSING")
    review = SameChainReview(ResearchQuarantine(args.eurostat_root), args.eurostat_id,
                             StatbelResearchQuarantine(args.statbel_root), args.statbel_id)
    report = review.read()
    body = json.dumps(report, ensure_ascii=False, indent=2)
    review.verify_current(report)
    print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
