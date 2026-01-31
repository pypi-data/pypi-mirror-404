"""Tool use evaluation metrics for agents."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from rotalabs_eval.metrics.base import Metric, MetricResult, register_metric

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """Represents a single tool call."""
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    success: bool = True
    error: Optional[str] = None

    def __hash__(self) -> int:
        params_str = json.dumps(self.parameters, sort_keys=True) if self.parameters else ""
        return hash((self.name, params_str))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ToolCall):
            return False
        return self.name == other.name and self.parameters == other.parameters


@dataclass
class ToolCallSequence:
    """A sequence of tool calls from an agent."""
    calls: List[ToolCall]
    task_description: str = ""
    final_answer: Optional[str] = None

    @property
    def tool_names(self) -> List[str]:
        return [c.name for c in self.calls]

    @property
    def unique_tools(self) -> Set[str]:
        return set(self.tool_names)

    @property
    def num_calls(self) -> int:
        return len(self.calls)

    @property
    def num_failures(self) -> int:
        return sum(1 for c in self.calls if not c.success)


@register_metric
class ToolSelectionAccuracyMetric(Metric):
    """Measures if the agent selected the correct tools."""
    name = "tool_selection_accuracy"

    def compute(self, predictions: List[str], references: List[str], **kwargs: Any) -> MetricResult:
        self.validate_inputs(predictions, references)
        scores: List[float] = []
        for pred, ref in zip(predictions, references):
            pred_tools = self._parse_tools(pred)
            ref_tools = self._parse_tools(ref)
            if not ref_tools:
                scores.append(1.0 if not pred_tools else 0.0)
                continue
            intersection = pred_tools & ref_tools
            union = pred_tools | ref_tools
            scores.append(len(intersection) / len(union) if union else 1.0)
        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )

    def _parse_tools(self, tools_str: str) -> Set[str]:
        if not tools_str:
            return set()
        return {t.strip().lower() for t in tools_str.split(",") if t.strip()}


@register_metric
class ToolOrderAccuracyMetric(Metric):
    """Measures if tools were called in the correct order using LCS."""
    name = "tool_order_accuracy"

    def compute(self, predictions: List[str], references: List[str], **kwargs: Any) -> MetricResult:
        self.validate_inputs(predictions, references)
        scores: List[float] = []
        for pred, ref in zip(predictions, references):
            pred_seq = self._parse_sequence(pred)
            ref_seq = self._parse_sequence(ref)
            if not ref_seq:
                scores.append(1.0 if not pred_seq else 0.0)
                continue
            lcs_len = self._lcs_length(pred_seq, ref_seq)
            scores.append(lcs_len / len(ref_seq))
        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )

    def _parse_sequence(self, seq_str: str) -> List[str]:
        if not seq_str:
            return []
        return [t.strip().lower() for t in seq_str.split(",") if t.strip()]

    def _lcs_length(self, seq1: List[str], seq2: List[str]) -> int:
        m, n = len(seq1), len(seq2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i - 1] == seq2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
        return dp[m][n]


@register_metric
class ToolParameterAccuracyMetric(Metric):
    """Measures accuracy of tool call parameters."""
    name = "tool_param_accuracy"

    def __init__(self, check_values: bool = True, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.check_values = check_values

    def compute(self, predictions: List[str], references: List[str], **kwargs: Any) -> MetricResult:
        self.validate_inputs(predictions, references)
        scores: List[float] = []
        for pred, ref in zip(predictions, references):
            pred_params = self._parse_params(pred)
            ref_params = self._parse_params(ref)
            if not ref_params:
                scores.append(1.0 if not pred_params else 0.0)
                continue
            if self.check_values:
                matching = sum(1 for k, v in ref_params.items() if k in pred_params and pred_params[k] == v)
            else:
                matching = len(set(pred_params.keys()) & set(ref_params.keys()))
            scores.append(matching / len(ref_params))
        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )

    def _parse_params(self, params_str: str) -> Dict[str, Any]:
        if not params_str:
            return {}
        try:
            return json.loads(params_str)
        except json.JSONDecodeError:
            return {}


@register_metric
class ToolCallEfficiencyMetric(Metric):
    """Measures efficiency of tool usage."""
    name = "tool_efficiency"

    def compute(self, predictions: List[str], references: List[str], **kwargs: Any) -> MetricResult:
        self.validate_inputs(predictions, references)
        scores: List[float] = []
        for pred, ref in zip(predictions, references):
            try:
                pred_count = int(pred) if pred else 0
                ref_count = int(ref) if ref else 0
            except ValueError:
                scores.append(0.0)
                continue
            if ref_count == 0:
                scores.append(1.0 if pred_count == 0 else 0.0)
                continue
            scores.append(min(1.0, ref_count / pred_count) if pred_count > 0 else 0.0)
        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )


@register_metric
class ToolErrorRecoveryMetric(Metric):
    """Measures how well the agent recovers from tool errors."""
    name = "tool_error_recovery"

    def __init__(self, max_retries: int = 3, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.max_retries = max_retries

    def compute(self, predictions: List[str], references: List[str], **kwargs: Any) -> MetricResult:
        self.validate_inputs(predictions, references)
        scores: List[float] = []
        for pred, ref in zip(predictions, references):
            pred_status = pred.lower().strip() if pred else ""
            ref_status = ref.lower().strip() if ref else ""
            if pred_status == ref_status:
                scores.append(1.0)
            elif pred_status == "recovered" and ref_status in ("recovered", "fallback"):
                scores.append(0.8)
            elif pred_status == "fallback" and ref_status == "recovered":
                scores.append(0.6)
            elif pred_status in ("stuck", "loop") and ref_status in ("recovered", "fallback"):
                scores.append(0.0)
            else:
                scores.append(0.5)
        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )


@register_metric
class ToolCallPrecisionRecallMetric(Metric):
    """Computes precision, recall, and F1 for tool calls."""
    name = "tool_call_f1"

    def compute(self, predictions: List[str], references: List[str], **kwargs: Any) -> MetricResult:
        self.validate_inputs(predictions, references)
        scores: List[float] = []
        precisions: List[float] = []
        recalls: List[float] = []
        for pred, ref in zip(predictions, references):
            pred_calls = {t.strip().lower() for t in pred.split(",") if t.strip()}
            ref_calls = {t.strip().lower() for t in ref.split(",") if t.strip()}
            if not pred_calls and not ref_calls:
                scores.append(1.0); precisions.append(1.0); recalls.append(1.0)
                continue
            tp = len(pred_calls & ref_calls)
            p = tp / len(pred_calls) if pred_calls else 0.0
            r = tp / len(ref_calls) if ref_calls else 0.0
            f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
            scores.append(f1); precisions.append(p); recalls.append(r)
        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
            metadata={
                "avg_precision": sum(precisions) / len(precisions) if precisions else 0.0,
                "avg_recall": sum(recalls) / len(recalls) if recalls else 0.0,
            },
        )


def parse_tool_calls_from_messages(messages: List[Dict[str, Any]]) -> ToolCallSequence:
    """Parse tool calls from chat messages."""
    calls: List[ToolCall] = []
    task_description = ""
    final_answer: Optional[str] = None

    for msg in messages:
        role = msg.get("role", "")
        if role == "user" and not task_description:
            task_description = msg.get("content", "")
        if role == "assistant":
            tool_calls = msg.get("tool_calls", [])
            for tc in tool_calls:
                func = tc.get("function", {})
                name = func.get("name", "")
                params_str = func.get("arguments", "{}")
                try:
                    params = json.loads(params_str) if isinstance(params_str, str) else params_str
                except json.JSONDecodeError:
                    params = {}
                calls.append(ToolCall(name=name, parameters=params))
            if not tool_calls and msg.get("content"):
                final_answer = msg.get("content")
        if role == "tool":
            content = msg.get("content", "")
            if calls:
                calls[-1].result = content
                if "error" in content.lower():
                    calls[-1].success = False
                    calls[-1].error = content

    return ToolCallSequence(calls=calls, task_description=task_description, final_answer=final_answer)
