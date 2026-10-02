import unittest

from sictra_block1.need_classification import (
    NeedClassificationViolation, classify_data_need,
)


class NeedClassificationTests(unittest.TestCase):
    def test_known_needs_have_specific_non_resolution_routes(self):
        self.assertEqual("INDEPENDENT_CORROBORATION", classify_data_need(
            "eurostat", "Independent corroborating source for the same geography and period."))
        self.assertEqual("SOURCE_METHODOLOGY", classify_data_need(
            "HN_ADUANAS_BULLETINS",
            "Nota metodológica que explique revisiones y la brecha de reconciliación."))
        self.assertEqual("COMPANY_EXPOSURE", classify_data_need(
            "eurostat", "Company-specific exposure data before estimating impact."))

    def test_drift_or_keyword_injection_cannot_select_a_route(self):
        self.assertEqual("UNCLASSIFIED", classify_data_need(
            "eurostat", "Independent source for another period."))
        self.assertEqual("UNCLASSIFIED", classify_data_need(
            "unapproved", "Una fuente independiente o espejo bilateral con identidad de raíz distinta."))
        self.assertEqual("UNCLASSIFIED", classify_data_need(
            "eurostat", "Una fuente independiente o espejo bilateral con identidad de raíz distinta."))
        with self.assertRaisesRegex(NeedClassificationViolation, "NEED_INPUT_INVALID"):
            classify_data_need("eurostat", " ")


if __name__ == "__main__":
    unittest.main()
