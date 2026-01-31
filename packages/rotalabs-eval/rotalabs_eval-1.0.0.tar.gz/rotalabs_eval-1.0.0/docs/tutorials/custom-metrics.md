# Custom Metrics

This tutorial shows three ways to create custom metrics in `rotalabs-eval`: the factory function, subclassing, and the decorator-based registration.

---

## 1. Create a Metric with the Factory Function

The simplest approach is `create_custom_metric`. You provide a name and a function that takes `(List[str], List[str])` and returns `List[float]`:

```python
from rotalabs_eval.metrics.custom import create_custom_metric
from rotalabs_eval.metrics.registry import MetricRegistry

def keyword_overlap(predictions, references):
    """Fraction of reference keywords found in the prediction."""
    scores = []
    for pred, ref in zip(predictions, references):
        ref_words = set(ref.lower().split())
        pred_words = set(pred.lower().split())
        if not ref_words:
            scores.append(1.0)
        else:
            scores.append(len(ref_words & pred_words) / len(ref_words))
    return scores

KeywordOverlapMetric = create_custom_metric("keyword_overlap", keyword_overlap)

# Register it so it can be looked up by name
registry = MetricRegistry()
registry.register("keyword_overlap", KeywordOverlapMetric)

# Use it
metric = registry.get("keyword_overlap")
result = metric.compute(
    predictions=["The quick brown fox jumps"],
    references=["quick fox"],
)
print(f"{result.name}: {result.value:.2f}")
# keyword_overlap: 1.00
print(result.per_example_scores)
# [1.0]
```

The factory returns a class (not an instance). When `.compute()` is called, it invokes your function, wraps the per-example scores into a `MetricResult`, and computes the aggregate mean automatically.

---

## 2. Create a Metric by Subclassing

For more control, subclass the `Metric` ABC directly and implement the `compute` method:

```python
from typing import Any, List
from rotalabs_eval.metrics.base import Metric, MetricResult

class LevenshteinSimilarityMetric(Metric):
    """Normalized Levenshtein similarity between prediction and reference."""

    name = "levenshtein_similarity"

    def compute(
        self,
        predictions: List[str],
        references: List[str],
        **kwargs: Any,
    ) -> MetricResult:
        self.validate_inputs(predictions, references)

        scores = []
        for pred, ref in zip(predictions, references):
            dist = self._levenshtein_distance(pred.lower(), ref.lower())
            max_len = max(len(pred), len(ref), 1)
            scores.append(1.0 - dist / max_len)

        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )

    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return LevenshteinSimilarityMetric._levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        prev_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row
        return prev_row[-1]
```

Key points:

- Call `self.validate_inputs(predictions, references)` to ensure lists have equal length.
- Return a `MetricResult` with `name`, `value` (aggregate), and `per_example_scores`.
- The `name` class attribute is used as the registry key and appears in `MetricResult.name`.

Test it:

```python
metric = LevenshteinSimilarityMetric()
result = metric.compute(
    predictions=["hello world", "foo bar"],
    references=["hello world", "foo baz"],
)
print(f"{result.name}: {result.value:.4f}")
# levenshtein_similarity: 0.9286
print(result.per_example_scores)
# [1.0, 0.8571428571428572]
```

---

## 3. Register with the @register_metric Decorator

To make your subclassed metric available through the global registry automatically, apply the `@register_metric` decorator:

```python
from rotalabs_eval.metrics.base import Metric, MetricResult, register_metric
from typing import Any, List

@register_metric
class SentenceLengthDiffMetric(Metric):
    """Absolute difference in word count, normalized."""

    name = "sentence_length_diff"

    def compute(
        self,
        predictions: List[str],
        references: List[str],
        **kwargs: Any,
    ) -> MetricResult:
        self.validate_inputs(predictions, references)

        scores = []
        for pred, ref in zip(predictions, references):
            pred_len = len(pred.split())
            ref_len = len(ref.split())
            max_len = max(pred_len, ref_len, 1)
            scores.append(1.0 - abs(pred_len - ref_len) / max_len)

        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )
```

The decorator registers the class in the global `_METRIC_REGISTRY` dict using the `name` attribute as the key. Now it is available via both `MetricRegistry` and `get_registered_metrics()`:

```python
from rotalabs_eval.metrics.base import get_registered_metrics
from rotalabs_eval.metrics.registry import MetricRegistry

# Check global registry
registered = get_registered_metrics()
print("sentence_length_diff" in registered)  # True

# Access through MetricRegistry singleton
registry = MetricRegistry()
metric = registry.get("sentence_length_diff")
result = metric.compute(
    predictions=["This is a short answer"],
    references=["This is a slightly longer reference answer"],
)
print(result)  # sentence_length_diff: 0.2857
```

---

## 4. Use Custom Metrics from the Registry

Once registered, custom metrics work identically to built-in metrics:

```python
from rotalabs_eval.metrics.registry import MetricRegistry

registry = MetricRegistry()

predictions = ["Paris is the capital", "Water is wet"]
references = ["Paris is the capital of France", "Water is a liquid"]

# Run all metrics including custom ones
for name in ["exact_match", "f1", "keyword_overlap", "sentence_length_diff"]:
    try:
        metric = registry.get(name)
        result = metric.compute(predictions, references)
        print(f"  {name:25s} {result.value:.4f}")
    except KeyError:
        print(f"  {name:25s} (not registered)")
```

This makes it easy to mix built-in and custom metrics in evaluation pipelines without changing any downstream code.
