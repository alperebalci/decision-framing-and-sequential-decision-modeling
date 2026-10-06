# Information requirements and implementation

A policy that performs well in a simulator can still be impossible to operate. The `InformationPlan` makes the implementation dependency explicit before deployment.

For each required input record:

- which decision consumes it;
- the source system or measurement process;
- when it must be available;
- acceptable latency;
- known data-quality risks;
- a fallback when the input is missing or stale.

Examples include ERP inventory positions, sensor health signals, forecast distributions, travel-time feeds, market prices, staffing attendance, and supplier capacity confirmations.

## Why this belongs in the decision model

Different policies can have different information requirements even when they address the same physical system. A simple rule may operate from a few robust signals, while a stochastic lookahead may require calibrated distributions, scenario generation, and substantially more computation. Policy evaluation should therefore consider not only objective value but also data burden, latency, robustness, explainability, tuning burden, and operational fallback behavior.

## Deployment loop

A production decision system should expose the full loop:

```text
observe / estimate state
        ↓
validate required information
        ↓
policy selects decision
        ↓
execute decision
        ↓
observe new information and outcomes
        ↓
update state / beliefs
        ↓
record performance metrics
```

This repository stops at the specification and audit layer; application repositories should implement the actual adapters, policies, simulator, and production controls.
