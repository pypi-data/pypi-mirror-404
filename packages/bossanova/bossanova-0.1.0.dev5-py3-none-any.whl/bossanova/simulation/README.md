# Simulation Module

> **Internal module** — This is primarily for bossanova's internal testing
> and validation. Advanced users may use it for power analysis or Monte Carlo
> studies, but it is not part of the stable public API.

## Purpose

This module provides data generating process (DGP) functions and Monte Carlo
harness for validating bossanova's statistical properties:

- Parameter recovery (bias, RMSE)
- Coverage probability (CI calibration)
- Type I/II error rates
- Power analysis

## Components

- **dgp.py**: Data generating functions for each model type
- **harness.py**: Monte Carlo simulation runner
- **metrics.py**: Simulation result metrics (bias, coverage, RMSE, etc.)

## How It Connects

```
Monte Carlo study
       │
       ▼
  simulation/       ← THIS MODULE
       │
       ├── generate_lm_data()   → Synthetic data with known β
       ├── monte_carlo()        → Run N simulations
       └── metrics              → Compute bias, coverage, etc.
       │
       ▼
  Validation that bossanova matches expected properties
```

## Why This Exists

Statistical software must be validated. This module enables:

1. **Parity testing**: Verify bossanova matches R's lme4/stats
2. **Coverage testing**: Confirm 95% CIs contain true value ~95% of the time
3. **Bias detection**: Ensure estimators are unbiased
4. **Regression testing**: Catch bugs that change statistical properties

## Example Usage

```python
from bossanova.simulation import generate_lm_data, monte_carlo
from bossanova import lm

result = monte_carlo(
    dgp_fn=generate_lm_data,
    dgp_params={"n": 100, "beta": [1.0, 2.0], "sigma": 1.0},
    fit_fn=lambda d: lm("y ~ x1", data=d).fit(),
    n_sims=500,
)
result.bias("x1")      # Should be ~0
result.coverage("x1")  # Should be ~0.95
```

## Key Exports

| Function | Purpose |
|----------|---------|
| `generate_lm_data` | DGP for linear models |
| `generate_glm_data` | DGP for GLMs |
| `generate_lmer_data` | DGP for linear mixed models |
| `monte_carlo` | Run Monte Carlo simulation |
| `bias`, `rmse`, `coverage` | Result metrics |
