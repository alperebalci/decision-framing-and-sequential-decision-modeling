import pytest

from decision_framing import BinaryBelief, InspectionMode


def test_more_specific_positive_signal_produces_stronger_posterior():
    prior = BinaryBelief(0.20)
    cheap = InspectionMode("cheap", sensitivity=0.65, specificity=0.80)
    deep = InspectionMode("deep", sensitivity=0.95, specificity=0.97)

    cheap_posterior = prior.update(True, cheap).probability_bad
    deep_posterior = prior.update(True, deep).probability_bad

    assert cheap_posterior > prior.probability_bad
    assert deep_posterior > cheap_posterior


def test_negative_signal_reduces_bad_state_belief():
    prior = BinaryBelief(0.40)
    mode = InspectionMode("deep", sensitivity=0.95, specificity=0.97)
    assert prior.update(False, mode).probability_bad < prior.probability_bad


def test_invalid_observation_model_is_rejected():
    with pytest.raises(ValueError):
        InspectionMode("invalid", sensitivity=1.2, specificity=0.9)
