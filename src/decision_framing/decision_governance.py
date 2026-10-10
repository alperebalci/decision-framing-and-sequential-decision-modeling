"""Explicit decision rights, deterministic decision tables, and reviewable overrides.

A constrained DMN-inspired example, not a BPMN/DMN standards implementation,
authorization service, append-only event store, or causal evaluation system.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from itertools import product
import json
from math import isfinite
from typing import Mapping

Scalar = str | int | float | bool


def _label(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")


def _scalar(value: Scalar) -> bool:
    return type(value) in (str, int, float, bool) and (
        not isinstance(value, float) or isfinite(value)
    )


def _equals(a: Scalar, b: Scalar) -> bool:
    return type(a) is type(b) and a == b


def fingerprint_inputs(facts: Mapping[str, Scalar]) -> str:
    """Reproducible content fingerprint, not a signature or privacy guarantee."""
    if any(not isinstance(key, str) or not key for key in facts):
        raise ValueError("input field names must be nonempty strings")
    if any(not _scalar(value) for value in facts.values()):
        raise ValueError("decision inputs must be finite JSON scalars")
    payload = json.dumps(facts, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class DecisionRule:
    identifier: str
    when: Mapping[str, tuple[Scalar, ...]]
    action: str

    def __post_init__(self) -> None:
        _label(self.identifier, "rule identifier")
        _label(self.action, "rule action")
        if not self.when:
            raise ValueError("unconditional rules require explicit default_action")
        for field, allowed in self.when.items():
            _label(field, "condition field")
            if not allowed or any(not _scalar(value) for value in allowed):
                raise ValueError("conditions must contain finite nonempty scalar options")


@dataclass(frozen=True)
class RuleResult:
    action: str
    matched_rule_ids: tuple[str, ...]
    default_used: bool


@dataclass(frozen=True)
class RuleCoverage:
    total_combinations: int
    uncovered_combinations: int
    overlapping_combinations: int


@dataclass(frozen=True)
class DecisionTable:
    fields: tuple[str, ...]
    rules: tuple[DecisionRule, ...]
    hit_policy: str = "UNIQUE"
    default_action: str | None = None

    def __post_init__(self) -> None:
        if not self.fields or len(set(self.fields)) != len(self.fields):
            raise ValueError("decision table requires unique nonempty fields")
        for field in self.fields:
            _label(field, "decision table field")
        if not self.rules:
            raise ValueError("decision table needs at least one explicit rule")
        if self.hit_policy not in ("UNIQUE", "FIRST"):
            raise ValueError("only UNIQUE and FIRST hit policies are supported")
        identifiers = [rule.identifier for rule in self.rules]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("decision rule identifiers must be unique")
        for rule in self.rules:
            if set(rule.when) - set(self.fields):
                raise ValueError("rule contains an undeclared decision input")
        if self.default_action is not None:
            _label(self.default_action, "default_action")

    def _validate_facts(self, facts: Mapping[str, Scalar]) -> None:
        if set(facts) != set(self.fields):
            raise ValueError("inputs must exactly match the declared decision fields")
        if any(not _scalar(facts[key]) for key in self.fields):
            raise ValueError("decision inputs must be finite JSON scalars")

    def matching_rules(self, facts: Mapping[str, Scalar]) -> tuple[DecisionRule, ...]:
        self._validate_facts(facts)
        return tuple(
            rule for rule in self.rules
            if all(any(_equals(facts[field], candidate) for candidate in allowed)
                   for field, allowed in rule.when.items())
        )

    def evaluate(self, facts: Mapping[str, Scalar]) -> RuleResult:
        matches = self.matching_rules(facts)
        if not matches:
            if self.default_action is None:
                raise ValueError("no rule matched and no explicit fallback action exists")
            return RuleResult(self.default_action, (), True)
        if self.hit_policy == "UNIQUE" and len(matches) != 1:
            raise ValueError("UNIQUE hit policy violated by overlapping rules")
        return RuleResult(matches[0].action, tuple(r.identifier for r in matches), False)

    def audit_coverage(self, domains: Mapping[str, tuple[Scalar, ...]],
                       limit: int = 10000) -> RuleCoverage:
        """Exhaustively count uncovered/overlapping inputs in a declared finite domain."""
        if set(domains) != set(self.fields):
            raise ValueError("audit domain must cover exactly the table fields")
        count = 1
        for field in self.fields:
            values = domains[field]
            if not values or any(not _scalar(value) for value in values):
                raise ValueError("each audit domain must contain finite scalar values")
            if len(values) != len({(type(v).__name__, repr(v)) for v in values}):
                raise ValueError("audit domains must not repeat values")
            count *= len(values)
        if count > limit or limit <= 0:
            raise ValueError("audit exceeds finite enumeration limit")
        misses = overlaps = 0
        for combo in product(*(domains[f] for f in self.fields)):
            matched = self.matching_rules(dict(zip(self.fields, combo)))
            misses += not matched
            overlaps += len(matched) > 1
        return RuleCoverage(count, misses, overlaps)


@dataclass(frozen=True)
class Recommendation:
    decision_id: str
    recommended_action: str
    allowed_actions: tuple[str, ...]
    policy_version: str
    input_fingerprint: str

    def __post_init__(self) -> None:
        for name in ("decision_id", "recommended_action", "policy_version", "input_fingerprint"):
            _label(getattr(self, name), name)
        if not self.allowed_actions or len(set(self.allowed_actions)) != len(self.allowed_actions):
            raise ValueError("allowed_actions must be a unique, nonempty action set")
        for value in self.allowed_actions:
            _label(value, "allowed action")
        if self.recommended_action not in self.allowed_actions:
            raise ValueError("recommended action must be in the allowlist")
        if len(self.input_fingerprint) != 64 or any(c not in "0123456789abcdef" for c in self.input_fingerprint):
            raise ValueError("input_fingerprint must be lowercase SHA-256 hex")


@dataclass(frozen=True)
class OverrideRequest:
    action: str
    actor_role: str
    justification: str
    observed_at: datetime

    def __post_init__(self) -> None:
        _label(self.action, "override action")
        _label(self.actor_role, "actor_role")
        if not isinstance(self.justification, str) or len(self.justification.strip()) < 10:
            raise ValueError("override requires a substantive justification")
        if not isinstance(self.observed_at, datetime) or self.observed_at.tzinfo is None:
            raise ValueError("override timestamp must include timezone")
        if self.observed_at.utcoffset() is None:
            raise ValueError("override timestamp must have a valid timezone")


@dataclass(frozen=True)
class DecisionRecord:
    decision_id: str
    recommended_action: str
    final_action: str
    policy_version: str
    input_fingerprint: str
    override_used: bool
    override_role: str | None
    override_reason: str | None
    observed_at_utc: str | None


def resolve_decision(recommendation: Recommendation,
                     override: OverrideRequest | None = None,
                     authorized_override_roles: tuple[str, ...] = ()) -> DecisionRecord:
    """Resolve an allowed human override. Authorization MUST be enforced upstream."""
    if override is None:
        return DecisionRecord(recommendation.decision_id, recommendation.recommended_action,
                              recommendation.recommended_action, recommendation.policy_version,
                              recommendation.input_fingerprint, False, None, None, None)
    if override.actor_role not in authorized_override_roles:
        raise PermissionError("actor role is not authorized to override")
    if override.action not in recommendation.allowed_actions:
        raise ValueError("override action is outside the declared decision allowlist")
    if override.action == recommendation.recommended_action:
        raise ValueError("an identical action is not an override")
    return DecisionRecord(
        recommendation.decision_id, recommendation.recommended_action, override.action,
        recommendation.policy_version, recommendation.input_fingerprint, True,
        override.actor_role, override.justification,
        override.observed_at.astimezone(timezone.utc).isoformat(),
    )


@dataclass(frozen=True)
class DescriptiveOverrideSummary:
    decisions: int
    overrides: int
    override_rate: float
    mean_observed_kpi_with_override: float | None
    mean_observed_kpi_without_override: float | None


def summarize_overrides(records: tuple[DecisionRecord, ...],
                        observed_kpis: Mapping[str, float]) -> DescriptiveOverrideSummary:
    """Descriptive aggregates only: no causal uplift or counterfactual inference."""
    ids = [row.decision_id for row in records]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate decision_id in decision records")
    if set(observed_kpis) - set(ids):
        raise ValueError("KPI results contain unknown decision IDs")
    if any(not _scalar(v) or type(v) is bool for v in observed_kpis.values()):
        raise ValueError("observed KPIs must be finite numeric values")
    by_override = [observed_kpis[r.decision_id] for r in records
                   if r.override_used and r.decision_id in observed_kpis]
    automatic = [observed_kpis[r.decision_id] for r in records
                 if not r.override_used and r.decision_id in observed_kpis]
    n = len(records)
    altered = sum(r.override_used for r in records)
    return DescriptiveOverrideSummary(
        n, altered, altered / n if n else 0.0,
        sum(by_override) / len(by_override) if by_override else None,
        sum(automatic) / len(automatic) if automatic else None,
    )
