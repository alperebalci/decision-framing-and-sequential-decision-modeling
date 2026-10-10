# Portfolio integration

This repository is the method-neutral front end for the broader Jors Academy decision and optimization portfolio.

The intended flow is:

```text
real-world narrative
    ↓
decision framing
    ↓
universal sequential-decision model
    ↓
policy architecture and solution method
    ↓
simulation / validation
    ↓
information architecture and implementation
```

## Relationship to other repositories

- **sequential-decision-analytics** — policy architectures, sequential simulation, dynamic programming, reinforcement learning, and PFA/CFA/VFA/DLA comparisons.
- **management-science** — application-oriented decision models and managerial interpretation.
- **optimization-methods-taxonomy** — classification of optimization methods once the problem and policy architecture are understood.
- **simulation-optimization-and-uncertainty-quantification** — simulation calibration, uncertainty propagation, sensitivity, noisy optimization, and experimental methodology.
- **stochastic-programming-methods** — multi-stage scenario models that can serve as stochastic lookahead policies when embedded inside a sequential decision process.

The design principle is to avoid duplicating specialized algorithms here. This repository defines the problem and traceability contract; specialist repositories provide methods and deeper implementations.
