"""Custom metric registration helpers."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from rotalabs_eval.metrics.base import Metric, MetricResult
from rotalabs_eval.metrics.registry import MetricRegistry


def create_custom_metric(
    name: str,
    compute_fn: Callable[[List[str], List[str]], List[float]],
    requires_reference: bool = True,
) -> type:
    """Create a custom metric from a function.

    Args:
        name: Metric name.
        compute_fn: Function that takes (predictions, references) and returns scores.
        requires_reference: Whether this metric needs references.

    Returns:
        Metric class.

    Example:
        def my_scorer(preds, refs):
            return [1.0 if p == r else 0.0 for p, r in zip(preds, refs)]

        MyMetric = create_custom_metric("my_metric", my_scorer)
        registry = MetricRegistry()
        registry.register("my_metric", MyMetric)
    """

    class CustomMetric(Metric):
        def compute(
            self,
            predictions: List[str],
            references: List[str],
            **kwargs: Any,
        ) -> MetricResult:
            if requires_reference:
                self.validate_inputs(predictions, references)
            scores = compute_fn(predictions, references)
            return MetricResult(
                name=name,
                value=sum(scores) / len(scores) if scores else 0.0,
                per_example_scores=scores,
            )

    CustomMetric.name = name
    return CustomMetric
