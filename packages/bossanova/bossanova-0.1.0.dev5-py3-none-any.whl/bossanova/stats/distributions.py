"""Distribution wrappers with automatic visualization in notebooks.

This module wraps scipy.stats distributions to provide:
- User-friendly parameterization (mean/sd instead of loc/scale)
- Automatic plotting in Jupyter notebooks via _repr_html_()
- Adaptive display: PDF curves for continuous, PMF bars for discrete
- Critical region shading for hypothesis testing visualization

Examples:
    >>> from bossanova.stats import normal, t_dist, binomial
    >>>
    >>> # Display in notebook shows plot automatically
    >>> d = normal(mean=0, sd=1)
    >>> d  # renders PDF curve
    >>>
    >>> # Hypothesis test visualization
    >>> t = t_dist(df=29)
    >>> t.plot(shade_region="critical_two", shade_color="red")
    >>>
    >>> # Discrete distributions show PMF bars
    >>> b = binomial(n=20, p=0.3)
    >>> b  # renders PMF bar chart
"""

from __future__ import annotations

import base64
from io import BytesIO
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
from scipy import stats
from scipy.stats._distn_infrastructure import rv_continuous_frozen, rv_discrete_frozen

from bossanova.viz._core import BOSSANOVA_STYLE

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from numpy.typing import ArrayLike


# Type alias for frozen scipy distributions
rv_frozen = rv_continuous_frozen | rv_discrete_frozen


def _figure_to_html(fig: Figure, dpi: int = 100) -> str:
    """Convert matplotlib figure to base64-encoded HTML img tag.

    Args:
        fig: Matplotlib figure to convert.
        dpi: Resolution for the PNG image.

    Returns:
        HTML string with embedded base64 PNG.
    """
    import matplotlib.pyplot as plt

    buf = BytesIO()
    fig.savefig(
        buf,
        format="png",
        dpi=dpi,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    plt.close(fig)

    return f'<img src="data:image/png;base64,{img_base64}" />'


class Distribution:
    """Wrapper for scipy.stats distributions with visualization.

    Provides a unified interface for probability distributions with:
    - Probability functions (pdf/pmf, cdf, ppf)
    - Random sampling (rvs)
    - Moments (mean, var, std)
    - Visualization with shading support
    - Automatic notebook rendering

    Args:
        dist: Frozen scipy.stats distribution.
        name: Display name for the distribution.
        params: User-facing parameter dictionary for display.

    Examples:
        >>> # Use factory functions instead of direct instantiation
        >>> from bossanova.stats import normal, t_dist
        >>> d = normal(mean=0, sd=1)
        >>> d.cdf(1.96)  # 0.975
        >>> d.ppf(0.975)  # 1.96
    """

    __slots__ = ("_dist", "_name", "_params", "_is_discrete")

    def __init__(
        self,
        dist: rv_frozen,
        name: str,
        params: dict[str, float],
    ) -> None:
        self._dist = dist
        self._name = name
        self._params = params
        self._is_discrete = isinstance(dist, rv_discrete_frozen)

    @property
    def is_discrete(self) -> bool:
        """Whether this is a discrete distribution."""
        return self._is_discrete

    @property
    def name(self) -> str:
        """Distribution name."""
        return self._name

    @property
    def params(self) -> dict[str, float]:
        """Distribution parameters."""
        return self._params.copy()

    # =========================================================================
    # Probability Functions
    # =========================================================================

    def pdf(self, x: ArrayLike) -> np.ndarray:
        """Probability density function (continuous distributions only).

        Args:
            x: Points at which to evaluate the PDF.

        Returns:
            PDF values at each point.

        Raises:
            AttributeError: If called on a discrete distribution.
        """
        if self._is_discrete:
            raise AttributeError(
                f"{self._name} is discrete. Use pmf() instead of pdf()."
            )
        return np.asarray(self._dist.pdf(x))

    def pmf(self, x: ArrayLike) -> np.ndarray:
        """Probability mass function (discrete distributions only).

        Args:
            x: Points at which to evaluate the PMF.

        Returns:
            PMF values at each point.

        Raises:
            AttributeError: If called on a continuous distribution.
        """
        if not self._is_discrete:
            raise AttributeError(
                f"{self._name} is continuous. Use pdf() instead of pmf()."
            )
        return np.asarray(self._dist.pmf(x))

    def prob(self, x: ArrayLike) -> np.ndarray:
        """Unified probability function (pdf or pmf based on type).

        Args:
            x: Points at which to evaluate.

        Returns:
            Probability values (density for continuous, mass for discrete).
        """
        if self._is_discrete:
            return self.pmf(x)
        return self.pdf(x)

    def cdf(self, x: ArrayLike) -> np.ndarray:
        """Cumulative distribution function.

        Args:
            x: Points at which to evaluate the CDF.

        Returns:
            CDF values (P(X <= x)) at each point.
        """
        return np.asarray(self._dist.cdf(x))

    def sf(self, x: ArrayLike) -> np.ndarray:
        """Survival function (1 - CDF).

        Args:
            x: Points at which to evaluate.

        Returns:
            Survival function values (P(X > x)) at each point.
        """
        return np.asarray(self._dist.sf(x))

    def ppf(self, q: ArrayLike) -> np.ndarray:
        """Percent point function (inverse CDF / quantile function).

        Args:
            q: Quantiles (probabilities between 0 and 1).

        Returns:
            Values x such that P(X <= x) = q.
        """
        return np.asarray(self._dist.ppf(q))

    def rvs(
        self,
        size: int | tuple[int, ...] = 1,
        seed: int | np.random.Generator | None = None,
    ) -> np.ndarray:
        """Generate random variates.

        Args:
            size: Number of samples or shape of output array.
            seed: Random seed or Generator for reproducibility.

        Returns:
            Array of random samples from the distribution.
        """
        return np.asarray(self._dist.rvs(size=size, random_state=seed))

    # =========================================================================
    # Moments
    # =========================================================================

    @property
    def mean(self) -> float:
        """Distribution mean (expected value)."""
        return float(self._dist.mean())

    @property
    def var(self) -> float:
        """Distribution variance."""
        return float(self._dist.var())

    @property
    def std(self) -> float:
        """Distribution standard deviation."""
        return float(self._dist.std())

    @property
    def median(self) -> float:
        """Distribution median."""
        return float(self._dist.median())

    def interval(self, confidence: float = 0.95) -> tuple[float, float]:
        """Central confidence interval containing given probability mass.

        Args:
            confidence: Probability mass in the interval (default 0.95).

        Returns:
            Tuple of (lower, upper) bounds.
        """
        lo, hi = self._dist.interval(confidence)
        return (float(lo), float(hi))

    # =========================================================================
    # Visualization
    # =========================================================================

    def _compute_x_range(self) -> tuple[float, float]:
        """Compute sensible x-range for plotting."""
        if self._is_discrete:
            # For discrete: use ppf to find range covering 99.9%
            low = max(0, int(self._dist.ppf(0.001)))
            high = int(self._dist.ppf(0.999)) + 1
            return (float(low), float(high))
        else:
            # For continuous: use ppf for 0.001 to 0.999
            low = self._dist.ppf(0.001)
            high = self._dist.ppf(0.999)
            # Add some padding
            padding = (high - low) * 0.05
            return (float(low - padding), float(high + padding))

    def _parse_shade_region(
        self,
        shade_region: tuple[float, float] | str | None,
    ) -> tuple[float, float] | None:
        """Parse shade_region argument to actual bounds."""
        if shade_region is None:
            return None

        if isinstance(shade_region, tuple):
            return shade_region

        # String shortcuts
        if shade_region == "ci95":
            return self.interval(0.95)
        elif shade_region == "ci99":
            return self.interval(0.99)
        elif shade_region == "ci90":
            return self.interval(0.90)
        elif shade_region == "critical_left":
            return (float("-inf"), float(self.ppf(0.05)))
        elif shade_region == "critical_right":
            return (float(self.ppf(0.95)), float("inf"))
        elif shade_region == "critical_two":
            return (float(self.ppf(0.025)), float(self.ppf(0.975)))
        else:
            raise ValueError(
                f"Unknown shade_region: {shade_region!r}. "
                "Use tuple, 'ci95', 'ci99', 'ci90', 'critical_left', "
                "'critical_right', or 'critical_two'."
            )

    def plot(
        self,
        *,
        ax: Axes | None = None,
        shade_region: tuple[float, float] | str | None = None,
        shade_direction: Literal["between", "outside", "left", "right"] = "between",
        shade_alpha: float = 0.3,
        shade_color: str | None = None,
        show_mean: bool = False,
        show_median: bool = False,
        x_range: tuple[float, float] | None = None,
        figsize: tuple[float, float] = (6, 4),
        color: str | None = None,
        title: str | None = None,
    ) -> Figure:
        """Plot the distribution.

        Args:
            ax: Matplotlib axes. If None, creates new figure.
            shade_region: Region to shade. Can be:
                - tuple[float, float]: Shade between these x values
                - "ci95", "ci99", "ci90": Shade confidence interval
                - "critical_left": Shade left tail (alpha=0.05)
                - "critical_right": Shade right tail (alpha=0.05)
                - "critical_two": Shade both tails (alpha=0.025 each)
            shade_direction: How to shade relative to bounds:
                - "between": Shade area between bounds (default for CI)
                - "outside": Shade area outside bounds (rejection regions)
                - "left": Shade left of lower bound
                - "right": Shade right of upper bound
            shade_alpha: Transparency for shaded region.
            shade_color: Color for shaded region (defaults to line color).
            show_mean: Show vertical line at mean.
            show_median: Show vertical line at median.
            x_range: Custom x-axis range (auto-computed if None).
            figsize: Figure size in inches.
            color: Line/bar color (uses palette default if None).
            title: Plot title (auto-generated if None).

        Returns:
            Matplotlib Figure object.
        """
        import matplotlib.pyplot as plt

        # Create figure if needed
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
        else:
            fig = ax.get_figure()

        # Get styling
        style = BOSSANOVA_STYLE
        plot_color = color or plt.cm.tab10(0)

        # Compute x range
        if x_range is None:
            x_lo, x_hi = self._compute_x_range()
        else:
            x_lo, x_hi = x_range

        # Plot based on distribution type
        if self._is_discrete:
            self._plot_discrete(ax, x_lo, x_hi, plot_color, style)
        else:
            self._plot_continuous(ax, x_lo, x_hi, plot_color, style)

        # Add shading
        bounds = self._parse_shade_region(shade_region)
        if bounds is not None:
            self._add_shading(
                ax,
                bounds,
                shade_direction,
                shade_alpha,
                shade_color or plot_color,
                x_lo,
                x_hi,
            )

        # Add reference lines
        if show_mean:
            ax.axvline(
                self.mean,
                color=style["ref_line_color"],
                linestyle="--",
                linewidth=style["ref_line_width"],
                label=f"Mean = {self.mean:.3g}",
            )
        if show_median:
            ax.axvline(
                self.median,
                color=style["ref_line_color"],
                linestyle=":",
                linewidth=style["ref_line_width"],
                label=f"Median = {self.median:.3g}",
            )

        # Labels
        param_str = ", ".join(f"{k}={v:.3g}" for k, v in self._params.items())
        default_title = f"{self._name}({param_str})"
        ax.set_title(title or default_title, fontsize=style["title_size"])
        ax.set_xlabel("x", fontsize=style["label_size"])
        ax.set_ylabel(
            "Probability" if self._is_discrete else "Density",
            fontsize=style["label_size"],
        )

        # Add legend if reference lines shown
        if show_mean or show_median:
            ax.legend(fontsize=style["font_size"])

        # Style
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, alpha=style["grid_alpha"], linestyle=style["grid_style"])

        fig.tight_layout()
        return fig

    def _plot_continuous(
        self,
        ax: Axes,
        x_lo: float,
        x_hi: float,
        color: Any,
        style: dict[str, Any],
    ) -> None:
        """Plot PDF for continuous distribution."""
        x = np.linspace(x_lo, x_hi, 200)
        y = self._dist.pdf(x)
        ax.plot(x, y, color=color, linewidth=style["line_width"])
        ax.fill_between(x, y, alpha=style["ci_alpha"] * 0.5, color=color)

    def _plot_discrete(
        self,
        ax: Axes,
        x_lo: float,
        x_hi: float,
        color: Any,
        style: dict[str, Any],
    ) -> None:
        """Plot PMF bars for discrete distribution."""
        x = np.arange(int(x_lo), int(x_hi) + 1)
        y = self._dist.pmf(x)
        ax.bar(x, y, width=0.8, color=color, alpha=0.7, edgecolor="white")

    def _add_shading(
        self,
        ax: Axes,
        bounds: tuple[float, float],
        direction: str,
        alpha: float,
        color: Any,
        x_lo: float,
        x_hi: float,
    ) -> None:
        """Add shaded region to plot."""
        lo, hi = bounds

        if self._is_discrete:
            # For discrete, shade bars
            x_all = np.arange(int(x_lo), int(x_hi) + 1)
            y_all = self._dist.pmf(x_all)

            if direction == "between":
                mask = (x_all >= lo) & (x_all <= hi)
            elif direction == "outside":
                mask = (x_all < lo) | (x_all > hi)
            elif direction == "left":
                mask = x_all <= lo
            elif direction == "right":
                mask = x_all >= hi
            else:
                return

            ax.bar(
                x_all[mask],
                y_all[mask],
                width=0.8,
                color=color,
                alpha=alpha + 0.3,
                edgecolor="white",
            )
        else:
            # For continuous, use fill_between
            x = np.linspace(x_lo, x_hi, 200)
            y = self._dist.pdf(x)

            if direction == "between":
                mask = (x >= lo) & (x <= hi)
                ax.fill_between(x, y, where=mask, alpha=alpha, color=color)
            elif direction == "outside":
                mask_left = x <= lo
                mask_right = x >= hi
                ax.fill_between(x, y, where=mask_left, alpha=alpha, color=color)
                ax.fill_between(x, y, where=mask_right, alpha=alpha, color=color)
            elif direction == "left":
                mask = x <= lo
                ax.fill_between(x, y, where=mask, alpha=alpha, color=color)
            elif direction == "right":
                mask = x >= hi
                ax.fill_between(x, y, where=mask, alpha=alpha, color=color)

    # =========================================================================
    # Display Methods
    # =========================================================================

    def __repr__(self) -> str:
        """Text representation."""
        param_str = ", ".join(f"{k}={v:.4g}" for k, v in self._params.items())
        lines = [
            f"{self._name}({param_str})",
            f"  mean = {self.mean:.4g}",
            f"  std  = {self.std:.4g}",
        ]
        return "\n".join(lines)

    def _repr_html_(self) -> str:
        """HTML representation with embedded plot for notebooks."""
        fig = self.plot()
        return _figure_to_html(fig)


# =============================================================================
# Factory Functions
# =============================================================================


def normal(mean: float = 0, sd: float = 1) -> Distribution:
    """Normal (Gaussian) distribution.

    Args:
        mean: Mean of the distribution.
        sd: Standard deviation (must be positive).

    Returns:
        Distribution object.

    Examples:
        >>> d = normal(mean=100, sd=15)
        >>> d.cdf(115)  # P(X <= 115)
        0.8413...
    """
    if sd <= 0:
        raise ValueError("sd must be positive")
    return Distribution(
        dist=stats.norm(loc=mean, scale=sd),
        name="Normal",
        params={"mean": mean, "sd": sd},
    )


def t_dist(df: float, mean: float = 0, sd: float = 1) -> Distribution:
    """Student's t distribution.

    Args:
        df: Degrees of freedom (must be positive).
        mean: Location parameter.
        sd: Scale parameter (must be positive).

    Returns:
        Distribution object.

    Examples:
        >>> t = t_dist(df=29)
        >>> t.ppf(0.975)  # Critical value for 95% CI
        2.045...
    """
    if df <= 0:
        raise ValueError("df must be positive")
    if sd <= 0:
        raise ValueError("sd must be positive")
    return Distribution(
        dist=stats.t(df=df, loc=mean, scale=sd),
        name="Student's t",
        params={"df": df, "mean": mean, "sd": sd},
    )


def chi2(df: float) -> Distribution:
    """Chi-squared distribution.

    Args:
        df: Degrees of freedom (must be positive).

    Returns:
        Distribution object.

    Examples:
        >>> c = chi2(df=5)
        >>> c.ppf(0.95)  # Critical value
        11.07...
    """
    if df <= 0:
        raise ValueError("df must be positive")
    return Distribution(
        dist=stats.chi2(df=df),
        name="Chi-squared",
        params={"df": df},
    )


def F_dist(df1: float, df2: float) -> Distribution:
    """F distribution.

    Args:
        df1: Numerator degrees of freedom (must be positive).
        df2: Denominator degrees of freedom (must be positive).

    Returns:
        Distribution object.

    Examples:
        >>> f = F_dist(df1=5, df2=20)
        >>> f.ppf(0.95)  # Critical value
        2.71...
    """
    if df1 <= 0 or df2 <= 0:
        raise ValueError("df1 and df2 must be positive")
    return Distribution(
        dist=stats.f(dfn=df1, dfd=df2),
        name="F",
        params={"df1": df1, "df2": df2},
    )


def beta(a: float, b: float) -> Distribution:
    """Beta distribution.

    Args:
        a: Shape parameter alpha (must be positive).
        b: Shape parameter beta (must be positive).

    Returns:
        Distribution object.

    Examples:
        >>> d = beta(a=2, b=5)
        >>> d.mean
        0.285...
    """
    if a <= 0 or b <= 0:
        raise ValueError("a and b must be positive")
    return Distribution(
        dist=stats.beta(a=a, b=b),
        name="Beta",
        params={"a": a, "b": b},
    )


def binomial(n: int, p: float) -> Distribution:
    """Binomial distribution.

    Args:
        n: Number of trials (must be non-negative integer).
        p: Probability of success (must be in [0, 1]).

    Returns:
        Distribution object.

    Examples:
        >>> b = binomial(n=20, p=0.3)
        >>> b.mean
        6.0
        >>> b.pmf(6)  # P(X = 6)
        0.191...
    """
    if n < 0 or not isinstance(n, int):
        raise ValueError("n must be a non-negative integer")
    if not 0 <= p <= 1:
        raise ValueError("p must be in [0, 1]")
    return Distribution(
        dist=stats.binom(n=n, p=p),
        name="Binomial",
        params={"n": n, "p": p},
    )


def poisson(mu: float) -> Distribution:
    """Poisson distribution.

    Args:
        mu: Expected number of events (rate, must be positive).

    Returns:
        Distribution object.

    Examples:
        >>> d = poisson(mu=5)
        >>> d.pmf(3)  # P(X = 3)
        0.140...
    """
    if mu <= 0:
        raise ValueError("mu must be positive")
    return Distribution(
        dist=stats.poisson(mu=mu),
        name="Poisson",
        params={"mu": mu},
    )


def exponential(rate: float) -> Distribution:
    """Exponential distribution (rate parameterization).

    Args:
        rate: Rate parameter lambda (must be positive).
            Mean = 1/rate.

    Returns:
        Distribution object.

    Examples:
        >>> d = exponential(rate=0.5)
        >>> d.mean
        2.0
    """
    if rate <= 0:
        raise ValueError("rate must be positive")
    # scipy uses scale = 1/rate
    return Distribution(
        dist=stats.expon(scale=1 / rate),
        name="Exponential",
        params={"rate": rate},
    )


def gamma(
    shape: float,
    rate: float | None = None,
    scale: float | None = None,
) -> Distribution:
    """Gamma distribution.

    Accepts either rate or scale parameterization (not both).

    Args:
        shape: Shape parameter (must be positive).
        rate: Rate parameter (1/scale). If provided, scale must be None.
        scale: Scale parameter. If provided, rate must be None.
            Default is scale=1 if neither specified.

    Returns:
        Distribution object.

    Raises:
        ValueError: If both rate and scale are provided.

    Examples:
        >>> g = gamma(shape=2, rate=0.5)
        >>> g.mean
        4.0
        >>> g = gamma(shape=2, scale=2)  # Equivalent
        >>> g.mean
        4.0
    """
    if shape <= 0:
        raise ValueError("shape must be positive")
    if rate is not None and scale is not None:
        raise ValueError("Specify either rate or scale, not both")
    if rate is not None:
        if rate <= 0:
            raise ValueError("rate must be positive")
        scale = 1 / rate
    elif scale is None:
        scale = 1.0
    if scale <= 0:
        raise ValueError("scale must be positive")

    params = {"shape": shape}
    if rate is not None:
        params["rate"] = rate
    else:
        params["scale"] = scale

    return Distribution(
        dist=stats.gamma(a=shape, scale=scale),
        name="Gamma",
        params=params,
    )


def uniform(low: float = 0, high: float = 1) -> Distribution:
    """Uniform distribution.

    Args:
        low: Lower bound.
        high: Upper bound (must be > low).

    Returns:
        Distribution object.

    Examples:
        >>> d = uniform(low=0, high=10)
        >>> d.mean
        5.0
    """
    if high <= low:
        raise ValueError("high must be greater than low")
    return Distribution(
        dist=stats.uniform(loc=low, scale=high - low),
        name="Uniform",
        params={"low": low, "high": high},
    )
