import unittest
from dataclasses import replace

from sictra_block2_design.model_gateway import (
    CreativeExecutionSpec, LocalDeterministicModelGateway, ModelGatewayViolation,
    ProviderManifest, execution_spec_for,
)
from sictra_block2_design.runtime import execute_block2
from tests.test_block2_e05_e08_runtime import NOW, complete_run_input


class ModelGatewayTests(unittest.TestCase):
    def test_runtime_emits_pinned_receipt_for_exact_e06_output(self):
        result = execute_block2(complete_run_input(), now=NOW)
        self.assertTrue(result.completed)
        self.assertEqual("EXECUTED", result.gateway_receipt.outcome)
        self.assertEqual("MANIFEST-LOCAL-STUB-0.1.0", result.gateway_receipt.provider_manifest_id)
        self.assertEqual(result.production.candidate.artifact.sha256, result.gateway_receipt.output_hash)
        self.assertEqual(0, result.gateway_receipt.cost_units)

    def test_non_e06_producer_cannot_construct_execution_spec(self):
        source = execution_spec_for(complete_run_input().production_request)
        with self.assertRaises(ModelGatewayViolation):
            replace(source, producer_engine="E05")

    def test_same_gateway_and_spec_replay_is_idempotent(self):
        gateway = LocalDeterministicModelGateway()
        first = execute_block2(complete_run_input(), now=NOW, model_gateway=gateway)
        replay = execute_block2(complete_run_input(), now=NOW, model_gateway=gateway)
        self.assertEqual("EXECUTED", first.gateway_receipt.outcome)
        self.assertEqual("IDEMPOTENT_REPLAY", replay.gateway_receipt.outcome)
        self.assertEqual(first.gateway_receipt.receipt_id, replay.gateway_receipt.receipt_id)
        self.assertEqual(first.gateway_receipt.output_hash, replay.gateway_receipt.output_hash)

    def test_remote_stub_manifest_is_quarantined_before_render(self):
        manifest = ProviderManifest(
            "MANIFEST-LOCAL-STUB-0.1.0", "REMOTE-MISCONFIGURED", "HTML_EMAIL_OR_SVG",
            "0.1.0", True, True, True,
        )
        result = execute_block2(
            complete_run_input(), now=NOW,
            model_gateway=LocalDeterministicModelGateway(manifest),
        )
        self.assertFalse(result.completed)
        self.assertEqual("E06", result.stopped_at)
        self.assertIn("REMOTE_IO_FORBIDDEN_IN_LOCAL_STUB", result.stages[-1].reasons)
        self.assertEqual("QUARANTINED", result.gateway_receipt.quarantine_state)
        self.assertIsNone(result.production.candidate)

    def test_provider_manifest_substitution_fails_closed(self):
        manifest = ProviderManifest(
            "MANIFEST-SUBSTITUTE", "LOCAL_DETERMINISTIC_STUB", "HTML_EMAIL_OR_SVG",
            "0.1.0", True, True, False,
        )
        result = execute_block2(
            complete_run_input(), now=NOW,
            model_gateway=LocalDeterministicModelGateway(manifest),
        )
        self.assertEqual("E06", result.stopped_at)
        self.assertIn("PROVIDER_MANIFEST_SUBSTITUTION", result.stages[-1].reasons)

    def test_same_manifest_id_with_mutated_content_fails_hash_binding(self):
        manifest = ProviderManifest(
            "MANIFEST-LOCAL-STUB-0.1.0", "SUBSTITUTED_PROVIDER", "HTML_EMAIL_OR_SVG",
            "0.1.0", True, True, False,
        )
        result = execute_block2(
            complete_run_input(), now=NOW,
            model_gateway=LocalDeterministicModelGateway(manifest),
        )
        self.assertEqual("E06", result.stopped_at)
        self.assertIn("PROVIDER_MANIFEST_HASH_MISMATCH", result.stages[-1].reasons)


if __name__ == "__main__":
    unittest.main()
