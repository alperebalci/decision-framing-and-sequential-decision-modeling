"""Minimal decision framing -> rules -> human review -> influence audit."""

from datetime import datetime, timezone

from decision_framing import (
    DecisionRule, DecisionTable, Recommendation, OverrideRequest,
    InfluenceArc, InfluenceGraph, InfluenceNode,
    fingerprint_inputs, resolve_decision, summarize_overrides,
)


def main() -> None:
    rules = DecisionTable(
        fields=("demand", "capacity"),
        rules=(
            DecisionRule("urgent", {"demand": ("high",), "capacity": ("low",)}, "request_capacity"),
            DecisionRule("normal", {"demand": ("normal",)}, "reserve"),
        ),
        default_action="manual_review",
    )
    inputs = {"demand": "high", "capacity": "low"}
    recommended = rules.evaluate(inputs).action
    recommendation = Recommendation(
        "shift-2026-01", recommended,
        ("request_capacity", "reserve", "manual_review"), "rules-v1",
        fingerprint_inputs(inputs),
    )
    override = OverrideRequest(
        action="manual_review",
        actor_role="operations_manager",
        justification="Known temporary outage requires manual dispatch before buying capacity",
        observed_at=datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc),
    )
    result = resolve_decision(recommendation, override, ("operations_manager",))
    graph = InfluenceGraph(
        (InfluenceNode("demand", "chance"), InfluenceNode("dispatch", "decision"),
         InfluenceNode("queue", "chance"), InfluenceNode("delay", "value")),
        (InfluenceArc("demand", "dispatch", "information"),
         InfluenceArc("dispatch", "queue", "causal"),
         InfluenceArc("queue", "delay", "utility")),
    )
    print("Rule audit:", rules.audit_coverage({"demand": ("normal", "high"),
                                               "capacity": ("low", "adequate")}))
    print("Final decision record:", result)
    print("Influence order:", graph.validate())
    print("Descriptive summary:", summarize_overrides((result,), {}))


if __name__ == "__main__":
    main()
