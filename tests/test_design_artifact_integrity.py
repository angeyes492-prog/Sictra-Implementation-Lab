"""Contract vectors for the B2 to B3 review renderer boundary."""
from copy import deepcopy
import unittest

from sictra_block2_design.design_artifact import (
    DesignArtifactError, fingerprint, render_designed_review_artifact,
)
from sictra_block3_precision.audience_draft import AudiencePolicyError, adapt_content_design


def _block(kind, body, claim_ids=()):
    return {"id": kind.lower(), "kind": kind, "title": kind,
            "body": body, "source_claim_ids": list(claim_ids)}


def _profile(geo_codes=()):
    return {"id": "profile-1", "label": "Generic", "role": "Reviewer",
            "depth": "DETAILED", "tone": "TECHNICAL", "geo_codes": list(geo_codes),
            "questions": [], "expires_at": 200}


def _valid_pair():
    # A small contract fixture: the assertions below come from the handoff
    # contract, not from the renderer's formatting or checksum implementation.
    design = {
        "version": 1, "artifact_type": "CONTENT_DESIGN_CANDIDATE",
        "format": "REVIEW_NEWSLETTER", "case_id": "case-1",
        "dossier_id": "dossier-1", "title": "Observed maritime change",
        "source_hash": "a" * 64, "evidence_id": "evidence-1",
        "source_id": "source-1", "expires_at": 200,
        "claims": [{"id": "claim-1", "geo_code": "BE", "text": "Measured change",
                    "observation": {}, "evidence": ["evidence-1"]}],
        "content_blocks": [
            _block("CONTEXT", "Literal observations only"),
            _block("OBSERVED_CHANGE", "Measured change", ("claim-1",)),
            _block("REVIEW_QUESTIONS", "What explains this?"),
            _block("EVIDENCE_GAP", "Independent observation needed"),
            _block("UNCERTAINTY", "Cause unknown"),
            _block("LIMITATION", "Scope limited to Belgium"),
            _block("PROVENANCE", "Source: source-1; evidence: evidence-1"),
        ],
        "status": "DESIGN_CANDIDATE_NOT_ACCEPTED",
        "review": "HUMAN_REVIEW_REQUIRED", "publication": "BLOCKED",
        "delivery": "NONE", "acceptance": "NOT_ACCEPTED",
    }
    design["fingerprint"] = fingerprint(design)
    return design, adapt_content_design(design, _profile(), now=100)


class DesignArtifactIntegrityTests(unittest.TestCase):
    def test_current_candidate_preserves_observation_and_limits(self):
        design, adaptation = _valid_pair()
        html, plain = render_designed_review_artifact(design, adaptation)
        for required in ("Measured change", "Cause unknown", "Scope limited to Belgium",
                         "Source: source-1; evidence: evidence-1"):
            self.assertIn(required, plain)
            self.assertIn(required, html)

    def test_design_changed_after_adaptation_is_rejected(self):
        design, adaptation = _valid_pair()
        altered = deepcopy(design)
        altered["title"] = "Unverified conclusion"
        with self.assertRaisesRegex(DesignArtifactError, "DESIGN_ARTIFACT_INVALID"):
            render_designed_review_artifact(altered, adaptation)

    def test_resealed_adaptation_cannot_omit_or_rewrite_required_limits(self):
        design, adaptation = _valid_pair()
        for kind in ("UNCERTAINTY", "LIMITATION", "PROVENANCE"):
            with self.subTest(kind=kind):
                altered = deepcopy(adaptation)
                altered["content_blocks"] = [b for b in altered["content_blocks"]
                                             if b["kind"] != kind]
                altered["fingerprint"] = fingerprint({k: v for k, v in altered.items()
                                                       if k != "fingerprint"})
                with self.assertRaisesRegex(DesignArtifactError, "REQUIRED_BLOCK_INVALID"):
                    render_designed_review_artifact(design, altered)
                rewritten = deepcopy(adaptation)
                next(b for b in rewritten["content_blocks"] if b["kind"] == kind)["body"] = "Safe to publish"
                rewritten["fingerprint"] = fingerprint({k: v for k, v in rewritten.items()
                                                         if k != "fingerprint"})
                with self.assertRaisesRegex(DesignArtifactError, "REQUIRED_BLOCK_INVALID"):
                    render_designed_review_artifact(design, rewritten)

    def test_resealed_adaptation_cannot_promote_publication(self):
        design, adaptation = _valid_pair()
        altered = deepcopy(adaptation)
        altered["publication"] = "ALLOWED"
        altered["fingerprint"] = fingerprint({k: v for k, v in altered.items()
                                              if k != "fingerprint"})
        with self.assertRaisesRegex(DesignArtifactError, "ADAPTATION_AUTHORITY_INVALID"):
            render_designed_review_artifact(design, altered)

    def test_resealed_adaptation_cannot_remove_or_rewrite_every_observation(self):
        design, adaptation = _valid_pair()
        for action in ("remove", "rewrite"):
            with self.subTest(action=action):
                altered = deepcopy(adaptation)
                if action == "remove":
                    altered["content_blocks"] = [block for block in altered["content_blocks"]
                                                 if block["kind"] != "OBSERVED_CHANGE"]
                else:
                    next(block for block in altered["content_blocks"]
                         if block["kind"] == "OBSERVED_CHANGE")["body"] = "Unsupported inference"
                altered["fingerprint"] = fingerprint({k: v for k, v in altered.items()
                                                       if k != "fingerprint"})
                with self.assertRaisesRegex(DesignArtifactError, "OBSERVATION_BLOCK_INVALID"):
                    render_designed_review_artifact(design, altered)

    def test_geographic_filter_can_keep_one_exact_observation_and_no_match_waits(self):
        design, _ = _valid_pair()
        design["claims"].append({"id": "claim-2", "geo_code": "DE", "text": "Second measurement",
                                 "observation": {}, "evidence": ["evidence-1"]})
        design["content_blocks"].insert(2, _block("OBSERVED_CHANGE", "Second measurement", ("claim-2",)))
        design["fingerprint"] = fingerprint({k: v for k, v in design.items() if k != "fingerprint"})
        adaptation = adapt_content_design(design, _profile(("BE",)), now=100)
        _, plain = render_designed_review_artifact(design, adaptation)
        self.assertIn("Measured change", plain)
        self.assertNotIn("Second measurement", plain)
        with self.assertRaisesRegex(AudiencePolicyError, "NO_GEOGRAPHIC_MATCH"):
            adapt_content_design(design, _profile(("ZZ",)), now=100)


if __name__ == "__main__":
    unittest.main()
