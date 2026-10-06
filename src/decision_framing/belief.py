from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InspectionMode:
    """Observation model selected by a measurement/inspection decision."""

    name: str
    sensitivity: float
    specificity: float
    cost: float = 0.0

    def __post_init__(self) -> None:
        for field_name in ("sensitivity", "specificity"):
            value = getattr(self, field_name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be in [0, 1]")
        if self.cost < 0:
            raise ValueError("inspection cost must be nonnegative")


@dataclass(frozen=True)
class BinaryBelief:
    """Belief that a latent binary condition is in the bad/positive state."""

    probability_bad: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.probability_bad <= 1.0:
            raise ValueError("probability_bad must be in [0, 1]")

    def update(self, positive_signal: bool, mode: InspectionMode) -> "BinaryBelief":
        prior = self.probability_bad
        if positive_signal:
            likelihood_bad = mode.sensitivity
            likelihood_good = 1.0 - mode.specificity
        else:
            likelihood_bad = 1.0 - mode.sensitivity
            likelihood_good = mode.specificity

        evidence = prior * likelihood_bad + (1.0 - prior) * likelihood_good
        if evidence <= 0.0:
            raise ValueError("observation has zero probability under the supplied belief and mode")

        posterior = prior * likelihood_bad / evidence
        return BinaryBelief(posterior)
