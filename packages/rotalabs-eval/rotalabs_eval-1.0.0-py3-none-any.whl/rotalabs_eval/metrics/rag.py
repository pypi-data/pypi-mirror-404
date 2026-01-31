"""RAG (Retrieval-Augmented Generation) evaluation metrics."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from rotalabs_eval.core.exceptions import EvalMetricError
from rotalabs_eval.metrics.base import Metric, MetricResult, register_metric
from rotalabs_eval.utils.helpers import safe_json_parse

logger = logging.getLogger(__name__)

RAG_RELEVANCE_PROMPT = """Given the query and context, rate how relevant the context is to answering the query.

Query: {query}
Context: {context}

Rate relevance from 1-5 where:
1 = Completely irrelevant
3 = Partially relevant
5 = Highly relevant

Respond with JSON: {{"score": <1-5>, "reasoning": "<explanation>"}}"""

RAG_FAITHFULNESS_PROMPT = """Determine if the answer is faithful to (grounded in) the provided context.
Does the answer contain any claims not supported by the context?

Context: {context}
Answer: {answer}

Rate faithfulness from 1-5 where:
1 = Completely unfaithful (hallucinated)
3 = Partially faithful
5 = Fully faithful (all claims grounded)

Respond with JSON: {{"score": <1-5>, "reasoning": "<explanation>"}}"""

RAG_ANSWER_RELEVANCE_PROMPT = """Rate how well the answer addresses the query.

Query: {query}
Answer: {answer}

Rate from 1-5 where:
1 = Does not address the query at all
3 = Partially addresses the query
5 = Fully and directly addresses the query

Respond with JSON: {{"score": <1-5>, "reasoning": "<explanation>"}}"""


class _BaseRAGMetric(Metric):
    """Base class for RAG metrics that use LLM judges."""

    def __init__(
        self,
        judge_model: str = "gpt-4o",
        prompt_template: str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.judge_model = judge_model
        self.prompt_template = prompt_template
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

    def _judge_score(self, prompt: str) -> float:
        from rotalabs_eval.inference.base import InferenceRequest

        engine = self._get_engine()
        request = InferenceRequest(prompt=prompt, temperature=0.0, max_tokens=512)
        response = engine.generate(request)

        if response.success and response.text:
            import re

            result = safe_json_parse(response.text)
            if result and "score" in result:
                try:
                    return float(result["score"]) / 5.0
                except (ValueError, TypeError):
                    pass
            numbers = re.findall(r"\b([1-5])\b", response.text)
            if numbers:
                return float(numbers[0]) / 5.0
        return 0.0


@register_metric
class ContextRelevanceMetric(_BaseRAGMetric):
    """Measures relevance of retrieved context to the query."""

    name = "context_relevance"

    def __init__(self, judge_model: str = "gpt-4o", **kwargs: Any) -> None:
        super().__init__(
            judge_model=judge_model,
            prompt_template=RAG_RELEVANCE_PROMPT,
            **kwargs,
        )

    def compute(
        self,
        predictions: List[str],
        references: List[str],
        **kwargs: Any,
    ) -> MetricResult:
        queries = kwargs.get("queries", [""] * len(predictions))
        contexts = kwargs.get("contexts", predictions)

        scores = []
        for query, context in zip(queries, contexts):
            ctx_str = context if isinstance(context, str) else " ".join(context)
            prompt = self.prompt_template.format(query=query, context=ctx_str)
            scores.append(self._judge_score(prompt))

        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )


@register_metric
class FaithfulnessMetric(_BaseRAGMetric):
    """Measures if the answer is grounded in the context (no hallucination)."""

    name = "faithfulness"

    def __init__(self, judge_model: str = "gpt-4o", **kwargs: Any) -> None:
        super().__init__(
            judge_model=judge_model,
            prompt_template=RAG_FAITHFULNESS_PROMPT,
            **kwargs,
        )

    def compute(
        self,
        predictions: List[str],
        references: List[str],
        **kwargs: Any,
    ) -> MetricResult:
        contexts = kwargs.get("contexts", references)

        scores = []
        for answer, context in zip(predictions, contexts):
            ctx_str = context if isinstance(context, str) else " ".join(context)
            prompt = self.prompt_template.format(context=ctx_str, answer=answer)
            scores.append(self._judge_score(prompt))

        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )


@register_metric
class AnswerRelevanceMetric(_BaseRAGMetric):
    """Measures if the answer addresses the query."""

    name = "answer_relevance"

    def __init__(self, judge_model: str = "gpt-4o", **kwargs: Any) -> None:
        super().__init__(
            judge_model=judge_model,
            prompt_template=RAG_ANSWER_RELEVANCE_PROMPT,
            **kwargs,
        )

    def compute(
        self,
        predictions: List[str],
        references: List[str],
        **kwargs: Any,
    ) -> MetricResult:
        queries = kwargs.get("queries", [""] * len(predictions))

        scores = []
        for answer, query in zip(predictions, queries):
            prompt = self.prompt_template.format(query=query, answer=answer)
            scores.append(self._judge_score(prompt))

        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )


@register_metric
class ContextRelevanceEmbeddingMetric(Metric):
    """Embedding-based context relevance (faster/cheaper than LLM judge)."""

    name = "context_relevance_embedding"

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                raise ImportError(
                    "sentence-transformers required. "
                    "Install with: pip install rotalabs-eval[embeddings]"
                )
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def compute(
        self,
        predictions: List[str],
        references: List[str],
        **kwargs: Any,
    ) -> MetricResult:
        import numpy as np

        queries = kwargs.get("queries", [""] * len(predictions))
        contexts = kwargs.get("contexts", predictions)

        model = self._get_model()

        query_embs = model.encode(
            [str(q) for q in queries], show_progress_bar=False
        )
        ctx_texts = [
            c if isinstance(c, str) else " ".join(c) for c in contexts
        ]
        ctx_embs = model.encode(ctx_texts, show_progress_bar=False)

        scores = []
        for qe, ce in zip(query_embs, ctx_embs):
            qn = qe / (np.linalg.norm(qe) + 1e-8)
            cn = ce / (np.linalg.norm(ce) + 1e-8)
            sim = float(np.dot(qn, cn))
            scores.append(max(0.0, sim))

        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )


@register_metric
class AnswerRelevanceEmbeddingMetric(Metric):
    """Embedding-based answer relevance."""

    name = "answer_relevance_embedding"

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                raise ImportError(
                    "sentence-transformers required. "
                    "Install with: pip install rotalabs-eval[embeddings]"
                )
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def compute(
        self,
        predictions: List[str],
        references: List[str],
        **kwargs: Any,
    ) -> MetricResult:
        import numpy as np

        queries = kwargs.get("queries", [""] * len(predictions))

        model = self._get_model()

        query_embs = model.encode(
            [str(q) for q in queries], show_progress_bar=False
        )
        answer_embs = model.encode(
            [str(p) if p else "" for p in predictions],
            show_progress_bar=False,
        )

        scores = []
        for qe, ae in zip(query_embs, answer_embs):
            qn = qe / (np.linalg.norm(qe) + 1e-8)
            an = ae / (np.linalg.norm(ae) + 1e-8)
            sim = float(np.dot(qn, an))
            scores.append(max(0.0, sim))

        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )
