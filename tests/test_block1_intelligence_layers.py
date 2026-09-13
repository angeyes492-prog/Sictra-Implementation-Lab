import unittest

from sictra_block1 import ContractViolation, KNOWN_TOPICS, normalize_research_frame, validate_research_frame_bundle


def frame(frame_id, layer, **changes):
    value = {
        "frame_id": frame_id, "layer": layer, "topic_keys": ["ocean_freight_rates"],
        "geographic_scope": "Asia-Americas", "period": "90D", "industry": None,
        "account_id": None, "global_frame_ids": [], "segment_frame_ids": [],
        "evidence_ids": ["E-1"], "certainty": "PLAUSIBLE", "confidence": "C",
    }
    if layer == "SEGMENT":
        value.update({"industry": "electronics", "global_frame_ids": ["G-1"]})
    if layer == "ACCOUNT":
        value.update({"industry": "electronics", "account_id": "acct-sterile-001", "global_frame_ids": ["G-1"], "segment_frame_ids": ["S-1"]})
    value.update(changes)
    return value


class ThreeLayerIntelligenceTests(unittest.TestCase):
    def test_catalog_covers_all_thematic_domains_and_valid_lineage(self):
        # The 173 numbered themes plus 17 industrial sectors contain four
        # intentional cross-domain duplicates, yielding 186 unique keys.
        self.assertEqual(len(KNOWN_TOPICS), 186)
        result = validate_research_frame_bundle((frame("G-1", "GLOBAL"), frame("S-1", "SEGMENT"), frame("A-1", "ACCOUNT")))
        self.assertEqual([item["layer"] for item in result], ["GLOBAL", "SEGMENT", "ACCOUNT"])

    def test_layers_require_their_exact_context_and_controlled_topics(self):
        for value in (frame("G-1", "GLOBAL", industry="electronics"), frame("S-1", "SEGMENT", global_frame_ids=[]), frame("A-1", "ACCOUNT", account_id=None), frame("S-1", "SEGMENT", industry="unregistered"), frame("G-1", "GLOBAL", topic_keys=["unknown"])):
            with self.subTest(value=value):
                with self.assertRaises(ContractViolation):
                    normalize_research_frame(value)

    def test_bundle_rejects_unresolved_wrong_layer_and_self_parent(self):
        cases = (
            (frame("S-1", "SEGMENT"),),
            (frame("G-1", "GLOBAL"), frame("S-1", "SEGMENT", global_frame_ids=["S-1"])),
            (frame("G-1", "GLOBAL"), frame("S-1", "SEGMENT"), frame("A-1", "ACCOUNT", segment_frame_ids=["A-1"])),
            (frame("G-1", "GLOBAL"), frame("S-1", "SEGMENT", industry="automotive"), frame("A-1", "ACCOUNT")),
        )
        for values in cases:
            with self.subTest(values=values):
                with self.assertRaises(ContractViolation):
                    validate_research_frame_bundle(values)


if __name__ == "__main__":
    unittest.main()
