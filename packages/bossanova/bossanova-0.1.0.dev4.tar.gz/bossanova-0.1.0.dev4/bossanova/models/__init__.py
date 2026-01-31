"""Model classes for bossanova.

This module provides the main model classes:
- lm: Linear models (OLS regression)
- glm: Generalized linear models
- lmer: Linear mixed-effects models
- glmer: Generalized linear mixed-effects models
"""

from bossanova.models.glm import glm
from bossanova.models.glmer import glmer
from bossanova.models.lm import lm
from bossanova.models.lmer import lmer

__all__ = ["lm", "glm", "lmer", "glmer"]
