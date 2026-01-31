# Basic Evaluation

This tutorial walks through running your first evaluation with `rotalabs-eval`, from creating sample data to inspecting per-example scores.

---

## 1. Create Sample Data

All metrics operate on paired lists of strings: predictions and references.

```python
predictions = [
    "The capital of France is Paris.",
    "Python is a compiled language.",
    "Water boils at 100 degrees Celsius.",
    "The Earth orbits the Moon.",
    "Machine learning is a subset of AI.",
]

references = [
    "The capital of France is Paris.",
    "Python is an interpreted language.",
    "Water boils at 100 degrees Celsius.",
    "The Earth orbits the Sun.",
    "Machine learning is a subset of artificial intelligence.",
]
```

---

## 2. Run Multiple Lexical Metrics

Instantiate each metric and call `.compute()` with the prediction and reference lists:

```python
from rotalabs_eval.metrics.lexical import ExactMatchMetric, F1Metric, ROUGELMetric

exact_match = ExactMatchMetric()
f1 = F1Metric()
rouge_l = ROUGELMetric()

em_result = exact_match.compute(predictions, references)
f1_result = f1.compute(predictions, references)
rl_result = rouge_l.compute(predictions, references)

print(em_result)  # exact_match: 0.4000
print(f1_result)  # f1: 0.8095
print(rl_result)  # rouge_l: 0.8095
```

Each metric takes `predictions: List[str]` and `references: List[str]` and returns a `MetricResult`.

---

## 3. Inspect MetricResult

Every `MetricResult` has two key attributes:

- **`.value`** -- The aggregate score (mean across all examples).
- **`.per_example_scores`** -- A list of floats, one per example.

```python
print(f"Aggregate exact match: {em_result.value:.4f}")
# Aggregate exact match: 0.4000

print("Per-example exact match scores:")
for i, score in enumerate(em_result.per_example_scores):
    print(f"  Example {i}: {score:.1f}")
# Per-example exact match scores:
#   Example 0: 1.0
#   Example 1: 0.0
#   Example 2: 1.0
#   Example 3: 0.0
#   Example 4: 0.0
```

You can also access the metric name and any metadata:

```python
print(em_result.name)      # "exact_match"
print(em_result.metadata)  # {}
```

---

## 4. Use the Registry to Get Metrics by Name

Instead of importing metric classes directly, use `MetricRegistry` to look them up by name:

```python
from rotalabs_eval.metrics.registry import MetricRegistry

registry = MetricRegistry()

# List all available metrics
print(registry.list_metrics())
# ['action_sequence_f1', 'argument_diversity', 'argument_quality', 'bleu',
#  'consensus_reached', 'contains', 'contribution_balance', 'debate_outcome_accuracy',
#  'debate_progression', 'exact_match', 'f1', 'goal_completion', 'length_ratio',
#  'rouge_l', 'tool_call_accuracy', 'tool_call_f1', 'tool_efficiency',
#  'tool_error_recovery', 'tool_order_accuracy', 'tool_param_accuracy',
#  'tool_selection_accuracy', 'trajectory_efficiency']

# Get a metric by name
em_metric = registry.get("exact_match")
result = em_metric.compute(predictions, references)
print(result)  # exact_match: 0.4000
```

You can also pass constructor arguments through `registry.get()`:

```python
bleu_metric = registry.get("bleu", max_n=2)
result = bleu_metric.compute(predictions, references)
print(result)  # bleu: 0.5841
```

---

## 5. Batch Evaluation Across a Dataset

Run all metrics over the same data and collect results into a summary:

```python
from rotalabs_eval.metrics.registry import MetricRegistry

registry = MetricRegistry()
metric_names = ["exact_match", "f1", "rouge_l", "bleu", "contains"]

results = {}
for name in metric_names:
    metric = registry.get(name)
    result = metric.compute(predictions, references)
    results[name] = result.value

print("Evaluation Summary")
print("-" * 35)
for name, value in results.items():
    print(f"  {name:20s} {value:.4f}")
# Evaluation Summary
# -----------------------------------
#   exact_match          0.4000
#   f1                   0.8095
#   rouge_l              0.8095
#   bleu                 0.5116
#   contains             0.4000
```

To access per-example breakdowns for error analysis:

```python
em = registry.get("exact_match")
result = em.compute(predictions, references)

failures = [
    (i, predictions[i], references[i])
    for i, score in enumerate(result.per_example_scores)
    if score == 0.0
]

print(f"\n{len(failures)} failures out of {len(predictions)} examples:")
for idx, pred, ref in failures:
    print(f"  [{idx}] Predicted: {pred[:60]}")
    print(f"       Reference: {ref[:60]}")
    print()
```
