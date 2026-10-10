"""Decision table, influence graph and override-governance regression tests."""

from datetime import datetime, timezone

import pytest

from decision_framing import (
    DecisionRule, DecisionTable, Recommendation, OverrideRequest,
    InfluenceGraph, InfluenceNode, InfluenceArc,
    fingerprint_inputs, resolve_decision, summarize_overrides,
)


def fixture_table():
    return DecisionTable(
        fields=("demand", "capacity"),
        rules=(
            DecisionRule("r1", {"demand": ("high",), "capacity": ("low",)}, "request_capacity"),
            DecisionRule("r2", {"demand": ("high",), "capacity": ("adequate",)}, "reserve"),
            DecisionRule("r3", {"demand": ("normal",)}, "normal"),
        ),
        default_action="manual_review",
    )


def fixture_recommendation(decision_id="item-1"):
    return Recommendation(
        decision_id, "reserve", ("reserve", "request_capacity", "manual_review"),
        "v1", fingerprint_inputs({"demand": "high", "capacity": "adequate"}),
    )


def test_finite_rule_table_complete_unique_and_fallback():
    table = fixture_table()
    audit = table.audit_coverage({"demand": ("high", "normal", "unknown"),
                                  "capacity": ("low", "adequate")})
    assert audit.total_combinations == 6
    assert audit.uncovered_combinations == 2
    assert audit.overlapping_combinations == 0
    assert table.evaluate({"demand": "high", "capacity": "low"}).action == "request_capacity"
    assert table.evaluate({"demand": "normal", "capacity": "adequate"}).action == "normal"
    fallback = table.evaluate({"demand": "unknown", "capacity": "low"})
    assert fallback.default_used and fallback.matched_rule_ids == ()
    assert fallback.action == "manual_review"


def test_missing_inputs_and_silent_unmatched_rules_rejected():
    table = fixture_table()
    with pytest.raises(ValueError, match="exactly"):
        table.evaluate({"demand": "high"})
    with pytest.raises(ValueError, match="exactly"):
        table.evaluate({"demand": "high", "capacity": "low", "secret": "anything"})
    without_fallback = DecisionTable(("state",), (DecisionRule("r", {"state": ("a",)}, "take_a"),))
    with pytest.raises(ValueError, match="no rule matched"):
        without_fallback.evaluate({"state": "b"})


def test_conflict_is_visible_in_unique_and_first_policy():
    rules = (DecisionRule("broad", {"demand": ("high",)}, "A"),
             DecisionRule("specific", {"demand": ("high",), "capacity": ("low",)}, "B"))
    one = DecisionTable(("demand", "capacity"), rules, hit_policy="UNIQUE")
    audit = one.audit_coverage({"demand": ("high", "normal"), "capacity": ("low", "adequate")})
    assert audit.overlapping_combinations == 1
    with pytest.raises(ValueError, match="UNIQUE"):
        one.evaluate({"demand": "high", "capacity": "low"})
    first = DecisionTable(("demand", "capacity"), rules, hit_policy="FIRST")
    res = first.evaluate({"demand": "high", "capacity": "low"})
    assert res.action == "A"
    assert res.matched_rule_ids == ("broad", "specific")


def test_audit_limits_duplicate_rule_and_typed_conditions():
    table = fixture_table()
    with pytest.raises(ValueError, match="limit"):
        table.audit_coverage({"demand": ("high", "normal"), "capacity": ("low", "adequate")}, limit=3)
    with pytest.raises(ValueError, match="unique"):
        DecisionTable(("x",), (DecisionRule("x", {"x": (1,)}, "one"),
                               DecisionRule("x", {"x": (2,)}, "two")))
    typed = DecisionTable(("value",), (DecisionRule("bool", {"value": (True,)}, "yes"),),
                          default_action="no")
    assert typed.evaluate({"value": 1}).action == "no"
    assert typed.evaluate({"value": True}).action == "yes"


def test_fingerprint_is_deterministic_but_not_a_signature():
    left = fingerprint_inputs({"a": 1, "b": "high"})
    right = fingerprint_inputs({"b": "high", "a": 1})
    assert left == right and len(left) == 64
    assert fingerprint_inputs({"a": 1}) != fingerprint_inputs({"a": True})


def test_authorized_human_override_with_utc_trace():
    reco = fixture_recommendation()
    request = OverrideRequest("manual_review", "operations_manager",
                              "Updated capacity signal requires manual confirmation",
                              datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc))
    result = resolve_decision(reco, request, ("operations_manager",))
    assert result.override_used
    assert result.final_action == "manual_review"
    assert result.recommended_action == "reserve"
    assert result.input_fingerprint == reco.input_fingerprint
    assert result.observed_at_utc.endswith("+00:00")
    assert result.override_reason == request.justification
    assert resolve_decision(reco).final_action == "reserve"


def test_unauthorized_or_out_of_policy_overrides_are_rejected():
    reco = fixture_recommendation()
    now = datetime.now(timezone.utc)
    request = OverrideRequest("request_capacity", "unapproved_role",
                              "This is a sufficiently detailed justification", now)
    with pytest.raises(PermissionError, match="authorized"):
        resolve_decision(reco, request, ("operations_manager",))
    wrong = OverrideRequest("invented", "operations_manager",
                            "This is a sufficiently detailed justification", now)
    with pytest.raises(ValueError, match="allowlist"):
        resolve_decision(reco, wrong, ("operations_manager",))
    same = OverrideRequest("reserve", "operations_manager",
                           "This is a sufficiently detailed justification", now)
    with pytest.raises(ValueError, match="identical"):
        resolve_decision(reco, same, ("operations_manager",))
    with pytest.raises(ValueError, match="justification"):
        OverrideRequest("manual_review", "operations_manager", "no", now)
    with pytest.raises(ValueError, match="timezone"):
        OverrideRequest("manual_review", "operations_manager",
                        "Some substantial operational context", datetime(2026, 1, 1))


def test_summary_is_observational_and_rejects_duplicate_ids():
    baseline = resolve_decision(fixture_recommendation())
    override = resolve_decision(
        fixture_recommendation("item-2"),
        OverrideRequest("request_capacity", "manager", "Operational risk model changed",
                        datetime(2026, 1, 1, tzinfo=timezone.utc)),
        ("manager",),
    )
    summary = summarize_overrides((baseline, override), {"item-1": 10., "item-2": 8.})
    assert summary.decisions == 2 and summary.overrides == 1
    assert summary.override_rate == pytest.approx(0.5)
    assert summary.mean_observed_kpi_with_override == 8
    assert summary.mean_observed_kpi_without_override == 10
    with pytest.raises(ValueError, match="duplicate"):
        summarize_overrides((baseline, baseline), {})


def fixture_graph():
    return InfluenceGraph(
        (InfluenceNode("demand", "chance"),
         InfluenceNode("dispatch", "decision"),
         InfluenceNode("queue", "chance"),
         InfluenceNode("delay", "value")),
        (InfluenceArc("demand", "dispatch", "information"),
         InfluenceArc("dispatch", "queue", "causal"),
         InfluenceArc("demand", "queue", "causal"),
         InfluenceArc("queue", "delay", "utility")),
    )


def test_influence_graph_predecision_information_is_topological():
    order = fixture_graph().validate()
    assert order.index("demand") < order.index("dispatch") < order.index("queue") < order.index("delay")


def test_influence_graph_rejects_backwards_information_and_cycles():
    nodes = (InfluenceNode("decision", "decision"), InfluenceNode("signal", "chance"))
    graph = InfluenceGraph(nodes, (InfluenceArc("decision", "signal", "causal"),
                                   InfluenceArc("signal", "decision", "information")))
    with pytest.raises(ValueError, match="cycle"):
        graph.validate()
    with pytest.raises(ValueError, match="invalid influence"):
        InfluenceGraph(nodes, (InfluenceArc("decision", "signal", "information"),)).validate()
    with pytest.raises(ValueError, match="unknown"):
        InfluenceGraph(nodes, (InfluenceArc("signal", "elsewhere", "information"),)).validate()
