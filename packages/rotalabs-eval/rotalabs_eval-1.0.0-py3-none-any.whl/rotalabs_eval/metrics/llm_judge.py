"""LLM-as-judge evaluation metrics."""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from rotalabs_eval.core.exceptions import EvalMetricError
from rotalabs_eval.metrics.base import Metric, MetricResult, register_metric
from rotalabs_eval.utils.helpers import safe_json_parse

logger = logging.getLogger(__name__)

DEFAULT_RUBRIC = """Rate the following response on a scale of 1-5:
1 = Completely incorrect or irrelevant
2 = Partially correct but has major issues
3 = Mostly correct with some issues
4 = Correct with minor issues
5 = Excellent, fully correct and well-written

Question: {question}
Reference Answer: {reference}
Model Response: {prediction}

Provide your rating as JSON: {{"score": <1-5>, "reasoning": "<explanation>"}}"""

PAIRWISE_TEMPLATE = """Compare these two responses and determine which is better.

Question: {question}
Reference Answer: {reference}

Response A: {prediction_a}
Response B: {prediction_b}

Which response is better? Reply with JSON: {{"winner": "A" or "B" or "tie", "reasoning": "<explanation>"}}"""


def _extract_score(text: str) -> Optional[float]:
    """Extract a numeric score from LLM judge response."""
    result = safe_json_parse(text)
    if result and "score" in result:
        try:
            return float(result["score"])
        except (ValueError, TypeError):
            pass

    # Fallback: look for a number
    numbers = re.findall(r"\b([1-5])\b", text)
    if numbers:
        return float(numbers[0])

    return None


@register_metric
class LLMJudgeMetric(Metric):
    """LLM-as-judge evaluation using custom rubrics.

    Uses an LLM to score responses on a configurable scale.
    """

    name = "llm_judge"

    def __init__(
        self,
        rubric: Optional[str] = None,
        judge_model: str = "gpt-4o",
        max_score: float = 5.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.rubric = rubric or DEFAULT_RUBRIC
        self.judge_model = judge_model
        self.max_score = max_score
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            from rotalabs_eval.inference.openai import OpenAIEngine

            self._engine = OpenAIEngine(
                model_name=self.judge_model,
                temperature=0.0,
                max_tokens=512,
            )
        return self._engine

    def compute(
        self,
        predictions: List[str],
        references: List[str],
        **kwargs: Any,
    ) -> MetricResult:
        self.validate_inputs(predictions, references)

        from rotalabs_eval.inference.base import InferenceRequest

        engine = self._get_engine()
        queries = kwargs.get("queries", [""] * len(predictions))

        scores = []
        for pred, ref, query in zip(predictions, references, queries):
            prompt = self.rubric.format(
                question=query,
                reference=ref,
                prediction=pred,
            )

            request = InferenceRequest(prompt=prompt, temperature=0.0, max_tokens=512)
            response = engine.generate(request)

            if response.success and response.text:
                score = _extract_score(response.text)
                if score is not None:
                    normalized = score / self.max_score
                    scores.append(normalized)
                else:
                    logger.warning(f"Could not extract score from judge response")
                    scores.append(0.0)
            else:
                logger.warning(f"Judge inference failed: {response.error}")
                scores.append(0.0)

        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )


@register_metric
class PairwiseJudgeMetric(Metric):
    """Pairwise comparison using LLM judge."""

    name = "pairwise_judge"

    def __init__(
        self,
        judge_model: str = "gpt-4o",
        template: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.judge_model = judge_model
        self.template = template or PAIRWISE_TEMPLATE
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            from rotalabs_eval.inference.openai import OpenAIEngine

            self._engine = OpenAIEngine(
                model_name=self.judge_model,
                temperature=0.0,
                max_tokens=512,
            )
        return self._engine

    def compute(
        self,
        predictions: List[str],
        references: List[str],
        **kwargs: Any,
    ) -> MetricResult:
        """Compare predictions_a (predictions) vs predictions_b (references)."""
        self.validate_inputs(predictions, references)

        from rotalabs_eval.inference.base import InferenceRequest

        engine = self._get_engine()
        queries = kwargs.get("queries", [""] * len(predictions))

        scores = []
        for pred_a, pred_b, query in zip(predictions, references, queries):
            prompt = self.template.format(
                question=query,
                reference="",
                prediction_a=pred_a,
                prediction_b=pred_b,
            )

            request = InferenceRequest(prompt=prompt, temperature=0.0, max_tokens=512)
            response = engine.generate(request)

            if response.success and response.text:
                result = safe_json_parse(response.text)
                if result and "winner" in result:
                    winner = result["winner"].upper()
                    if winner == "A":
                        scores.append(1.0)
                    elif winner == "B":
                        scores.append(0.0)
                    else:
                        scores.append(0.5)
                else:
                    scores.append(0.5)
            else:
                scores.append(0.5)

        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )


@register_metric
class GEvalMetric(Metric):
    """G-Eval: Multi-criteria evaluation with weighted scoring."""

    name = "geval"

    def __init__(
        self,
        criteria: Optional[Dict[str, float]] = None,
        judge_model: str = "gpt-4o",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.criteria = criteria or {
            "relevance": 0.3,
            "coherence": 0.3,
            "fluency": 0.2,
            "consistency": 0.2,
        }
        self.judge_model = judge_model
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            from rotalabs_eval.inference.openai import OpenAIEngine

            self._engine = OpenAIEngine(
                model_name=self.judge_model,
                temperature=0.0,
                max_tokens=1024,
            )
        return self._engine

    def compute(
        self,
        predictions: List[str],
        references: List[str],
        **kwargs: Any,
    ) -> MetricResult:
        self.validate_inputs(predictions, references)

        from rotalabs_eval.inference.base import InferenceRequest

        engine = self._get_engine()
        queries = kwargs.get("queries", [""] * len(predictions))

        criteria_str = "\n".join(
            f"- {name} (weight: {weight}): Rate 1-5"
            for name, weight in self.criteria.items()
        )

        scores = []
        for pred, ref, query in zip(predictions, references, queries):
            prompt = (
                f"Evaluate the following response on multiple criteria.\n\n"
                f"Question: {query}\n"
                f"Reference: {ref}\n"
                f"Response: {pred}\n\n"
                f"Criteria:\n{criteria_str}\n\n"
                f"Provide scores as JSON: {{\"criterion_name\": score, ...}}"
            )

            request = InferenceRequest(prompt=prompt, temperature=0.0, max_tokens=1024)
            response = engine.generate(request)

            if response.success and response.text:
                result = safe_json_parse(response.text)
                if result:
                    weighted_sum = 0.0
                    total_weight = 0.0
                    for criterion, weight in self.criteria.items():
                        if criterion in result:
                            try:
                                val = float(result[criterion]) / 5.0
                                weighted_sum += weight * val
                                total_weight += weight
                            except (ValueError, TypeError):
                                pass
                    score = weighted_sum / total_weight if total_weight > 0 else 0.0
                    scores.append(score)
                else:
                    scores.append(0.0)
            else:
                scores.append(0.0)

        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )
