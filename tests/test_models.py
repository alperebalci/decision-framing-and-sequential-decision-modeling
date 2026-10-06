import pytest

from decision_framing import DecisionFrame, DecisionType, MetricDirection, PerformanceMetric, UncertaintySource


def base_frame(**overrides):
    payload = dict(
        problem_name="test",
        problem_description="test decision problem",
        metrics=(PerformanceMetric("cost", MetricDirection.MINIMIZE),),
        decisions=(DecisionType("dispatch", "operator", timing="hourly"),),
        uncertainties=(UncertaintySource("travel_time", representation="empirical distribution"),),
        decision_impacts={"dispatch": {"cost": 4}},
        uncertainty_impacts={"travel_time": {"cost": 5}},
    )
    payload.update(overrides)
    return DecisionFrame(**payload)


def test_weighted_impacts_use_metric_priorities():
    frame = DecisionFrame(
        problem_name="weighted",
        problem_description="weighted impact example",
        metrics=(
            PerformanceMetric("cost", MetricDirection.MINIMIZE, priority=2.0),
            PerformanceMetric("service", MetricDirection.MAXIMIZE, priority=0.5),
        ),
        decisions=(DecisionType("dispatch", "operator"),),
        uncertainties=(UncertaintySource("demand"),),
        decision_impacts={"dispatch": {"cost": 3, "service": 4}},
    )
    assert frame.weighted_decision_impact("dispatch") == pytest.approx(8.0)


def test_impact_scores_are_bounded():
    with pytest.raises(ValueError, match=r"integer in \[0, 5\]"):
        base_frame(decision_impacts={"dispatch": {"cost": 6}})


def test_target_metric_requires_target():
    with pytest.raises(ValueError, match="target value"):
        PerformanceMetric("temperature", MetricDirection.TARGET)
