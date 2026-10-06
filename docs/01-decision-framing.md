# Decision framing

Decision framing is deliberately method-neutral. The purpose is to understand the decision system before selecting optimization, simulation, forecasting, reinforcement learning, stochastic programming, or any other analytical technique.

The framing starts from a plain-language problem description and three groups of questions.

## 1. Performance metrics

Specify what good performance means before building a model. Metrics should have an operational definition, direction, unit, time scale, and—when useful—a target or priority.

Examples include total operating cost, fill rate, lateness, throughput, emissions, risk, reliability, and response time. A model objective can later aggregate or constrain these metrics, but the frame should preserve the original business or engineering meaning.

## 2. Decisions and decision makers

List the controllable decisions that affect performance. Record who or what makes each decision, when it is made, how frequently it is revisited, what information is available at that point, and the important feasibility constraints.

This avoids a common failure mode: starting from an optimization formulation and silently treating its variables as if they were the complete real-world decision process.

## 3. Sources of uncertainty

Identify what is unknown when each decision is made. For every uncertainty source, record when it is revealed, whether it depends on the decision, its temporal structure, and a plausible representation.

The representation might be a predictive distribution, scenario generator, stochastic process, ambiguity set, empirical trace library, forecast-error model, or a deliberately deterministic approximation. The representation should follow from the decision problem rather than define it.

## Impact matrices

The package supports optional 0–5 impact matrices for decisions-to-metrics and uncertainties-to-metrics. These are prioritization aids, not statistical estimates. Their purpose is to expose which decisions and uncertainties deserve modeling effort.

## Exit criterion

A frame is useful when another person can answer four questions without seeing an algorithm:

1. What is being improved?
2. What can be decided, by whom, and when?
3. What is unknown at each decision epoch?
4. Which parts have the largest effect on performance?

Only then should the work proceed to a formal sequential-decision model.
