"""HTML report generation for evaluation results."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from rotalabs_eval.core.result import EvalResult


def generate_html_report(
    result: EvalResult,
    title: Optional[str] = None,
) -> str:
    """Generate an HTML report for evaluation results.

    Args:
        result: Evaluation result.
        title: Optional report title.

    Returns:
        HTML string.
    """
    title = title or f"Evaluation Report: {result.task_id}"

    metrics_rows = ""
    for name, mv in result.metrics.items():
        ci_lo = f"{mv.ci_lower:.4f}" if mv.ci_lower is not None else "—"
        ci_hi = f"{mv.ci_upper:.4f}" if mv.ci_upper is not None else "—"
        metrics_rows += f"""
        <tr>
            <td>{name}</td>
            <td>{mv.value:.4f}</td>
            <td>{ci_lo}</td>
            <td>{ci_hi}</td>
            <td>{mv.sample_size}</td>
        </tr>"""

    cost_section = ""
    if result.cost:
        cost_section = f"""
        <h2>Cost</h2>
        <p>Total: ${result.cost.total_cost_usd:.4f} | Tokens: {result.cost.total_tokens} | Requests: {result.cost.num_requests}</p>
        """

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; margin: 40px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f5f5f5; }}
        h1 {{ color: #333; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p>Examples: {result.num_examples} | Failures: {result.num_failures} | Success Rate: {result.success_rate:.1%}</p>

    <h2>Metrics</h2>
    <table>
        <tr><th>Metric</th><th>Value</th><th>CI Lower</th><th>CI Upper</th><th>N</th></tr>
        {metrics_rows}
    </table>
    {cost_section}
</body>
</html>"""
