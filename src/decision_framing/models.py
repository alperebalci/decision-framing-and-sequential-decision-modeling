from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class MetricDirection(str, Enum):
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"
    TARGET = "target"
    MONITOR = "monitor"


class StateKind(str, Enum):
    PHYSICAL = "physical"
    RESOURCE = "resource"
    INFORMATION = "information"
    BELIEF = "belief"
    TIME = "time"
    OTHER = "other"


@dataclass(frozen=True)
class PerformanceMetric:
    name: str
    direction: MetricDirection
    description: str = ""
    unit: str = ""
    target: float | None = None
    priority: float = 1.0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("metric name must not be empty")
        if self.priority <= 0:
            raise ValueError("metric priority must be positive")
        if self.direction is MetricDirection.TARGET and self.target is None:
            raise ValueError("target metrics require a target value")


@dataclass(frozen=True)
class DecisionType:
    name: str
    decision_maker: str
    description: str = ""
    timing: str = ""
    cadence: str = ""
    information_available: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("decision name must not be empty")
        if not self.decision_maker.strip():
            raise ValueError(f"decision {self.name!r} requires a decision maker")


@dataclass(frozen=True)
class UncertaintySource:
    name: str
    description: str = ""
    timing: str = ""
    observed_before_decision: bool = False
    decision_dependent: bool = False
    decision_dependence_note: str = ""
    observation_process: str = ""
    temporal_structure: str = "unspecified"
    representation: str = "unspecified"

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("uncertainty name must not be empty")


@dataclass(frozen=True)
class DecisionFrame:
    problem_name: str
    problem_description: str
    metrics: tuple[PerformanceMetric, ...]
    decisions: tuple[DecisionType, ...]
    uncertainties: tuple[UncertaintySource, ...]
    decision_impacts: Mapping[str, Mapping[str, int]] = field(default_factory=dict)
    uncertainty_impacts: Mapping[str, Mapping[str, int]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.problem_name.strip():
            raise ValueError("problem_name must not be empty")
        if not self.problem_description.strip():
            raise ValueError("problem_description must not be empty")
        if not self.metrics:
            raise ValueError("at least one performance metric is required")
        if not self.decisions:
            raise ValueError("at least one decision type is required")
        if not self.uncertainties:
            raise ValueError("at least one uncertainty source is required")
        _require_unique("metric", [m.name for m in self.metrics])
        _require_unique("decision", [d.name for d in self.decisions])
        _require_unique("uncertainty", [u.name for u in self.uncertainties])
        self._validate_impact_matrix(self.decision_impacts, {d.name for d in self.decisions}, "decision")
        self._validate_impact_matrix(self.uncertainty_impacts, {u.name for u in self.uncertainties}, "uncertainty")

    @property
    def metric_names(self) -> tuple[str, ...]:
        return tuple(m.name for m in self.metrics)

    def weighted_decision_impact(self, decision_name: str) -> float:
        return self._weighted_impact(decision_name, self.decision_impacts)

    def weighted_uncertainty_impact(self, uncertainty_name: str) -> float:
        return self._weighted_impact(uncertainty_name, self.uncertainty_impacts)

    def _weighted_impact(self, item_name: str, matrix: Mapping[str, Mapping[str, int]]) -> float:
        scores = matrix.get(item_name, {})
        return sum(metric.priority * scores.get(metric.name, 0) for metric in self.metrics)

    def _validate_impact_matrix(
        self,
        matrix: Mapping[str, Mapping[str, int]],
        valid_rows: set[str],
        row_label: str,
    ) -> None:
        metric_names = set(self.metric_names)
        unknown_rows = set(matrix) - valid_rows
        if unknown_rows:
            raise ValueError(f"unknown {row_label} rows in impact matrix: {sorted(unknown_rows)}")
        for row, scores in matrix.items():
            unknown_metrics = set(scores) - metric_names
            if unknown_metrics:
                raise ValueError(f"unknown metric columns for {row!r}: {sorted(unknown_metrics)}")
            for metric, score in scores.items():
                if not isinstance(score, int) or not 0 <= score <= 5:
                    raise ValueError(f"impact score {row!r}/{metric!r} must be an integer in [0, 5]")


@dataclass(frozen=True)
class StateComponent:
    name: str
    kind: StateKind
    description: str
    observed: bool = True
    update_source: str = ""
    source_information: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("state component name must not be empty")
        if not self.description.strip():
            raise ValueError(f"state component {self.name!r} requires a description")


@dataclass(frozen=True)
class DecisionVariable:
    name: str
    linked_decision: str
    domain: str
    constraints: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExogenousInformation:
    name: str
    linked_uncertainty: str
    description: str
    arrival_timing: str = "after decision"
    model: str = "unspecified"


@dataclass(frozen=True)
class TransitionRule:
    name: str
    description: str
    equation: str = ""


@dataclass(frozen=True)
class UniversalModelSpec:
    state: tuple[StateComponent, ...]
    decisions: tuple[DecisionVariable, ...]
    exogenous_information: tuple[ExogenousInformation, ...]
    transitions: tuple[TransitionRule, ...]
    objective: str
    horizon: str = ""

    def __post_init__(self) -> None:
        if not self.state:
            raise ValueError("universal model requires at least one state component")
        if not self.decisions:
            raise ValueError("universal model requires at least one decision variable")
        if not self.exogenous_information:
            raise ValueError("universal model requires exogenous information")
        if not self.transitions:
            raise ValueError("universal model requires at least one transition rule")
        if not self.objective.strip():
            raise ValueError("universal model requires an objective")
        _require_unique("state component", [x.name for x in self.state])
        _require_unique("decision variable", [x.name for x in self.decisions])
        _require_unique("exogenous information", [x.name for x in self.exogenous_information])
        _require_unique("transition", [x.name for x in self.transitions])


@dataclass(frozen=True)
class InformationRequirement:
    name: str
    used_by_decision: str
    source_system: str
    availability_timing: str
    latency_tolerance: str
    quality_risk: str = ""
    fallback: str = ""
    required: bool = True

    def __post_init__(self) -> None:
        for field_name in ("name", "used_by_decision", "source_system", "availability_timing", "latency_tolerance"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"information requirement field {field_name!r} must not be empty")


@dataclass(frozen=True)
class InformationPlan:
    requirements: tuple[InformationRequirement, ...]

    def __post_init__(self) -> None:
        _require_unique("information requirement", [x.name for x in self.requirements])


def _require_unique(label: str, values: list[str]) -> None:
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise ValueError(f"duplicate {label} names: {duplicates}")
