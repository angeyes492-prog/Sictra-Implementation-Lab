import unittest

from sictra_block4_orchestrator.platform_adapters import (
    AdapterConfiguration, AdapterContractError, AdapterOperation,
    admit_adapter_operation, plan_adapter_operation,
)


class PlatformAdapterContractTests(unittest.TestCase):
    def figma_config(self, **changes):
        values = {"adapter_id": "figma-reference", "platform": "FIGMA", "mode": "DISABLED",
                  "allowed_operations": ("READ_DESIGN_REFERENCE",)}
        values.update(changes)
        return AdapterConfiguration(**values)

    def request(self, **changes):
        values = {"case_id": "CASE-001", "run_id": "RUN-001", "artifact_id": "ARTIFACT-001",
                  "source_hash": "a" * 64, "platform": "FIGMA", "operation": "READ_DESIGN_REFERENCE",
                  "input_fields": ()}
        values.update(changes)
        return AdapterOperation(**values)

    def test_disabled_figma_operation_can_be_planned_but_not_executed(self):
        planned = plan_adapter_operation(self.figma_config(), self.request())
        self.assertEqual("PLANNED", planned.state)
        self.assertIn("NO_NETWORK_EXECUTED", planned.restrictions)
        with self.assertRaisesRegex(AdapterContractError, "ADAPTER_NOT_ACTIVE"):
            admit_adapter_operation(self.figma_config(), self.request())

    def test_active_framer_draft_requires_receipts_and_binds_without_execution(self):
        config = AdapterConfiguration("framer-drafts", "FRAMER", "ACTIVE", ("EXPORT_REVIEW_DRAFT",),
                                      credential_reference="vault://telecare/framer", activation_receipt="ACT-012")
        request = AdapterOperation("CASE-002", "RUN-002", "ARTIFACT-002", "b" * 64, "FRAMER",
                                   "EXPORT_REVIEW_DRAFT", (), human_authorization="HUMAN-EXPORT-012")
        bound = admit_adapter_operation(config, request)
        self.assertEqual("BOUND_NOT_EXECUTED", bound.state)
        self.assertIn("NO_PUBLICATION", bound.restrictions)

    def test_hubspot_rejects_direct_identifiers_and_write_like_operations(self):
        config = AdapterConfiguration("hubspot-context", "HUBSPOT", "DISABLED", ("READ_AUDIENCE_CONTEXT",))
        pii = AdapterOperation("CASE-003", "RUN-003", "DOSSIER-003", "c" * 64, "HUBSPOT",
                               "READ_AUDIENCE_CONTEXT", ("industry", "email"))
        with self.assertRaisesRegex(AdapterContractError, "HUBSPOT_FIELD_NOT_MINIMIZED"):
            plan_adapter_operation(config, pii)
        write_like = AdapterOperation("CASE-003", "RUN-003", "DOSSIER-003", "c" * 64, "HUBSPOT",
                                      "CREATE_CONTACT", ("industry",))
        with self.assertRaisesRegex(AdapterContractError, "OPERATION_NOT_APPROVED"):
            plan_adapter_operation(config, write_like)

    def test_disabled_adapter_cannot_carry_a_secret_reference(self):
        with self.assertRaisesRegex(AdapterContractError, "DISABLED_ADAPTER_MUST_NOT_BIND_CREDENTIALS"):
            plan_adapter_operation(self.figma_config(credential_reference="vault://should-not-bind"), self.request())

    def test_active_adapter_rejects_a_literal_secret_instead_of_a_vault_reference(self):
        config = self.figma_config(mode="ACTIVE", credential_reference="sk-live-not-a-reference", activation_receipt="ACT-013")
        with self.assertRaisesRegex(AdapterContractError, "CREDENTIAL_REFERENCE_NOT_VAULT_URI"):
            plan_adapter_operation(config, self.request())


if __name__ == "__main__":
    unittest.main()
