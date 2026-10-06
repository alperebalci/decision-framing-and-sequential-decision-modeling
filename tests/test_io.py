from pathlib import Path

from decision_framing import MetricDirection, load_frame


def test_load_example_frame():
    path = Path(__file__).resolve().parents[1] / "examples" / "inventory_frame.json"
    frame = load_frame(path)
    assert frame.problem_name == "Finite-horizon inventory replenishment"
    assert frame.metrics[0].direction is MetricDirection.MINIMIZE
    assert frame.weighted_uncertainty_impact("customer_demand") == 8.0
