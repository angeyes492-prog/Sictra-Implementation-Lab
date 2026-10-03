"""Read-only extraction of quarantined official methodology, not resolution."""
from hashlib import sha256
from html.parser import HTMLParser
import json
import time

from .research_acquisition import ResearchAcquisitionError, ResearchQuarantine, canonical

SECTIONS = ("meta_last_update", "data_descr", "coverage_sector", "coverage_time",
            "rev_policy", "rev_practice", "source_type", "freq_coll")


class MethodologyParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sections = {}
        self.selected = None
        self.heading = False
        self.paragraph = None
        self.ignored = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "svg", "template", "noscript"}:
            self.ignored.append(tag)
        if self.ignored:
            return
        if tag in {"h2", "h3", "button"}:
            if self.paragraph is not None:
                raise ResearchAcquisitionError("METADATA_PARAGRAPH_UNCLOSED")
            self.selected = None
            self.heading = tag == "h3"
        if tag == "a" and self.heading:
            names = [value for key, value in attrs if key == "name"]
            if len(names) > 1:
                raise ResearchAcquisitionError("METADATA_ANCHOR_INVALID")
            if names and names[0] in SECTIONS:
                name = names[0]
                if name in self.sections:
                    raise ResearchAcquisitionError("METADATA_ANCHOR_DUPLICATE")
                self.sections[name] = []
                self.selected = name
        if tag == "p" and self.selected and not self.heading:
            if self.paragraph is not None:
                raise ResearchAcquisitionError("METADATA_PARAGRAPH_INVALID")
            self.paragraph = []
        if tag == "br" and self.paragraph is not None:
            self.paragraph.append(" ")

    def handle_endtag(self, tag):
        if self.ignored:
            if tag == self.ignored[-1]:
                self.ignored.pop()
            return
        if tag == "h3":
            self.heading = False
        if tag == "p" and self.paragraph is not None:
            text = " ".join("".join(self.paragraph).split())
            if text:
                self.sections[self.selected].append(text)
            self.paragraph = None

    def handle_data(self, data):
        if not self.ignored and self.paragraph is not None:
            self.paragraph.append(data)


def extract_maritime_methodology(content):
    """Pure text extraction; does not validate source or grant authority."""
    if not isinstance(content, bytes) or not 0 < len(content) <= 1024 * 1024:
        raise ResearchAcquisitionError("METADATA_CONTENT_SIZE_INVALID")
    try:
        html = content.decode("utf-8-sig", errors="strict")
    except UnicodeError as error:
        raise ResearchAcquisitionError("METADATA_ENCODING_INVALID") from error
    parser = MethodologyParser()
    parser.feed(html)
    parser.close()
    if parser.paragraph is not None or parser.ignored or parser.heading or set(parser.sections) != set(SECTIONS):
        raise ResearchAcquisitionError("METADATA_SECTIONS_INCOMPLETE")
    sections = {key: "\n".join(parser.sections[key]) for key in SECTIONS}
    if any(not value or len(value) > 16000 for value in sections.values()):
        raise ResearchAcquisitionError("METADATA_SECTION_EMPTY_OR_OVERSIZED")
    return sections


def review_methodology_candidate(quarantine, candidate_id, *, clock=time.time):
    initial_time = int(clock())
    descriptor, content = quarantine.read(candidate_id, now=initial_time, expected_recipe="EUROSTAT_MAR_METADATA")
    terms, terms_bytes = quarantine.read(descriptor["terms_candidate_id"], now=initial_time,
                                         expected_recipe="EUROSTAT_REUSE_NOTICE")
    sections = extract_maritime_methodology(content)
    # Slow parsing must not keep expired, changed or substituted bytes alive.
    final_time = int(clock())
    current, current_bytes = quarantine.read(candidate_id, now=final_time, expected_recipe="EUROSTAT_MAR_METADATA")
    current_terms, current_terms_bytes = quarantine.read(descriptor["terms_candidate_id"], now=final_time,
                                                         expected_recipe="EUROSTAT_REUSE_NOTICE")
    if current != descriptor or current_bytes != content or current_terms != terms or current_terms_bytes != terms_bytes:
        raise ResearchAcquisitionError("METHODOLOGY_CHANGED_DURING_READ")
    report = {"version": "0.1.0", "source_id": descriptor["source_id"], "candidate_id": candidate_id,
        "content_sha256": descriptor["content_sha256"], "source_url": descriptor["final_url"],
        "terms_candidate_id": descriptor["terms_candidate_id"], "acquired_at": descriptor["acquired_at"],
        "expires_at": min(descriptor["expires_at"], terms["expires_at"]),
        "source_expires_at": descriptor["expires_at"], "terms_expires_at": terms["expires_at"],
        "terms_content_sha256": terms["content_sha256"],
        "publisher_metadata_update_raw": sections["meta_last_update"],
        "requirement": descriptor["requirement"], "need_type": "SOURCE_METHODOLOGY",
        "sections": [{"anchor": key, "source_ref": descriptor["final_url"] + "#" + key,
                      "text": text, "text_sha256": sha256(text.encode()).hexdigest()}
                     for key, text in sections.items()],
        "verdict": "REVIEW_REQUIRED", "resolution": "NOT_RESOLVED", "acceptance": "NOT_ACCEPTED",
        "evidence_state": "QUARANTINED_NOT_ADMITTED", "runtime_effect": "NONE", "publication": "BLOCKED",
        "specific_change_cause": "UNCONFIRMED", "independent_corroboration": "INSUFFICIENT EVIDENCE",
        "next_action": "REVIEW_SOURCE_ADMISSION_AND_RELEASE_SPECIFIC_EXPLANATION",
        "limitations": ["General domain metadata does not explain a particular release/measurement change",
                        "Acquisition time is not publisher update or independent root evidence",
                        "Extraction does not attest evidence, resolve a task or modify a dossier"]}
    report["fingerprint"] = sha256(canonical(report)).hexdigest()
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--candidate-id", required=True)
    args = parser.parse_args()
    print(json.dumps(review_methodology_candidate(ResearchQuarantine(args.root), args.candidate_id),
                     ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
