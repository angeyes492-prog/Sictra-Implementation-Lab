from itertools import combinations

from sictra.block2_e01_observation import Observation, assess_observation


REQUIRED = frozenset({"identity", "visibility"})


def specimen(**changes):
    values = dict(
        observation_id="obs-invariant",
        claim_id="claim-1",
        source_class="human-perception",
        provenance="external-review-1",
        observed_conditions=REQUIRED,
        contamination_flags=frozenset(),
        externally_observed=True,
        observer_id="reviewer-2",
        evidence_author_id="author-1",
    )
    values.update(changes)
    return Observation(**values)


def test_acceptance_implies_admissibility():
    result = assess_observation(specimen(), required_conditions=REQUIRED)
    assert result.accepted is True
    assert result.admissible is True


def test_any_single_required_gate_failure_blocks_acceptance():
    mutations = (
        dict(provenance=""),
        dict(contamination_flags=frozenset({"leak"})),
        dict(observed_conditions=frozenset({"identity"})),
        dict(externally_observed=False),
        dict(observer_id=""),
        dict(observer_id="author-1", evidence_author_id="author-1"),
    )
    for mutation in mutations:
        result = assess_observation(specimen(**mutation), required_conditions=REQUIRED)
        assert result.accepted is False


def test_external_flag_cannot_promote_synthetic_or_internal_source():
    for source_class in ("synthetic", "internal-agent", "simulation"):
        result = assess_observation(
            specimen(source_class=source_class, externally_observed=True),
            required_conditions=REQUIRED,
        )
        assert result.admissible is True
        assert result.accepted is False
        assert "EXTERNAL_SOURCE_CLASS_REQUIRED" in result.reasons


def test_same_identity_cannot_self_attest():
    result = assess_observation(
        specimen(observer_id="author-1", evidence_author_id="author-1"),
        required_conditions=REQUIRED,
    )
    assert result.accepted is False
    assert "INDEPENDENT_OBSERVER_REQUIRED" in result.reasons


def test_multiple_simultaneous_failures_never_restore_acceptance():
    failures = (
        ("provenance", ""),
        ("contamination_flags", frozenset({"same-author"})),
        ("observed_conditions", frozenset({"identity"})),
        ("externally_observed", False),
        ("observer_id", ""),
    )
    for size in range(2, len(failures) + 1):
        for combo in combinations(failures, size):
            result = assess_observation(
                specimen(**dict(combo)), required_conditions=REQUIRED
            )
            assert result.accepted is False


def test_extra_observed_conditions_do_not_bypass_required_gates():
    result = assess_observation(
        specimen(
            observed_conditions=REQUIRED | {"salience", "contrast"},
            externally_observed=False,
        ),
        required_conditions=REQUIRED,
    )
    assert result.admissible is True
    assert result.accepted is False
    assert "EXTERNAL_OBSERVATION_REQUIRED" in result.reasons
