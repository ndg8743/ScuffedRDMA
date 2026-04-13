# LLM Inference Optimization: Key Insights on KV Cache

**Source URL:** https://pub.towardsai.net/llm-inference-optimization-730b2d718a44  
**Date Fetched:** 2026-04-12

## Core Concepts

The article explains that LLM inference occurs in two distinct phases:

### Prefill Stage
The prompt is tokenized and processed through the model. This phase is compute-bound where GPU resources are well-utilized since multiple operations can happen in parallel.

### Decode Stage
Tokens are generated auto-regressively, one at a time. This phase is memory-bound where compute remains underutilized, creating the primary bottleneck.

## KV Cache Optimization

During inference, Key and Value embeddings need to be generated for each token in the prompt and Attention operations performed on the same. Rather than recalculating these for every forward pass, KV caching stores them, enabling significant speedups—typically 2-4X improvements.

Notably, Query vectors aren't cached because only the latest token's query is needed for attention calculations. The cache size formula accounts for batch size, sequence length, number of heads, and layers, making memory management critical for large models.

## Supporting Techniques

### Batching
Processing multiple requests simultaneously improves throughput. Continuous batching dynamically adds and removes requests after each iteration rather than waiting for entire batches to complete.

### PagedAttention
Allocates KV cache in blocks dynamically rather than contiguous chunks, achieving near-zero waste in KV cache memory.

### Flash Attention
Optimizes memory I/O by restructuring softmax calculations through tiling, reducing memory usage from quadratic to linear in sequence length.

### MQA/GQA
Share Key-Value pairs across attention heads, dramatically reducing cache requirements while maintaining quality.
