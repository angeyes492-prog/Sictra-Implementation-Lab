from sictra.block2_e01_observation import Observation, assess_observation


def specimen(**changes):
    values = dict(
        observation_id="obs-1",
        claim_id="claim-1",
        source_class="human-perception",
        provenance="external-review-1",
        observed_conditions=frozenset({"identity", "visibility"}),
        contamination_flags=frozenset(),
        externally_observed=False,
    )
    values.update(changes)
    return Observation(**values)


def test_structural_admissibility_does_not_imply_external_acceptance():
    result = assess_observation(
        specimen(), required_conditions=frozenset({"identity", "visibility"})
    )
    assert result.admissible is True
    assert result.accepted is False
    assert result.reasons == ("EXTERNAL_OBSERVATION_REQUIRED",)


def test_external_observation_can_close_bounded_acceptance():
    result = assess_observation(
        specimen(externally_observed=True),
        required_conditions=frozenset({"identity", "visibility"}),
    )
    assert result.admissible is True
    assert result.accepted is True
    assert result.reasons == ()


def test_missing_provenance_is_rejected_even_if_external_flag_is_true():
    result = assess_observation(
        specimen(provenance="", externally_observed=True),
        required_conditions=frozenset({"identity", "visibility"}),
    )
    assert result.admissible is False
    assert result.accepted is False
    assert "PROVENANCE_MISSING" in result.reasons


def test_contamination_prevents_acceptance():
    result = assess_observation(
        specimen(contamination_flags=frozenset({"same-author"}), externally_observed=True),
        required_conditions=frozenset({"identity", "visibility"}),
    )
    assert result.admissible is False
    assert result.accepted is False
    assert "CONTAMINATED" in result.reasons


def test_missing_required_condition_is_rejected():
    result = assess_observation(
        specimen(observed_conditions=frozenset({"identity"}), externally_observed=True),
        required_conditions=frozenset({"identity", "visibility"}),
    )
    assert result.admissible is False
    assert result.accepted is False
    assert "REQUIRED_CONDITIONS_MISSING" in result.reasons
