# Optimize Module

> **Internal module** — This is an implementation detail of bossanova.
> Users should not import from this module directly. Use the model classes
> (`lmer`, `glmer`) which handle optimization automatically.

## Purpose

This module provides optimization routines for fitting mixed-effects models,
specifically the BOBYQA (Bound Optimization BY Quadratic Approximation)
algorithm used to optimize the random effects variance parameters (theta).

## Components

- **bobyqa.py**: BOBYQA optimizer for bound-constrained optimization of theta

## How It Connects

```
lmer/glmer.fit()
       │
       ▼
  optimize/         ← THIS MODULE: Find optimal theta
       │
       ▼
  Converged model with variance components
```

Mixed-effects models require optimizing the profile deviance or REML criterion
over the variance-covariance parameters of the random effects. This module
provides the optimizer that searches for the optimal theta values.

## Why BOBYQA?

BOBYQA is the same optimizer used by R's lme4 package (via the `nloptr` package).
Using the same algorithm helps ensure numerical parity with R results.

Key properties:
- Derivative-free (doesn't require gradients)
- Handles bound constraints (variance parameters must be non-negative)
- Robust for the likelihood surfaces typical of mixed models

## Key Exports

| Function | Purpose |
|----------|---------|
| `optimize_theta` | Optimize random effects variance parameters |
