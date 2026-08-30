from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import sqlite3
import tempfile
import unittest

from sictra_block3_precision.account_knowledge import AccountKnowledgeDossier, AccountSeed, OfficialWebsitePolicy
from sictra_block3_precision.account_memory import AccountKnowledgeStore
from sictra_block3_precision.account_research import (
    AccountResearchCoordinator,
    AccountResearchPolicy,
    ResearchApproval,
    ResearchReceiptLedger,
)
from sictra_block3_precision.contracts import EvidenceRef, PrecisionContractViolation, fingerprint
from sictra_block3_precision.excel_account_import import ExcelAccountImportBatch, ImportedAccountSeed
from sictra_block3_precision.excel_account_import import ExcelAccountImportPolicy, ExcelAccountSeedImporter
from tests.test_block3_excel_account_import import workbook_bytes


NOW = 2_000_000_000
KEY = b"account-research-ledger-test-key-32bytes"
SEED = AccountSeed("tenant-a", "account-a", "https://example.test/", "ACCOUNT_RESEARCH")
WEB_POLICY = OfficialWebsitePolicy("official-web-v1", "authority:official-web")
RESEARCH_POLICY = AccountResearchPolicy("research-run-v1", "authority:research-run")


def batch_for(seed=SEED):
    content_hash = sha256(b"synthetic-workbook").hexdigest()
    root = f"excel-workbook:{content_hash}"
    imported = ImportedAccountSeed(
        seed=seed, row_number=2, company_name="Example Logistics", source_reference="fixture",
        evidence=EvidenceRef(
            evidence_id="excel-account-seed:fixture", source_identity="EXCEL_WORKBOOK:accounts.xlsx",
            root_provenance=root, observed_at=NOW, temporal_state="CURRENT", epistemic_state="UNCONFIRMED",
            confidence="C", provenance_refs=(root, "row:2"),
        ),
        restrictions=("READ_ONLY_IMPORT", "WORKBOOK_DECLARATION_NOT_FACT", "NO_CRAWL_EXECUTED"),
    )
    return ExcelAccountImportBatch(
        import_id="excel-import:fixture", tenant_id=seed.tenant_id, policy_id="excel-seed-v1",
        source_filename="accounts.xlsx", source_content_hash=content_hash, imported_at=NOW,
        accepted=(imported,), rejected=(), restrictions=("SHADOW_IMPORT_ONLY", "NO_CRAWL_EXECUTED"),
    )


def approval_for(batch, seed=SEED, **changes):
    values = dict(
        approval_id="review:fixture", tenant_id=seed.tenant_id, import_id=batch.import_id,
        workbook_content_hash=batch.source_content_hash, account_id=seed.account_id, row_number=2,
        seed_fingerprint=fingerprint(seed), approval_reference="review-ticket:1", reviewer_reference="operator:fixture",
        approved_at=NOW - 1, expires_at=NOW + 100,
    )
    values.update(changes)
    return ResearchApproval(**values)


class FakeEnricher:
    def __init__(self, *, wrong_account=False, wrong_policy=False, future_capture=False):
        self.calls = 0
        self.wrong_account = wrong_account
        self.wrong_policy = wrong_policy
        self.future_capture = future_capture

    def enrich(self, *, seed, policy, now):
        self.calls += 1
        account_id = "other-account" if self.wrong_account else seed.account_id
        return AccountKnowledgeDossier(
            dossier_id=f"account-dossier:{seed.account_id}:fixture", tenant_id=seed.tenant_id,
            account_id=account_id, official_url=seed.official_url,
            policy_id="wrong-policy" if self.wrong_policy else policy.policy_id,
            captured_at=now + 1 if self.future_capture else now, expires_at=now + 100, observations=(), quarantined_observation_ids=(),
            skipped_urls=(), restrictions=("SHADOW_ENRICHMENT_ONLY", "NO_FACT_PROMOTION"),
        )


class AccountResearchCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        path = Path(self.temp.name)
        self.memory = AccountKnowledgeStore(path / "memory.sqlite3", integrity_key=KEY)
        self.ledger = ResearchReceiptLedger(path / "receipts.sqlite3", integrity_key=KEY)
        self.enricher = FakeEnricher()
        self.coordinator = AccountResearchCoordinator(
            policy=RESEARCH_POLICY, website_policy=WEB_POLICY, enricher=self.enricher,
            knowledge_store=self.memory, receipt_ledger=self.ledger,
        )
        self.batch = batch_for()

    def tearDown(self):
        self.memory.close()
        self.ledger.close()
        self.temp.cleanup()

    def test_approved_seed_runs_end_to_end_to_durable_dossier_and_receipt(self):
        receipt = self.coordinator.execute(batch=self.batch, approval=approval_for(self.batch), now=NOW)
        self.assertEqual("SHADOW_COMPLETED", receipt.status)
        self.assertEqual("account-a", receipt.account_id)
        self.assertIn("NO_DELIVERY", receipt.restrictions)
        self.assertEqual(1, self.enricher.calls)
        self.assertEqual(receipt.dossier_id, self.memory.latest_snapshot(tenant_id="tenant-a", account_id="account-a", now=NOW)["dossier_id"])
        self.assertEqual(receipt.receipt_id, self.ledger.records(tenant_id="tenant-a", account_id="account-a", now=NOW)[0]["receipt_id"])

    def test_expired_or_substituted_approval_cannot_open_network_path(self):
        with self.assertRaises(PrecisionContractViolation):
            self.coordinator.execute(batch=self.batch, approval=approval_for(self.batch, expires_at=NOW - 1), now=NOW)
        with self.assertRaises(PrecisionContractViolation):
            self.coordinator.execute(batch=self.batch, approval=approval_for(self.batch, account_id="other-account"), now=NOW)
        with self.assertRaises(PrecisionContractViolation):
            self.coordinator.execute(batch=self.batch, approval=approval_for(self.batch, seed_fingerprint="wrong"), now=NOW)
        self.assertEqual(0, self.enricher.calls)

    def test_cross_tenant_batch_or_workbook_hash_cannot_be_approved(self):
        with self.assertRaises(PrecisionContractViolation):
            self.coordinator.execute(batch=self.batch, approval=approval_for(self.batch, tenant_id="tenant-b"), now=NOW)
        with self.assertRaises(PrecisionContractViolation):
            self.coordinator.execute(batch=self.batch, approval=approval_for(self.batch, workbook_content_hash="other-hash"), now=NOW)
        self.assertEqual(0, self.enricher.calls)

    def test_enricher_account_substitution_cannot_reach_memory_or_ledger(self):
        bad = AccountResearchCoordinator(
            policy=RESEARCH_POLICY, website_policy=WEB_POLICY, enricher=FakeEnricher(wrong_account=True),
            knowledge_store=self.memory, receipt_ledger=self.ledger,
        )
        with self.assertRaises(PrecisionContractViolation):
            bad.execute(batch=self.batch, approval=approval_for(self.batch), now=NOW)
        self.assertIsNone(self.memory.latest_snapshot(tenant_id="tenant-a", account_id="account-a", now=NOW))
        self.assertEqual((), self.ledger.records(tenant_id="tenant-a", account_id="account-a", now=NOW))

    def test_enricher_future_or_policy_substitution_cannot_reach_memory(self):
        for enricher in (FakeEnricher(wrong_policy=True), FakeEnricher(future_capture=True)):
            coordinator = AccountResearchCoordinator(
                policy=RESEARCH_POLICY, website_policy=WEB_POLICY, enricher=enricher,
                knowledge_store=self.memory, receipt_ledger=self.ledger,
            )
            with self.assertRaises(PrecisionContractViolation):
                coordinator.execute(batch=self.batch, approval=approval_for(self.batch), now=NOW)
        self.assertIsNone(self.memory.latest_snapshot(tenant_id="tenant-a", account_id="account-a", now=NOW))

    def test_exact_replay_is_one_durable_receipt(self):
        approval = approval_for(self.batch)
        first = self.coordinator.execute(batch=self.batch, approval=approval, now=NOW)
        second = self.coordinator.execute(batch=self.batch, approval=approval, now=NOW)
        self.assertEqual(first.receipt_id, second.receipt_id)
        self.assertEqual(1, len(self.ledger.records(tenant_id="tenant-a", account_id="account-a", now=NOW)))

    def test_real_excel_parser_handoff_reaches_dossier_and_receipt(self):
        importer = ExcelAccountSeedImporter(policy=ExcelAccountImportPolicy("excel-seed-v1", "authority:excel-import"))
        imported_batch = importer.import_workbook(
            tenant_id="tenant-a", authorized_purpose="ACCOUNT_RESEARCH", source_filename="accounts.xlsx", now=NOW,
            workbook=workbook_bytes(["Account ID", "Official Website"], [["account-a", "https://example.test/"]], shared_strings=True),
        )
        imported_seed = imported_batch.accepted[0].seed
        receipt = self.coordinator.execute(
            batch=imported_batch, approval=approval_for(imported_batch, seed=imported_seed), now=NOW,
        )
        self.assertEqual(imported_batch.import_id, receipt.import_id)
        self.assertEqual("account-a", receipt.account_id)


class ResearchReceiptLedgerIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "receipts.sqlite3"
        self.ledger = ResearchReceiptLedger(self.path, integrity_key=KEY)
        batch = batch_for()
        approval = approval_for(batch)
        self.memory = AccountKnowledgeStore(Path(self.temp.name) / "memory.sqlite3", integrity_key=KEY)
        self.record = AccountResearchCoordinator(
            policy=RESEARCH_POLICY, website_policy=WEB_POLICY, enricher=FakeEnricher(),
            knowledge_store=self.memory,
            receipt_ledger=self.ledger,
        ).execute(batch=batch, approval=approval, now=NOW)

    def tearDown(self):
        self.memory.close()
        self.ledger.close()
        self.temp.cleanup()

    def test_record_tampering_or_deletion_is_detected(self):
        connection = sqlite3.connect(self.path)
        connection.execute("UPDATE research_receipts SET record_json='{}'")
        connection.commit()
        connection.close()
        with self.assertRaises(PrecisionContractViolation):
            self.ledger.records(tenant_id="tenant-a", account_id="account-a", now=NOW)

    def test_headed_record_deletion_is_detected(self):
        connection = sqlite3.connect(self.path)
        connection.execute("DELETE FROM research_receipts")
        connection.commit()
        connection.close()
        with self.assertRaises(PrecisionContractViolation):
            self.ledger.records(tenant_id="tenant-a", account_id="account-a", now=NOW)

    def test_unapproved_trigger_is_detected_before_read(self):
        connection = sqlite3.connect(self.path)
        connection.execute("CREATE TRIGGER malicious_receipt_trigger AFTER INSERT ON research_receipts BEGIN SELECT 1; END")
        connection.commit()
        connection.close()
        with self.assertRaises(PrecisionContractViolation):
            self.ledger.records(tenant_id="tenant-a", account_id="account-a", now=NOW)

    def test_expired_receipt_remains_integrity_checked_but_is_not_returned(self):
        self.assertEqual((), self.ledger.records(tenant_id="tenant-a", account_id="account-a", now=self.record.expires_at + 1))


if __name__ == "__main__":
    unittest.main()


