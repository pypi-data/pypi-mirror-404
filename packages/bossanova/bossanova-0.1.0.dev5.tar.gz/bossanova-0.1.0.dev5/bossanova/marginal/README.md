# Marginal Module

> **Internal module** — This is an implementation detail of bossanova.
> Users should not import from this module directly. Use model methods like
> `.emmeans()`, `.emtrends()`, `.mee()`, or `.jointtest()` on fitted models.

## Purpose

This module provides the computational infrastructure for estimated marginal
means (EMMs), marginal effects, and joint hypothesis tests. It implements
the approach used by R's emmeans package.

## Components

- **grid.py**: Reference grid construction for marginal predictions
- **emm.py**: EMM computation and formatting
- **contrasts.py**: Contrast matrix builders (pairwise, sum-to-zero, custom)
- **hypothesis.py**: F-tests, chi-square tests, t-tests for contrasts
- **joint_tests.py**: Joint tests of EMM contrasts (ANOVA via emmeans)

## How It Connects

```
model.emmeans("~ group")
       │
       ▼
  marginal/         ← THIS MODULE: Compute EMMs
       │
       ├── grid.py      → Build reference grid
       ├── emm.py       → Compute means & SEs
       └── contrasts.py → Build contrast matrices
       │
       ▼
  Polars DataFrame with estimates, CIs, p-values
```

## What Are EMMs?

Estimated Marginal Means (EMMs, formerly "least-squares means") are model-based
predictions at specific covariate values, typically averaging over other factors.
They answer questions like:

- "What is the predicted outcome for each treatment group, averaging over
  other covariates?"
- "Are the marginal means different between groups?" (via contrasts)

## Key Exports

| Function | Purpose |
|----------|---------|
| `build_reference_grid` | Create grid of predictor combinations |
| `compute_emm` | Calculate marginal means and SEs |
| `build_pairwise_contrast` | Pairwise comparison matrix |
| `compute_f_test` | F-test for joint hypotheses |
| `joint_tests` | EMM-based ANOVA table |
