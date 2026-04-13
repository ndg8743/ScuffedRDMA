# Extracting Hidden States from vLLM

**Source URL:** https://vllm.ai/blog/extract-hidden-states

**Date Fetched:** 2026-04-12

## Overview

PR #33736 (vLLM v0.18.0+) introduced a system for extracting hidden states directly from vLLM, enabling more efficient speculative decoding model training.

## Key Concepts

**Hidden States**: Internal intermediate representations of token sequences that provide insight into a model's internal state and are heavily used in speculative decoding.

**Speculative Decoding**: Combines a large "verifier" model with a small "draft" model. The draft produces candidate tokens that the verifier validates in parallel, potentially achieving 2-5x speedups in memory-bound scenarios.

## Design Approach

The system addresses several critical requirements:

1. **Performance**: Hidden states can be massive (e.g., 268 MB for Qwen3-8B with 8k tokens). Serializing directly in response bodies isn't practical, so the system uses disk or alternative storage methods.

2. **Memory Management**: Hidden states require VRAM allocation with careful handling for concurrent requests, chunked prefills, and preemption to prevent out-of-memory errors.

3. **Zero Overhead**: The feature must not impact vLLM's standard operations since most deployments don't need hidden states extraction.

4. **Flexibility**: Different use cases require different output methods—offline training caches to disk while online training needs efficient device-to-device transfers.

## Implementation Strategy

The solution leverages existing vLLM infrastructure:

- Reuses Eagle-3 speculative decoding pathways for hidden state routing
- Employs the extensible KV Connector API (used for Prefill/Decode Disaggregation)
- Stores hidden states in a dummy draft model's attention layers
- Manages memory using vLLM's paged memory system

## Usage

Users can extract hidden states via command-line server setup with `--speculative_config` and `--kv_transfer_config` flags, specifying which model layers to extract and where to store the data.

## Future Development

Planned improvements include integration with the Speculators library (v0.5.0), asynchronous write optimization, and advanced device-to-device connectors for multi-node environments.
