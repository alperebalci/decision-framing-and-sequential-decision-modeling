from __future__ import annotations

from dataclasses import dataclass

from .models import DecisionFrame, InformationPlan, StateKind, UniversalModelSpec


@dataclass(frozen=True)
class AuditFinding:
    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class AuditReport:
    findings: tuple[AuditFinding, ...]

    @property
    def errors(self) -> tuple[AuditFinding, ...]:
        return tuple(x for x in self.findings if x.severity == "error")

    @property
    def warnings(self) -> tuple[AuditFinding, ...]:
        return tuple(x for x in self.findings if x.severity == "warning")

    @property
    def ok(self) -> bool:
        return not self.errors


def audit_frame(frame: DecisionFrame) -> AuditReport:
    findings: list[AuditFinding] = []
    if not frame.decision_impacts:
        findings.append(AuditFinding("warning", "decision-impact-matrix-missing", "No decision-to-metric impact scores are defined."))
    if not frame.uncertainty_impacts:
        findings.append(AuditFinding("warning", "uncertainty-impact-matrix-missing", "No uncertainty-to-metric impact scores are defined."))
    for decision in frame.decisions:
        if not decision.timing:
            findings.append(AuditFinding("warning", "decision-timing-missing", f"Decision {decision.name!r} has no timing description."))
    for uncertainty in frame.uncertainties:
        if uncertainty.representation == "unspecified":
            findings.append(AuditFinding("warning", "uncertainty-representation-missing", f"Uncertainty {uncertainty.name!r} has no proposed representation."))
    return AuditReport(tuple(findings))


def audit_model(frame: DecisionFrame, model: UniversalModelSpec) -> AuditReport:
    findings: list[AuditFinding] = []
    frame_decisions = {x.name for x in frame.decisions}
    model_decisions = {x.linked_decision for x in model.decisions}
    frame_uncertainties = {x.name for x in frame.uncertainties}
    model_uncertainties = {x.linked_uncertainty for x in model.exogenous_information}

    for name in sorted(frame_decisions - model_decisions):
        findings.append(AuditFinding("error", "decision-not-modeled", f"Framed decision {name!r} has no decision variable in the universal model."))
    for name in sorted(model_decisions - frame_decisions):
        findings.append(AuditFinding("error", "unknown-modeled-decision", f"Model decision links to unknown framed decision {name!r}."))
    for name in sorted(frame_uncertainties - model_uncertainties):
        findings.append(AuditFinding("warning", "uncertainty-not-modeled", f"Framed uncertainty {name!r} is not represented as exogenous information."))
    for name in sorted(model_uncertainties - frame_uncertainties):
        findings.append(AuditFinding("error", "unknown-modeled-uncertainty", f"Exogenous information links to unknown uncertainty {name!r}."))

    if not any(component.kind is StateKind.BELIEF for component in model.state):
        latent = [u.name for u in frame.uncertainties if not u.observed_before_decision]
        if latent:
            findings.append(AuditFinding(
                "warning",
                "belief-state-review",
                "Some uncertainty is not observed before decisions, but no belief-state component is defined. Review whether a belief or forecast state is needed: " + ", ".join(latent),
            ))

    return AuditReport(tuple(findings))


def audit_information_plan(frame: DecisionFrame, plan: InformationPlan) -> AuditReport:
    findings: list[AuditFinding] = []
    valid_decisions = {x.name for x in frame.decisions}
    covered: set[str] = set()
    for requirement in plan.requirements:
        if requirement.used_by_decision not in valid_decisions:
            findings.append(AuditFinding("error", "unknown-information-consumer", f"Information requirement {requirement.name!r} references unknown decision {requirement.used_by_decision!r}."))
        else:
            covered.add(requirement.used_by_decision)
        if requirement.required and not requirement.fallback:
            findings.append(AuditFinding("warning", "required-information-no-fallback", f"Required information {requirement.name!r} has no fallback strategy."))
    for decision in sorted(valid_decisions - covered):
        findings.append(AuditFinding("warning", "decision-information-unmapped", f"Decision {decision!r} has no explicit information requirement."))
    return AuditReport(tuple(findings))
