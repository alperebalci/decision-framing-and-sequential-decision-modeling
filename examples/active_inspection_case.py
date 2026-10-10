from decision_framing import (
    BinaryBelief,
    DecisionFrame,
    DecisionType,
    DecisionVariable,
    ExogenousInformation,
    InspectionMode,
    MetricDirection,
    PerformanceMetric,
    StateComponent,
    StateKind,
    TransitionRule,
    UncertaintySource,
    UniversalModelSpec,
    audit_frame,
    audit_model,
)


frame = DecisionFrame(
    problem_name="Active machine inspection",
    problem_description=(
        "Choose an inspection mode whose accuracy and cost affect the information "
        "available for a later maintenance decision."
    ),
    metrics=(
        PerformanceMetric("inspection_cost", MetricDirection.MINIMIZE, unit="currency", priority=0.4),
        PerformanceMetric("failure_risk", MetricDirection.MINIMIZE, unit="probability", priority=1.0),
    ),
    decisions=(
        DecisionType(
            "choose_inspection_mode",
            decision_maker="maintenance planner",
            timing="before observing the diagnostic signal",
            information_available=("machine_context", "failure_belief"),
        ),
    ),
    uncertainties=(
        UncertaintySource(
            "inspection_signal",
            description="Noisy diagnostic signal about a latent failure condition.",
            timing="after the inspection mode is selected",
            observed_before_decision=False,
            decision_dependent=True,
            decision_dependence_note=(
                "The selected inspection mode changes signal sensitivity and specificity."
            ),
            observation_process="binary diagnostic signal conditional on latent condition and inspection mode",
            temporal_structure="single diagnostic observation",
            representation="decision-dependent likelihood model",
        ),
    ),
)

model = UniversalModelSpec(
    state=(
        StateComponent(
            "machine_context",
            StateKind.INFORMATION,
            "Observed operating context available before inspection.",
            source_information=("machine_context",),
        ),
        StateComponent(
            "failure_belief",
            StateKind.BELIEF,
            "Probability that the machine is in the latent bad condition.",
            observed=False,
            update_source="Bayesian update from inspection signal",
            source_information=("failure_belief",),
        ),
    ),
    decisions=(
        DecisionVariable(
            "inspection_mode",
            linked_decision="choose_inspection_mode",
            domain="{cheap, deep}",
        ),
    ),
    exogenous_information=(
        ExogenousInformation(
            "diagnostic_signal",
            linked_uncertainty="inspection_signal",
            description="Positive or negative diagnostic signal.",
            arrival_timing="after inspection mode selection",
            model="decision-dependent sensitivity/specificity",
        ),
    ),
    transitions=(
        TransitionRule(
            "belief_update",
            "Update the latent-failure belief using Bayes' rule and the chosen inspection mode.",
        ),
    ),
    objective="Balance inspection cost against downstream failure risk.",
    horizon="two-stage information acquisition and maintenance setting",
)

prior = BinaryBelief(0.20)
cheap = InspectionMode("cheap", sensitivity=0.65, specificity=0.80, cost=1.0)
deep = InspectionMode("deep", sensitivity=0.95, specificity=0.97, cost=5.0)

if __name__ == "__main__":
    print("[frame audit]")
    for finding in audit_frame(frame).findings:
        print(f"  {finding.severity}: {finding.code} - {finding.message}")

    print("[model audit]")
    for finding in audit_model(frame, model).findings:
        print(f"  {finding.severity}: {finding.code} - {finding.message}")

    print("[posterior after positive signal]")
    print(f"  prior: {prior.probability_bad:.4f}")
    print(f"  cheap inspection: {prior.update(True, cheap).probability_bad:.4f}")
    print(f"  deep inspection:  {prior.update(True, deep).probability_bad:.4f}")
