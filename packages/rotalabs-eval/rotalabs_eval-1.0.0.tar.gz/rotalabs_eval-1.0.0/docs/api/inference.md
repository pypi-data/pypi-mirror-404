# Inference

LLM inference engines for OpenAI and Ollama with rate limiting and batch processing.

## Base

### InferenceRequest

::: rotalabs_eval.inference.base.InferenceRequest
    options:
      show_source: true

### InferenceResponse

::: rotalabs_eval.inference.base.InferenceResponse
    options:
      show_source: true

### InferenceEngine

::: rotalabs_eval.inference.base.InferenceEngine
    options:
      show_source: true

## OpenAI

### OpenAIEngine

::: rotalabs_eval.inference.openai.OpenAIEngine
    options:
      show_source: true

## Ollama

### OllamaEngine

::: rotalabs_eval.inference.ollama.OllamaEngine
    options:
      show_source: true

## Rate Limiting

### TokenBucketRateLimiter

::: rotalabs_eval.inference.rate_limiter.TokenBucketRateLimiter
    options:
      show_source: true

### AsyncRateLimiter

::: rotalabs_eval.inference.rate_limiter.AsyncRateLimiter
    options:
      show_source: true

## Batch Processing

### create_engine

::: rotalabs_eval.inference.batch.create_engine
    options:
      show_source: true

### run_batch_inference

::: rotalabs_eval.inference.batch.run_batch_inference
    options:
      show_source: true
