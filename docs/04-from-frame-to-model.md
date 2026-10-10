# From a frame to a universal sequential-decision model

The `UniversalModelSpec` is a compact bridge from the method-neutral frame to a formal decision model.

It records five elements:

1. **State** — information available to the decision process.
2. **Decision variables** — mathematical representation of the framed decisions.
3. **Exogenous information** — new information associated with framed uncertainties.
4. **Transition rules** — how state evolves after decisions and information arrive.
5. **Objective** — how a policy is evaluated over time.

The model spec deliberately does not prescribe a solution method. A policy can later be a direct rule, a parameterized optimization model, a value-based policy, a deterministic or stochastic lookahead, a reinforcement-learning policy, or a hybrid.

## Traceability

`audit_model(frame, model)` checks traceability in both directions:

- every framed decision should map to at least one decision variable;
- every decision variable should link to a framed decision;
- framed uncertainties should be reviewed for exogenous-information representation;
- exogenous-information elements should link back to a known uncertainty source;
- partially observed problems should trigger a review of belief-state design.

The goal is not to prove that a model is correct. It is to prevent silent loss of important real-world decisions and uncertainties during formalization.
