"""Fixed Statbel HTML research receipts for the construction agent only.

This module is not imported by Telecare's operations scheduler. Receipts are
quarantined, self-checking records of bytes, not source approval or evidence
of an upstream-independent maritime observation.
"""

from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
import http.client
import re
import socket
import time
from urllib.parse import urlsplit

from .research_acquisition import (
    AUTHORITY, BOUNDARY, MAX_FILE, MAX_SESSION, ResearchAcquisitionError,
    ResearchQuarantine, SessionBudget, canonical, pinned_response,
    public_addresses,
)


TERMS_RECIPE = "STATBEL_CC_BY_4_0"
DATA_RECIPE = "STATBEL_BE_SEA_TRANSPORT_HTML"
STATBEL_TERMS_URL = "https://statbel.fgov.be/en/cc-40"
STATBEL_DATA_URL = "https://statbel.fgov.be/en/themes/mobility/transport/sea-transport"
STATBEL_RECIPES = {TERMS_RECIPE: STATBEL_TERMS_URL, DATA_RECIPE: STATBEL_DATA_URL}
PUBLISHER = "Statbel / Statistics Belgium"
SOURCE_ID = "statbel_maritime_research_candidate"
ROOT_CLAIM = "BELGIAN_SEAPORT_ADMIN_CHAIN_CANDIDATE"
RIGHTS_NOTE = "CC_BY_4_0_STATBEL_OWNED_CONTENT_SUBJECT_TO_THIRD_PARTY_EXCEPTIONS"
SCOPE = "Belgian sea ports; annual cargo loaded and unloaded, 2023 and 2024, thousand tonnes"
CONTENT = {
    TERMS_RECIPE: ("TERMS_REVIEW", "Statbel reuse terms for Statbel-owned content."),
    DATA_RECIPE: ("SAME_CHAIN_SCOPE_REVIEW", "Statbel Belgian maritime cargo series; not independent Eurostat corroboration."),
}
FIELDS = {"version", "recipe", "publisher", "source_id", "upstream_root_claim",
          "original_url", "final_url", "rights_url", "rights_note", "scope",
          "need_type", "requirement", "acquired_at", "expires_at",
          "acquired_utc", "media_type", "byte_length", "content_sha256",
          "terms_candidate_id", "collection_authority", "publisher_release_extracted",
          "revision_policy", "http_last_modified", "http_etag", *BOUNDARY}


def validate_statbel_recipe(recipe):
    if recipe not in (TERMS_RECIPE, DATA_RECIPE):
        raise ResearchAcquisitionError("RECIPE_UNSUPPORTED")
    expected = STATBEL_TERMS_URL if recipe == TERMS_RECIPE else STATBEL_DATA_URL
    url = STATBEL_RECIPES[recipe]
    parsed = urlsplit(url)
    if (url != expected or parsed.scheme != "https"
            or parsed.netloc != "statbel.fgov.be" or parsed.query or parsed.fragment
            or any(ord(char) < 33 or char == "\\" for char in url)):
        raise ResearchAcquisitionError("RECIPE_URL_INVALID")
    return url, parsed.hostname, parsed.path


class _VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, _attrs):
        if tag in {"script", "style"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def _validate_visible_identity(recipe, content):
    try:
        parser = _VisibleText()
        parser.feed(content.decode("utf-8"))
        parser.close()
    except UnicodeError as error:
        raise ResearchAcquisitionError("CONTENT_ENCODING_INVALID") from error
    visible = " ".join(" ".join(parser.parts).split()).casefold()
    markers = (("cc by 4.0", "statbel", "general terms of use") if recipe == TERMS_RECIPE
               else ("sea transport", "belgian sea ports", "cargo loaded",
                     "cargo unloaded", "2023", "2024", "source: statbel"))
    if not all(marker in visible for marker in markers):
        raise ResearchAcquisitionError("CONTENT_IDENTITY_INVALID")


class _TableRows(HTMLParser):
    """Collect literal cells; interpretation remains a separate review step."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables, self.rows, self.row = [], None, None
        self.cell = None

    def handle_starttag(self, tag, _attrs):
        if tag == "table":
            if self.rows is not None:
                raise ResearchAcquisitionError("STATBEL_NESTED_TABLE")
            self.rows = []
        elif self.rows is not None and tag == "tr":
            if self.row is not None:
                raise ResearchAcquisitionError("STATBEL_ROW_SHAPE_INVALID")
            self.row = []
        elif self.row is not None and tag in {"td", "th"}:
            if self.cell is not None:
                raise ResearchAcquisitionError("STATBEL_CELL_SHAPE_INVALID")
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in {"td", "th"} and self.cell is not None:
            self.row.append(" ".join(" ".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if self.cell is not None:
                raise ResearchAcquisitionError("STATBEL_CELL_SHAPE_INVALID")
            self.rows.append(self.row)
            self.row = None
        elif tag == "table" and self.rows is not None:
            if self.row is not None:
                raise ResearchAcquisitionError("STATBEL_ROW_SHAPE_INVALID")
            self.tables.append(self.rows)
            self.rows = None


def extract_maritime_table(content):
    """Decode fixed 2023/2024 rows, without claiming Eurostat comparability."""
    if not isinstance(content, bytes) or not 0 < len(content) <= MAX_FILE:
        raise ResearchAcquisitionError("STATBEL_CONTENT_SIZE_INVALID")
    _validate_visible_identity(DATA_RECIPE, content)
    parser = _TableRows()
    parser.feed(content.decode("utf-8"))
    parser.close()
    tables = [rows for rows in parser.tables if rows and rows[0]
              and rows[0][0].startswith("Sea transport (")
              and "2023" in rows[0] and "2024" in rows[0]]
    if len(tables) != 1:
        raise ResearchAcquisitionError("STATBEL_TABLE_AMBIGUOUS_OR_MISSING")
    rows = tables[0]
    years = rows[0][1:]
    if len(years) != len(set(years)) or years.count("2023") != 1 or years.count("2024") != 1:
        raise ResearchAcquisitionError("STATBEL_YEAR_COLUMNS_INVALID")
    wanted = {"Cargo loaded (x 1,000 t)": "loaded_thousand_tonnes",
              "Cargo unloaded (x 1,000 t)": "unloaded_thousand_tonnes"}
    extracted = {}
    for row in rows[1:]:
        if row and row[0] in wanted:
            if row[0] in extracted or len(row) != len(years) + 1:
                raise ResearchAcquisitionError("STATBEL_MEASUREMENT_AMBIGUOUS")
            values = {}
            for year in ("2023", "2024"):
                raw = row[1 + years.index(year)]
                if re.fullmatch(r"(?:0|[1-9][0-9]{0,2}(?:,[0-9]{3})*)", raw) is None:
                    raise ResearchAcquisitionError("STATBEL_VALUE_INVALID")
                values[year] = int(raw.replace(",", ""))
            extracted[row[0]] = values
    if set(extracted) != set(wanted):
        raise ResearchAcquisitionError("STATBEL_MEASUREMENT_MISSING")
    loaded, unloaded = extracted["Cargo loaded (x 1,000 t)"], extracted["Cargo unloaded (x 1,000 t)"]
    return [{"year": int(year), "loaded_thousand_tonnes": loaded[year],
             "unloaded_thousand_tonnes": unloaded[year],
             "sum_thousand_tonnes": loaded[year] + unloaded[year]}
            for year in ("2023", "2024")]


class StatbelResearchQuarantine(ResearchQuarantine):
    """Same atomic byte store as Eurostat, with a disjoint exact descriptor."""

    def _validate(self, candidate_id, descriptor, content, *, now, expected_recipe=None):
        if (not isinstance(descriptor, dict) or set(descriptor) != FIELDS
                or sha256(canonical(descriptor)).hexdigest() != candidate_id
                or any(descriptor.get(key) != value for key, value in BOUNDARY.items())
                or descriptor.get("version") != "0.1.0"
                or descriptor.get("collection_authority") != AUTHORITY
                or descriptor.get("publisher") != PUBLISHER
                or descriptor.get("source_id") != SOURCE_ID
                or descriptor.get("upstream_root_claim") != ROOT_CLAIM
                or descriptor.get("rights_url") != STATBEL_TERMS_URL
                or descriptor.get("rights_note") != RIGHTS_NOTE
                or descriptor.get("scope") != SCOPE
                or descriptor.get("publisher_release_extracted") != "UNAVAILABLE"
                or descriptor.get("revision_policy") != "UNCONFIRMED"
                or descriptor.get("media_type") != "text/html"
                or type(descriptor.get("byte_length")) is not int
                or descriptor["byte_length"] != len(content) or not content
                or descriptor.get("content_sha256") != sha256(content).hexdigest()):
            raise ResearchAcquisitionError("CANDIDATE_INTEGRITY_INVALID")
        if expected_recipe is not None and descriptor["recipe"] != expected_recipe:
            raise ResearchAcquisitionError("CANDIDATE_TERMS_INVALID")
        url, _, _ = validate_statbel_recipe(descriptor["recipe"])
        need_type, requirement = CONTENT[descriptor["recipe"]]
        if (descriptor["original_url"] != url or descriptor["final_url"] != url
                or descriptor["need_type"] != need_type
                or descriptor["requirement"] != requirement):
            raise ResearchAcquisitionError("CANDIDATE_URL_OR_SCOPE_INVALID")
        for key in ("http_last_modified", "http_etag"):
            value = descriptor[key]
            if value is not None and (not isinstance(value, str) or not value
                                      or len(value) > 200
                                      or any(ord(char) < 32 for char in value)):
                raise ResearchAcquisitionError("CANDIDATE_HTTP_VERSION_INVALID")
        acquired, expiry = descriptor["acquired_at"], descriptor["expires_at"]
        if (type(acquired) is not int or type(expiry) is not int
                or not 0 <= acquired <= now < expiry or expiry != acquired + 86400
                or descriptor["acquired_utc"] != datetime.fromtimestamp(
                    acquired, timezone.utc).isoformat()):
            raise ResearchAcquisitionError("CANDIDATE_NOT_CURRENT")
        _validate_visible_identity(descriptor["recipe"], content)
        if descriptor["recipe"] == TERMS_RECIPE:
            if descriptor["terms_candidate_id"] is not None:
                raise ResearchAcquisitionError("CANDIDATE_TERMS_INVALID")
        else:
            self.read(descriptor["terms_candidate_id"], now=now,
                      expected_recipe=TERMS_RECIPE)


class StatbelResearchAcquirer:
    def __init__(self, root, *, clock=time.time, monotonic=time.monotonic,
                 resolver=socket.getaddrinfo, transport=pinned_response):
        self.quarantine = StatbelResearchQuarantine(root)
        self.clock, self.monotonic = clock, monotonic
        self.resolver, self.transport = resolver, transport
        self.budget = SessionBudget()

    def acquire(self, recipe, *, terms_candidate_id=None):
        url, host, path = validate_statbel_recipe(recipe)
        now = int(self.clock())
        if now < 0:
            raise ResearchAcquisitionError("CLOCK_INVALID")
        if recipe == TERMS_RECIPE:
            if terms_candidate_id is not None:
                raise ResearchAcquisitionError("CANDIDATE_TERMS_INVALID")
        else:
            self.quarantine.read(terms_candidate_id, now=now,
                                 expected_recipe=TERMS_RECIPE)
        if self.budget.attempts >= 100 or self.budget.received_bytes >= MAX_SESSION:
            raise ResearchAcquisitionError("SESSION_BUDGET_EXHAUSTED")
        self.budget.attempts += 1
        addresses = public_addresses(host, self.resolver)
        deadline = self.monotonic() + 30
        with self.transport(host, addresses[0], path) as response:
            headers = {}
            for key, value in response.getheaders():
                key = key.lower()
                if key in {"content-length", "content-type", "content-encoding",
                           "transfer-encoding", "last-modified", "etag"} and key in headers:
                    raise ResearchAcquisitionError("RESPONSE_DUPLICATE_HEADER")
                headers[key] = value.strip()
            if response.status != 200:
                raise ResearchAcquisitionError("RESPONSE_STATUS_REJECTED")
            if headers.get("content-encoding", "identity").lower() != "identity":
                raise ResearchAcquisitionError("RESPONSE_ENCODING_REJECTED")
            if headers.get("content-type", "").split(";", 1)[0].lower() != "text/html":
                raise ResearchAcquisitionError("RESPONSE_MEDIA_REJECTED")
            length, transfer = headers.get("content-length"), headers.get("transfer-encoding")
            if transfer is not None and (transfer.lower() != "chunked" or length is not None):
                raise ResearchAcquisitionError("RESPONSE_FRAMING_REJECTED")
            if length is not None and (re.fullmatch(r"[0-9]+", length) is None
                                       or not 0 < int(length) <= MAX_FILE):
                raise ResearchAcquisitionError("RESPONSE_SIZE_REJECTED")
            chunks, size = [], 0
            while True:
                if self.monotonic() >= deadline:
                    raise ResearchAcquisitionError("RESPONSE_DEADLINE")
                amount = min(65536, MAX_FILE - size + 1,
                             MAX_SESSION - self.budget.received_bytes + 1)
                try:
                    chunk = response.read1(amount)
                except http.client.IncompleteRead as error:
                    self.budget.received_bytes += len(error.partial)
                    raise ResearchAcquisitionError("RESPONSE_TRUNCATED") from error
                self.budget.received_bytes += len(chunk)
                size += len(chunk)
                if size > MAX_FILE or self.budget.received_bytes > MAX_SESSION:
                    raise ResearchAcquisitionError("RESPONSE_SIZE_REJECTED")
                if not chunk:
                    break
                chunks.append(chunk)
            if not size or (length is not None and size != int(length)):
                raise ResearchAcquisitionError("RESPONSE_TRUNCATED")
            content = b"".join(chunks)
        if self.monotonic() >= deadline:
            raise ResearchAcquisitionError("RESPONSE_DEADLINE")
        finished = int(self.clock())
        if not now <= finished < now + 30:
            raise ResearchAcquisitionError("ACQUISITION_CLOCK_OR_DEADLINE")
        _validate_visible_identity(recipe, content)
        if terms_candidate_id is not None:
            self.quarantine.read(terms_candidate_id, now=finished,
                                 expected_recipe=TERMS_RECIPE)
        need_type, requirement = CONTENT[recipe]
        descriptor = {"version": "0.1.0", "recipe": recipe,
            "publisher": PUBLISHER, "source_id": SOURCE_ID,
            "upstream_root_claim": ROOT_CLAIM, "original_url": url, "final_url": url,
            "rights_url": STATBEL_TERMS_URL, "rights_note": RIGHTS_NOTE,
            "scope": SCOPE, "need_type": need_type, "requirement": requirement,
            "acquired_at": now, "expires_at": now + 86400,
            "acquired_utc": datetime.fromtimestamp(now, timezone.utc).isoformat(),
            "media_type": "text/html", "byte_length": size,
            "content_sha256": sha256(content).hexdigest(),
            "terms_candidate_id": terms_candidate_id,
            "collection_authority": AUTHORITY,
            "publisher_release_extracted": "UNAVAILABLE",
            "revision_policy": "UNCONFIRMED",
            "http_last_modified": headers.get("last-modified"),
            "http_etag": headers.get("etag"), **BOUNDARY}
        identity = self.quarantine.retain(descriptor, content)
        return {"candidate_id": identity, **descriptor}


def main():
    import argparse
    from pathlib import Path
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--recipe", required=True, choices=(TERMS_RECIPE, DATA_RECIPE))
    parser.add_argument("--terms-candidate-id")
    args = parser.parse_args()
    session = StatbelResearchAcquirer(args.root)
    receipt = session.acquire(args.recipe, terms_candidate_id=args.terms_candidate_id)
    print(json.dumps({"receipt": receipt, "budget": vars(session.budget)},
                     ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
