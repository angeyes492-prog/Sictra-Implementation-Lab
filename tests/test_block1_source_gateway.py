from dataclasses import replace
from hashlib import sha256
import unittest

from sictra_block1 import (
    AuthorityIssuer, ContractViolation, EvidenceIssuer, IntelligenceRuntime,
    SourceApprovalRecord, SourceBindingIssuer, SourceBindingVerifier,
    SourceCandidate, SourceGateway, SourceRegistration,
)


NOW = 10_000
EVIDENCE_KEY = b"e" * 32
AUTHORITY_KEY = b"a" * 32
EXECUTION_KEY = b"x" * 32
DECISION_KEY = b"d" * 32
STORAGE_KEY = b"s" * 32
BINDING_KEY = b"b" * 32


def registration(source_id="unctad", **changes):
    value = SourceRegistration(
        source_id=source_id,
        publisher="UN Trade and Development",
        scope="intelligence",
        allowed_hosts=("unctad.org", "unctadstat.unctad.org"),
        claim_keys=frozenset(("logistics-connectivity",)),
        status="BOUND",
        max_content_bytes=512,
    )
    return replace(value, **changes) if changes else value


def source_candidate(source_id="unctad"):
    return SourceCandidate(
        source_id=source_id,
        publisher="UN Trade and Development",
        candidate_hosts=("unctad.org", "unctadstat.unctad.org"),
        regions=frozenset(("GLOBAL",)),
        domains=frozenset(("MARITIME",)),
        cadence="ANNUAL",
    )


def binding(source_id="unctad", *, now=NOW):
    approval = SourceApprovalRecord(
        source_id=source_id,
        reviewer_id="reviewer-01",
        reviewed_at=now - 1,
        terms_evidence_ref=f"review://terms/{source_id}",
        approved_hosts=("unctad.org", "unctadstat.unctad.org"),
        approved_claim_keys=frozenset(("logistics-connectivity",)),
        max_content_bytes=512,
        access_method="MANUAL_SOURCE_BUNDLE",
        decision="APPROVED",
    )
    return SourceBindingIssuer("source-review", BINDING_KEY).issue(
        approval=approval, candidate=source_candidate(source_id), scope="intelligence", now=now, ttl=100,
    )


def gateway(registrations, *, now=NOW, authorizations=None):
    authorizations = authorizations if authorizations is not None else {
        value.source_id: binding(value.source_id, now=now)
        for value in registrations if value.status == "BOUND"
    }
    return SourceGateway(
        registrations=registrations,
        issuer=EvidenceIssuer("source-gateway", EVIDENCE_KEY),
        scope="intelligence",
        binding_authorizations=authorizations,
        binding_verifier=SourceBindingVerifier({"source-review": BINDING_KEY}, "intelligence"),
        now=now,
    )


class SourceGatewayTests(unittest.TestCase):
    def setUp(self):
        self.issuer = EvidenceIssuer("source-gateway", EVIDENCE_KEY)
        self.gateway = gateway((registration(),))

    def bundle(self, **changes):
        value = {
            "source_id": "unctad",
            "source_url": "https://unctad.org/publication/review-maritime-transport-2025",
            "content": "The registered source observation.",
            "observed_at": NOW - 1,
            "claim_key": "logistics-connectivity",
            "polarity": 1,
            "correlation_id": "unctad-rmt-2025",
        }
        value.update(changes)
        return value

    def test_bound_source_bundle_is_attested_with_fixed_root_and_hash(self):
        first = self.gateway.attest_manual_bundle(self.bundle(), now=NOW)
        second = self.gateway.attest_manual_bundle(
            self.bundle(content="A later report from the same registered source.", correlation_id="other"),
            now=NOW,
        )
        self.assertEqual(first["root_provenance"], "gateway-source:unctad")
        self.assertEqual(first["content_sha256"], sha256(self.bundle()["content"].encode()).hexdigest())
        self.assertEqual(first["ingestion_method"], "MANUAL_SOURCE_BUNDLE")
        self.assertEqual(first["source_url"], self.bundle()["source_url"])
        self.assertEqual(second["root_provenance"], first["root_provenance"])
        self.assertNotEqual(second["content_sha256"], first["content_sha256"])

    def test_output_is_admissible_to_runtime_then_tampering_is_rejected(self):
        source = self.gateway.attest_manual_bundle(self.bundle(), now=NOW)
        runtime = IntelligenceRuntime.operational(
            authority_keys={"governance": AUTHORITY_KEY}, authority_audience="gateway-runtime",
            authority_epoch=1, evidence_keys={"source-gateway": EVIDENCE_KEY},
            evidence_scope="intelligence", evidence_max_age=10,
            evidence_claims=frozenset(("logistics-connectivity",)),
            execution_key=EXECUTION_KEY, decision_key=DECISION_KEY,
            storage_integrity_key=STORAGE_KEY, clock=lambda: NOW,
        )
        authority = AuthorityIssuer("governance", AUTHORITY_KEY, "gateway-runtime", 1).issue(
            task_id="gateway", run_id="run-1", actions=("store_candidate",), now=NOW, ttl=10,
        )
        try:
            accepted = runtime.run(
                task_id="gateway", run_id="run-1", objective="assess port connectivity",
                sources=(source,), authority=authority,
            )
            self.assertEqual(accepted.payload["assessment"]["disposition"], "CANDIDATE")
            altered = dict(source)
            altered["content_sha256"] = "0" * 64
            rejected = runtime.run(
                task_id="gateway", run_id="run-2", objective="assess port connectivity",
                sources=(altered,), authority=AuthorityIssuer(
                    "governance", AUTHORITY_KEY, "gateway-runtime", 1,
                ).issue(task_id="gateway", run_id="run-2", actions=("store_candidate",), now=NOW, ttl=10),
            )
            self.assertEqual(rejected.payload["assessment"]["disposition"], "INSUFFICIENT")
            self.assertIn("SOURCE_ATTESTATION_INVALID", rejected.payload["rejected_sources"][0])
            altered_url = dict(source)
            altered_url["source_url"] = "https://unctad.org/other-report"
            rejected_url = runtime.run(
                task_id="gateway", run_id="run-3", objective="assess port connectivity",
                sources=(altered_url,), authority=AuthorityIssuer(
                    "governance", AUTHORITY_KEY, "gateway-runtime", 1,
                ).issue(task_id="gateway", run_id="run-3", actions=("store_candidate",), now=NOW, ttl=10),
            )
            self.assertIn("SOURCE_ATTESTATION_INVALID", rejected_url.payload["rejected_sources"][0])
        finally:
            runtime.close()

    def test_registry_rejects_duplicate_ids_and_fifty_first_entry(self):
        with self.assertRaises(ContractViolation):
            gateway((registration(), registration()))
        registrations = tuple(registration(f"source-{number}", status="PROPOSED") for number in range(51))
        with self.assertRaises(ContractViolation):
            gateway(registrations)
        with self.assertRaises(ContractViolation):
            registration(allowed_hosts=("unctad.org/not-a-host",))

    def test_registry_accepts_exactly_fifty_sources(self):
        registered = gateway(tuple(registration(f"source-{number}", status="PROPOSED") for number in range(50)))
        self.assertEqual(registered.registered_source_count, 50)

    def test_rejects_unbound_unknown_and_wrong_claim_sources(self):
        proposed = gateway((registration(status="PROPOSED"),))
        for source_gateway, bundle in (
            (self.gateway, self.bundle(source_id="unknown")),
            (proposed, self.bundle()),
            (self.gateway, self.bundle(claim_key="unregistered-claim")),
        ):
            with self.subTest(bundle=bundle):
                with self.assertRaises(ContractViolation):
                    source_gateway.attest_manual_bundle(bundle, now=NOW)

    def test_bound_registration_requires_current_matching_binding_authorization(self):
        with self.assertRaises(ContractViolation):
            gateway((registration(),), authorizations={})
        with self.assertRaises(ContractViolation):
            gateway((registration(),), now=NOW, authorizations={"unctad": binding(now=100)})
        altered = replace(binding(), max_content_bytes=513)
        with self.assertRaises(ContractViolation):
            gateway((registration(),), authorizations={"unctad": altered})

    def test_rejects_url_escape_attempts_and_future_time(self):
        invalid_urls = (
            "http://unctad.org/report",
            "https://attacker.example/report",
            "https://127.0.0.1/report",
            "https://[::1]/report",
            "https://localhost/report",
            "https://user@unctad.org/report",
            "https://unctad.org:8443/report",
            "https://unctad.org/report#fragment",
        )
        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ContractViolation):
                    self.gateway.attest_manual_bundle(self.bundle(source_url=url), now=NOW)
        with self.assertRaises(ContractViolation):
            self.gateway.attest_manual_bundle(self.bundle(observed_at=NOW + 1), now=NOW)

    def test_rejects_bundle_shape_content_limit_polarity_and_network_access(self):
        cases = (
            {**self.bundle(), "unexpected": "field"},
            self.bundle(content="x" * 513),
            self.bundle(polarity=0),
        )
        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(ContractViolation):
                    self.gateway.attest_manual_bundle(value, now=NOW)
        with self.assertRaises(ContractViolation):
            self.gateway.fetch_network_source("https://unctad.org/")
