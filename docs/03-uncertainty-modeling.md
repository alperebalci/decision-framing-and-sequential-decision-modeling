# Uncertainty modeling

Uncertainty modeling begins with the framing question “what is unknown when the decision is made?” rather than with a preferred probability distribution.

For each source of uncertainty, document at least:

- **revelation timing** — before or after which decision does information arrive?
- **observability** — is the quantity observed directly, partially observed, delayed, censored, or inferred?
- **decision dependence** — can the decision change the information distribution or what is observed?
- **temporal structure** — independent, seasonal, autocorrelated, regime-switching, drifting, event-driven;
- **cross-sectional structure** — spatial, network, common-factor, correlated across products/assets/resources;
- **representation** — empirical traces, predictive distribution, stochastic process, scenarios, ambiguity set, simulator, deterministic forecast plus error model;
- **model risk** — how might the representation fail under distribution shift or misspecification?

The formal universal model represents information arriving after the decision as exogenous information. “Exogenous” does not mean “statistically independent of the decision” in every application; decision-dependent observations or outcomes should be documented explicitly.

## Separate forecasting from decision modeling

A forecasting model produces decision-relevant information. It is not itself the decision policy. The sequential model should make the handoff explicit:

```text
historical/context data
        ↓
forecast or belief update
        ↓
information state / belief state
        ↓
policy chooses decision
        ↓
new outcome is observed
        ↓
state and beliefs are updated
```

This separation makes it possible to test forecast quality and decision quality independently as well as end-to-end.


## Decision-dependent observations

Some actions change what information will be observed. Inspection intensity, sensor placement, sampling effort, experimental design, market probing, exploration actions, and diagnostic tests are examples.

For these cases, `UncertaintySource.decision_dependent` should be true and `decision_dependence_note` should explain the mechanism. The optional `observation_process` field records the likelihood or measurement model.

The executable `examples/active_inspection_case.py` uses a latent binary machine condition. A cheap and a deep inspection have different sensitivity and specificity. The same positive signal therefore produces different posterior failure beliefs because the observation model is conditional on the selected action. This is an information-acquisition decision, not merely an external random disturbance.
