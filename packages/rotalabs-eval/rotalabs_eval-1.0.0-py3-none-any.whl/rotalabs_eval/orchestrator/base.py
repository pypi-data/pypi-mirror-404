"""Abstract base class for evaluation orchestrators."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import pandas as pd

from rotalabs_eval.core.config import InferenceConfig, MetricConfig, ModelConfig, StatisticsConfig
from rotalabs_eval.core.result import EvalResult
from rotalabs_eval.core.task import EvalTask


class Orchestrator(ABC):
    """Abstract orchestrator for evaluation pipelines."""

    @abstractmethod
    def run(
        self,
        data: pd.DataFrame,
        task: EvalTask,
        model_config: ModelConfig,
        metrics: List[MetricConfig],
        inference_config: Optional[InferenceConfig] = None,
        statistics_config: Optional[StatisticsConfig] = None,
    ) -> EvalResult:
        """Run a complete evaluation.

        Args:
            data: Evaluation dataset.
            task: Task definition.
            model_config: Model configuration.
            metrics: List of metrics to compute.
            inference_config: Inference configuration.
            statistics_config: Statistics configuration.

        Returns:
            Complete evaluation result.
        """
        ...
