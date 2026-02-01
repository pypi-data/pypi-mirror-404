# Ops Module

> **Internal module** — This is an implementation detail of bossanova.
> Users should not import from this module directly. Use the model classes
> (`lm`, `glm`, `lmer`, `glmer`) or access results via model properties.

## Purpose

This module contains the shared computational functions (the "functional core")
used by all model classes. It provides backend-agnostic implementations that
work with both JAX and NumPy.

## Components

- **linalg.py**: QR and SVD solvers for ordinary least squares
- **diagnostics.py**: Leverage, Cook's D, VIF, studentized residuals
- **inference.py**: Standard errors, confidence intervals, p-values
- **batching.py**: Memory-aware batch sizing for JAX operations
- **rng.py**: Unified RNG abstraction for JAX/NumPy backends
- **_get_ops.py**: Backend detection and operator dispatch

## How It Connects

```
models/             ← User-facing API
   │
   ▼
ops/                ← THIS MODULE: Computational core
   │
   ├── linalg      → QR/SVD solving
   ├── diagnostics → Residual analysis
   └── inference   → SE, CI, p-values
```

Model classes delegate computation to these pure functions:

```python
# Inside lm.fit():
result = qr_solve(X, y)           # ops/linalg.py
se = compute_se_from_vcov(vcov)   # ops/inference.py
leverage = compute_leverage(X)    # ops/diagnostics.py
```

## Design Philosophy

These functions are:

- **Pure**: No side effects, deterministic outputs
- **Backend-agnostic**: Work with JAX or NumPy arrays
- **Composable**: Can be combined for different model types
- **Tested against R**: Validated for numerical parity with lme4/stats

## Key Exports

| Function | Purpose |
|----------|---------|
| `qr_solve` | Solve least squares via QR decomposition |
| `svd_solve` | Solve least squares via SVD (rank-deficient) |
| `compute_leverage` | Hat matrix diagonals |
| `compute_cooks_distance` | Influence diagnostics |
| `compute_se_from_vcov` | Extract SEs from variance-covariance |
| `compute_ci` | Confidence intervals |
| `adjust_pvalues` | Multiple testing corrections |
