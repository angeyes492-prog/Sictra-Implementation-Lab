import time
import unittest
from dataclasses import replace

from sictra_block2_design.model_gateway import ProviderManifest, execution_spec_for
from sictra_block2_design.provider_sandbox import (
    CancellationRegistry, GovernedProviderSandbox, ProviderResponse, SandboxPolicy,
)
from sictra_block2_design.runtime import execute_block2
from tests.test_block2_e05_e08_runtime import NOW, complete_run_input


class FakeAdapter:
    def __init__(self, *, cost=2, delay=0, mutation=b"", media="text/html", fail=False):
        self.cost = cost
        self.delay = delay
        self.mutation = mutation
        self.media = media
        self.fail = fail
        self.calls = 0

    def invoke(self, spec, expected_content):
        self.calls += 1
        if self.delay:
            time.sleep(self.delay)
        if self.fail:
            raise RuntimeError("synthetic provider failure")
        return ProviderResponse(expected_content + self.mutation, self.media, self.cost)


def manifest(**changes):
    value = ProviderManifest(
        "MANIFEST-SANDBOX-0.1.0", "INJECTED_PROVIDER_FIXTURE", "HTML_EMAIL",
        "0.1.0", True, True, False,
    )
    return replace(value, **changes)


def policy(**changes):
    value = SandboxPolicy(
        "POLICY-SANDBOX-001", "0.1.0", 10, 1000, 500_000,
        ("HTML_EMAIL",), "rights-current-001", False,
    )
    return replace(value, **changes)


def sandbox(adapter=None, *, provider_manifest=None, sandbox_policy=None, cancellations=None):
    return GovernedProviderSandbox(
        provider_manifest or manifest(), sandbox_policy or policy(),
        adapter or FakeAdapter(), cancellations=cancellations,
    )


class ProviderSandboxTests(unittest.TestCase):
    def test_runtime_executes_exact_output_with_budgeted_receipt(self):
        gateway = sandbox()
        result = execute_block2(complete_run_input(), now=NOW, model_gateway=gateway)
        self.assertTrue(result.completed)
        self.assertEqual("EXECUTED", result.gateway_receipt.outcome)
        self.assertEqual(2, result.gateway_receipt.cost_units)
        self.assertEqual(10, result.gateway_receipt.budget_limit_units)
        self.assertEqual(1000, result.gateway_receipt.timeout_ms)
        self.assertEqual(policy().content_hash, result.gateway_receipt.policy_hash)

    def test_budget_overrun_quarantines_output(self):
        result = execute_block2(
            complete_run_input(), now=NOW,
            model_gateway=sandbox(FakeAdapter(cost=11)),
        )
        self.assertEqual("E06", result.stopped_at)
        self.assertIn("PROVIDER_BUDGET_EXCEEDED", result.stages[-1].reasons)
        self.assertEqual("QUARANTINED", result.gateway_receipt.quarantine_state)
        self.assertIsNone(result.production.candidate)

    def test_timeout_requests_cancel_and_quarantines(self):
        result = execute_block2(
            complete_run_input(), now=NOW,
            model_gateway=sandbox(FakeAdapter(delay=.05), sandbox_policy=policy(timeout_ms=5)),
        )
        self.assertEqual("E06", result.stopped_at)
        self.assertEqual("TIMEOUT", result.gateway_receipt.outcome)
        self.assertEqual("CANCEL_REQUESTED_AFTER_TIMEOUT", result.gateway_receipt.cancel_state)
        self.assertIn("PROVIDER_TIMEOUT", result.stages[-1].reasons)

    def test_pre_execution_cancel_never_invokes_provider(self):
        data = complete_run_input()
        adapter = FakeAdapter()
        cancellations = CancellationRegistry()
        gateway = sandbox(adapter, cancellations=cancellations)
        spec = execution_spec_for(data.production_request, gateway.manifest)
        cancellations.cancel(spec.idempotency_key)
        result = execute_block2(data, now=NOW, model_gateway=gateway)
        self.assertEqual("CANCELED", result.gateway_receipt.outcome)
        self.assertEqual(0, adapter.calls)
        self.assertIn("EXECUTION_CANCELED", result.stages[-1].reasons)

    def test_hash_or_media_mutation_is_quarantined(self):
        for adapter, reason in (
            (FakeAdapter(mutation=b"tampered"), "PROVIDER_OUTPUT_HASH_MISMATCH"),
            (FakeAdapter(media="image/png"), "PROVIDER_MEDIA_TYPE_MISMATCH"),
        ):
            with self.subTest(reason=reason):
                result = execute_block2(
                    complete_run_input(), now=NOW, model_gateway=sandbox(adapter),
                )
                self.assertIn(reason, result.stages[-1].reasons)
                self.assertEqual("QUARANTINED", result.gateway_receipt.outcome)

    def test_remote_io_returns_upstream_even_under_permissive_policy(self):
        adapter = FakeAdapter()
        forbidden = sandbox(
            adapter, provider_manifest=manifest(remote_io=True),
            sandbox_policy=policy(allow_remote_io=True),
        )
        result = execute_block2(complete_run_input(), now=NOW, model_gateway=forbidden)
        self.assertIn("REMOTE_IO_RETURN_UPSTREAM", result.stages[-1].reasons)
        self.assertEqual(0, adapter.calls)

    def test_provider_exception_is_typed_and_quarantined(self):
        result = execute_block2(
            complete_run_input(), now=NOW,
            model_gateway=sandbox(FakeAdapter(fail=True)),
        )
        self.assertEqual("PROVIDER_ERROR", result.gateway_receipt.outcome)
        self.assertIn("PROVIDER_EXCEPTION", result.stages[-1].reasons)

    def test_exact_replay_does_not_bill_or_invoke_twice(self):
        adapter = FakeAdapter(cost=3)
        gateway = sandbox(adapter)
        first = execute_block2(complete_run_input(), now=NOW, model_gateway=gateway)
        replay = execute_block2(complete_run_input(), now=NOW, model_gateway=gateway)
        self.assertEqual("EXECUTED", first.gateway_receipt.outcome)
        self.assertEqual("IDEMPOTENT_REPLAY", replay.gateway_receipt.outcome)
        self.assertEqual(1, adapter.calls)
        self.assertEqual(first.gateway_receipt.receipt_id, replay.gateway_receipt.receipt_id)


if __name__ == "__main__":
    unittest.main()
