import itertools
import unittest

from sictra.block2_e01_trial_readiness import (
    FIXTURE_DIMENSIONS,
    ObserverIndependenceProfile,
    TaskLeakageRecord,
    TrialFixture,
    assess_trial_readiness,
)


def oracle(observer, task, fixture):
    identity_ok = bool(observer.observer_id and observer.observer_role and task.wording and task.version)
    observer_clean = not any((observer.prior_exposure, observer.thesis_exposure, observer.examples_seen, observer.evaluation_context_disclosed))
    task_clean = len(task.potential_cues) == 0
    parity_complete = set(fixture.parity) >= set(FIXTURE_DIMENSIONS)
    parity_equal = parity_complete and all(fixture.parity.get(d, False) for d in FIXTURE_DIMENSIONS)
    semantics_clean = not fixture.hidden_semantic_changes
    controls = fixture.randomized_order and fixture.familiarity_balanced
    return all((identity_ok, observer_clean, task_clean, parity_equal, semantics_clean, controls))


class TrialReadinessOracleTests(unittest.TestCase):
    def test_differential_mutation_matrix(self):
        for exposed, cue, asymmetry, semantic_change, randomized, familiar in itertools.product((False, True), repeat=6):
            observer = ObserverIndependenceProfile("o", "reviewer", thesis_exposure=exposed)
            task = TaskLeakageRecord("Neutral task", frozenset({"target"}), frozenset({"cue"}) if cue else frozenset())
            parity = {d: True for d in FIXTURE_DIMENSIONS}
            if asymmetry:
                parity["annotation"] = False
            fixture = TrialFixture(
                "f", parity,
                frozenset({"uncertainty"}) if semantic_change else frozenset(),
                randomized_order=randomized,
                familiarity_balanced=familiar,
            )
            observed = assess_trial_readiness(observer, task, fixture).ready
            self.assertEqual(observed, oracle(observer, task, fixture))

    def test_externality_alone_does_not_bypass_readiness(self):
        observer = ObserverIndependenceProfile("external-o", "external-reviewer", thesis_exposure=True)
        task = TaskLeakageRecord("Neutral", frozenset())
        fixture = TrialFixture("f", {d: True for d in FIXTURE_DIMENSIONS}, randomized_order=True, familiarity_balanced=True)
        self.assertFalse(assess_trial_readiness(observer, task, fixture).ready)
        self.assertFalse(oracle(observer, task, fixture))


if __name__ == "__main__":
    unittest.main()
