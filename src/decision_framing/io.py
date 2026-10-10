from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import DecisionFrame, DecisionType, MetricDirection, PerformanceMetric, UncertaintySource


def load_frame(path: str | Path) -> DecisionFrame:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return frame_from_dict(data)


def frame_from_dict(data: dict[str, Any]) -> DecisionFrame:
    return DecisionFrame(
        problem_name=data["problem_name"],
        problem_description=data["problem_description"],
        metrics=tuple(
            PerformanceMetric(
                name=item["name"],
                direction=MetricDirection(item["direction"]),
                description=item.get("description", ""),
                unit=item.get("unit", ""),
                target=item.get("target"),
                priority=float(item.get("priority", 1.0)),
            )
            for item in data["metrics"]
        ),
        decisions=tuple(
            DecisionType(
                name=item["name"],
                decision_maker=item["decision_maker"],
                description=item.get("description", ""),
                timing=item.get("timing", ""),
                cadence=item.get("cadence", ""),
                information_available=tuple(item.get("information_available", [])),
                constraints=tuple(item.get("constraints", [])),
            )
            for item in data["decisions"]
        ),
        uncertainties=tuple(
            UncertaintySource(
                name=item["name"],
                description=item.get("description", ""),
                timing=item.get("timing", ""),
                observed_before_decision=bool(item.get("observed_before_decision", False)),
                decision_dependent=bool(item.get("decision_dependent", False)),
                decision_dependence_note=item.get("decision_dependence_note", ""),
                observation_process=item.get("observation_process", ""),
                temporal_structure=item.get("temporal_structure", "unspecified"),
                representation=item.get("representation", "unspecified"),
            )
            for item in data["uncertainties"]
        ),
        decision_impacts=data.get("decision_impacts", {}),
        uncertainty_impacts=data.get("uncertainty_impacts", {}),
    )
