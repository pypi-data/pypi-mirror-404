"""Local parallel evaluation orchestrator."""
from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from tqdm import tqdm

from rotalabs_eval.core.config import InferenceConfig, MetricConfig, ModelConfig, StatisticsConfig
from rotalabs_eval.core.result import CostBreakdown, EvalResult, LatencyStats, MetricValue
from rotalabs_eval.core.task import EvalTask
from rotalabs_eval.orchestrator.base import Orchestrator

logger = logging.getLogger(__name__)


class LocalOrchestrator(Orchestrator):
    """Local orchestrator that runs evaluation on a single machine."""

    def __init__(self, show_progress: bool = True) -> None:
        self.show_progress = show_progress

    def run(
        self,
        data: pd.DataFrame,
        task: EvalTask,
        model_config: ModelConfig,
        metrics: List[MetricConfig],
        inference_config: Optional[InferenceConfig] = None,
        statistics_config: Optional[StatisticsConfig] = None,
    ) -> EvalResult:
        """Run evaluation locally."""
        start_time = time.time()
        if inference_config is None:
            inference_config = InferenceConfig()
        if statistics_config is None:
            statistics_config = StatisticsConfig()

        n_examples = len(data)
        logger.info(f"Starting evaluation: {task.task_id} ({n_examples} examples)")

        # Prepare prompts
        prompts = self._prepare_prompts(data, task)

        # Run inference
        predictions, cost_info, latencies = self._run_inference(
            prompts, model_config, inference_config
        )

        # Compute metrics
        references = data[task.reference_column].tolist() if task.reference_column and task.reference_column in data.columns else [""] * n_examples
        metric_scores = self._compute_metrics(predictions, references, metrics, data, task)

        # Compute statistics
        metric_values = self._compute_statistics(metric_scores, statistics_config)

        elapsed = time.time() - start_time

        return EvalResult(
            task_id=task.task_id,
            run_id=None,
            timestamp=datetime.now(),
            metrics=metric_values,
            cost=cost_info,
            latency=LatencyStats(
                mean_ms=float(np.mean(latencies)) if latencies else 0.0,
                median_ms=float(np.median(latencies)) if latencies else 0.0,
                p95_ms=float(np.percentile(latencies, 95)) if latencies else 0.0,
                p99_ms=float(np.percentile(latencies, 99)) if latencies else 0.0,
                min_ms=float(np.min(latencies)) if latencies else 0.0,
                max_ms=float(np.max(latencies)) if latencies else 0.0,
                total_duration_s=elapsed,
            ),
            num_examples=n_examples,
            num_failures=sum(1 for p in predictions if p is None),
            config_snapshot={
                "model": model_config.model_name,
                "provider": model_config.provider.value,
            },
        )

    def _prepare_prompts(self, data: pd.DataFrame, task: EvalTask) -> List[str]:
        """Build prompts from template and data."""
        if not task.prompt_template:
            return data[task.input_column].tolist()

        prompts = []
        template_cols = task.get_template_columns()
        for _, row in data.iterrows():
            prompt = task.prompt_template
            for col in template_cols:
                prompt = prompt.replace("{{" + col + "}}", str(row.get(col, "")))
            prompts.append(prompt)
        return prompts

    def _run_inference(
        self,
        prompts: List[str],
        model_config: ModelConfig,
        inference_config: InferenceConfig,
    ) -> tuple:
        """Run inference on all prompts."""
        from rotalabs_eval.inference.batch import run_batch_inference

        responses = run_batch_inference(
            prompts, model_config, inference_config, show_progress=self.show_progress
        )

        predictions = []
        total_cost = 0.0
        total_input = 0
        total_output = 0
        latencies = []

        for resp in responses:
            predictions.append(resp.text if resp.success else None)
            total_cost += resp.cost_usd
            total_input += resp.input_tokens
            total_output += resp.output_tokens
            latencies.append(resp.latency_ms)

        cost = CostBreakdown(
            total_cost_usd=total_cost,
            input_tokens=total_input,
            output_tokens=total_output,
            num_requests=len(prompts),
        )

        return predictions, cost, latencies

    def _compute_metrics(
        self,
        predictions: List[Optional[str]],
        references: List[str],
        metrics: List[MetricConfig],
        data: pd.DataFrame,
        task: EvalTask,
    ) -> Dict[str, List[float]]:
        """Compute all metrics."""
        from rotalabs_eval.metrics.registry import get_metric

        # Filter out failed predictions
        valid_preds = [p if p is not None else "" for p in predictions]

        extra_kwargs: Dict[str, Any] = {}
        if task.input_column in data.columns:
            extra_kwargs["queries"] = data[task.input_column].tolist()
        if task.context_columns:
            for col in task.context_columns:
                if col in data.columns:
                    extra_kwargs["contexts"] = data[col].tolist()
                    break

        results: Dict[str, List[float]] = {}
        for mc in metrics:
            metric = get_metric(mc.name, **mc.kwargs)
            result = metric.compute(valid_preds, references, **{**extra_kwargs, **mc.kwargs})
            if result.per_example_scores:
                results[mc.name] = result.per_example_scores
            else:
                results[mc.name] = [result.value]

        return results

    def _compute_statistics(
        self,
        metrics: Dict[str, List[float]],
        config: StatisticsConfig,
    ) -> Dict[str, MetricValue]:
        """Compute CIs for each metric."""
        from rotalabs_eval.statistics import analytical_ci_proportion, bootstrap_ci

        results: Dict[str, MetricValue] = {}
        for name, scores in metrics.items():
            scores_arr = np.array(scores)
            is_binary = set(scores_arr.flatten()).issubset({0, 1, 0.0, 1.0})

            if is_binary and config.ci_method == "analytical":
                successes = int(np.sum(scores_arr))
                _, ci, se = analytical_ci_proportion(
                    successes, len(scores_arr), config.confidence_level
                )
            else:
                _, ci, se = bootstrap_ci(
                    scores_arr,
                    confidence_level=config.confidence_level,
                    n_iterations=config.bootstrap_iterations,
                )

            results[name] = MetricValue(
                value=float(np.mean(scores_arr)),
                confidence_interval=ci,
                confidence_level=config.confidence_level,
                standard_error=se,
                sample_size=len(scores_arr),
            )

        return results
