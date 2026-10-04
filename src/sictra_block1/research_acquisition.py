"""Explicit agent research downloads into quarantine; never runtime admission."""
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import http.client
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import socket
import ssl
import tempfile
import threading
import time
from urllib.parse import urlsplit

from .common import ContractViolation


class ResearchAcquisitionError(ContractViolation):
    pass


TERMS_URL = "https://ec.europa.eu/eurostat/help/copyright-notice"
METADATA_URL = "https://ec.europa.eu/eurostat/cache/metadata/EN/mar_esms.htm"
NATIONAL_METADATA_RECIPE = "EUROSTAT_BE_MAR_METADATA"
NATIONAL_METADATA_URL = "https://ec.europa.eu/eurostat/cache/metadata/EN/mar_esms_be.htm"
STATISTICS_RECIPE = "EUROSTAT_MAR_BE_2023_2024"
STATISTICS_URL = ("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/tran_r_mago_nm"
                  "?lang=EN&freq=A&tra_meas=FR_LD_NLD&unit=THS_T&geo=BE&sinceTimePeriod=2023&untilTimePeriod=2024")
RECIPES = {"EUROSTAT_REUSE_NOTICE": TERMS_URL, "EUROSTAT_MAR_METADATA": METADATA_URL,
           NATIONAL_METADATA_RECIPE: NATIONAL_METADATA_URL,
           STATISTICS_RECIPE: STATISTICS_URL}
RECIPE_CONTENT = {
    "EUROSTAT_REUSE_NOTICE": ("text/html", "TERMS_REVIEW", "Eurostat reuse notice."),
    "EUROSTAT_MAR_METADATA": ("text/html", "SOURCE_METHODOLOGY", "Source metadata explaining revisions and coverage changes."),
    NATIONAL_METADATA_RECIPE: ("text/html", "NATIONAL_METHODOLOGY_REVIEW",
        "Belgian maritime source origin, coverage and revision methodology; not independent measurement evidence."),
    STATISTICS_RECIPE: ("application/json", "STATISTICAL_SCOPE_REVIEW",
                        "Annual maritime freight loaded and unloaded, Belgium, 2023-2024, thousand tonnes."),
}
MAX_FILE = 8 * 1024 * 1024
MAX_SESSION = 100 * 1024 * 1024
AUTHORITY = "AGENTS.md#owner-authorized-public-source-research--2026-10-03"
BOUNDARY = {"state": "QUARANTINED", "admission": "NOT_ADMITTED", "runtime_effect": "NONE",
            "publication": "BLOCKED", "root_provenance": "UNCONFIRMED"}
FIELDS = {"version", "recipe", "publisher", "source_id", "original_url", "final_url", "need_type",
          "requirement", "acquired_at", "expires_at", "acquired_utc", "media_type", "byte_length",
          "content_sha256", "terms_candidate_id", "collection_authority", *BOUNDARY}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _safe_path(path):
    path = Path(path).absolute()
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ResearchAcquisitionError("QUARANTINE_SYMLINK")
    return path


def validate_recipe(recipe):
    if not isinstance(recipe, str) or recipe not in RECIPES:
        raise ResearchAcquisitionError("RECIPE_UNSUPPORTED")
    url = RECIPES[recipe]
    p = urlsplit(url)
    if (p.scheme != "https" or p.netloc != "ec.europa.eu" or p.fragment
            or (recipe == NATIONAL_METADATA_RECIPE and url != NATIONAL_METADATA_URL)
            or (recipe == STATISTICS_RECIPE and url != STATISTICS_URL)
            or (p.query and not (recipe == STATISTICS_RECIPE and url == STATISTICS_URL))
            or any(ord(c) < 33 or c == "\\" for c in url)):
        raise ResearchAcquisitionError("RECIPE_URL_INVALID")
    return url, p.hostname, p.path + ("?" + p.query if p.query else "")


def public_addresses(host, resolver=socket.getaddrinfo):
    answers = resolver(host, 443, type=socket.SOCK_STREAM)
    addresses = []
    for answer in answers:
        try:
            ip = ipaddress.ip_address(answer[4][0])
        except (ValueError, IndexError, TypeError) as error:
            raise ResearchAcquisitionError("DNS_ANSWER_INVALID") from error
        effective = ip.ipv4_mapped if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped else ip
        if not effective.is_global or effective.is_multicast or effective.is_reserved:
            raise ResearchAcquisitionError("DNS_NON_PUBLIC")
        if str(ip) not in addresses:
            addresses.append(str(ip))
    if not addresses:
        raise ResearchAcquisitionError("DNS_EMPTY")
    return tuple(addresses)


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host, address):
        super().__init__(host, timeout=30, context=ssl.create_default_context())
        self.address = address

    def connect(self):
        raw = socket.create_connection((self.address, 443), timeout=self.timeout)
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except BaseException:
            raw.close()
            raise


@contextmanager
def pinned_response(host, address, path):
    connection = PinnedHTTPSConnection(host, address)
    connection.connect()
    connected = connection.sock
    def abort():
        try:
            connected.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
    deadline = threading.Timer(30, abort)
    deadline.daemon = True
    deadline.start()
    try:
        connection.request("GET", path, headers={"Accept-Encoding": "identity",
            "User-Agent": "Telecare-Laboratory-Research/0.1", "Connection": "close"})
        response = connection.getresponse()
        try:
            yield response
        finally:
            response.close()
    finally:
        deadline.cancel()
        connection.close()


class ResearchQuarantine:
    def __init__(self, root):
        self.root = _safe_path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def read(self, candidate_id, *, now, expected_recipe=None):
        if not isinstance(candidate_id, str) or not re.fullmatch(r"[0-9a-f]{64}", candidate_id):
            raise ResearchAcquisitionError("CANDIDATE_ID_INVALID")
        if type(now) is not int or now < 0:
            raise ResearchAcquisitionError("CLOCK_INVALID")
        folder = _safe_path(self.root / candidate_id)
        manifest_path, content_path = _safe_path(folder / "manifest.json"), _safe_path(folder / "content.bin")
        try:
            if manifest_path.stat().st_size > 16000 or content_path.stat().st_size > MAX_FILE:
                raise ResearchAcquisitionError("CANDIDATE_SIZE_INVALID")
            def unique(pairs):
                result = {}
                for key, value in pairs:
                    if key in result:
                        raise ResearchAcquisitionError("CANDIDATE_DUPLICATE_FIELD")
                    result[key] = value
                return result
            descriptor = json.loads(manifest_path.read_bytes(), object_pairs_hook=unique)
            content = content_path.read_bytes()
        except (OSError, ValueError) as error:
            raise ResearchAcquisitionError("CANDIDATE_READ_INVALID") from error
        self._validate(candidate_id, descriptor, content, now=now, expected_recipe=expected_recipe)
        return descriptor, content

    def _validate(self, candidate_id, descriptor, content, *, now, expected_recipe=None):
        if (not isinstance(descriptor, dict) or set(descriptor) != FIELDS
                or sha256(canonical(descriptor)).hexdigest() != candidate_id
                or any(descriptor.get(k) != v for k, v in BOUNDARY.items())
                or descriptor.get("version") != "0.1.0"
                or descriptor.get("collection_authority") != AUTHORITY
                or descriptor.get("publisher") != "Eurostat / European Commission"
                or descriptor.get("source_id") != "eurostat"
                or type(descriptor.get("byte_length")) is not int
                or descriptor["byte_length"] != len(content) or not content
                or descriptor.get("content_sha256") != sha256(content).hexdigest()):
            raise ResearchAcquisitionError("CANDIDATE_INTEGRITY_INVALID")
        if expected_recipe is not None and descriptor["recipe"] != expected_recipe:
            raise ResearchAcquisitionError("CANDIDATE_TERMS_INVALID")
        url, _, _ = validate_recipe(descriptor["recipe"])
        media_type, need_type, requirement = RECIPE_CONTENT[descriptor["recipe"]]
        if (descriptor["media_type"] != media_type or descriptor["need_type"] != need_type
                or descriptor["requirement"] != requirement):
            raise ResearchAcquisitionError("CANDIDATE_NEED_OR_MEDIA_INVALID")
        if descriptor["original_url"] != url or descriptor["final_url"] != url:
            raise ResearchAcquisitionError("CANDIDATE_URL_INVALID")
        acquired, expiry = descriptor["acquired_at"], descriptor["expires_at"]
        if (type(acquired) is not int or type(expiry) is not int or not 0 <= acquired <= now < expiry
                or expiry != acquired + 86400
                or descriptor["acquired_utc"] != datetime.fromtimestamp(acquired, timezone.utc).isoformat()):
            raise ResearchAcquisitionError("CANDIDATE_NOT_CURRENT")
        if descriptor["recipe"] == "EUROSTAT_REUSE_NOTICE":
            if descriptor["terms_candidate_id"] is not None or descriptor["need_type"] != "TERMS_REVIEW" or descriptor["requirement"] != "Eurostat reuse notice.":
                raise ResearchAcquisitionError("CANDIDATE_TERMS_INVALID")
        else:
            self.read(descriptor["terms_candidate_id"], now=now, expected_recipe="EUROSTAT_REUSE_NOTICE")

    def retain(self, descriptor, content):
        identity = sha256(canonical(descriptor)).hexdigest()
        self._validate(identity, descriptor, content, now=descriptor["acquired_at"])
        final = _safe_path(self.root / identity)
        if final.exists():
            existing, data = self.read(identity, now=descriptor["acquired_at"])
            if existing != descriptor or data != content:
                raise ResearchAcquisitionError("CANDIDATE_REPLAY_COLLISION")
            return identity
        pending = Path(tempfile.mkdtemp(prefix=".pending-", dir=self.root))
        try:
            for name, data in (("content.bin", content), ("manifest.json", canonical(descriptor))):
                with (pending / name).open("xb") as output:
                    output.write(data)
                    output.flush()
                    os.fsync(output.fileno())
            os.rename(pending, final)
        finally:
            if pending.exists():
                shutil.rmtree(pending)
        self.read(identity, now=descriptor["acquired_at"])
        return identity


@dataclass
class SessionBudget:
    attempts: int = 0
    received_bytes: int = 0


class ResearchAcquirer:
    def __init__(self, root, *, clock=time.time, monotonic=time.monotonic,
                 resolver=socket.getaddrinfo, transport=pinned_response):
        self.quarantine = ResearchQuarantine(root)
        self.clock, self.monotonic = clock, monotonic
        self.resolver, self.transport = resolver, transport
        self.budget = SessionBudget()

    def acquire(self, recipe, *, terms_candidate_id=None):
        url, host, path = validate_recipe(recipe)
        now = int(self.clock())
        if now < 0:
            raise ResearchAcquisitionError("CLOCK_INVALID")
        media_type, need_type, requirement = RECIPE_CONTENT[recipe]
        if recipe != "EUROSTAT_REUSE_NOTICE":
            self.quarantine.read(terms_candidate_id, now=now, expected_recipe="EUROSTAT_REUSE_NOTICE")
        elif terms_candidate_id is not None:
            raise ResearchAcquisitionError("CANDIDATE_TERMS_INVALID")
        if self.budget.attempts >= 100 or self.budget.received_bytes >= MAX_SESSION:
            raise ResearchAcquisitionError("SESSION_BUDGET_EXHAUSTED")
        self.budget.attempts += 1
        addresses = public_addresses(host, self.resolver)
        deadline = self.monotonic() + 30
        with self.transport(host, addresses[0], path) as response:
            headers = {}
            for key, value in response.getheaders():
                key = key.lower()
                if key in {"content-length", "content-type", "content-encoding", "transfer-encoding"} and key in headers:
                    raise ResearchAcquisitionError("RESPONSE_DUPLICATE_FRAMING")
                headers[key] = value.strip()
            if response.status != 200:
                raise ResearchAcquisitionError("RESPONSE_STATUS_REJECTED")
            if headers.get("content-encoding", "identity").lower() != "identity":
                raise ResearchAcquisitionError("RESPONSE_ENCODING_REJECTED")
            if headers.get("content-type", "").split(";", 1)[0].lower() != media_type:
                raise ResearchAcquisitionError("RESPONSE_MEDIA_REJECTED")
            length, transfer = headers.get("content-length"), headers.get("transfer-encoding")
            if transfer is not None and (transfer.lower() != "chunked" or length is not None):
                raise ResearchAcquisitionError("RESPONSE_FRAMING_REJECTED")
            if length is not None and (not re.fullmatch(r"[0-9]+", length) or not 0 < int(length) <= MAX_FILE):
                raise ResearchAcquisitionError("RESPONSE_SIZE_REJECTED")
            chunks, size = [], 0
            while True:
                if self.monotonic() >= deadline:
                    raise ResearchAcquisitionError("RESPONSE_DEADLINE")
                amount = min(65536, MAX_FILE - size + 1, MAX_SESSION - self.budget.received_bytes + 1)
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
        if terms_candidate_id is not None:
            self.quarantine.read(terms_candidate_id, now=finished)
        descriptor = {"version": "0.1.0", "recipe": recipe, "publisher": "Eurostat / European Commission",
            "source_id": "eurostat", "original_url": url, "final_url": url,
            "need_type": need_type, "requirement": requirement,
            "acquired_at": now, "expires_at": now + 86400,
            "acquired_utc": datetime.fromtimestamp(now, timezone.utc).isoformat(), "media_type": media_type,
            "byte_length": size, "content_sha256": sha256(content).hexdigest(),
            "terms_candidate_id": terms_candidate_id, "collection_authority": AUTHORITY, **BOUNDARY}
        identity = self.quarantine.retain(descriptor, content)
        return {"candidate_id": identity, **descriptor}


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--recipe", required=True, choices=tuple(RECIPES))
    parser.add_argument("--terms-candidate-id")
    args = parser.parse_args()
    session = ResearchAcquirer(args.root)
    receipt = session.acquire(args.recipe, terms_candidate_id=args.terms_candidate_id)
    print(json.dumps({"receipt": receipt, "budget": vars(session.budget)}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
