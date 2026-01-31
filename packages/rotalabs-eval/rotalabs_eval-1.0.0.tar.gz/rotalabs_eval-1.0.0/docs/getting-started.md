# Getting Started

## Installation

### Basic Installation

```bash
pip install rotalabs-eval
```

### With Optional Dependencies

```bash
# OpenAI inference client
pip install rotalabs-eval[openai]

# Ollama inference client
pip install rotalabs-eval[ollama]

# Sentence-transformer embeddings (BERTScore, semantic metrics)
pip install rotalabs-eval[embeddings]

# PySpark distributed orchestrator
pip install rotalabs-eval[spark]

# Dask distributed orchestrator
pip install rotalabs-eval[dask]

# Ray distributed orchestrator
pip install rotalabs-eval[ray]

# MLflow experiment tracking
pip install rotalabs-eval[tracking]

# Weights & Biases experiment tracking
pip install rotalabs-eval[wandb]

# Visualization (matplotlib, plotly, seaborn)
pip install rotalabs-eval[viz]

# Development tools (pytest, ruff, black, mypy)
pip install rotalabs-eval[dev]

# All optional dependencies
pip install rotalabs-eval[all]
```

## Core Dependencies

The base package requires:

- `pandas>=2.0.0`
- `numpy>=1.24.0`
- `scipy>=1.10.0`
- `scikit-learn>=1.3.0`
- `tiktoken>=0.5.0`
- `tqdm>=4.65.0`
- `pyyaml>=6.0`
- `requests>=2.28.0`

## Basic Usage

### 1. Evaluate with Lexical Metrics

```python
from rotalabs_eval.metrics.lexical import ExactMatchMetric, F1Metric

predictions = [
    "The capital of France is Paris",
    "Python is a programming language",
    "The Earth orbits the Sun",
]
references = [
    "Paris is the capital of France",
    "Python is a programming language",
    "The Earth revolves around the Sun",
]

# Exact match
em = ExactMatchMetric()
em_result = em.compute(predictions, references)
print(f"Exact Match: {em_result.value:.3f}")
# Exact Match: 0.333

# Token-level F1
f1 = F1Metric()
f1_result = f1.compute(predictions, references)
print(f"F1 Score: {f1_result.value:.3f}")
# F1 Score: 0.833

# Per-example scores are available
print(f"Per-example F1: {f1_result.per_example_scores}")
```

### 2. Compare Two Models

```python
import numpy as np
from rotalabs_eval.statistics import bootstrap_ci, paired_ttest, cohens_d

# Scores from two models on the same test set
model_a_scores = np.array([0.85, 0.90, 0.78, 0.92, 0.88, 0.76, 0.95, 0.82, 0.91, 0.87])
model_b_scores = np.array([0.80, 0.85, 0.75, 0.88, 0.82, 0.72, 0.90, 0.78, 0.86, 0.83])

# Bootstrap confidence interval for Model A
point_estimate, (ci_lower, ci_upper), se = bootstrap_ci(
    model_a_scores, confidence_level=0.95, n_iterations=1000, seed=42
)
print(f"Model A: {point_estimate:.3f} [{ci_lower:.3f}, {ci_upper:.3f}] (SE={se:.4f})")

# Paired t-test for significance
sig_result = paired_ttest(model_a_scores, model_b_scores, alpha=0.05)
print(f"Paired t-test: p={sig_result.p_value:.4f}, significant={sig_result.significant}")

# Effect size
effect = cohens_d(model_a_scores, model_b_scores)
print(f"Cohen's d: {effect.value:.3f} ({effect.interpretation})")
```

### 3. Use the Metric Registry

```python
from rotalabs_eval.metrics.registry import MetricRegistry

registry = MetricRegistry()

# List all available metrics
print(registry.list_metrics())
# ['bleu', 'contains', 'exact_match', 'f1', 'length_ratio', 'rouge_l', ...]

# Get a metric by name
bleu = registry.get("bleu")
result = bleu.compute(
    predictions=["The cat sat on the mat"],
    references=["The cat is sitting on the mat"],
)
print(f"BLEU: {result.value:.3f}")

# Get a metric with configuration
bleu_2gram = registry.get("bleu", max_n=2)
```

## Next Steps

- Read [Core Concepts](concepts.md) to understand the evaluation methodology
- Follow [Basic Evaluation](tutorials/basic-evaluation.md) for a detailed walkthrough
- See [API Reference](api/core.md) for full documentation
