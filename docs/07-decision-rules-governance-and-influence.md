# Decision rules, influence framing and reviewable human overrides

This extension makes the **organizational decision interface** explicit, complementing mathematical solvers elsewhere in the portfolio. It does not replace the repository's core framing models or the normative AHP/EVSI decision-science methods in [Management Science](https://github.com/alperebalci/management-science/tree/main/case-studies/flagships/decision-science-preferences-and-information).

## Architecture

1. Describe actors, metrics and uncertain inputs using `DecisionFrame`.
2. Describe what observations precede which actions with a **structural influence graph** (`InfluenceGraph`). Allowed arcs: chance→chance or decision→chance (causal), chance→decision (information), and decision/chance→value (utility). The validator rejects cycles and impossible lookahead.
3. Run a **deterministic decision table** (`DecisionTable`) over a small set of named inputs and declarative matching rules.
4. Produce a versioned `Recommendation` with an input fingerprint and an explicit allowed-action set.
5. Allow a documented human `OverrideRequest` **only after external authorization**, with a substantive reason, timezone-aware timestamp and within the allowed actions.
6. Record the original and final action together; compute descriptive override rates and realized KPI averages without calling observational differences causal improvements.

## Run

`python examples/governance_case.py`

The existing CI runs `pytest` on Python 3.10 and 3.12.

## Decision-table semantics

This is a tiny **DMN-inspired** decision table, not a standards-compliant DMN implementation: there is no FEEL evaluator, DMN XML roundtrip, full hit-policy set or formal executable DMN engine.

- `UNIQUE` rejects overlapping matched rules, rather than silently choosing a favorable answer.
- `FIRST` uses declared rule order and reports all matching IDs.
- Missing/extra inputs are rejected. Unmatched inputs require an explicit `default_action` or raise an error.
- `audit_coverage` enumerates a **declared finite input domain** and counts unmatched and overlapping cases. It does not prove coverage outside the tested domain.

## Influence and causal boundaries

Influence arcs document **assumed** dependencies, choices and observation timing; they do not imply validated causal relationships, learned Bayesian-network CPTs, causal identification, intervention effects, or probabilistic decision evaluation. The graph audit checks structure and time order only. Domain experts must justify dependencies and enforce information availability operationally.

## Human–AI governance boundaries

The code is deliberately a **policy-layer reference**, not a deployed authorization or audit infrastructure:

- Role strings are metadata, **not authenticated identities**. Authentication, approval policy, access control, privacy, signing, immutable storage and incident response must be supplied by a real host system.
- `fingerprint_inputs` is a deterministic SHA-256 digest, not a digital signature; low-entropy values may still be guessed. Do not log sensitive fields without data protection.
- The model rejects out-of-allowlist actions, same-action “overrides,” missing justifications and naive timestamps.
- An override rate or average observed KPI is **descriptive only**. Override decisions are selected/nonrandom. Their observed difference cannot estimate human value-add, algorithm aversion, algorithmic fairness or causal ROI without an evaluation design (e.g., randomized assignment or justified off-policy analysis).
- Fallback conditions, post-decision realized metrics, reviewer escalation and metric drift should be specified before production deployment.

This establishes reproducible decision governance interfaces, not organizational certification or DMN compliance.
