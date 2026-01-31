"""Base classes for evaluation metrics."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger(__name__)

# Global metric registry
_METRIC_REGISTRY: Dict[str, Type[Metric]] = {}


def register_metric(cls: Type[Metric]) -> Type[Metric]:
    """Decorator to register a metric class.

    Args:
        cls: Metric class to register.

    Returns:
        The same class (unmodified).
    """
    name = getattr(cls, "name", cls.__name__)
    _METRIC_REGISTRY[name] = cls
    return cls


def get_registered_metrics() -> Dict[str, Type[Metric]]:
    """Get all registered metrics."""
    return dict(_METRIC_REGISTRY)


@dataclass
class MetricResult:
    """Result from computing a metric.

    Args:
        name: Metric name.
        value: Aggregate metric value.
        per_example_scores: Optional per-example scores.
        metadata: Additional result metadata.
    """

    name: str
    value: float
    per_example_scores: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.name}: {self.value:.4f}"


class Metric(ABC):
    """Abstract base class for evaluation metrics."""

    name: str = "base_metric"

    def __init__(self, **kwargs: Any) -> None:
        self.config = kwargs

    @abstractmethod
    def compute(
        self,
        predictions: List[str],
        references: List[str],
        **kwargs: Any,
    ) -> MetricResult:
        """Compute the metric.

        Args:
            predictions: Model predictions.
            references: Reference/ground truth values.
            **kwargs: Additional arguments.

        Returns:
            MetricResult with computed values.
        """
        ...

    def validate_inputs(
        self, predictions: List[str], references: List[str]
    ) -> None:
        """Validate input lengths match."""
        if len(predictions) != len(references):
            raise ValueError(
                f"predictions ({len(predictions)}) and references ({len(references)}) "
                f"must have the same length"
            )


class ReferenceFreeMetric(Metric):
    """Base class for metrics that don't require references."""

    def compute(
        self,
        predictions: List[str],
        references: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        """Compute metric without references."""
        return self.compute_without_reference(predictions, **kwargs)

    @abstractmethod
    def compute_without_reference(
        self,
        predictions: List[str],
        **kwargs: Any,
    ) -> MetricResult:
        """Compute metric on predictions only."""
        ...
