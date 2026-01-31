# rotalabs-eval

Comprehensive LLM evaluation framework with statistical rigor. Run evaluations with confidence intervals, significance tests, and effect size analysis.

## Overview

`rotalabs-eval` provides a complete toolkit for evaluating LLM outputs across multiple dimensions: lexical accuracy, semantic similarity, RAG quality, and LLM-as-judge assessments. It includes built-in statistical analysis so you can make data-driven decisions about model performance with proper uncertainty quantification.

### Key Features

- **20+ Built-in Metrics**: Exact match, F1, BLEU, ROUGE-L, BERTScore, embedding similarity, LLM-as-judge, RAG faithfulness, and more
- **Statistical Rigor**: Bootstrap confidence intervals, paired significance tests, effect sizes, and power analysis
- **Multiple LLM Providers**: OpenAI and Ollama support out of the box
- **Agent Evaluation**: Multi-turn trajectory scoring, tool use accuracy, and multi-agent debate analysis
- **Flexible Backends**: Run locally, or scale with Spark, Dask, or Ray (optional)
- **Experiment Tracking**: MLflow and Weights & Biases integrations
- **Response Caching**: SQLite disk cache and in-memory LRU cache to avoid redundant API calls
- **Cost Tracking**: Token counting and cost estimation for major LLM providers

## Installation

### Basic Installation

```bash
pip install rotalabs-eval
```

### With Optional Dependencies

```bash
# OpenAI inference
pip install rotalabs-eval[openai]

# Local models via Ollama
pip install rotalabs-eval[ollama]

# Embedding-based metrics (BERTScore, semantic similarity)
pip install rotalabs-eval[embeddings]

# Distributed backends
pip install rotalabs-eval[spark]
pip install rotalabs-eval[dask]
pip install rotalabs-eval[ray]

# Experiment tracking
pip install rotalabs-eval[tracking]    # MLflow
pip install rotalabs-eval[wandb]       # Weights & Biases

# Visualization
pip install rotalabs-eval[viz]

# Everything
pip install rotalabs-eval[all]

# Development
pip install rotalabs-eval[dev]
```

## Quick Start

### Define and Run an Evaluation

```python
import pandas as pd
from rotalabs_eval import ModelConfig, ModelProvider, MetricConfig, EvalTask
from rotalabs_eval.orchestrator import LocalOrchestrator

# Prepare your dataset
data = pd.DataFrame({
    "question": ["What is Python?", "What is Rust?"],
    "reference": ["A programming language", "A systems programming language"],
})

# Configure the model
model_config = ModelConfig(
    provider=ModelProvider.OPENAI,
    model_name="gpt-4o-mini",
    api_key="sk-...",  # or set OPENAI_API_KEY env var
    temperature=0.0,
)

# Define the evaluation task
task = EvalTask(
    task_id="qa_eval",
    prompt_template="Answer concisely: {question}",
    reference_column="reference",
)

# Choose metrics
metrics = [
    MetricConfig(name="exact_match"),
    MetricConfig(name="f1"),
    MetricConfig(name="rouge_l"),
]

# Run
orchestrator = LocalOrchestrator()
result = orchestrator.run(data, task, model_config, metrics)
print(result)
```

### Use Individual Metrics

```python
from rotalabs_eval.metrics.lexical import ExactMatchMetric, F1Metric, BLEUMetric

exact = ExactMatchMetric()
print(exact.compute("hello world", "hello world"))  # MetricResult(score=1.0)

f1 = F1Metric()
print(f1.compute("the cat sat", "the cat"))  # MetricResult(score=0.8)

bleu = BLEUMetric()
print(bleu.compute("the cat is on the mat", "the cat sat on the mat"))
```

### Statistical Comparisons

```python
import numpy as np
from rotalabs_eval.statistics import (
    bootstrap_ci,
    paired_ttest,
    cohens_d,
)

model_a_scores = np.array([0.82, 0.75, 0.91, 0.78, 0.85])
model_b_scores = np.array([0.79, 0.71, 0.88, 0.80, 0.83])

# Confidence interval for Model A's mean
ci = bootstrap_ci(model_a_scores, confidence_level=0.95)
print(f"Model A: {np.mean(model_a_scores):.3f} [{ci[0]:.3f}, {ci[1]:.3f}]")

# Is the difference significant?
sig = paired_ttest(model_a_scores, model_b_scores)
print(f"p-value: {sig.p_value:.4f}, significant: {sig.significant}")

# How large is the effect?
effect = cohens_d(model_a_scores, model_b_scores)
print(f"Cohen's d: {effect.value:.3f} ({effect.interpretation})")
```

### Power Analysis

```python
from rotalabs_eval.statistics.power import sample_size_for_mean_diff

# How many examples do I need to detect a 0.05 improvement?
result = sample_size_for_mean_diff(
    effect_size=0.05,
    std_dev=0.15,
    alpha=0.05,
    power=0.80,
)
print(f"Required sample size: {result.sample_size}")
```

### Agent Evaluation

```python
from rotalabs_eval.agents.trajectory import GoalCompletionMetric
from rotalabs_eval.agents.tool_use import ToolSelectionAccuracyMetric

# Evaluate goal completion from a trajectory
goal_metric = GoalCompletionMetric()
result = goal_metric.compute(
    trajectory="User: Book a flight to NYC\nAssistant: I've booked your flight to NYC for tomorrow.",
    reference="Book a flight",
)
print(f"Goal completion: {result.score}")

# Evaluate tool selection accuracy
tool_metric = ToolSelectionAccuracyMetric()
result = tool_metric.compute(
    predicted_tools=["search", "book_flight"],
    expected_tools=["search", "book_flight", "confirm"],
)
print(f"Tool selection accuracy: {result.score:.2f}")
```

### Custom Metrics

```python
from rotalabs_eval.metrics.custom import create_custom_metric

# Create a metric from a function
def word_count_ratio(prediction: str, reference: str) -> float:
    pred_words = len(prediction.split())
    ref_words = len(reference.split())
    return min(pred_words, ref_words) / max(pred_words, ref_words) if ref_words else 0.0

WordCountRatio = create_custom_metric("word_count_ratio", word_count_ratio)
metric = WordCountRatio()
print(metric.compute("hello world", "hello beautiful world"))
```

### Caching Responses

```python
from rotalabs_eval.cache import MemoryCache, DiskCache

# In-memory LRU cache
cache = MemoryCache(max_size=1000)
cache.put("key1", {"response": "cached value"})
print(cache.get("key1"))

# Persistent SQLite cache
disk_cache = DiskCache(cache_dir="./eval_cache")
disk_cache.put("key1", {"response": "persisted value"})
```

## Available Metrics

### Lexical Metrics
| Metric | Class | Description |
|--------|-------|-------------|
| `exact_match` | `ExactMatchMetric` | Exact string match (with optional normalization) |
| `f1` | `F1Metric` | Token-level F1 score |
| `bleu` | `BLEUMetric` | BLEU score for n-gram overlap |
| `rouge_l` | `ROUGELMetric` | ROUGE-L using longest common subsequence |
| `contains` | `ContainsMetric` | Check if reference appears in prediction |
| `length_ratio` | `LengthRatioMetric` | Length ratio between prediction and reference |

### Semantic Metrics
| Metric | Class | Description |
|--------|-------|-------------|
| `bert_score` | `BERTScoreMetric` | Contextual embedding similarity |
| `embedding_similarity` | `EmbeddingSimilarityMetric` | Cosine similarity of sentence embeddings |

### LLM-as-Judge Metrics
| Metric | Class | Description |
|--------|-------|-------------|
| `llm_judge` | `LLMJudge` | Single-answer grading with LLM |
| `pairwise_judge` | `PairwiseJudge` | Pairwise comparison between two models |
| `g_eval` | `GEval` | G-Eval framework for multi-aspect evaluation |

### RAG Metrics
| Metric | Class | Description |
|--------|-------|-------------|
| `context_relevance` | `ContextRelevanceMetric` | Relevance of retrieved context to query |
| `faithfulness` | `FaithfulnessMetric` | Whether answer is grounded in context |
| `answer_relevance` | `AnswerRelevanceMetric` | Relevance of answer to the question |

## Statistical Analysis

### Confidence Intervals
- `bootstrap_ci()` - Percentile bootstrap
- `bootstrap_ci_bca()` - Bias-corrected and accelerated bootstrap
- `analytical_ci_mean()` - t-distribution CI for means
- `analytical_ci_proportion()` - Wilson/Normal/Clopper-Pearson for proportions

### Significance Tests
- `paired_ttest()` - Paired t-test for continuous metrics
- `mcnemar_test()` - McNemar's test for binary outcomes
- `wilcoxon_signed_rank()` - Non-parametric alternative
- `bootstrap_significance()` - Bootstrap permutation test
- `choose_test()` - Auto-select appropriate test based on data

### Effect Sizes
- `cohens_d()` - Standardized mean difference
- `hedges_g()` - Small-sample corrected Cohen's d
- `odds_ratio()` - Odds ratio for binary outcomes
- `relative_improvement()` - Percentage improvement

### Power Analysis
- `sample_size_for_mean_diff()` - Required n for detecting mean differences
- `sample_size_for_proportion_diff()` - Required n for proportion differences
- `compute_power()` - Statistical power for a given sample size

## Development

```bash
# Clone and install in development mode
git clone https://github.com/rotalabs/rotalabs-eval.git
cd rotalabs-eval
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Format code
black src/ tests/
ruff check src/ tests/
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- PyPI: https://pypi.org/project/rotalabs-eval/
- GitHub: https://github.com/rotalabs/rotalabs-eval
- Documentation: https://rotalabs.github.io/rotalabs-eval/
- Website: https://rotalabs.ai
- Contact: research@rotalabs.ai
