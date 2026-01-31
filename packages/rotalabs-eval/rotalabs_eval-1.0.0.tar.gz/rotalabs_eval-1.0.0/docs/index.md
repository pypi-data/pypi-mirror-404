# rotalabs-eval

Comprehensive LLM evaluation framework with statistical rigor. Evaluate model outputs using lexical, semantic, LLM-judge, and RAG metrics backed by proper confidence intervals and significance testing.

## What is rotalabs-eval?

rotalabs-eval provides a complete toolkit for evaluating large language model outputs with the statistical rigor required for production decision-making. Key capabilities include:

- **30+ built-in metrics** across lexical, semantic, LLM-judge, RAG, and agent evaluation categories
- **Statistical analysis** with bootstrap confidence intervals, significance tests, effect sizes, and power analysis
- **Distributed execution** via Spark, Dask, and Ray orchestrators for large-scale evaluations
- **Inference management** with OpenAI and Ollama clients, rate limiting, batch processing, and caching
- **Experiment tracking** through MLflow and Weights & Biases integrations
- **Metric registry** for dynamic lookup and custom metric registration

## Package Overview

```
rotalabs_eval/
├── core/           # Configuration, types, results, tasks, exceptions
├── metrics/        # Evaluation metrics
│   ├── lexical     # ExactMatch, F1, BLEU, ROUGE-L, Contains, LengthRatio
│   ├── semantic    # BERTScore, EmbeddingSimilarity
│   ├── llm_judge   # LLMJudge, PairwiseJudge, GEval
│   ├── rag         # ContextRelevance, Faithfulness, AnswerRelevance
│   ├── custom      # User-defined metrics via create_metric()
│   └── registry    # MetricRegistry for dynamic lookup
├── statistics/     # Statistical analysis tools
│   ├── confidence  # bootstrap_ci, analytical_ci_mean, analytical_ci_proportion
│   ├── significance# paired_ttest, mcnemar_test, wilcoxon_signed_rank
│   ├── effect_size # cohens_d, hedges_g, odds_ratio, relative_improvement
│   └── power       # sample_size_for_mean_diff, compute_power
├── inference/      # LLM API clients
│   ├── openai      # OpenAI inference client
│   ├── ollama      # Ollama inference client
│   ├── batch       # Batch inference executor
│   └── rate_limiter# Token-bucket rate limiter
├── cache/          # Response caching
│   ├── disk        # DiskCache (store/lookup)
│   └── memory      # MemoryCache (put/get)
├── orchestrator/   # Distributed execution
│   ├── local       # Single-machine executor
│   ├── async_executor # Async executor
│   ├── spark       # PySpark orchestrator
│   ├── dask        # Dask distributed orchestrator
│   └── ray         # Ray orchestrator
├── agents/         # Agent evaluation
│   ├── trajectory  # GoalCompletion, TrajectoryEfficiency, ToolCallAccuracy
│   ├── tool_use    # ToolSelectionAccuracy, ToolParameterAccuracy, ToolErrorRecovery
│   └── debate      # ConsensusReached, ArgumentDiversity, DebateOutcomeAccuracy
├── tracking/       # Experiment tracking
│   ├── mlflow      # MLflow integration
│   └── wandb       # Weights & Biases integration
├── reporting/      # Results reporting and visualization
│   ├── results     # Result formatting
│   ├── html        # HTML report generation
│   └── viz         # Plotting utilities
└── utils/          # Helpers, cost estimation, tiktoken cache
```

## Available Metrics

### Lexical Metrics

| Metric | Class | Description |
|--------|-------|-------------|
| `exact_match` | `ExactMatchMetric` | Binary exact match after normalization |
| `f1` | `F1Metric` | Token-level F1 score (SQuAD-style) |
| `bleu` | `BLEUMetric` | BLEU score with configurable n-gram order |
| `rouge_l` | `ROUGELMetric` | ROUGE-L using longest common subsequence |
| `contains` | `ContainsMetric` | Substring containment check |
| `length_ratio` | `LengthRatioMetric` | Prediction-to-reference length ratio |

### Semantic Metrics

| Metric | Class | Description |
|--------|-------|-------------|
| `bertscore` | `BERTScoreMetric` | BERTScore using contextual embeddings |
| `embedding_similarity` | `EmbeddingSimilarityMetric` | Cosine similarity of sentence embeddings |

### LLM Judge Metrics

| Metric | Class | Description |
|--------|-------|-------------|
| `llm_judge` | `LLMJudgeMetric` | LLM-as-judge with customizable rubric |
| `pairwise_judge` | `PairwiseJudgeMetric` | Pairwise comparison between two responses |
| `g_eval` | `GEvalMetric` | G-Eval framework for multi-aspect scoring |

### RAG Metrics

| Metric | Class | Description |
|--------|-------|-------------|
| `context_relevance` | `ContextRelevanceMetric` | LLM-judged context relevance to query |
| `faithfulness` | `FaithfulnessMetric` | Answer faithfulness to retrieved context |
| `answer_relevance` | `AnswerRelevanceMetric` | Answer relevance to the original query |
| `context_relevance_embedding` | `ContextRelevanceEmbeddingMetric` | Embedding-based context relevance |
| `answer_relevance_embedding` | `AnswerRelevanceEmbeddingMetric` | Embedding-based answer relevance |

## Statistical Tools

| Function | Module | Description |
|----------|--------|-------------|
| `bootstrap_ci` | `statistics.confidence` | Percentile bootstrap confidence interval |
| `bootstrap_ci_bca` | `statistics.confidence` | Bias-corrected accelerated bootstrap CI |
| `analytical_ci_mean` | `statistics.confidence` | Analytical CI for mean (t-distribution) |
| `analytical_ci_proportion` | `statistics.confidence` | CI for proportion (Wilson/normal/Clopper-Pearson) |
| `paired_ttest` | `statistics.significance` | Paired t-test for matched samples |
| `mcnemar_test` | `statistics.significance` | McNemar's test for paired binary outcomes |
| `wilcoxon_signed_rank` | `statistics.significance` | Non-parametric paired test |
| `bootstrap_significance` | `statistics.significance` | Bootstrap-based significance test |
| `cohens_d` | `statistics.effect_size` | Cohen's d effect size |
| `hedges_g` | `statistics.effect_size` | Hedges' g (small-sample corrected) |
| `odds_ratio` | `statistics.effect_size` | Odds ratio for paired binary outcomes |
| `sample_size_for_mean_diff` | `statistics.power` | Required sample size for detecting a mean difference |
| `compute_power` | `statistics.power` | Statistical power at a given sample size |

## Quick Links

- [Getting Started](getting-started.md) - Installation and first steps
- [Core Concepts](concepts.md) - Understanding evaluation methodology
- [API Reference](api/core.md) - Detailed API documentation
- [Tutorials](tutorials/basic-evaluation.md) - Step-by-step guides
