# Decision Framing and Sequential Decision Modeling

A method-neutral toolkit for translating real-world decision problems into explicit sequential-decision models before choosing an optimization, simulation, machine-learning, reinforcement-learning, or stochastic-programming method.

The repository is organized around a simple discipline:

```text
plain-language problem
        ↓
performance metrics
+ decisions and decision makers
+ sources of uncertainty
        ↓
universal sequential-decision model
        ↓
policy architecture
        ↓
simulation / production implementation
        ↓
information requirements and field performance
```

The framing layer intentionally comes before method selection. This reduces the risk of defining the real problem around the variables and assumptions of a preferred algorithm.

## What is implemented

The Python package provides typed, dependency-free primitives for:

- performance metrics with direction, units, targets, and priorities;
- decision types with decision makers, timing, information, and constraints;
- uncertainty sources with observability, timing, decision dependence, temporal structure, and representation;
- optional decision-to-metric and uncertainty-to-metric impact matrices;
- a five-part universal model specification: state, decisions, exogenous information, transitions, objective;
- explicit physical/resource/information/belief/time state roles;
- traceability audits from the frame into the formal model;
- information requirements for operational policies, including latency, data-quality risk, and fallback behavior;
- JSON loading and a small validation CLI.

This is not a solver. It is the layer that answers **what problem is being solved** and **what information the decision process requires** before a solver or policy architecture is selected.

## Installation

```bash
python -m pip install -e ".[dev]"
```

## Run the example

```bash
python examples/inventory_case.py
python -m decision_framing examples/inventory_frame.json
```

The inventory example shows the full chain from a method-neutral frame to a universal model and an implementation information plan.

## Minimal API example

```python
from decision_framing import (
    DecisionFrame,
    DecisionType,
    MetricDirection,
    PerformanceMetric,
    UncertaintySource,
)

frame = DecisionFrame(
    problem_name="Fleet dispatch",
    problem_description="Assign available vehicles to requests as demand arrives.",
    metrics=(
        PerformanceMetric("service_delay", MetricDirection.MINIMIZE, unit="minutes"),
    ),
    decisions=(
        DecisionType("assign_vehicle", decision_maker="dispatcher", timing="on each request"),
    ),
    uncertainties=(
        UncertaintySource(
            "future_requests",
            timing="after current dispatch decisions",
            observed_before_decision=False,
            temporal_structure="time-varying arrivals",
            representation="arrival model or empirical traces",
        ),
    ),
)
```

From this point, the formal model should define state variables, the decision variable, exogenous information, transition rules, and the objective used to evaluate a policy.

## Repository structure

```text
.
├── src/decision_framing/
│   ├── models.py
│   ├── audit.py
│   ├── io.py
│   └── __main__.py
├── examples/
│   ├── inventory_case.py
│   └── inventory_frame.json
├── docs/
│   ├── 01-decision-framing.md
│   ├── 02-state-variable-design.md
│   ├── 03-uncertainty-modeling.md
│   ├── 04-from-frame-to-model.md
│   ├── 05-information-and-implementation.md
│   └── 06-portfolio-integration.md
├── tests/
└── .github/workflows/tests.yml
```

## Methodological position

The repository follows Warren B. Powell's Sequential Decision Analytics perspective as an important methodological reference: frame problems using performance metrics, decisions, and uncertainties; formalize sequential problems with state variables, decision variables, exogenous information, transition functions, and an objective; and treat the method for making decisions as a policy that can be designed and evaluated separately from the underlying problem model.

The code and documentation in this repository are an independent implementation and synthesis for the Jors Academy portfolio. They are not an official Powell project and do not reproduce his decision-framing application.

Useful primary references:

- Warren B. Powell, *Framing Decision Problems*: https://warrenpowell.org/framingdecisionproblems/
- Warren B. Powell, *Bridging Decision Problems*: https://warrenpowell.org/bridgingdecisionproblems/
- Warren B. Powell, *Policies*: https://warrenpowell.org/policies/
- Warren B. Powell, *Reinforcement Learning and Stochastic Optimization*: https://warrenpowell.org/rlso/

## Portfolio role

This repository should be read **before** method-specific repositories. It provides the front-end modeling contract; `sequential-decision-analytics` then addresses policy design and sequential solution architectures, while simulation, stochastic programming, robust optimization, reinforcement learning, and other repositories provide specialist methods.

See [docs/06-portfolio-integration.md](docs/06-portfolio-integration.md) for the cross-repository map.

## Tests

```bash
pytest
```

CI runs on Python 3.10 and 3.12 and executes both the JSON validator and the executable inventory case.

## Scope and limitations

- Impact scores are structured prioritization aids, not probabilities or statistical confidence measures.
- The audit functions check traceability and obvious omissions; they do not prove model correctness, Markov sufficiency, identifiability, or optimality.
- Uncertainty representations are application-dependent and should be validated in specialist simulation/UQ or stochastic-modeling work.
- Policy design is intentionally delegated to `sequential-decision-analytics` and related repositories.

## License

This repository uses the Jors Academy Restricted Source License v1.0. See `LICENSE.md`.
