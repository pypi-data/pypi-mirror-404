"""Charts and dashboards for evaluation results."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def plot_metrics_comparison(
    results: Dict[str, Dict[str, float]],
    title: str = "Model Comparison",
    output_path: Optional[str] = None,
) -> Any:
    """Plot metrics comparison across models.

    Args:
        results: Dict of model_name -> {metric_name: value}.
        title: Plot title.
        output_path: Optional path to save figure.

    Returns:
        Matplotlib figure or None.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError(
            "matplotlib required. Install with: pip install rotalabs-eval[viz]"
        )

    models = list(results.keys())
    if not models:
        return None

    metrics = list(results[models[0]].keys())
    x = range(len(metrics))

    fig, ax = plt.subplots(figsize=(12, 6))

    bar_width = 0.8 / len(models)
    for i, model in enumerate(models):
        values = [results[model].get(m, 0) for m in metrics]
        positions = [xi + i * bar_width for xi in x]
        ax.bar(positions, values, bar_width, label=model)

    ax.set_xlabel("Metrics")
    ax.set_ylabel("Score")
    ax.set_title(title)
    ax.set_xticks([xi + bar_width * (len(models) - 1) / 2 for xi in x])
    ax.set_xticklabels(metrics, rotation=45, ha="right")
    ax.legend()
    ax.set_ylim(0, 1.1)

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")

    return fig
