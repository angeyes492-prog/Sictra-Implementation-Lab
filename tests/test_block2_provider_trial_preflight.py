import unittest
import ast
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import sictra_block2_design.provider_trial_preflight as preflight_module

from sictra_block2_design.provider_trial_preflight import (
    ProviderTrialPreflightViolation, ProviderTrialReadinessRecord,
    assess_provider_trial_readiness,
)


NOW = datetime(2026, 9, 2, 18, tzinfo=timezone.utc)


def record(**changes):
    value = ProviderTrialReadinessRecord(
        "PROVIDER-PREFLIGHT-001", "0.1.0", "GENERATIVE_MEDIA", "OPENAI",
        "gpt-image-2:snapshot-fixture", "vault://sictra/openai/design-trial",
        "AVAILABLE", "terms:openai:2026-09", "policy:design-data:v1", "a" * 64,
        "budget:trial:v1", "authority:trial-owner:v1", "mar:block2:pending-review",
        ("IMAGE_GENERATION",), NOW, NOW + timedelta(hours=1),
    )
    return replace(value, **changes)


class ProviderTrialPreflightTests(unittest.TestCase):
    def test_complete_declaration_never_authorizes_execution_or_acceptance(self):
        assessment = assess_provider_trial_readiness(record(), now=NOW)
        self.assertEqual("PRECONDITIONS_DECLARED", assessment.disposition)
        self.assertFalse(assessment.execution_authorized)
        self.assertEqual("NOT_ACCEPTED", assessment.acceptance_state)

    def test_credential_and_expiry_fail_closed(self):
        assessment = assess_provider_trial_readiness(record(
            credential_state="EXPIRED", expires_at=NOW,
        ), now=NOW)
        self.assertEqual("RETURN_UPSTREAM", assessment.disposition)
        self.assertEqual(("CREDENTIAL_EXPIRED", "PREFLIGHT_EXPIRED"), assessment.reasons)

    def test_lane_scope_is_not_interchangeable(self):
        assessment = assess_provider_trial_readiness(record(
            lane="DESIGN_PLATFORM", declared_scopes=("DESIGN_CREATE",),
        ), now=NOW)
        self.assertEqual("RETURN_UPSTREAM", assessment.disposition)
        self.assertEqual(("SCOPE_MISSING_DESIGN_EXPORT",), assessment.reasons)

    def test_secret_material_is_rejected_before_assessment(self):
        for handle in (
            "sk-real-secret-must-not-enter-contract", "Bearer actual-secret",
            "vault://sictra/provider?token=actual-secret",
            "vault://sictra/provider?x-api-key=actual-secret",
        ):
            with self.subTest(handle=handle), self.assertRaises(ProviderTrialPreflightViolation):
                record(credential_handle=handle)

    def test_credential_handle_must_be_a_vault_reference(self):
        with self.assertRaises(ProviderTrialPreflightViolation):
            record(credential_handle="reference://sictra/openai/design-trial")

    def test_preflight_module_has_no_transport_or_secret_resolver_dependency(self):
        """Independent AST guard for the deliberately non-operational boundary."""

        source = Path(preflight_module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_roots = {
            alias.name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertFalse(imported_roots.intersection({
            "aiohttp", "httpx", "openai", "requests", "socket", "urllib",
        }))


if __name__ == "__main__":
    unittest.main()
