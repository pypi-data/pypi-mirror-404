# Resample Module

> **Internal module** — This is an implementation detail of bossanova.
> Users should not import from this module directly. Use model methods like
> `.bootstrap()`, `.permute()`, or grammar verbs like `bootstrap()`, `permute()`.

## Purpose

This module provides JAX-accelerated implementations of resampling-based
inference methods: permutation tests, bootstrap procedures, and cross-validation.

## Components

- **indices.py**: Generate permutation, bootstrap, and CV index arrays
- **bootstrap.py**: Bootstrap CI methods (percentile, basic, BCa)
- **permutation.py**: Permutation test infrastructure
- **cv.py**: K-fold and leave-one-out cross-validation
- **lm_resample.py**: Optimized resampling for linear models
- **glm_resample.py**: Resampling for generalized linear models
- **lmer_resample.py**: Parametric bootstrap for mixed models
- **glmer_resample.py**: Bootstrap for generalized mixed models

## How It Connects

```
model.bootstrap(n_boot=1000)
       │
       ▼
  resample/         ← THIS MODULE: Run bootstrap
       │
       ├── Generate bootstrap indices
       ├── Refit model on each resample
       └── Compute CIs from distribution
       │
       ▼
  BootstrapResult with CIs
```

## Resampling Methods

| Method | Use Case |
|--------|----------|
| **Permutation** | Exact/approximate p-values under null hypothesis |
| **Bootstrap** | CIs when asymptotic assumptions may not hold |
| **Cross-validation** | Predictive performance estimation |

## JAX Acceleration

These methods are computationally intensive (thousands of model refits).
The JAX backend enables:

- Vectorized operations across resamples
- GPU acceleration when available
- Memory-efficient batching for large datasets

## Key Exports

| Function | Purpose |
|----------|---------|
| `lm_bootstrap` | Bootstrap inference for lm |
| `lm_permute` | Permutation test for lm |
| `glm_bootstrap` | Bootstrap for GLMs |
| `lmer_bootstrap` | Parametric bootstrap for mixed models |
| `bootstrap_ci_bca` | BCa confidence intervals |
