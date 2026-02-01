# Data Module

> **User-facing** — Use `from bossanova import load_dataset, show_datasets`
> or `from bossanova.data import load_dataset`

## Purpose

This module provides sample datasets commonly used in regression and
mixed-effects modeling tutorials. Datasets are bundled with the package
for offline access and are returned as Polars DataFrames.

## Basic Usage

```python
from bossanova import load_dataset, show_datasets

# See available datasets
show_datasets()

# Load a dataset
mtcars = load_dataset("mtcars")
sleep = load_dataset("sleep")
penguins = load_dataset("penguins")
```

## Available Datasets

| Dataset | Description |
|---------|-------------|
| `mtcars` | Motor Trend Car Road Tests (1974) |
| `sleep` | Sleep study (reaction time vs sleep deprivation) |
| `penguins` | Palmer Penguins dataset |
| `titanic` | Titanic survival data |
| `chickweight` | Chick weight vs age by diet |
| `advertising` | TV, radio, newspaper ad spend vs sales |
| `credit` | Credit card balance prediction |
| `gammas` | Gamma distribution example |
| `poker` | Poker hand data with repeated measures |

## Why Bundled Data?

- **Reproducibility**: Examples work offline, no network required
- **Consistency**: Same data across all bossanova versions
- **Tutorials**: Documentation examples use these datasets
- **Testing**: Parity tests compare against R using identical data

## Data Format

All datasets are stored as Parquet files and returned as Polars DataFrames:

```python
>>> sleep = load_dataset("sleep")
>>> type(sleep)
<class 'polars.dataframe.frame.DataFrame'>
>>> sleep.columns
['Reaction', 'Days', 'Subject']
```

## Key Exports

| Function | Purpose |
|----------|---------|
| `load_dataset` | Load a dataset by name |
| `show_datasets` | Print available datasets with descriptions |
