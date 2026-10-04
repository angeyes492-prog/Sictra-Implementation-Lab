"""Candidate origin/scope review of retained Belgian maritime methodology."""
from hashlib import sha256
import json
import time

from .research_acquisition import (
    ResearchAcquisitionError, ResearchQuarantine, NATIONAL_METADATA_RECIPE, canonical,
)
from .research_methodology import _extract_methodology_sections

SECTIONS = ("contact_organisation", "meta_last_update", "data_descr", "stat_conc_def",
    "stat_unit", "stat_pop", "ref_area", "unit_measure", "ref_period", "rev_policy",
    "rev_practice", "source_type", "freq_coll", "coll_method", "data_validation", "data_comp")
TOP_SECTIONS = ("unit_measure", "ref_period")


def _system_clock():
    return int(time.time())


def _now(clock):
    value = clock()
    if type(value) is not int or value < 0:
        raise ResearchAcquisitionError("NATIONAL_METHODOLOGY_CLOCK_INVALID")
    return value


def extract_national_methodology(content):
    return _extract_methodology_sections(content, SECTIONS, top_sections=TOP_SECTIONS, capture_lists=True)


def review_national_methodology(quarantine, candidate_id, *, clock=_system_clock):
    start = _now(clock)
    descriptor, content = quarantine.read(candidate_id, now=start, expected_recipe=NATIONAL_METADATA_RECIPE)
    terms, terms_bytes = quarantine.read(descriptor["terms_candidate_id"], now=start,
                                         expected_recipe="EUROSTAT_REUSE_NOTICE")
    sections = extract_national_methodology(content)
    finish = _now(clock)
    if finish < start:
        raise ResearchAcquisitionError("NATIONAL_METHODOLOGY_CLOCK_REGRESSED")
    current, current_bytes = quarantine.read(candidate_id, now=finish, expected_recipe=NATIONAL_METADATA_RECIPE)
    current_terms, current_terms_bytes = quarantine.read(descriptor["terms_candidate_id"], now=finish,
                                                         expected_recipe="EUROSTAT_REUSE_NOTICE")
    if (current != descriptor or current_bytes != content or current_terms != terms
            or current_terms_bytes != terms_bytes):
        raise ResearchAcquisitionError("NATIONAL_METHODOLOGY_CHANGED_DURING_READ")
    expiry = min(descriptor["expires_at"], terms["expires_at"])
    report = {"schema_version": "0.1.0", "scope": "BLOCK1_BELGIAN_METHODOLOGY_RESEARCH_REVIEW",
        "candidate_id": candidate_id, "source_id": descriptor["source_id"],
        "hosting_publisher": descriptor["publisher"], "source_url": descriptor["final_url"],
        "content_sha256": descriptor["content_sha256"], "acquired_at": descriptor["acquired_at"],
        "publisher_metadata_update_raw": sections["meta_last_update"],
        "compiling_agency_claim_raw": sections["contact_organisation"],
        "terms_candidate_id": descriptor["terms_candidate_id"], "terms_content_sha256": terms["content_sha256"],
        "source_expires_at": descriptor["expires_at"], "terms_expires_at": terms["expires_at"],
        "expires_at": expiry,
        "sections": [{"anchor": key, "source_ref": descriptor["final_url"] + "#" + key,
            "text": text, "text_sha256": sha256(text.encode()).hexdigest()} for key, text in sections.items()],
        "verdict": "REVIEW_REQUIRED", "resolution": "NOT_RESOLVED", "acceptance": "NOT_ACCEPTED",
        "independent_corroboration": "INSUFFICIENT EVIDENCE", "root_provenance": "UNCONFIRMED",
        "specific_change_cause": "UNCONFIRMED", "runtime_effect": "NONE", "publication": "BLOCKED",
        "evidence_state": "QUARANTINED_NOT_ADMITTED", "next_action": "REVIEW_ORIGIN_OVERLAP_AND_ACTUAL_MEASUREMENT_SCOPE",
        "limitations": ["Metadata publisher/host is not an independent statistical origin",
            "A historical metadata update is not a new measurement release or a particular revision explanation",
            "Prose definitions do not prove the retained statistical dataset's exact coverage",
            "Unavailable compilation remains unavailable, not valid or inferred",
            "This review approves no source and mutates no dossier, registry, task or runtime"]}
    report["fingerprint"] = sha256(canonical(report)).hexdigest()
    end = _now(clock)
    if not finish <= end < expiry:
        raise ResearchAcquisitionError("NATIONAL_METHODOLOGY_RETURN_EXPIRED_OR_CLOCK_REGRESSED")
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--candidate-id", required=True)
    args = parser.parse_args()
    print(json.dumps(review_national_methodology(ResearchQuarantine(args.root), args.candidate_id),
                     ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
