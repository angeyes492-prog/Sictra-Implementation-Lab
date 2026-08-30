"""Governed shadow orchestration from an Excel account seed to durable evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import hmac
import json
from pathlib import Path
import sqlite3
from threading import RLock
from typing import Any, Literal, Protocol

from .account_knowledge import (
    AccountKnowledgeDossier,
    AccountKnowledgeEngine,
    AccountSeed,
    OfficialWebsiteCrawler,
    OfficialWebsitePolicy,
    SafeUrllibWebsiteFetcher,
)
from .account_memory import AccountKnowledgeStore
from .contracts import PrecisionCapacityExceeded, PrecisionContractViolation, fingerprint, require_text
from .excel_account_import import ExcelAccountImportBatch, ImportedAccountSeed


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def _encoded(value: Any) -> str:
    return json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True, slots=True)
class AccountResearchPolicy:
    policy_id: str
    authority_reference: str
    receipt_retention_seconds: int = 31_536_000
    max_receipts: int = 100_000

    def __post_init__(self) -> None:
        for name in ("policy_id", "authority_reference"):
            require_text(name, getattr(self, name))
        for name in ("receipt_retention_seconds", "max_receipts"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise PrecisionContractViolation(f"{name} must be a positive integer")


@dataclass(frozen=True, slots=True)
class ResearchApproval:
    approval_id: str
    tenant_id: str
    import_id: str
    workbook_content_hash: str
    account_id: str
    row_number: int
    seed_fingerprint: str
    approval_reference: str
    reviewer_reference: str
    approved_at: int
    expires_at: int
    decision: Literal["APPROVED"] = "APPROVED"

    def __post_init__(self) -> None:
        for name in (
            "approval_id", "tenant_id", "import_id", "workbook_content_hash", "account_id",
            "seed_fingerprint", "approval_reference", "reviewer_reference",
        ):
            require_text(name, getattr(self, name))
        if not isinstance(self.row_number, int) or self.row_number < 2:
            raise PrecisionContractViolation("approval must bind a data row")
        if not isinstance(self.approved_at, int) or not isinstance(self.expires_at, int):
            raise PrecisionContractViolation("approval times must be integer timestamps")
        if self.approved_at < 0 or self.expires_at < self.approved_at:
            raise PrecisionContractViolation("approval expiry precedes approval")
        if self.decision != "APPROVED":
            raise PrecisionContractViolation("research approval must be explicitly APPROVED")


@dataclass(frozen=True, slots=True)
class AccountResearchReceipt:
    receipt_id: str
    tenant_id: str
    account_id: str
    approval_id: str
    import_id: str
    dossier_id: str
    dossier_fingerprint: str
    policy_id: str
    captured_at: int
    persisted_at: int
    expires_at: int
    status: Literal["SHADOW_COMPLETED"]
    restrictions: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in (
            "receipt_id", "tenant_id", "account_id", "approval_id", "import_id",
            "dossier_id", "dossier_fingerprint", "policy_id",
        ):
            require_text(name, getattr(self, name))
        if self.status != "SHADOW_COMPLETED":
            raise PrecisionContractViolation("research receipt status is not governed")
        if not all(isinstance(value, int) and value >= 0 for value in (self.captured_at, self.persisted_at, self.expires_at)):
            raise PrecisionContractViolation("research receipt times are invalid")
        if self.captured_at > self.persisted_at:
            raise PrecisionContractViolation("research receipt cannot precede its captured dossier")
        if self.expires_at < self.persisted_at:
            raise PrecisionContractViolation("research receipt expiry precedes persistence")
        object.__setattr__(self, "restrictions", tuple(self.restrictions))


class AccountEnricher(Protocol):
    def enrich(self, *, seed: AccountSeed, policy: OfficialWebsitePolicy, now: int) -> AccountKnowledgeDossier:
        """Return only an official-site, bounded dossier."""


class SafeOfficialAccountEnricher:
    """Constructs an account-bound safe fetcher for one explicit shadow request."""

    def __init__(self, *, timeout_seconds: int = 10) -> None:
        if timeout_seconds < 1:
            raise PrecisionContractViolation("shadow enrichment timeout must be positive")
        self._timeout_seconds = timeout_seconds

    def enrich(self, *, seed: AccountSeed, policy: OfficialWebsitePolicy, now: int) -> AccountKnowledgeDossier:
        fetcher = SafeUrllibWebsiteFetcher(
            now=now, approved_host=seed.official_host, allow_subdomains=policy.allow_subdomains,
        )
        crawler = OfficialWebsiteCrawler(fetcher=fetcher, timeout_seconds=self._timeout_seconds)
        return AccountKnowledgeEngine(crawler=crawler).enrich(seed=seed, policy=policy, now=now)


class ResearchReceiptLedger:
    """Tenant/account-scoped HMAC receipt ledger; not a credential or key vault."""

    _VERSION = 1

    def __init__(self, path: str | Path = ":memory:", *, integrity_key: bytes, max_receipts: int = 100_000) -> None:
        if len(integrity_key) < 32 or max_receipts < 1:
            raise PrecisionContractViolation("research ledger requires a 32-byte integrity key and positive capacity")
        self._key = bytes(integrity_key)
        self._max_receipts = max_receipts
        self._lock = RLock()
        self._db = sqlite3.connect(str(path), check_same_thread=False, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        try:
            self._db.execute("PRAGMA foreign_keys = ON")
            self._initialize()
        except Exception:
            self._db.close()
            raise

    def close(self) -> None:
        self._db.close()

    def _mac(self, value: str) -> str:
        return hmac.new(self._key, value.encode("utf-8"), sha256).hexdigest()

    def _initialize(self) -> None:
        self._db.execute("BEGIN IMMEDIATE")
        try:
            version = self._db.execute("PRAGMA user_version").fetchone()[0]
            if version == 0:
                existing = self._db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
                if existing:
                    raise PrecisionContractViolation("unversioned research ledger must be empty")
                self._db.execute("""CREATE TABLE research_receipts (
                    tenant_id TEXT NOT NULL, account_id TEXT NOT NULL, sequence INTEGER NOT NULL,
                    receipt_id TEXT NOT NULL, persisted_at INTEGER NOT NULL, expires_at INTEGER NOT NULL,
                    record_json TEXT NOT NULL, previous_hash TEXT NOT NULL, record_hash TEXT NOT NULL,
                    PRIMARY KEY(tenant_id, account_id, sequence), UNIQUE(tenant_id, receipt_id)
                )""")
                self._db.execute("""CREATE TABLE research_heads (
                    tenant_id TEXT NOT NULL, account_id TEXT NOT NULL, receipt_count INTEGER NOT NULL,
                    receipt_head TEXT NOT NULL, head_mac TEXT NOT NULL,
                    PRIMARY KEY(tenant_id, account_id)
                )""")
                self._db.execute("""CREATE TABLE research_ledger_metadata (
                    singleton INTEGER PRIMARY KEY CHECK(singleton = 1), max_receipts INTEGER NOT NULL, key_check TEXT NOT NULL
                )""")
                self._db.execute("INSERT INTO research_ledger_metadata VALUES (1, ?, ?)", (
                    self._max_receipts, self._mac(f"research-ledger-v{self._VERSION}:{self._max_receipts}"),
                ))
                self._db.execute(f"PRAGMA user_version = {self._VERSION}")
            elif version != self._VERSION:
                raise PrecisionContractViolation("unsupported research ledger schema version")
            self._assert_schema()
            self._assert_metadata()
            self._db.execute("COMMIT")
        except Exception:
            self._db.execute("ROLLBACK")
            raise

    def _assert_schema(self) -> None:
        actual = {(row["type"], row["name"]) for row in self._db.execute(
            "SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
        ).fetchall()}
        expected = {
            ("table", "research_receipts"), ("table", "research_heads"), ("table", "research_ledger_metadata"),
        }
        if actual != expected:
            raise PrecisionContractViolation("research ledger contains unapproved schema objects")

    def _assert_metadata(self) -> None:
        row = self._db.execute("SELECT max_receipts, key_check FROM research_ledger_metadata WHERE singleton=1").fetchone()
        expected = self._mac(f"research-ledger-v{self._VERSION}:{self._max_receipts}")
        if row is None or row["max_receipts"] != self._max_receipts or not hmac.compare_digest(row["key_check"], expected):
            raise PrecisionContractViolation("research ledger capacity or integrity key mismatch")

    def _head_mac(self, tenant_id: str, account_id: str, count: int, head: str) -> str:
        return self._mac("research-head-v1:" + _encoded((tenant_id, account_id, count, head)))

    def _head(self, tenant_id: str, account_id: str) -> tuple[int, str]:
        row = self._db.execute("SELECT receipt_count, receipt_head, head_mac FROM research_heads WHERE tenant_id=? AND account_id=?", (tenant_id, account_id)).fetchone()
        if row is None:
            return 0, "GENESIS"
        count, head = int(row["receipt_count"]), str(row["receipt_head"])
        if not hmac.compare_digest(row["head_mac"], self._head_mac(tenant_id, account_id, count, head)):
            raise PrecisionContractViolation("research ledger head integrity verification failed")
        return count, head

    def _verify(self, tenant_id: str, account_id: str) -> tuple[int, str]:
        count, expected_head = self._head(tenant_id, account_id)
        previous = "GENESIS"
        rows = self._db.execute(
            "SELECT sequence, record_json, previous_hash, record_hash FROM research_receipts WHERE tenant_id=? AND account_id=? ORDER BY sequence",
            (tenant_id, account_id),
        ).fetchall()
        for sequence, row in enumerate(rows, start=1):
            if row["sequence"] != sequence or row["previous_hash"] != previous:
                raise PrecisionContractViolation("research receipt chain sequence is invalid")
            expected = self._mac("research-receipt-v1:" + previous + ":" + row["record_json"])
            if not hmac.compare_digest(row["record_hash"], expected):
                raise PrecisionContractViolation("research receipt chain integrity verification failed")
            previous = row["record_hash"]
        if len(rows) != count or previous != expected_head:
            raise PrecisionContractViolation("research receipt head mismatch")
        return count, expected_head

    def append(self, receipt: AccountResearchReceipt) -> str:
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                self._assert_schema()
                self._assert_metadata()
                count, previous = self._verify(receipt.tenant_id, receipt.account_id)
                material = _encoded(receipt)
                existing = self._db.execute(
                    "SELECT record_json FROM research_receipts WHERE tenant_id=? AND receipt_id=?", (receipt.tenant_id, receipt.receipt_id),
                ).fetchone()
                if existing is not None:
                    if existing["record_json"] != material:
                        raise PrecisionContractViolation("research receipt identity collision")
                    self._db.execute("COMMIT")
                    return receipt.receipt_id
                total = self._db.execute("SELECT COUNT(*) AS n FROM research_receipts").fetchone()["n"]
                if total >= self._max_receipts:
                    raise PrecisionCapacityExceeded("research receipt ledger capacity exhausted")
                record_hash = self._mac("research-receipt-v1:" + previous + ":" + material)
                self._db.execute(
                    "INSERT INTO research_receipts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (receipt.tenant_id, receipt.account_id, count + 1, receipt.receipt_id, receipt.persisted_at,
                     receipt.expires_at, material, previous, record_hash),
                )
                head_mac = self._head_mac(receipt.tenant_id, receipt.account_id, count + 1, record_hash)
                self._db.execute(
                    """INSERT INTO research_heads VALUES (?, ?, ?, ?, ?)
                       ON CONFLICT(tenant_id, account_id) DO UPDATE SET receipt_count=excluded.receipt_count,
                       receipt_head=excluded.receipt_head, head_mac=excluded.head_mac""",
                    (receipt.tenant_id, receipt.account_id, count + 1, record_hash, head_mac),
                )
                self._db.execute("COMMIT")
                return receipt.receipt_id
            except Exception:
                self._db.execute("ROLLBACK")
                raise

    def records(self, *, tenant_id: str, account_id: str, now: int) -> tuple[dict[str, Any], ...]:
        require_text("tenant_id", tenant_id)
        require_text("account_id", account_id)
        if not isinstance(now, int) or now < 0:
            raise PrecisionContractViolation("receipt query requires non-negative logical time")
        with self._lock:
            self._assert_schema()
            self._assert_metadata()
            self._verify(tenant_id, account_id)
            rows = self._db.execute(
                "SELECT record_json FROM research_receipts WHERE tenant_id=? AND account_id=? AND expires_at>=? ORDER BY sequence",
                (tenant_id, account_id, now),
            ).fetchall()
            return tuple(json.loads(row["record_json"]) for row in rows)


class AccountResearchCoordinator:
    """Executes one explicitly approved, read-only research request and records it."""

    def __init__(
        self,
        *,
        policy: AccountResearchPolicy,
        website_policy: OfficialWebsitePolicy,
        enricher: AccountEnricher,
        knowledge_store: AccountKnowledgeStore,
        receipt_ledger: ResearchReceiptLedger,
    ) -> None:
        self._policy = policy
        self._website_policy = website_policy
        self._enricher = enricher
        self._knowledge_store = knowledge_store
        self._receipt_ledger = receipt_ledger

    @staticmethod
    def _approved_seed(batch: ExcelAccountImportBatch, approval: ResearchApproval, now: int) -> ImportedAccountSeed:
        if approval.tenant_id != batch.tenant_id or approval.import_id != batch.import_id:
            raise PrecisionContractViolation("approval is not bound to this tenant/import batch")
        if approval.workbook_content_hash != batch.source_content_hash:
            raise PrecisionContractViolation("approval workbook hash does not match import batch")
        if approval.approved_at > now or approval.expires_at < now:
            raise PrecisionContractViolation("approval is not currently valid")
        matches = [item for item in batch.accepted if item.row_number == approval.row_number and item.seed.account_id == approval.account_id]
        if len(matches) != 1:
            raise PrecisionContractViolation("approval does not bind one accepted account seed")
        selected = matches[0]
        if fingerprint(selected.seed) != approval.seed_fingerprint:
            raise PrecisionContractViolation("approval seed fingerprint does not match import batch")
        return selected

    def execute(self, *, batch: ExcelAccountImportBatch, approval: ResearchApproval, now: int) -> AccountResearchReceipt:
        if not isinstance(now, int) or now < 0:
            raise PrecisionContractViolation("research execution requires non-negative logical time")
        selected = self._approved_seed(batch, approval, now)
        dossier = self._enricher.enrich(seed=selected.seed, policy=self._website_policy, now=now)
        if (
            dossier.tenant_id != selected.seed.tenant_id or dossier.account_id != selected.seed.account_id
            or dossier.official_url != selected.seed.official_url
        ):
            raise PrecisionContractViolation("enricher returned dossier outside approved account seed")
        if dossier.policy_id != self._website_policy.policy_id or dossier.captured_at > now:
            raise PrecisionContractViolation("enricher returned dossier outside approved policy or time")
        self._knowledge_store.append_dossier(dossier)
        identity = fingerprint((approval.approval_id, batch.import_id, dossier.dossier_id, dossier.output_fingerprint, self._policy.policy_id))
        receipt = AccountResearchReceipt(
            receipt_id=f"research-receipt:{identity}", tenant_id=selected.seed.tenant_id,
            account_id=selected.seed.account_id, approval_id=approval.approval_id, import_id=batch.import_id,
            dossier_id=dossier.dossier_id, dossier_fingerprint=dossier.output_fingerprint,
            policy_id=self._policy.policy_id, captured_at=dossier.captured_at, persisted_at=now,
            expires_at=now + self._policy.receipt_retention_seconds, status="SHADOW_COMPLETED",
            restrictions=(
                "EXPLICIT_HUMAN_REVIEW_BINDING", "SHADOW_RESEARCH_ONLY", "NO_FACT_PROMOTION",
                "NO_CRM_WRITE", "NO_DELIVERY", "REVIEWER_IDENTITY_NOT_AUTHENTICATED",
            ),
        )
        self._receipt_ledger.append(receipt)
        return receipt


