"""Statistical analysis tools for evaluation results."""
from __future__ import annotations

from rotalabs_eval.statistics.confidence import (
    analytical_ci_mean,
    analytical_ci_proportion,
    bootstrap_ci,
    bootstrap_ci_bca,
    compare_cis,
)
from rotalabs_eval.statistics.effect_size import (
    EffectSizeResult,
    cohens_d,
    hedges_g,
    odds_ratio,
    relative_improvement,
)
from rotalabs_eval.statistics.significance import (
    SignificanceResult,
    bootstrap_significance,
    choose_test,
    mcnemar_test,
    paired_ttest,
    wilcoxon_signed_rank,
)

__all__ = [
    "bootstrap_ci",
    "bootstrap_ci_bca",
    "analytical_ci_mean",
    "analytical_ci_proportion",
    "compare_cis",
    "SignificanceResult",
    "paired_ttest",
    "mcnemar_test",
    "bootstrap_significance",
    "wilcoxon_signed_rank",
    "choose_test",
    "EffectSizeResult",
    "cohens_d",
    "hedges_g",
    "odds_ratio",
    "relative_improvement",
]
