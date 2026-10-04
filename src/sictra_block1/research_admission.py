"""Explicit reviewed admission port for retained statistical research candidates."""
from hashlib import sha256
import json
import time

from .common import ContractViolation
from .evidence import EvidenceIssuer, EvidenceVerifier
from .research_acquisition import ResearchQuarantine, canonical
from .research_methodology import review_methodology_candidate
from .research_statistics import inspect_statistics_candidate
from .source_control_store import SourceControlStore

SCOPE = "BLOCK1_EUROSTAT_STATISTICS_BE_2023_2024"
CLAIM = "maritime_freight_weight_thousand_tonnes"
MEDIA = "application/vnd.sictra.eurostat-statistical-selection+json"


class StatisticalAdmissionViolation(ContractViolation):
    pass


def _check(condition, reason):
    if not condition:
        raise StatisticalAdmissionViolation(reason)


def _time(clock):
    now = clock()
    _check(type(now) is int and now >= 0, "ADMISSION_CLOCK_INVALID")
    return now


def _inputs(quarantine, data_id, metadata_id, now):
    data = inspect_statistics_candidate(quarantine, data_id, clock=lambda: now)
    metadata = review_methodology_candidate(quarantine, metadata_id, clock=lambda: now)
    _check(data["terms_candidate_id"] == metadata["terms_candidate_id"]
           and data["terms_content_sha256"] == metadata["terms_content_sha256"],
           "ADMISSION_TERMS_LINEAGE_MISMATCH")
    terms, _ = quarantine.read(data["terms_candidate_id"], now=now, expected_recipe="EUROSTAT_REUSE_NOTICE")
    return data, metadata, terms


def _terms_reference(data, metadata):
    return "quarantine:" + data["terms_candidate_id"] + ":" + metadata["candidate_id"]


def prepare_admission_review(quarantine, data_id, metadata_id, *, clock=lambda: int(time.time())):
    initial = _time(clock)
    data, metadata, terms = _inputs(quarantine, data_id, metadata_id, initial)
    final = _time(clock)
    _check(final >= initial, "ADMISSION_CLOCK_REGRESSED")
    _check((data, metadata, terms) == _inputs(quarantine, data_id, metadata_id, final),
           "ADMISSION_INPUT_CHANGED")
    report = {"version": "0.1.0", "source_id": "eurostat", "status": "PROPOSED",
        "data": data, "methodology": metadata,
        "terms": {"candidate_id": data["terms_candidate_id"], "content_sha256": terms["content_sha256"],
                  "source_url": terms["final_url"], "acquired_at": terms["acquired_at"]},
        "required_registration": {"source_id": "eurostat", "publisher": "Eurostat / European Commission",
            "scope": SCOPE, "allowed_hosts": ["ec.europa.eu"], "claim_keys": [CLAIM],
            "access_method": "MANUAL_SOURCE_BUNDLE", "maximum_content_bytes": 131072},
        "required_approval": {"terms_evidence_ref": _terms_reference(data, metadata),
            "review_not_before": max(terms["acquired_at"], metadata["acquired_at"]),
            "reviewer_id": None, "decision": "PENDING"},
        "expires_at": min(data["expires_at"], metadata["expires_at"]),
        "admission": "NOT_ADMITTED", "acceptance": "NOT_ACCEPTED", "runtime_effect": "NONE",
        "publication": "BLOCKED"}
    report["fingerprint"] = sha256(canonical(report)).hexdigest()
    return report


def _record(control, review, now):
    _check(isinstance(control, SourceControlStore), "ADMISSION_CONTROL_INVALID")
    record = control.active_record("eurostat", now=now)
    _check(record is not None, "ADMISSION_APPROVAL_MISSING_OR_EXPIRED")
    registration, approval, binding = record["registration"], record["approval"], record["binding"]
    _check(registration["scope"] == SCOPE and registration["publisher"] == "Eurostat / European Commission"
           and registration["allowed_hosts"] == ["ec.europa.eu"] and registration["claim_keys"] == [CLAIM]
           and registration["access_method"] == "MANUAL_SOURCE_BUNDLE"
           and 0 < registration["max_content_bytes"] <= 131072, "ADMISSION_SCOPE_MISMATCH")
    _check(approval["terms_evidence_ref"] == review["required_approval"]["terms_evidence_ref"],
           "ADMISSION_REVIEW_LINEAGE_MISMATCH")
    _check(review["required_approval"]["review_not_before"] <= approval["reviewed_at"] <= now,
           "ADMISSION_REVIEW_TIME_INVALID")
    _check(now < binding["expires_at"] and now < review["expires_at"], "ADMISSION_NOT_CURRENT")
    return record


def _bundle(review, record):
    data = review["data"]
    _check(any(not row["missing"] for row in data["observations"]), "ADMISSION_NO_OBSERVED_VALUES")
    body = {"schema_version": "0.1.0", "content_type": MEDIA,
        "bundle_state": "UNATTESTED_STATISTICAL_BUNDLE", "source_scope": SCOPE,
        "provenance": {"data_candidate_id": data["candidate_id"], "source_file_sha256": data["content_sha256"],
            "methodology_candidate_id": review["methodology"]["candidate_id"],
            "methodology_sha256": review["methodology"]["content_sha256"],
            "terms_candidate_id": review["terms"]["candidate_id"], "terms_sha256": review["terms"]["content_sha256"],
            "dataset_code": data["dataset_code"], "publisher_updated_raw": data["publisher_updated_raw"],
            "acquired_at": data["acquired_at"], "approval_fingerprint": record["binding"]["approval_fingerprint"],
            "binding_id": record["binding_id"], "reviewed_at": record["approval"]["reviewed_at"]},
        "expires_at": min(review["expires_at"], record["binding"]["expires_at"]),
        "filters": data["filters"], "grain": data["grain"], "observations": data["observations"],
        "interpretations": [], "hypotheses": [], "resolution": "NOT_RESOLVED", "publication": "BLOCKED"}
    content = canonical(body).decode()
    _check(len(content.encode()) <= record["registration"]["max_content_bytes"], "ADMISSION_CONTENT_LIMIT")
    return {"source_id": "eurostat", "source_url": data["source_url"], "content": content,
            "observed_at": data["acquired_at"], "claim_key": CLAIM, "polarity": 1,
            "correlation_id": "eurostat-stats:" + data["candidate_id"]}


def _snapshot(quarantine, data_id, metadata_id, control, now):
    review = prepare_admission_review(quarantine, data_id, metadata_id, clock=lambda: now)
    record = _record(control, review, now)
    return review, record, _bundle(review, record)


def attest_statistics_candidate(quarantine, data_id, metadata_id, control, issuer, *, clock=lambda: int(time.time())):
    _check(isinstance(issuer, EvidenceIssuer), "ADMISSION_ISSUER_INVALID")
    start = _time(clock)
    snapshot = _snapshot(quarantine, data_id, metadata_id, control, start)
    source = control.build_gateway("eurostat", evidence_issuer=issuer, now=start).attest_manual_bundle(snapshot[2], now=start)
    finish = _time(clock)
    _check(finish >= start, "ADMISSION_CLOCK_REGRESSED")
    _check(snapshot == _snapshot(quarantine, data_id, metadata_id, control, finish), "ADMISSION_INPUT_CHANGED")
    return source


def verify_statistics_candidate(source, quarantine, data_id, metadata_id, control, verifier,
                                *, clock=lambda: int(time.time())):
    _check(isinstance(source, dict) and isinstance(verifier, EvidenceVerifier), "ADMISSION_VERIFIER_INVALID")
    start = _time(clock)
    snapshot = _snapshot(quarantine, data_id, metadata_id, control, start)
    valid, reason = verifier.verify(source, now=start)
    _check(valid, "ADMISSION_ATTESTATION_REJECTED:" + reason)
    record, bundle = snapshot[1], snapshot[2]
    expected = {**bundle, "schema_version": "0.3.0", "root_provenance": "gateway-source:eurostat",
        "evidence_class": "OBSERVED", "scope": SCOPE, "publisher": record["registration"]["publisher"],
        "content_sha256": sha256(bundle["content"].encode()).hexdigest(), "ingestion_method": "MANUAL_SOURCE_BUNDLE",
        "source_approval_fingerprint": record["binding"]["approval_fingerprint"]}
    # Existing gateway binds the unsigned token plus its signature; preserve
    # that public fingerprint instead of borrowing the producer signing key.
    token = record["binding"]
    material = json.dumps({k: v for k, v in token.items() if k != "signature"}, sort_keys=True, separators=(",", ":")).encode()
    expected["source_binding_fingerprint"] = sha256(material + token["signature"].encode()).hexdigest()
    unsigned = {k: v for k, v in source.items() if k not in {"attestation", "attestation_issuer"}}
    _check(unsigned == expected, "ADMISSION_SOURCE_LINEAGE_OR_CONTENT_MISMATCH")
    finish = _time(clock)
    _check(finish >= start, "ADMISSION_CLOCK_REGRESSED")
    _check(snapshot == _snapshot(quarantine, data_id, metadata_id, control, finish), "ADMISSION_INPUT_CHANGED")
    valid, reason = verifier.verify(source, now=finish)
    _check(valid, "ADMISSION_ATTESTATION_REJECTED:" + reason)
    return {"status": "VERIFIED_LOCAL_ADMISSION", "source_id": "eurostat", "scope": SCOPE,
            "data_candidate_id": data_id, "source_sha256": expected["content_sha256"],
            "approval_fingerprint": expected["source_approval_fingerprint"],
            "binding_id": record["binding_id"], "expires_at": json.loads(bundle["content"])["expires_at"],
            "runtime_effect": "NONE", "publication": "BLOCKED", "resolution": "NOT_RESOLVED"}


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--data-candidate-id", required=True)
    parser.add_argument("--metadata-candidate-id", required=True)
    args = parser.parse_args()
    print(json.dumps(prepare_admission_review(ResearchQuarantine(args.root), args.data_candidate_id,
                                             args.metadata_candidate_id), ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
