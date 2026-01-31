"""Metric registry for dynamic metric lookup and registration."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Type

from rotalabs_eval.metrics.base import Metric, _METRIC_REGISTRY

logger = logging.getLogger(__name__)


class MetricRegistry:
    """Registry for managing evaluation metrics.

    Provides a central registry for metric classes with support for
    custom metric registration and lazy loading of built-in metrics.
    """

    _instance: Optional[MetricRegistry] = None
    _initialized: bool = False

    def __new__(cls) -> MetricRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not self._initialized:
            self._custom_metrics: Dict[str, Type[Metric]] = {}
            self._initialized = True

    def _ensure_builtins_loaded(self) -> None:
        """Ensure built-in metrics are imported (triggers registration)."""
        try:
            import rotalabs_eval.metrics.lexical
        except ImportError:
            pass
        try:
            import rotalabs_eval.metrics.semantic
        except ImportError:
            pass
        try:
            import rotalabs_eval.metrics.llm_judge
        except ImportError:
            pass
        try:
            import rotalabs_eval.metrics.rag
        except ImportError:
            pass
        try:
            import rotalabs_eval.agents.trajectory
        except ImportError:
            pass
        try:
            import rotalabs_eval.agents.tool_use
        except ImportError:
            pass
        try:
            import rotalabs_eval.agents.debate
        except ImportError:
            pass

    def register(self, name: str, metric_cls: Type[Metric]) -> None:
        """Register a custom metric.

        Args:
            name: Metric name for lookup.
            metric_cls: Metric class.
        """
        self._custom_metrics[name] = metric_cls
        logger.debug(f"Registered custom metric: {name}")

    def get(self, name: str, **kwargs: Any) -> Metric:
        """Get a metric instance by name.

        Args:
            name: Metric name.
            **kwargs: Arguments passed to metric constructor.

        Returns:
            Instantiated metric.

        Raises:
            KeyError: If metric not found.
        """
        # Check custom metrics first
        if name in self._custom_metrics:
            return self._custom_metrics[name](**kwargs)

        # Check global registry
        self._ensure_builtins_loaded()
        if name in _METRIC_REGISTRY:
            return _METRIC_REGISTRY[name](**kwargs)

        raise KeyError(
            f"Metric '{name}' not found. Available: {self.list_metrics()}"
        )

    def list_metrics(self) -> List[str]:
        """List all available metric names."""
        self._ensure_builtins_loaded()
        all_names = set(_METRIC_REGISTRY.keys()) | set(self._custom_metrics.keys())
        return sorted(all_names)


def get_metric(name: str, **kwargs: Any) -> Metric:
    """Get a metric instance by name.

    Convenience function using the global registry.

    Args:
        name: Metric name.
        **kwargs: Arguments passed to metric constructor.

    Returns:
        Instantiated metric.
    """
    registry = MetricRegistry()
    return registry.get(name, **kwargs)
