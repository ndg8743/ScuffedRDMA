# vLLM TPU: A New Unified Backend Supporting PyTorch and JAX on TPU

**Source URL:** https://vllm.ai/blog/vllm-tpu

**Date Fetched:** 2026-04-12

## Overview

vLLM has released a new TPU backend powered by tpu-inference, a hardware plugin that unifies JAX and PyTorch under a single lowering path. This represents a significant advancement in open-source TPU inference performance.

## Key Achievements

The new architecture delivers impressive performance gains:
- **3.6x throughput improvement** for Llama 3.1-8B on v6e-1
- **2.1x improvement** for Llama 3.1-70B on v6e-8
- Nearly **5x performance gains** compared to the February 2025 prototype

## Core Technical Innovations

**Unified Lowering Path**: Rather than maintaining separate PyTorch/XLA and JAX implementations, the system now lowers all models through JAX, achieving "~20% higher throughput" without code modifications.

**Ragged Paged Attention V3**: The enhanced attention kernel now supports arbitrary model specifications, quantization dtypes, and tensor parallelism configurations, while increasing throughput by approximately 10% over the previous version.

**SPMD Programming Model**: Single Program, Multi-Data replaces the previous multi-worker approach, enabling "advanced optimizations like overlapping communication with computation."

## Supported Features

**Current capabilities include:**
- Prefix caching and chunked prefill
- Multimodal inputs
- Structured decoding
- Speculative decoding (Ngram)
- Quantization support
- TPU generations: Trillium (v6e) and v5e

## Getting Started

Installation is simplified with a single command: `pip install vllm-tpu`

The system automatically prioritizes TPU-optimized models from tpu-inference before falling back to standard vLLM implementations.

## Future Roadmap

Planned enhancements include MoE and MLA kernels, RL integrations, and distributed serving capabilities across multiple hosts.
