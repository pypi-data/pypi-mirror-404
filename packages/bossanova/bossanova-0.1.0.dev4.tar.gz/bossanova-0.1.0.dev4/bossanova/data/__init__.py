"""Dataset loading utilities for bossanova.

This module provides functions to load sample datasets commonly used
in regression and mixed-effects modeling tutorials. Datasets are bundled
with the package for offline access.

Examples:
    >>> from bossanova.data import load_dataset
    >>> sleep = load_dataset("sleep")
    >>> mtcars = load_dataset("mtcars")
"""

from __future__ import annotations

from importlib.resources import files
from typing import Literal

import polars as pl

__all__ = [
    "load_dataset",
    "show_datasets",
]

# Available datasets with descriptions
DATASETS: dict[str, str] = {
    "advertising": "Advertising data with TV, radio, newspaper spend and sales",
    "chickweight": "Weight vs age of chicks on different diets",
    "credit": "Credit card balance prediction data",
    "gammas": "Gamma distribution example data",
    "mtcars": "Motor Trend Car Road Tests (1974)",
    "penguins": "Palmer Penguins dataset",
    "poker": "Poker hand data with repeated measures",
    "sleep": "Sleep study data (reaction time vs days of sleep deprivation)",
    "titanic": "Titanic survival data",
    "titanic_train": "Titanic training set",
    "titanic_test": "Titanic test set",
}

DatasetName = Literal[
    "advertising",
    "chickweight",
    "credit",
    "gammas",
    "mtcars",
    "penguins",
    "poker",
    "sleep",
    "titanic",
    "titanic_train",
    "titanic_test",
]


def show_datasets() -> pl.DataFrame:
    """Show available datasets with descriptions.

    Returns:
        DataFrame with columns: name, description.

    Examples:
        >>> from bossanova.data import show_datasets
        >>> show_datasets()
        shape: (11, 2)
        ┌───────────────┬─────────────────────────────────┐
        │ name          ┆ description                     │
        │ ---           ┆ ---                             │
        │ str           ┆ str                             │
        ╞═══════════════╪═════════════════════════════════╡
        │ sleep         ┆ Sleep study data (reaction ...  │
        │ mtcars        ┆ Motor Trend Car Road Tests ...  │
        │ ...           ┆ ...                             │
        └───────────────┴─────────────────────────────────┘
    """
    rows = [{"name": name, "description": desc} for name, desc in DATASETS.items()]
    return pl.DataFrame(rows)


def load_dataset(name: DatasetName) -> pl.DataFrame:
    """Load a sample dataset as a Polars DataFrame.

    Datasets are bundled with the package and loaded directly from
    package resources. No network access required.

    Args:
        name: Name of the dataset to load. Use `show_datasets()` to see
            available options.

    Returns:
        The requested dataset as a Polars DataFrame.

    Raises:
        ValueError: If the dataset name is not recognized.

    Examples:
        >>> from bossanova.data import load_dataset
        >>>
        >>> # Load sleep study data for mixed models
        >>> sleep = load_dataset("sleep")
        >>> print(sleep.head())
        >>>
        >>> # Load mtcars for regression examples
        >>> mtcars = load_dataset("mtcars")
    """
    if name not in DATASETS:
        valid = list(DATASETS.keys())
        raise ValueError(f"Unknown dataset: '{name}'. Valid options are: {valid}")

    # Load from package resources
    data_files = files("bossanova.data")
    csv_path = data_files.joinpath(f"{name}.csv")

    # Read CSV from package resource
    with csv_path.open("rb") as f:
        return pl.read_csv(f)
