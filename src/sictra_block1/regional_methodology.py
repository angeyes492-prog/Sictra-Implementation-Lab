"""Read-only review of quarantined Eurostat regional maritime scope metadata."""
from hashlib import sha256
import json
import re
import time

from .research_acquisition import (
    REGIONAL_METADATA_RECIPE, ResearchAcquisitionError, ResearchQuarantine, canonical,
)
from .research_methodology import _extract_methodology_sections

MAIN_PORTS_STATEMENT = (
    "For the tables presenting maritime data at regional level the same "
    "aggregation method (exclusion of double counting) is applied taking "
    "into account main ports only. Only for these ports (handling more "
    "than one million tonnes of goods or recording more than 200 000 "
    "passenger movements annually) the detailed statistics allow such aggregation."
)
RETRACTED_MARKUP = re.compile(rb"<\s*(?:del|strike|s)\b|text-decoration\s*:\s*line-through", re.I)
RETRACTION_TEXT = ("no longer applies", "has been withdrawn", "has been superseded")


def _now(clock):
    value = clock()
    if type(value) is not int or value < 0:
        raise ResearchAcquisitionError("REGIONAL_METHODOLOGY_CLOCK_INVALID")
    return value


def _snapshot(quarantine, candidate_id, now):
    descriptor, content = quarantine.read(candidate_id, now=now,
        expected_recipe=REGIONAL_METADATA_RECIPE)
    terms, terms_bytes = quarantine.read(descriptor["terms_candidate_id"], now=now,
        expected_recipe="EUROSTAT_REUSE_NOTICE")
    return descriptor, content, terms, terms_bytes


def review_regional_methodology(quarantine, candidate_id, *, clock=lambda: int(time.time())):
    if (not isinstance(quarantine, ResearchQuarantine)
            or not isinstance(candidate_id, str)
            or re.fullmatch(r"[0-9a-f]{64}", candidate_id) is None
            or not callable(clock)):
        raise ResearchAcquisitionError("REGIONAL_METHODOLOGY_CONFIGURATION_INVALID")
    start = _now(clock)
    first = _snapshot(quarantine, candidate_id, start)
    descriptor, content, terms, terms_bytes = first
    section = _extract_methodology_sections(content, ("data_descr",),
        capture_lists=True)["data_descr"]
    finish = _now(clock)
    if finish < start:
        raise ResearchAcquisitionError("REGIONAL_METHODOLOGY_CLOCK_REGRESSED")
    second = _snapshot(quarantine, candidate_id, finish)
    if first != second:
        raise ResearchAcquisitionError("REGIONAL_METHODOLOGY_CHANGED_DURING_READ")
    expiry = min(descriptor["expires_at"], terms["expires_at"])
    paragraphs = [paragraph.casefold() for paragraph in section.splitlines()]
    explicit = (MAIN_PORTS_STATEMENT.casefold() in paragraphs
                and RETRACTED_MARKUP.search(content) is None
                and not any(marker in section.casefold() for marker in RETRACTION_TEXT))
    report = {"schema_version": "0.1.0", "candidate_id": candidate_id,
        "source_id": descriptor["source_id"], "source_url": descriptor["final_url"],
        "content_sha256": descriptor["content_sha256"],
        "terms_candidate_id": descriptor["terms_candidate_id"],
        "terms_content_sha256": terms["content_sha256"],
        "acquired_at": descriptor["acquired_at"],
        "source_expires_at": descriptor["expires_at"],
        "terms_expires_at": terms["expires_at"], "expires_at": expiry,
        "checked_at": finish, "section_anchor": "data_descr",
        "section_text": section, "section_sha256": sha256(section.encode()).hexdigest(),
        "regional_scope_label": "EXPLICIT_MAIN_PORTS_ONLY" if explicit else "UNCONFIRMED",
        "statbel_scope_equivalence": "UNCONFIRMED",
        "specific_gap_cause": "UNCONFIRMED", "independent_root": "NOT_ESTABLISHED",
        "admission": "NOT_ADMITTED", "resolution": "NOT_RESOLVED",
        "acceptance": "NOT_ACCEPTED", "runtime_effect": "NONE",
        "publication": "BLOCKED"}
    report["fingerprint"] = sha256(canonical(report)).hexdigest()
    end = _now(clock)
    if not finish <= end < expiry:
        raise ResearchAcquisitionError("REGIONAL_METHODOLOGY_RETURN_EXPIRED_OR_CLOCK_REGRESSED")
    return report


def verify_regional_methodology_current(quarantine, candidate_id, report,
                                        *, clock=lambda: int(time.time())):
    if (not isinstance(report, dict) or report.get("fingerprint") != sha256(canonical(
            {key: value for key, value in report.items() if key != "fingerprint"})).hexdigest()):
        raise ResearchAcquisitionError("REGIONAL_METHODOLOGY_REPORT_INVALID")
    now = _now(clock)
    if (type(report.get("checked_at")) is not int
            or type(report.get("expires_at")) is not int
            or not report["checked_at"] <= now < report["expires_at"]):
        raise ResearchAcquisitionError("REGIONAL_METHODOLOGY_NOT_CURRENT")
    fresh = review_regional_methodology(quarantine, candidate_id, clock=clock)
    end = _now(clock)
    if not now <= fresh["checked_at"] <= end < fresh["expires_at"]:
        raise ResearchAcquisitionError("REGIONAL_METHODOLOGY_CLOCK_REGRESSED_OR_EXPIRED")
    stable = lambda value: {key: item for key, item in value.items()
                            if key not in {"checked_at", "fingerprint"}}
    if canonical(stable(report)) != canonical(stable(fresh)):
        raise ResearchAcquisitionError("REGIONAL_METHODOLOGY_INPUT_CHANGED")


def main():
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--candidate-id", required=True)
    args = parser.parse_args()
    if not Path(args.root).is_dir():
        raise ResearchAcquisitionError("REGIONAL_METHODOLOGY_ROOT_MISSING")
    quarantine = ResearchQuarantine(args.root)
    report = review_regional_methodology(quarantine, args.candidate_id)
    body = json.dumps(report, ensure_ascii=True, indent=2)
    verify_regional_methodology_current(quarantine, args.candidate_id, report)
    print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
