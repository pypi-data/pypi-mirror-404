"""Data generating process (DGP) utilities for simulation studies.

Each DGP function generates synthetic data with known true parameters,
returning both the data and a dictionary of ground truth values for validation.
"""

from bossanova.simulation.dgp.glm import generate_glm_data
from bossanova.simulation.dgp.glmer import generate_glmer_data
from bossanova.simulation.dgp.lm import generate_lm_data
from bossanova.simulation.dgp.lmer import generate_lmer_data

__all__ = [
    "generate_lm_data",
    "generate_glm_data",
    "generate_lmer_data",
    "generate_glmer_data",
]
