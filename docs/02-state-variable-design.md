# State-variable design

A state variable is not merely a list of physical measurements. It is the information representation used by a policy and transition model to make and evaluate decisions over time.

This repository distinguishes several state roles:

- **physical state** — locations, temperatures, machine condition, queue position;
- **resource state** — inventory, cash, workforce, capacity, energy, vehicles;
- **information state** — observed forecasts, orders, schedules, context, covariates;
- **belief state** — probability distributions, parameter estimates, posterior beliefs, hidden-state estimates;
- **time state** — period, season, time to deadline, remaining horizon.

## Design test

For each candidate state component ask:

1. Is it known when the decision is made?
2. Can it affect a performance metric now or later?
3. Can it affect feasible decisions now or later?
4. Is it needed to update the system after new information arrives?
5. If something important is not observed directly, what belief or estimate represents current knowledge about it?

A state that contains too little information can make the transition or policy logically inconsistent. A state that contains everything ever observed can be computationally useless. State design is therefore iterative: begin with a defensible information set and expand it when validation exposes missing decision-relevant information.

## Belief-state warning

`audit_model` raises a review warning when the framing contains uncertainty that is not observed before a decision but the model contains no belief-state component. The warning is intentionally not an error: not every latent uncertainty requires an explicit Bayesian belief state, but the omission should be conscious.


## Information-to-state traceability

A framed decision can list the information available when it is made. `StateComponent.source_information` records how those operational information items are represented in the formal state. The model audit warns when a decision claims to use information that is absent from the state representation.

This is deliberately a traceability check rather than a proof of Markov sufficiency. It catches a common modeling error: a policy description refers to a forecast, context feature, estimate, or measurement that the formal state silently omits.
