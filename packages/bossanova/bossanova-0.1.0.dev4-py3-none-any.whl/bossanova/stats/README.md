# Stats Module

> **Partially user-facing** — The `compare()` and `lrt()` functions are part of
> bossanova's public API. Other exports (Satterthwaite utilities, effect sizes)
> are internal implementation details.

## Purpose

This module provides statistical utilities for model comparison and inference,
including likelihood ratio tests, model comparison tables, and specialized
computations for mixed models (Satterthwaite degrees of freedom).

## Components

- **compare.py**: Multi-model comparison tables (AIC, BIC, etc.)
- **lrt.py**: Likelihood ratio tests between nested models
- **satterthwaite.py**: Satterthwaite df approximation for mixed models
- **effect_sizes.py**: Cohen's d, eta-squared, and other effect sizes

## Public API

These functions are exported at the package level:

```python
from bossanova import compare, lrt

# Compare multiple models
compare(model1, model2, model3)

# Likelihood ratio test
lrt(null_model, full_model)
```

## How It Connects

```
User: compare(m1, m2, m3)
       │
       ▼
  stats/compare.py  ← Extract fit statistics
       │
       ▼
  Comparison table (AIC, BIC, logLik, df)
```

For mixed models, Satterthwaite degrees of freedom are used for t-tests:

```
lmer.summary()
       │
       ▼
  stats/satterthwaite.py  ← Compute denominator df
       │
       ▼
  t-statistics with appropriate df
```

## Key Exports

| Function | Public? | Purpose |
|----------|---------|---------|
| `compare` | Yes | Compare models by fit statistics |
| `lrt` | Yes | Likelihood ratio test |
| `satterthwaite_df` | No | Denominator df for mixed models |
| `compute_effect_sizes` | No | Effect size calculations |
