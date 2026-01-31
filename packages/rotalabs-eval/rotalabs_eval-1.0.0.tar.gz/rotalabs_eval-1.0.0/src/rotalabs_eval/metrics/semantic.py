"""Semantic evaluation metrics using embeddings."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from rotalabs_eval.metrics.base import Metric, MetricResult, register_metric

logger = logging.getLogger(__name__)


@register_metric
class BERTScoreMetric(Metric):
    """BERTScore using contextual embeddings.

    Requires the sentence-transformers package.
    """

    name = "bertscore"

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
        self.validate_inputs(predictions, references)

        import numpy as np

        model = self._get_model()

        pred_embeddings = model.encode(
            [str(p) if p else "" for p in predictions],
            show_progress_bar=False,
        )
        ref_embeddings = model.encode(
            [str(r) if r else "" for r in references],
            show_progress_bar=False,
        )

        # Cosine similarity per pair
        scores = []
        for pe, re_ in zip(pred_embeddings, ref_embeddings):
            pe_norm = pe / (np.linalg.norm(pe) + 1e-8)
            re_norm = re_ / (np.linalg.norm(re_) + 1e-8)
            sim = float(np.dot(pe_norm, re_norm))
            scores.append(max(0.0, sim))

        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )


@register_metric
class EmbeddingSimilarityMetric(Metric):
    """Cosine similarity using sentence embeddings."""

    name = "embedding_similarity"

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
        self.validate_inputs(predictions, references)

        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity

        model = self._get_model()

        pred_emb = model.encode(
            [str(p) if p else "" for p in predictions],
            show_progress_bar=False,
        )
        ref_emb = model.encode(
            [str(r) if r else "" for r in references],
            show_progress_bar=False,
        )

        scores = []
        for i in range(len(predictions)):
            sim = float(cosine_similarity([pred_emb[i]], [ref_emb[i]])[0][0])
            scores.append(max(0.0, sim))

        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )


# Alias for convenience
SemanticSimilarityMetric = EmbeddingSimilarityMetric
