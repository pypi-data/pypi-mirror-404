# Viz Module

> **User-facing** — Use `from bossanova import viz` or call plot methods
> directly on fitted models: `model.plot_params()`, `model.plot_resid()`

## Purpose

This module provides visualization functions for model exploration and
diagnostics. All functions follow the functional core pattern—they take
a model as input and return matplotlib Figure or Axes objects.

## Basic Usage

```python
from bossanova import lm, viz
from bossanova.data import load_dataset

mtcars = load_dataset("mtcars")
model = lm("mpg ~ wt + hp", data=mtcars).fit()

# Via viz module
viz.plot_params(model)
viz.plot_resid(model)

# Or via model methods (convenience wrappers)
model.plot_params()
model.plot_resid()
```

## Available Plots

| Function | Purpose |
|----------|---------|
| `plot_params` | Forest plot of parameter estimates |
| `plot_resid` | Residual diagnostic grid (4 panels) |
| `plot_predict` | Marginal predictions across predictor range |
| `plot_mee` | Marginal effects/means visualization |
| `plot_fit` | Composite diagnostic panel |
| `plot_compare` | Multi-model coefficient comparison |
| `plot_dag` | Causal DAG visualization |
| `plot_lattice` | Model lattice (Hasse diagram) |
| `plot_cognition` | Combined DAG + lattice |

## Residual Diagnostics

`plot_resid()` produces a 2×2 grid:

```
┌─────────────────┬─────────────────┐
│ Residuals vs    │ Q-Q Plot        │
│ Fitted          │ (normality)     │
├─────────────────┼─────────────────┤
│ Scale-Location  │ Residuals vs    │
│ (homoscedast.)  │ Leverage        │
└─────────────────┴─────────────────┘
```

## Forest Plots

`plot_params()` shows coefficient estimates with confidence intervals:

```
            ─────●───── Intercept
      ─●─────           wt
          ──●──         hp
     ◄──────────────────────────────►
    -2    -1     0     1     2     3
```

## Styling

Plots use a consistent bossanova style. Customize via matplotlib:

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
viz.plot_params(model, ax=ax)
ax.set_title("My Custom Title")
plt.savefig("params.png")
```

## Key Exports

| Function | Purpose |
|----------|---------|
| `plot_params` | Forest plot of coefficients |
| `plot_resid` | Residual diagnostics |
| `plot_predict` | Prediction curves |
| `plot_mee` | Marginal effects plot |
| `plot_compare` | Multi-model comparison |
