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
    audit_information_plan,
    audit_model,
)


def frame():
    return DecisionFrame(
        problem_name="inventory",
        problem_description="inventory control",
        metrics=(PerformanceMetric("cost", MetricDirection.MINIMIZE),),
        decisions=(DecisionType("order", "planner"),),
        uncertainties=(UncertaintySource("demand", observed_before_decision=False, representation="distribution"),),
    )


def test_model_audit_flags_missing_belief_review():
    model = UniversalModelSpec(
        state=(StateComponent("inventory", StateKind.RESOURCE, "net inventory"),),
        decisions=(DecisionVariable("x", "order", "integer"),),
        exogenous_information=(ExogenousInformation("demand", "demand", "realized demand"),),
        transitions=(TransitionRule("balance", "inventory balance"),),
        objective="minimize cost",
    )
    report = audit_model(frame(), model)
    assert report.ok
    assert "belief-state-review" in {finding.code for finding in report.warnings}


def test_model_audit_rejects_unknown_decision_link():
    model = UniversalModelSpec(
        state=(StateComponent("inventory", StateKind.RESOURCE, "net inventory"),),
        decisions=(DecisionVariable("x", "unknown", "integer"),),
        exogenous_information=(ExogenousInformation("demand", "demand", "realized demand"),),
        transitions=(TransitionRule("balance", "inventory balance"),),
        objective="minimize cost",
    )
    report = audit_model(frame(), model)
    assert not report.ok
    assert "unknown-modeled-decision" in {finding.code for finding in report.errors}
    assert "decision-not-modeled" in {finding.code for finding in report.errors}


def test_information_plan_checks_decision_coverage_and_fallback():
    plan = InformationPlan(
        (
            InformationRequirement(
                "inventory_position",
                used_by_decision="order",
                source_system="ERP",
                availability_timing="before order",
                latency_tolerance="one hour",
            ),
        )
    )
    report = audit_information_plan(frame(), plan)
    assert report.ok
    assert "required-information-no-fallback" in {finding.code for finding in report.warnings}


def test_model_audit_checks_decision_information_is_represented_in_state():
    local_frame = DecisionFrame(
        problem_name="inspection",
        problem_description="choose a diagnostic action",
        metrics=(PerformanceMetric("risk", MetricDirection.MINIMIZE),),
        decisions=(
            DecisionType(
                "inspect",
                "planner",
                information_available=("context", "failure_belief"),
            ),
        ),
        uncertainties=(
            UncertaintySource(
                "signal",
                observed_before_decision=False,
                representation="likelihood model",
            ),
        ),
    )
    incomplete = UniversalModelSpec(
        state=(
            StateComponent(
                "failure_belief",
                StateKind.BELIEF,
                "latent failure probability",
                source_information=("failure_belief",),
            ),
        ),
        decisions=(DecisionVariable("mode", "inspect", "binary"),),
        exogenous_information=(ExogenousInformation("signal", "signal", "diagnostic result"),),
        transitions=(TransitionRule("update", "belief update"),),
        objective="minimize risk",
    )
    report = audit_model(local_frame, incomplete)
    assert "decision-information-not-in-state" in {finding.code for finding in report.warnings}


def test_decision_dependent_uncertainty_without_mechanism_is_flagged():
    local_frame = DecisionFrame(
        problem_name="active sensing",
        problem_description="choose how to observe a latent condition",
        metrics=(PerformanceMetric("risk", MetricDirection.MINIMIZE),),
        decisions=(DecisionType("sense", "planner"),),
        uncertainties=(
            UncertaintySource(
                "signal",
                decision_dependent=True,
                representation="likelihood model",
            ),
        ),
    )
    from decision_framing import audit_frame

    report = audit_frame(local_frame)
    assert "decision-dependent-uncertainty-undocumented" in {
        finding.code for finding in report.warnings
    }
