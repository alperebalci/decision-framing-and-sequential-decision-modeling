from decision_framing import (
    DecisionFrame,
    DecisionType,
    DecisionVariable,
    ExogenousInformation,
    InformationPlan,
    InformationRequirement,
    MetricDirection,
    PerformanceMetric,
    StateComponent,
    StateKind,
    TransitionRule,
    UncertaintySource,
    UniversalModelSpec,
    audit_frame,
    audit_information_plan,
    audit_model,
)


frame = DecisionFrame(
    problem_name="Finite-horizon inventory replenishment",
    problem_description="Choose replenishment quantities over time while customer demand is uncertain.",
    metrics=(
        PerformanceMetric("operating_cost", MetricDirection.MINIMIZE, unit="currency", priority=1.0),
        PerformanceMetric("fill_rate", MetricDirection.MAXIMIZE, unit="fraction", priority=0.6),
    ),
    decisions=(
        DecisionType(
            "replenish_inventory",
            decision_maker="inventory planner",
            timing="before demand in each period",
            cadence="daily",
            information_available=("on_hand_inventory", "demand_forecast"),
            constraints=("order quantity is nonnegative", "order quantity <= supplier capacity"),
        ),
    ),
    uncertainties=(
        UncertaintySource(
            "customer_demand",
            timing="during each period after replenishment",
            observed_before_decision=False,
            temporal_structure="seasonal and serially correlated",
            representation="predictive demand distribution",
        ),
    ),
    decision_impacts={"replenish_inventory": {"operating_cost": 5, "fill_rate": 5}},
    uncertainty_impacts={"customer_demand": {"operating_cost": 5, "fill_rate": 5}},
)

model = UniversalModelSpec(
    state=(
        StateComponent("time", StateKind.TIME, "Current decision epoch."),
        StateComponent("inventory", StateKind.RESOURCE, "Net inventory before ordering."),
        StateComponent(
            "demand_belief",
            StateKind.BELIEF,
            "Current forecast distribution for future demand.",
            observed=False,
            update_source="forecasting model",
        ),
    ),
    decisions=(DecisionVariable("order_quantity", "replenish_inventory", "integer >= 0"),),
    exogenous_information=(
        ExogenousInformation(
            "realized_demand",
            "customer_demand",
            "Demand observed after the order is placed.",
            model="predictive demand distribution",
        ),
    ),
    transitions=(
        TransitionRule("inventory_balance", "Update net inventory after demand.", "I[t+1] = I[t] + x[t] - W[t+1]"),
        TransitionRule("forecast_update", "Update the demand belief when new data arrives."),
    ),
    objective="Minimize expected cumulative operating cost while monitoring service performance.",
    horizon="finite",
)

information_plan = InformationPlan(
    requirements=(
        InformationRequirement(
            "inventory_position",
            used_by_decision="replenish_inventory",
            source_system="ERP/WMS",
            availability_timing="before each decision",
            latency_tolerance="less than one planning cycle",
            quality_risk="late receipts and inventory-record error",
            fallback="use last reconciled inventory position and flag the decision",
        ),
        InformationRequirement(
            "demand_forecast",
            used_by_decision="replenish_inventory",
            source_system="forecasting service",
            availability_timing="before each decision",
            latency_tolerance="less than one planning cycle",
            quality_risk="distribution shift or stale forecast",
            fallback="use a documented seasonal baseline distribution",
        ),
    )
)


if __name__ == "__main__":
    for title, report in (
        ("frame", audit_frame(frame)),
        ("model", audit_model(frame, model)),
        ("information plan", audit_information_plan(frame, information_plan)),
    ):
        print(f"[{title}]")
        if not report.findings:
            print("  no findings")
        for finding in report.findings:
            print(f"  {finding.severity}: {finding.code} - {finding.message}")
