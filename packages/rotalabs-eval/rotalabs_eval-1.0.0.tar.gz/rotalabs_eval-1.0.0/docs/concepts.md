# Core Concepts

This page explains the fundamental concepts behind `rotalabs-eval` and how the different components fit together.

---

## Evaluation Pipeline

Every evaluation in `rotalabs-eval` follows a five-stage pipeline:

```
Dataset --> Inference --> Metrics --> Statistics --> Results
```

1. **Dataset** -- Load evaluation examples from Parquet, CSV, JSON, or in-memory lists. Each example has an input, an optional reference (ground truth), and an optional ID.

2. **Inference** -- Send inputs through one or more models to obtain predictions. Supports OpenAI, Anthropic, Google, Ollama, Databricks, vLLM, and custom providers.

3. **Metrics** -- Score each prediction against its reference using one or more metrics. Metrics return a `MetricResult` containing an aggregate `.value` and optional `.per_example_scores`.

4. **Statistics** -- Compute confidence intervals, significance tests, effect sizes, and power analyses over the metric scores to quantify uncertainty and compare models rigorously.

5. **Results** -- Aggregate everything into structured results that can be saved as Parquet, CSV, or JSON, rendered as HTML reports, or logged to MLflow/W&B.

### How the Configuration Objects Tie Together

Three dataclasses wire the pipeline together:

- **`EvalTask`** -- Defines *what* to evaluate: dataset path, input/reference columns, prompt template with `{{column}}` placeholders, and optional context columns for RAG evaluation.

- **`ModelConfig`** -- Defines *which model* to call: provider (`ModelProvider` enum), model name, temperature, max tokens, API key, and optional extra parameters.

- **`MetricConfig`** -- Defines *how* to score: metric name (must match the registry), constructor kwargs, whether a reference is required, and an optional weight for composite scoring.

```python
from rotalabs_eval.core.task import EvalTask
from rotalabs_eval.core.config import ModelConfig, MetricConfig, ModelProvider

task = EvalTask(
    dataset_path="data/qa.parquet",
    input_column="question",
    reference_column="answer",
    prompt_template="Answer concisely: {{question}}",
)

model = ModelConfig(
    provider=ModelProvider.OPENAI,
    model_name="gpt-4o",
    temperature=0.0,
)

metrics = [
    MetricConfig(name="exact_match"),
    MetricConfig(name="f1"),
    MetricConfig(name="rouge_l"),
]
```

---

## Metric Types

Metrics are organized into four categories based on what they measure and what dependencies they require.

### Lexical Metrics

Token-level and string-level comparisons. No extra dependencies needed.

| Metric | Class | What it measures |
|--------|-------|------------------|
| `exact_match` | `ExactMatchMetric` | Binary match after lowercasing, stripping punctuation, and collapsing whitespace |
| `f1` | `F1Metric` | Token-level F1 (SQuAD-style) using precision and recall over token overlap |
| `bleu` | `BLEUMetric` | BLEU score with configurable n-gram order (default 4) and brevity penalty |
| `rouge_l` | `ROUGELMetric` | ROUGE-L F1 using longest common subsequence |
| `contains` | `ContainsMetric` | Whether the reference is a substring of the prediction (case-insensitive by default) |
| `length_ratio` | `LengthRatioMetric` | Character-length ratio of prediction to reference |

All lexical metrics follow the same interface:

```python
metric = ExactMatchMetric()
result = metric.compute(predictions=["Paris"], references=["paris"])
# result.value == 1.0
```

### Semantic Metrics

Embedding-based similarity measures. Requires the `[embeddings]` extra:

```
pip install rotalabs-eval[embeddings]
```

| Metric | What it measures |
|--------|------------------|
| `BERTScore` | Contextual embedding similarity using BERT |
| `EmbeddingSimilarity` | Cosine similarity between sentence embeddings |

### LLM-as-Judge Metrics

Use a language model to evaluate output quality. Requires the `[openai]` extra:

```
pip install rotalabs-eval[openai]
```

| Metric | What it measures |
|--------|------------------|
| `LLMJudge` | Single-output quality scoring with a rubric |
| `PairwiseJudge` | Head-to-head comparison of two outputs |
| `GEval` | G-Eval framework for fine-grained evaluation |

### RAG Metrics

Evaluate retrieval-augmented generation pipelines. These metrics assess whether retrieved context is relevant, whether the answer is faithful to the context, and whether the answer addresses the question.

| Metric | What it measures |
|--------|------------------|
| `ContextRelevance` | How relevant the retrieved context is to the query |
| `Faithfulness` | Whether the answer is grounded in the provided context |
| `AnswerRelevance` | Whether the answer addresses the original question |

---

## Statistical Analysis

The `statistics` module provides rigorous tools for quantifying uncertainty and comparing models.

### Confidence Intervals

Compute intervals around a point estimate to express uncertainty.

| Function | Method | When to use |
|----------|--------|-------------|
| `bootstrap_ci` | Percentile bootstrap | General-purpose, any statistic |
| `bootstrap_ci_bca` | Bias-corrected and accelerated bootstrap | Skewed distributions, more accurate |
| `analytical_ci_mean` | t-distribution | Continuous scores, large samples |
| `analytical_ci_proportion` | Wilson / Normal / Clopper-Pearson | Binary metrics (exact match, pass/fail) |

All CI functions return `(point_estimate, (ci_lower, ci_upper), standard_error)`.

```python
from rotalabs_eval.statistics.confidence import bootstrap_ci
import numpy as np

scores = np.array([0.8, 0.9, 0.7, 0.85, 0.95])
point, (lo, hi), se = bootstrap_ci(scores, seed=42)
```

For proportions, `analytical_ci_proportion` supports three methods selected via the `method` parameter: `"wilson"` (default, recommended), `"normal"`, and `"clopper_pearson"` (exact).

### Significance Testing

Determine whether two models are statistically different.

| Function | Test | Data type |
|----------|------|-----------|
| `paired_ttest` | Paired t-test | Continuous, normal |
| `mcnemar_test` | McNemar's test | Binary (correct/incorrect) |
| `wilcoxon_signed_rank` | Wilcoxon signed-rank | Continuous, non-parametric |
| `bootstrap_significance` | Permutation test | Any paired data |
| `choose_test` | Auto-selects from above | Any paired data |

All tests return a `SignificanceResult` with `.test_name`, `.statistic`, `.p_value`, `.significant`, `.alpha`, and `.details`.

`choose_test` automatically picks the right test: McNemar for binary data, Wilcoxon for non-normal continuous data (Shapiro-Wilk p < 0.05), and paired t-test otherwise.

### Effect Sizes

Quantify the magnitude of a difference between models, beyond just significance.

| Function | Measure | Notes |
|----------|---------|-------|
| `cohens_d` | Cohen's d | Standard effect size; returns `EffectSizeResult` with `.value`, `.ci`, `.interpretation` |
| `hedges_g` | Hedges' g | Small-sample corrected Cohen's d |
| `odds_ratio` | Odds ratio | For paired binary outcomes |
| `relative_improvement` | Percentage change | Simple relative improvement of A over B |

Interpretation thresholds for Cohen's d / Hedges' g: negligible (< 0.2), small (0.2-0.5), medium (0.5-0.8), large (>= 0.8).

### Power Analysis

Plan your evaluation size before running experiments.

| Function | Purpose |
|----------|---------|
| `sample_size_for_mean_diff` | Minimum n to detect a continuous score difference (Cohen's d) |
| `sample_size_for_proportion_diff` | Minimum n to detect a difference between two proportions |
| `compute_power` | Power achieved at a given n and effect size |

`sample_size_for_mean_diff` and `sample_size_for_proportion_diff` return a `PowerAnalysisResult` with `.required_sample_size`, `.achieved_power`, `.effect_size`, `.alpha`, and `.desired_power`.

`compute_power` returns a float between 0 and 1.

---

## Caching

LLM inference is expensive. The cache layer avoids redundant API calls.

### MemoryCache

In-memory LRU cache. Keys are derived from `(prompt, model, temperature)`. Suitable for single-process runs.

```python
from rotalabs_eval.cache.memory import MemoryCache

cache = MemoryCache(max_entries=10000)
cache.put(prompt="Hello", model="gpt-4o", temperature=0.0, response={"text": "Hi"})
hit = cache.get(prompt="Hello", model="gpt-4o", temperature=0.0)
```

### DiskCache

SQLite-backed persistent cache with TTL and cache versioning. Keys incorporate prompt, model name, provider, temperature, max tokens, and extra parameters.

- **TTL**: Entries expire after `ttl_hours` (configurable).
- **Cache versioning**: Bump `cache_version` in `CacheConfig` to invalidate old entries without deleting the database.
- **Policies**: `READ_WRITE` (default), `READ_ONLY`, `WRITE_ONLY`, `DISABLED`.

---

## Agent Evaluation

The `agents` module provides structured evaluation for agentic AI systems.

### Trajectory Evaluation

Evaluate multi-turn agent conversations.

- **`Trajectory`** -- A sequence of `Turn` objects, each with a `TurnRole` (USER, ASSISTANT, SYSTEM, TOOL), content, and optional `Action` and `Observation`.
- **`Action`** -- Represents what the agent did: `ActionType` (RESPONSE, TOOL_CALL, THINK, DELEGATE, TERMINATE), content, and parameters.
- **`Observation`** -- The result of an action: content, success flag, and optional error.

Key trajectory metrics:

| Metric | What it measures |
|--------|------------------|
| `goal_completion` | Whether the agent achieved its goal |
| `trajectory_efficiency` | Ratio of optimal to actual turns |
| `tool_call_accuracy` | Whether tool calls match the reference sequence |
| `action_sequence_f1` | F1 over predicted vs. reference action sets |

### Tool Use Evaluation

Evaluate how well agents use tools.

- **`ToolCall`** -- A single tool invocation with name, parameters, result, and success flag.
- **`ToolCallSequence`** -- An ordered list of `ToolCall` objects for a task.

Key tool use metrics:

| Metric | What it measures |
|--------|------------------|
| `tool_selection_accuracy` | Jaccard similarity of predicted vs. reference tool sets |
| `tool_order_accuracy` | LCS-based ordering accuracy |
| `tool_param_accuracy` | Parameter key/value matching accuracy |
| `tool_efficiency` | Ratio of optimal to actual tool call count |
| `tool_error_recovery` | How well the agent recovers from tool errors |
| `tool_call_f1` | Precision, recall, and F1 for tool call sets |

### Debate Evaluation

Evaluate multi-agent debate sessions.

- **`Argument`** -- A single argument with `DebateRole` (PROPONENT, OPPONENT, MEDIATOR, JUDGE) and `ArgumentType` (CLAIM, SUPPORT, COUNTER, CONCESSION, SYNTHESIS, CLARIFICATION).
- **`DebateRound`** -- A list of arguments within a single round.
- **`DebateSession`** -- The complete debate: topic, agents, rounds, verdict, and consensus flag.

Key debate metrics:

| Metric | What it measures |
|--------|------------------|
| `consensus_reached` | Whether the debate reached consensus |
| `argument_diversity` | Variety of argument types used |
| `contribution_balance` | Entropy-based balance of contributions across agents |
| `debate_progression` | Whether argument types follow valid transitions |
| `debate_outcome_accuracy` | Whether the predicted outcome matches the reference |
| `argument_quality` | Weighted composite of relevance, coherence, evidence, and response quality |

---

## Metric Registry

The registry provides a central lookup for all metrics, both built-in and custom.

### Automatic Registration

Use the `@register_metric` decorator on any `Metric` subclass. The class's `.name` attribute becomes the lookup key:

```python
from rotalabs_eval.metrics.base import Metric, MetricResult, register_metric

@register_metric
class MyMetric(Metric):
    name = "my_metric"

    def compute(self, predictions, references, **kwargs):
        ...
```

### MetricRegistry Singleton

`MetricRegistry` is a singleton that merges the global `@register_metric` registry with custom registrations:

```python
from rotalabs_eval.metrics.registry import MetricRegistry

registry = MetricRegistry()
metric = registry.get("exact_match")       # Returns an ExactMatchMetric instance
names = registry.list_metrics()             # Returns sorted list of all metric names
```

### Custom Metric Factory

For simple scoring functions, use `create_custom_metric` instead of writing a full class:

```python
from rotalabs_eval.metrics.custom import create_custom_metric

def length_match(preds, refs):
    return [1.0 if len(p) == len(r) else 0.0 for p, r in zip(preds, refs)]

LengthMatchMetric = create_custom_metric("length_match", length_match)

registry = MetricRegistry()
registry.register("length_match", LengthMatchMetric)
```
