# Metrics

Evaluation metrics for lexical, semantic, LLM-as-judge, and RAG assessment.

## Base

### Metric

::: rotalabs_eval.metrics.base.Metric
    options:
      show_source: true

### MetricResult

::: rotalabs_eval.metrics.base.MetricResult
    options:
      show_source: true

## Lexical

### ExactMatchMetric

::: rotalabs_eval.metrics.lexical.ExactMatchMetric
    options:
      show_source: true

### F1Metric

::: rotalabs_eval.metrics.lexical.F1Metric
    options:
      show_source: true

### BLEUMetric

::: rotalabs_eval.metrics.lexical.BLEUMetric
    options:
      show_source: true

### ROUGELMetric

::: rotalabs_eval.metrics.lexical.ROUGELMetric
    options:
      show_source: true

### ContainsMetric

::: rotalabs_eval.metrics.lexical.ContainsMetric
    options:
      show_source: true

### LengthRatioMetric

::: rotalabs_eval.metrics.lexical.LengthRatioMetric
    options:
      show_source: true

## Semantic

### BERTScoreMetric

::: rotalabs_eval.metrics.semantic.BERTScoreMetric
    options:
      show_source: true

### EmbeddingSimilarityMetric

::: rotalabs_eval.metrics.semantic.EmbeddingSimilarityMetric
    options:
      show_source: true

## LLM Judge

### LLMJudgeMetric

::: rotalabs_eval.metrics.llm_judge.LLMJudgeMetric
    options:
      show_source: true

### PairwiseJudgeMetric

::: rotalabs_eval.metrics.llm_judge.PairwiseJudgeMetric
    options:
      show_source: true

### GEvalMetric

::: rotalabs_eval.metrics.llm_judge.GEvalMetric
    options:
      show_source: true

## RAG

### ContextRelevanceMetric

::: rotalabs_eval.metrics.rag.ContextRelevanceMetric
    options:
      show_source: true

### FaithfulnessMetric

::: rotalabs_eval.metrics.rag.FaithfulnessMetric
    options:
      show_source: true

### AnswerRelevanceMetric

::: rotalabs_eval.metrics.rag.AnswerRelevanceMetric
    options:
      show_source: true

## Custom

### create_custom_metric

::: rotalabs_eval.metrics.custom.create_custom_metric
    options:
      show_source: true

## Registry

### MetricRegistry

::: rotalabs_eval.metrics.registry.MetricRegistry
    options:
      show_source: true
