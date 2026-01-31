"""Evaluation results formatting and comparison."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from rotalabs_eval.core.result import EvalResult, MetricValue


def format_results_table(result: EvalResult) -> str:
    """Format evaluation results as a text table.

    Args:
        result: Evaluation result.

    Returns:
        Formatted string.
    """
    lines = [
        f"Evaluation: {result.task_id}",
        f"Examples: {result.num_examples} (failures: {result.num_failures})",
        "",
        f"{'Metric':<30} {'Value':>10} {'CI Lower':>10} {'CI Upper':>10} {'SE':>10}",
        "-" * 72,
    ]
    for name, mv in result.metrics.items():
        ci_lo = f"{mv.ci_lower:.4f}" if mv.ci_lower is not None else "N/A"
        ci_hi = f"{mv.ci_upper:.4f}" if mv.ci_upper is not None else "N/A"
        se = f"{mv.standard_error:.4f}" if mv.standard_error is not None else "N/A"
        lines.append(f"{name:<30} {mv.value:>10.4f} {ci_lo:>10} {ci_hi:>10} {se:>10}")

    if result.cost:
        lines.extend([
            "",
            f"Cost: ${result.cost.total_cost_usd:.4f} "
            f"({result.cost.total_tokens} tokens, {result.cost.num_requests} requests)",
        ])

    if result.latency:
        lines.extend([
            f"Latency: mean={result.latency.mean_ms:.0f}ms, "
            f"p95={result.latency.p95_ms:.0f}ms, "
            f"total={result.latency.total_duration_s:.1f}s",
        ])

    return "\n".join(lines)


def compare_results(
    result_a: EvalResult,
    result_b: EvalResult,
    label_a: str = "Model A",
    label_b: str = "Model B",
) -> str:
    """Format a comparison of two evaluation results.

    Args:
        result_a: First evaluation result.
        result_b: Second evaluation result.
        label_a: Label for first model.
        label_b: Label for second model.

    Returns:
        Formatted comparison string.
    """
    lines = [
        f"Comparison: {label_a} vs {label_b}",
        "",
        f"{'Metric':<25} {label_a:>12} {label_b:>12} {'Diff':>10} {'Winner':>10}",
        "-" * 72,
    ]

    all_metrics = set(result_a.metrics.keys()) | set(result_b.metrics.keys())
    for name in sorted(all_metrics):
        va = result_a.metrics.get(name)
        vb = result_b.metrics.get(name)
        val_a = f"{va.value:.4f}" if va else "N/A"
        val_b = f"{vb.value:.4f}" if vb else "N/A"

        if va and vb:
            diff = va.value - vb.value
            diff_str = f"{diff:+.4f}"
            winner = label_a if diff > 0 else label_b if diff < 0 else "Tie"
        else:
            diff_str = "N/A"
            winner = "N/A"

        lines.append(f"{name:<25} {val_a:>12} {val_b:>12} {diff_str:>10} {winner:>10}")

    return "\n".join(lines)


def results_to_json(result: EvalResult) -> str:
    """Serialize evaluation result to JSON."""
    return json.dumps(result.to_dict(), indent=2, default=str)
