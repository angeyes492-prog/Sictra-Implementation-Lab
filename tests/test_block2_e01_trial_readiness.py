import unittest

from sictra.block2_e01_trial_readiness import (
    FIXTURE_DIMENSIONS,
    ObserverIndependenceProfile,
    TaskLeakageRecord,
    TrialFixture,
    assess_trial_readiness,
)


def clean_observer():
    return ObserverIndependenceProfile("observer-1", "naive-reviewer")


def clean_task():
    return TaskLeakageRecord("Choose the representation that best supports the task.", frozenset({"target", "scope"}))


def clean_fixture():
    return TrialFixture("fixture-1", {d: True for d in FIXTURE_DIMENSIONS}, randomized_order=True, familiarity_balanced=True)


class TrialReadinessTests(unittest.TestCase):
    def test_clean_fixture_is_ready(self):
        self.assertTrue(assess_trial_readiness(clean_observer(), clean_task(), clean_fixture()).ready)

    def test_thesis_exposure_blocks_readiness(self):
        observer = ObserverIndependenceProfile("o", "reviewer", thesis_exposure=True)
        result = assess_trial_readiness(observer, clean_task(), clean_fixture())
        self.assertFalse(result.ready)
        self.assertIn("OBSERVER_EXPOSURE_CONTAMINATION", result.reasons)

    def test_task_cue_blocks_readiness(self):
        task = TaskLeakageRecord("Find the bottleneck", frozenset({"target"}), frozenset({"bottleneck"}))
        self.assertIn("TASK_WORDING_LEAKAGE", assess_trial_readiness(clean_observer(), task, clean_fixture()).reasons)

    def test_annotation_asymmetry_blocks_readiness(self):
        parity = {d: True for d in FIXTURE_DIMENSIONS}
        parity["annotation"] = False
        fixture = TrialFixture("f", parity, randomized_order=True, familiarity_balanced=True)
        self.assertIn("FIXTURE_ASYMMETRY", assess_trial_readiness(clean_observer(), clean_task(), fixture).reasons)

    def test_hidden_uncertainty_semantics_blocks_readiness(self):
        fixture = TrialFixture("f", {d: True for d in FIXTURE_DIMENSIONS}, frozenset({"uncertainty"}), True, True)
        self.assertIn("HIDDEN_SEMANTIC_CHANGE", assess_trial_readiness(clean_observer(), clean_task(), fixture).reasons)

    def test_order_effect_blocks_readiness(self):
        fixture = TrialFixture("f", {d: True for d in FIXTURE_DIMENSIONS}, randomized_order=False, familiarity_balanced=True)
        self.assertIn("ORDER_EFFECT_UNCONTROLLED", assess_trial_readiness(clean_observer(), clean_task(), fixture).reasons)

    def test_familiarity_imbalance_blocks_readiness(self):
        fixture = TrialFixture("f", {d: True for d in FIXTURE_DIMENSIONS}, randomized_order=True, familiarity_balanced=False)
        self.assertIn("FAMILIARITY_UNCONTROLLED", assess_trial_readiness(clean_observer(), clean_task(), fixture).reasons)

    def test_multiple_failures_cannot_restore_readiness(self):
        observer = ObserverIndependenceProfile("o", "reviewer", prior_exposure=True, evaluation_context_disclosed=True)
        task = TaskLeakageRecord("Find bottleneck", frozenset(), frozenset({"bottleneck"}))
        fixture = TrialFixture("f", {d: False for d in FIXTURE_DIMENSIONS})
        result = assess_trial_readiness(observer, task, fixture)
        self.assertFalse(result.ready)
        self.assertGreaterEqual(len(result.reasons), 5)


if __name__ == "__main__":
    unittest.main()
