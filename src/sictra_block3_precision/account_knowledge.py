"""Shadow-only enrichment from an account's approved official website.

This module deliberately treats website text as untrusted source material. It
captures attributable declarations and makes them available as *hypotheses*;
it never turns a page into a fact, a delivery permission, or an instruction.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from hashlib import sha256
from html.parser import HTMLParser
import ipaddress
import re
import socket
from typing import Literal, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.robotparser import RobotFileParser

from .context import ContextSignal
from .contracts import EvidenceRef, PrecisionContractViolation, fingerprint, require_text


PageKind = Literal["HOME", "ABOUT", "SERVICES", "INDUSTRIES", "CONTACT", "OTHER"]
_PAGE_KINDS = frozenset(PageKind.__args__)
_INSTRUCTION_PATTERNS = (
    "ignore previous instructions", "ignore all previous instructions",
    "system prompt", "developer message", "you are chatgpt", "act as an ai",
    "do not follow the", "reveal your instructions",
)
_TOKEN = re.compile(r"[a-z0-9][a-z0-9_-]{1,}", re.IGNORECASE)


def _canonical_url(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PrecisionContractViolation("website URL must be non-empty")
    parsed = urlsplit(value.strip())
    if parsed.username or parsed.password or not parsed.hostname:
        raise PrecisionContractViolation("website URL has unsafe authority syntax")
    scheme = parsed.scheme.lower()
    host = parsed.hostname.lower().rstrip(".")
    port = parsed.port
    netloc = host if port is None else f"{host}:{port}"
    path = parsed.path or "/"
    return urlunsplit((scheme, netloc, path, "", ""))


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(sorted(set(item.casefold() for item in _TOKEN.findall(value))))


def _excerpt(value: str, limit: int = 420) -> str:
    value = " ".join(value.split())
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def _page_kind(url: str, title: str) -> PageKind:
    basis = f"{urlsplit(url).path} {title}".casefold()
    if any(term in basis for term in ("about", "nosotros", "company", "empresa")):
        return "ABOUT"
    if any(term in basis for term in ("service", "solution", "producto", "servicio")):
        return "SERVICES"
    if any(term in basis for term in ("industr", "sector", "market", "mercado")):
        return "INDUSTRIES"
    if any(term in basis for term in ("contact", "contacto", "location", "ubicacion")):
        return "CONTACT"
    if urlsplit(url).path in ("", "/"):
        return "HOME"
    return "OTHER"


def _is_instruction_like(value: str) -> bool:
    normalized = " ".join(value.casefold().split())
    return any(pattern in normalized for pattern in _INSTRUCTION_PATTERNS)


@dataclass(frozen=True, slots=True)
class OfficialWebsitePolicy:
    policy_id: str
    authority_reference: str
    user_agent: str = "TeleCareOS-AccountResearch/0.1"
    allowed_schemes: tuple[str, ...] = ("https",)
    max_pages: int = 12
    max_depth: int = 2
    max_bytes_per_page: int = 512_000
    max_observations_per_page: int = 10
    retention_seconds: int = 31_536_000
    allow_subdomains: bool = True

    def __post_init__(self) -> None:
        for name in ("policy_id", "authority_reference", "user_agent"):
            require_text(name, getattr(self, name))
        schemes = tuple(item.casefold().strip() for item in self.allowed_schemes)
        if not schemes or any(item not in {"http", "https"} for item in schemes):
            raise PrecisionContractViolation("allowed_schemes must be governed HTTP schemes")
        object.__setattr__(self, "allowed_schemes", schemes)
        for name in (
            "max_pages", "max_depth", "max_bytes_per_page", "max_observations_per_page",
            "retention_seconds",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise PrecisionContractViolation(f"{name} must be a positive integer")
        if self.max_pages > 100 or self.max_depth > 5 or self.max_bytes_per_page > 2_000_000:
            raise PrecisionContractViolation("official website crawl policy exceeds bounded shadow limits")


@dataclass(frozen=True, slots=True)
class AccountSeed:
    tenant_id: str
    account_id: str
    official_url: str
    authorized_purpose: str

    def __post_init__(self) -> None:
        for name in ("tenant_id", "account_id", "official_url", "authorized_purpose"):
            require_text(name, getattr(self, name))
        object.__setattr__(self, "official_url", _canonical_url(self.official_url))

    @property
    def official_host(self) -> str:
        host = urlsplit(self.official_url).hostname
        if host is None:
            raise PrecisionContractViolation("official_url lacks hostname")
        return host.casefold().rstrip(".")


@dataclass(frozen=True, slots=True)
class WebsiteFetchResponse:
    requested_url: str
    final_url: str
    status: int
    headers: tuple[tuple[str, str], ...]
    body: bytes
    fetched_at: int

    def __post_init__(self) -> None:
        for name in ("requested_url", "final_url"):
            require_text(name, getattr(self, name))
        if not isinstance(self.status, int) or not 100 <= self.status <= 599:
            raise PrecisionContractViolation("HTTP response status is invalid")
        if not isinstance(self.fetched_at, int) or self.fetched_at < 0:
            raise PrecisionContractViolation("fetch timestamp is invalid")
        object.__setattr__(self, "headers", tuple((str(key), str(value)) for key, value in self.headers))
        object.__setattr__(self, "body", bytes(self.body))

    def header(self, name: str) -> str | None:
        lowered = name.casefold()
        for key, value in self.headers:
            if key.casefold() == lowered:
                return value
        return None


class WebsiteFetcher(Protocol):
    def fetch(self, url: str, *, timeout_seconds: int, max_bytes: int) -> WebsiteFetchResponse:
        """Return a bounded response; implementations must not execute page content."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


class SafeUrllibWebsiteFetcher:
    """Minimal public-web fetcher with SSRF checks and manually checked redirects."""

    def __init__(
        self,
        *,
        now: int,
        approved_host: str,
        allow_subdomains: bool = True,
        max_redirects: int = 3,
    ) -> None:
        if not isinstance(now, int) or now < 0 or max_redirects < 0:
            raise PrecisionContractViolation("safe fetcher requires logical time and valid redirect bound")
        normalized_host = approved_host.strip().casefold().rstrip(".")
        if not normalized_host or any(token in normalized_host for token in ("://", "/", "@", ":")):
            raise PrecisionContractViolation("safe fetcher requires one approved DNS host")
        self._now = now
        self._max_redirects = max_redirects
        self._approved_host = normalized_host
        self._allow_subdomains = allow_subdomains
        self._opener = build_opener(_NoRedirect())

    def _assert_approved_target(self, url: str) -> None:
        host = (urlsplit(url).hostname or "").casefold().rstrip(".")
        if host != self._approved_host and not (
            self._allow_subdomains and host.endswith("." + self._approved_host)
        ):
            raise PrecisionContractViolation("web redirect leaves the approved official domain")

    @staticmethod
    def _assert_public_target(url: str) -> None:
        parsed = urlsplit(url)
        if parsed.scheme.casefold() not in {"http", "https"} or parsed.username or parsed.password:
            raise PrecisionContractViolation("web fetch target is not an unauthenticated HTTP(S) URL")
        if parsed.port not in {None, 80, 443} or not parsed.hostname:
            raise PrecisionContractViolation("web fetch target uses an unapproved host or port")
        host = parsed.hostname.rstrip(".")
        try:
            literal = ipaddress.ip_address(host)
            addresses = (literal,)
        except ValueError:
            try:
                addresses = tuple({
                    ipaddress.ip_address(item[4][0])
                    for item in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
                })
            except socket.gaierror as error:
                raise PrecisionContractViolation("web fetch target cannot be resolved") from error
        if not addresses or any(not address.is_global for address in addresses):
            raise PrecisionContractViolation("web fetch target resolves to a non-public address")

    def fetch(self, url: str, *, timeout_seconds: int, max_bytes: int) -> WebsiteFetchResponse:
        if timeout_seconds < 1 or max_bytes < 1:
            raise PrecisionContractViolation("fetch limits must be positive")
        current = _canonical_url(url)
        for _ in range(self._max_redirects + 1):
            self._assert_approved_target(current)
            self._assert_public_target(current)
            request = Request(current, headers={"User-Agent": "TeleCareOS-AccountResearch/0.1"})
            try:
                response = self._opener.open(request, timeout=timeout_seconds)
                status = int(response.status)
                headers = tuple((key, value) for key, value in response.headers.items())
                body = response.read(max_bytes + 1)
                if len(body) > max_bytes:
                    raise PrecisionContractViolation("web response exceeds approved byte limit")
                return WebsiteFetchResponse(current, response.url, status, headers, body, self._now)
            except HTTPError as error:
                if error.code not in {301, 302, 303, 307, 308}:
                    return WebsiteFetchResponse(current, current, error.code, (), b"", self._now)
                location = error.headers.get("Location") if error.headers else None
                if not location:
                    raise PrecisionContractViolation("redirect lacks location")
                current = _canonical_url(urljoin(current, location))
            except (OSError, URLError) as error:
                raise PrecisionContractViolation("official website fetch failed") from error
        raise PrecisionContractViolation("web redirect limit exceeded")


class _OfficialPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: list[str] = []
        self.description: str | None = None
        self.headings: list[str] = []
        self.text: list[str] = []
        self.links: list[str] = []
        self._suppressed = 0
        self._heading_level: str | None = None
        self._heading_parts: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.casefold()
        attributes = {key.casefold(): value or "" for key, value in attrs}
        if tag in {"script", "style", "template", "noscript", "svg"}:
            self._suppressed += 1
        elif tag == "title":
            self._in_title = True
        elif tag in {"h1", "h2", "h3"}:
            self._heading_level = tag
            self._heading_parts = []
        elif tag == "meta" and attributes.get("name", "").casefold() == "description":
            self.description = attributes.get("content") or None
        elif tag == "a" and attributes.get("href"):
            self.links.append(attributes["href"])

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        if tag in {"script", "style", "template", "noscript", "svg"} and self._suppressed:
            self._suppressed -= 1
        elif tag == "title":
            self._in_title = False
        elif tag == self._heading_level:
            heading = " ".join(self._heading_parts).strip()
            if heading:
                self.headings.append(heading)
            self._heading_level = None
            self._heading_parts = []

    def handle_data(self, data: str) -> None:
        if self._suppressed:
            return
        normalized = " ".join(data.split())
        if not normalized:
            return
        self.text.append(normalized)
        if self._in_title:
            self.title.append(normalized)
        if self._heading_level:
            self._heading_parts.append(normalized)


@dataclass(frozen=True, slots=True)
class CrawledPage:
    url: str
    kind: PageKind
    title: str
    description: str | None
    headings: tuple[str, ...]
    visible_text: str
    content_hash: str
    captured_at: int
    links: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WebObservation:
    observation_id: str
    tenant_id: str
    account_id: str
    source_url: str
    page_kind: PageKind
    label: str
    excerpt: str
    tags: tuple[str, ...]
    captured_at: int
    expires_at: int
    source_content_hash: str
    evidence: EvidenceRef
    quarantined: bool
    restrictions: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in (
            "observation_id", "tenant_id", "account_id", "source_url", "label",
            "excerpt", "source_content_hash",
        ):
            require_text(name, getattr(self, name))
        if self.page_kind not in _PAGE_KINDS:
            raise PrecisionContractViolation("website page kind is not governed")
        if self.expires_at < self.captured_at:
            raise PrecisionContractViolation("website observation expiry precedes capture")
        if self.evidence.observed_at != self.captured_at:
            raise PrecisionContractViolation("website observation evidence time mismatch")
        object.__setattr__(self, "tags", tuple(sorted(set(_tokens(" ".join(self.tags))))))
        object.__setattr__(self, "restrictions", tuple(self.restrictions))


@dataclass(frozen=True, slots=True)
class AccountKnowledgeDossier:
    dossier_id: str
    tenant_id: str
    account_id: str
    official_url: str
    policy_id: str
    captured_at: int
    expires_at: int
    observations: tuple[WebObservation, ...]
    quarantined_observation_ids: tuple[str, ...]
    skipped_urls: tuple[str, ...]
    restrictions: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("dossier_id", "tenant_id", "account_id", "official_url", "policy_id"):
            require_text(name, getattr(self, name))
        if self.expires_at < self.captured_at:
            raise PrecisionContractViolation("dossier expiry precedes capture")
        if any(
            item.tenant_id != self.tenant_id or item.account_id != self.account_id
            for item in self.observations
        ):
            raise PrecisionContractViolation("dossier observations must share tenant and account identity")
        object.__setattr__(self, "observations", tuple(self.observations))
        object.__setattr__(self, "quarantined_observation_ids", tuple(self.quarantined_observation_ids))
        object.__setattr__(self, "skipped_urls", tuple(self.skipped_urls))
        object.__setattr__(self, "restrictions", tuple(self.restrictions))

    @property
    def output_fingerprint(self) -> str:
        return fingerprint(self)

    def to_context_hypotheses(self, *, insight_id: str) -> tuple[ContextSignal, ...]:
        """Expose official-site declarations as M05 hypotheses, never as facts."""
        require_text("insight_id", insight_id)
        signals = []
        for observation in self.observations:
            if observation.quarantined:
                continue
            statement = f"Official website declaration ({observation.label}): {observation.excerpt}"
            signals.append(ContextSignal(
                signal_id=f"web-context:{observation.observation_id}",
                insight_id=insight_id,
                target_id=self.account_id,
                scope="ACCOUNT",
                claim_key=f"web-declaration:{observation.observation_id}",
                statement=statement,
                kind="HYPOTHESIS",
                polarity=1,
                tags=observation.tags or ("official-website",),
                valid_from=observation.captured_at,
                valid_until=observation.expires_at,
                evidence=observation.evidence,
            ))
        return tuple(signals)


class OfficialWebsiteCrawler:
    """Bounded crawler. Its only authority is to retrieve approved public pages."""

    def __init__(self, *, fetcher: WebsiteFetcher, timeout_seconds: int = 10) -> None:
        if timeout_seconds < 1:
            raise PrecisionContractViolation("crawler timeout must be positive")
        self._fetcher = fetcher
        self._timeout_seconds = timeout_seconds

    @staticmethod
    def _in_scope(url: str, *, seed: AccountSeed, policy: OfficialWebsitePolicy) -> bool:
        parsed = urlsplit(url)
        if parsed.scheme.casefold() not in policy.allowed_schemes or not parsed.hostname:
            return False
        host = parsed.hostname.casefold().rstrip(".")
        root = seed.official_host
        return host == root or (policy.allow_subdomains and host.endswith("." + root))

    @staticmethod
    def _parse_robots(raw: str, robots_url: str) -> RobotFileParser:
        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(raw.splitlines())
        return parser

    def crawl(self, *, seed: AccountSeed, policy: OfficialWebsitePolicy, now: int) -> tuple[tuple[CrawledPage, ...], tuple[str, ...]]:
        if not isinstance(now, int) or now < 0:
            raise PrecisionContractViolation("crawler requires non-negative logical time")
        if not self._in_scope(seed.official_url, seed=seed, policy=policy):
            raise PrecisionContractViolation("seed official URL violates website policy")
        parsed_seed = urlsplit(seed.official_url)
        robots_url = urlunsplit((parsed_seed.scheme, parsed_seed.netloc, "/robots.txt", "", ""))
        robots = self._fetcher.fetch(robots_url, timeout_seconds=self._timeout_seconds, max_bytes=32_000)
        if not self._in_scope(_canonical_url(robots.final_url), seed=seed, policy=policy):
            return (), (f"ROBOTS_REDIRECT_OUT_OF_SCOPE:{robots.final_url}",)
        if robots.status == 404:
            robot_policy = None
        elif 200 <= robots.status < 300:
            robot_policy = self._parse_robots(robots.body.decode("utf-8", "replace"), robots_url)
        else:
            return (), (f"ROBOTS_UNAVAILABLE:{robots_url}",)

        queue: deque[tuple[str, int]] = deque(((seed.official_url, 0),))
        visited: set[str] = set()
        pages: list[CrawledPage] = []
        skipped: list[str] = []
        while queue and len(pages) < policy.max_pages:
            candidate, depth = queue.popleft()
            candidate = _canonical_url(candidate)
            if candidate in visited:
                continue
            visited.add(candidate)
            if not self._in_scope(candidate, seed=seed, policy=policy):
                skipped.append(f"OUT_OF_SCOPE:{candidate}")
                continue
            if robot_policy is not None and not robot_policy.can_fetch(policy.user_agent, candidate):
                skipped.append(f"ROBOTS_DISALLOWED:{candidate}")
                continue
            response = self._fetcher.fetch(candidate, timeout_seconds=self._timeout_seconds, max_bytes=policy.max_bytes_per_page)
            final_url = _canonical_url(response.final_url)
            if not self._in_scope(final_url, seed=seed, policy=policy):
                skipped.append(f"REDIRECT_OUT_OF_SCOPE:{final_url}")
                continue
            content_type = (response.header("Content-Type") or "").casefold()
            if response.status < 200 or response.status >= 300:
                skipped.append(f"HTTP_{response.status}:{candidate}")
                continue
            if "html" not in content_type:
                skipped.append(f"NON_HTML:{final_url}")
                continue
            parser = _OfficialPageParser()
            parser.feed(response.body.decode("utf-8", "replace"))
            parser.close()
            title = _excerpt(" ".join(parser.title), 240)
            visible = _excerpt(" ".join(parser.text), 4_000)
            page = CrawledPage(
                url=final_url, kind=_page_kind(final_url, title), title=title,
                description=_excerpt(parser.description or "", 500) or None,
                headings=tuple(_excerpt(item, 240) for item in parser.headings[:10]),
                visible_text=visible, content_hash=sha256(response.body).hexdigest(),
                captured_at=response.fetched_at, links=tuple(parser.links),
            )
            pages.append(page)
            if depth >= policy.max_depth:
                continue
            for href in page.links:
                try:
                    next_url = _canonical_url(urljoin(final_url, href))
                except (PrecisionContractViolation, ValueError):
                    skipped.append(f"INVALID_LINK:{href}")
                    continue
                if self._in_scope(next_url, seed=seed, policy=policy):
                    queue.append((next_url, depth + 1))
                else:
                    skipped.append(f"LINK_OUT_OF_SCOPE:{next_url}")
        return tuple(pages), tuple(sorted(set(skipped)))


class AccountKnowledgeEngine:
    """Produces a reviewable dossier from declarations captured by the crawler."""

    def __init__(self, *, crawler: OfficialWebsiteCrawler) -> None:
        self._crawler = crawler

    @staticmethod
    def _observation(*, seed: AccountSeed, policy: OfficialWebsitePolicy, page: CrawledPage, label: str, value: str, ordinal: int) -> WebObservation | None:
        excerpt = _excerpt(value)
        if not excerpt:
            return None
        identity_seed = (seed.tenant_id, seed.account_id, page.url, page.content_hash, label, ordinal, excerpt)
        identity = sha256(repr(identity_seed).encode("utf-8")).hexdigest()
        root = f"official-web:{seed.tenant_id}:{seed.account_id}:{page.content_hash}"
        evidence = EvidenceRef(
            evidence_id=f"web-evidence:{identity}", source_identity=f"OFFICIAL_WEBSITE:{urlsplit(page.url).hostname}",
            root_provenance=root, observed_at=page.captured_at, temporal_state="CURRENT",
            epistemic_state="VERIFIED", confidence="B", provenance_refs=(root, page.url),
        )
        quarantined = _is_instruction_like(excerpt)
        return WebObservation(
            observation_id=f"web-observation:{identity}", tenant_id=seed.tenant_id, account_id=seed.account_id,
            source_url=page.url, page_kind=page.kind, label=label, excerpt=excerpt,
            tags=tuple(sorted(set(_tokens(f"{page.kind} {label} {excerpt}"))))[:30],
            captured_at=page.captured_at, expires_at=page.captured_at + policy.retention_seconds,
            source_content_hash=page.content_hash, evidence=evidence, quarantined=quarantined,
            restrictions=(
                "OFFICIAL_SITE_DECLARATION_NOT_INDEPENDENTLY_VERIFIED",
                "UNTRUSTED_WEB_CONTENT_NOT_INSTRUCTION", "NOT_DELIVERY_PERMISSION",
                "NOT_PERSONAL_DATA_ENRICHMENT",
            ) + (("QUARANTINED_INSTRUCTION_PATTERN",) if quarantined else ()),
        )

    def enrich(self, *, seed: AccountSeed, policy: OfficialWebsitePolicy, now: int) -> AccountKnowledgeDossier:
        pages, skipped = self._crawler.crawl(seed=seed, policy=policy, now=now)
        observations: list[WebObservation] = []
        for page in pages:
            values: list[tuple[str, str]] = []
            if page.title:
                values.append(("PAGE_TITLE", page.title))
            if page.description:
                values.append(("META_DESCRIPTION", page.description))
            values.extend(("HEADING", heading) for heading in page.headings)
            if page.visible_text:
                values.append(("VISIBLE_PAGE_EXCERPT", page.visible_text))
            for ordinal, (label, value) in enumerate(values[: policy.max_observations_per_page]):
                observation = self._observation(seed=seed, policy=policy, page=page, label=label, value=value, ordinal=ordinal)
                if observation is not None:
                    observations.append(observation)
        captured_at = max((page.captured_at for page in pages), default=now)
        unique = tuple(sorted({item.observation_id: item for item in observations}.values(), key=lambda item: item.observation_id))
        return AccountKnowledgeDossier(
            dossier_id=f"account-dossier:{fingerprint((seed, policy.policy_id, unique, skipped))}",
            tenant_id=seed.tenant_id, account_id=seed.account_id, official_url=seed.official_url,
            policy_id=policy.policy_id, captured_at=captured_at, expires_at=captured_at + policy.retention_seconds,
            observations=unique, quarantined_observation_ids=tuple(item.observation_id for item in unique if item.quarantined),
            skipped_urls=skipped,
            restrictions=(
                "SHADOW_ENRICHMENT_ONLY", "NO_CRM_WRITE", "NO_DELIVERY", "NO_FACT_PROMOTION",
                "TENANT_SCOPED", "RETENTION_BOUNDED", "SEMANTIC_RETRIEVAL_NOT_AUTHORITY",
            ),
        )
