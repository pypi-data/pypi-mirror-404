"""Lexical evaluation metrics: exact match, F1, BLEU, ROUGE-L."""
from __future__ import annotations

import logging
import re
import string
from collections import Counter
from typing import Any, Dict, List, Optional

from rotalabs_eval.metrics.base import Metric, MetricResult, register_metric

logger = logging.getLogger(__name__)


def _normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = " ".join(text.split())
    return text


def _tokenize(text: str) -> List[str]:
    """Simple whitespace tokenization after normalization."""
    return _normalize_text(text).split()


@register_metric
class ExactMatchMetric(Metric):
    """Binary exact match after normalization."""

    name = "exact_match"

    def compute(
        self,
        predictions: List[str],
        references: List[str],
        **kwargs: Any,
    ) -> MetricResult:
        self.validate_inputs(predictions, references)

        scores = []
        for pred, ref in zip(predictions, references):
            pred_norm = _normalize_text(str(pred) if pred else "")
            ref_norm = _normalize_text(str(ref) if ref else "")
            scores.append(1.0 if pred_norm == ref_norm else 0.0)

        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )


@register_metric
class F1Metric(Metric):
    """Token-level F1 score (SQuAD-style)."""

    name = "f1"

    def compute(
        self,
        predictions: List[str],
        references: List[str],
        **kwargs: Any,
    ) -> MetricResult:
        self.validate_inputs(predictions, references)

        scores = []
        for pred, ref in zip(predictions, references):
            pred_tokens = _tokenize(str(pred) if pred else "")
            ref_tokens = _tokenize(str(ref) if ref else "")

            if not pred_tokens and not ref_tokens:
                scores.append(1.0)
                continue
            if not pred_tokens or not ref_tokens:
                scores.append(0.0)
                continue

            common = Counter(pred_tokens) & Counter(ref_tokens)
            num_common = sum(common.values())

            if num_common == 0:
                scores.append(0.0)
                continue

            precision = num_common / len(pred_tokens)
            recall = num_common / len(ref_tokens)
            f1 = 2 * precision * recall / (precision + recall)
            scores.append(f1)

        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )


@register_metric
class BLEUMetric(Metric):
    """BLEU score with configurable n-gram order."""

    name = "bleu"

    def __init__(self, max_n: int = 4, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.max_n = max_n

    def compute(
        self,
        predictions: List[str],
        references: List[str],
        **kwargs: Any,
    ) -> MetricResult:
        self.validate_inputs(predictions, references)

        scores = []
        for pred, ref in zip(predictions, references):
            pred_tokens = _tokenize(str(pred) if pred else "")
            ref_tokens = _tokenize(str(ref) if ref else "")

            if not pred_tokens or not ref_tokens:
                scores.append(0.0)
                continue

            # Compute n-gram precisions
            precisions = []
            for n in range(1, self.max_n + 1):
                pred_ngrams = self._get_ngrams(pred_tokens, n)
                ref_ngrams = self._get_ngrams(ref_tokens, n)

                if not pred_ngrams:
                    precisions.append(0.0)
                    continue

                clipped = sum(
                    min(pred_ngrams[ng], ref_ngrams.get(ng, 0))
                    for ng in pred_ngrams
                )
                precisions.append(clipped / sum(pred_ngrams.values()))

            # Geometric mean of precisions
            import math

            if any(p == 0 for p in precisions):
                bleu = 0.0
            else:
                log_avg = sum(math.log(p) for p in precisions) / len(precisions)
                bleu = math.exp(log_avg)

            # Brevity penalty
            bp = min(1.0, math.exp(1 - len(ref_tokens) / len(pred_tokens)))
            bleu *= bp

            scores.append(bleu)

        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )

    @staticmethod
    def _get_ngrams(tokens: List[str], n: int) -> Dict[str, int]:
        ngrams: Dict[str, int] = {}
        for i in range(len(tokens) - n + 1):
            ng = " ".join(tokens[i : i + n])
            ngrams[ng] = ngrams.get(ng, 0) + 1
        return ngrams


@register_metric
class ROUGELMetric(Metric):
    """ROUGE-L score using longest common subsequence."""

    name = "rouge_l"

    def compute(
        self,
        predictions: List[str],
        references: List[str],
        **kwargs: Any,
    ) -> MetricResult:
        self.validate_inputs(predictions, references)

        scores = []
        for pred, ref in zip(predictions, references):
            pred_tokens = _tokenize(str(pred) if pred else "")
            ref_tokens = _tokenize(str(ref) if ref else "")

            if not pred_tokens and not ref_tokens:
                scores.append(1.0)
                continue
            if not pred_tokens or not ref_tokens:
                scores.append(0.0)
                continue

            lcs_len = self._lcs_length(pred_tokens, ref_tokens)

            precision = lcs_len / len(pred_tokens)
            recall = lcs_len / len(ref_tokens)

            if precision + recall == 0:
                scores.append(0.0)
            else:
                f1 = 2 * precision * recall / (precision + recall)
                scores.append(f1)

        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )

    @staticmethod
    def _lcs_length(seq1: List[str], seq2: List[str]) -> int:
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
class ContainsMetric(Metric):
    """Substring containment check."""

    name = "contains"

    def __init__(self, case_sensitive: bool = False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.case_sensitive = case_sensitive

    def compute(
        self,
        predictions: List[str],
        references: List[str],
        **kwargs: Any,
    ) -> MetricResult:
        self.validate_inputs(predictions, references)

        scores = []
        for pred, ref in zip(predictions, references):
            p = str(pred) if pred else ""
            r = str(ref) if ref else ""
            if not self.case_sensitive:
                p = p.lower()
                r = r.lower()
            scores.append(1.0 if r in p else 0.0)

        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )


@register_metric
class LengthRatioMetric(Metric):
    """Ratio of prediction length to reference length."""

    name = "length_ratio"

    def compute(
        self,
        predictions: List[str],
        references: List[str],
        **kwargs: Any,
    ) -> MetricResult:
        self.validate_inputs(predictions, references)

        scores = []
        for pred, ref in zip(predictions, references):
            pred_len = len(str(pred)) if pred else 0
            ref_len = len(str(ref)) if ref else 0
            if ref_len == 0:
                scores.append(1.0 if pred_len == 0 else 0.0)
            else:
                scores.append(pred_len / ref_len)

        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )
