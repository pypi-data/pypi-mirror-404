"""Statistical power analysis for evaluation planning."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class PowerAnalysisResult:
    """Result of a power analysis.

    Args:
        required_sample_size: Minimum sample size needed.
        achieved_power: Power at the given sample size.
        effect_size: Effect size used.
        alpha: Significance level.
        desired_power: Target power level.
    """

    required_sample_size: int
    achieved_power: float
    effect_size: float
    alpha: float
    desired_power: float

    def __str__(self) -> str:
        return (
            f"Power Analysis: n={self.required_sample_size} needed "
            f"(effect={self.effect_size:.3f}, alpha={self.alpha}, power={self.desired_power})"
        )


def sample_size_for_mean_diff(
    effect_size: float,
    alpha: float = 0.05,
    power: float = 0.80,
    paired: bool = True,
) -> PowerAnalysisResult:
    """Compute required sample size to detect a mean difference.

    Uses Cohen's d as the effect size measure.

    Args:
        effect_size: Expected Cohen's d.
        alpha: Significance level.
        power: Desired statistical power.
        paired: Whether using paired design.

    Returns:
        PowerAnalysisResult.
    """
    if effect_size == 0:
        return PowerAnalysisResult(
            required_sample_size=0,
            achieved_power=0.0,
            effect_size=0.0,
            alpha=alpha,
            desired_power=power,
        )

    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)

    if paired:
        n = int(np.ceil(((z_alpha + z_beta) / effect_size) ** 2))
    else:
        n = int(np.ceil(2 * ((z_alpha + z_beta) / effect_size) ** 2))

    # Compute achieved power at this n
    if paired:
        ncp = effect_size * np.sqrt(n)
    else:
        ncp = effect_size * np.sqrt(n / 2)

    achieved_power = float(1 - stats.norm.cdf(z_alpha - ncp))

    return PowerAnalysisResult(
        required_sample_size=n,
        achieved_power=achieved_power,
        effect_size=effect_size,
        alpha=alpha,
        desired_power=power,
    )


def sample_size_for_proportion_diff(
    p1: float,
    p2: float,
    alpha: float = 0.05,
    power: float = 0.80,
) -> PowerAnalysisResult:
    """Compute required sample size to detect a difference in proportions.

    Args:
        p1: Expected proportion for model A.
        p2: Expected proportion for model B.
        alpha: Significance level.
        power: Desired power.

    Returns:
        PowerAnalysisResult.
    """
    diff = abs(p1 - p2)
    if diff == 0:
        return PowerAnalysisResult(
            required_sample_size=0,
            achieved_power=0.0,
            effect_size=0.0,
            alpha=alpha,
            desired_power=power,
        )

    p_avg = (p1 + p2) / 2
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)

    n = int(np.ceil(
        ((z_alpha * np.sqrt(2 * p_avg * (1 - p_avg)) +
          z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) / diff) ** 2
    ))

    effect_size = diff / np.sqrt(p_avg * (1 - p_avg))

    return PowerAnalysisResult(
        required_sample_size=n,
        achieved_power=power,
        effect_size=float(effect_size),
        alpha=alpha,
        desired_power=power,
    )


def compute_power(
    n: int,
    effect_size: float,
    alpha: float = 0.05,
    paired: bool = True,
) -> float:
    """Compute statistical power for a given sample size.

    Args:
        n: Sample size.
        effect_size: Expected effect size (Cohen's d).
        alpha: Significance level.
        paired: Whether using paired design.

    Returns:
        Statistical power (0-1).
    """
    if n <= 0 or effect_size == 0:
        return 0.0

    z_alpha = stats.norm.ppf(1 - alpha / 2)

    if paired:
        ncp = effect_size * np.sqrt(n)
    else:
        ncp = effect_size * np.sqrt(n / 2)

    power = float(1 - stats.norm.cdf(z_alpha - ncp))
    return power
