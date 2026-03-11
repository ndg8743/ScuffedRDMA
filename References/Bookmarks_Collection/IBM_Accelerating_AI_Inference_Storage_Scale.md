# Accelerating AI Inference with IBM Storage Scale

**Source URL:** https://research.ibm.com/blog/accelerating-ai-inference-with-ibm-storage-scale
**Date Accessed:** 2026-03-11

**Publication Date:** November 18, 2025

**Authors:** Yue Zhu, Radu Stoica, Animesh Trivedi, Jonathan Terner, Frank Schmuck, Jeremy Cohn, Christof Schmitt, Anthony Hsu, Guy Margalit, Vasily Tarasov, Swaminathan Sundararaman, Talia Gershon, Vincent Hsu

---

## Overview

This technical article addresses a critical challenge in modern AI inference: managing the computational burden of processing large language models (LLMs). While GPUs receive primary focus in AI discussions, the research team demonstrates that "without the right network and storage infrastructure, today's AI applications would be slow" regardless of GPU sophistication.

## Core Problem: KV Cache Management

Modern transformer-based LLMs generate substantial intermediate data during inference—specifically key (K) and value (V) tensors. The study notes that for Llama3-70B processing 128K input tokens, "the size of KV cache...is about 40GB" with a time-to-first-token (TTFT) of approximately 19 seconds on four H100 GPUs.

The fundamental challenge: GPU memory capacity limitations force discarding cached values to accommodate new requests, eliminating reuse opportunities and forcing redundant recalculation.

## IBM Storage Scale Solution

The researchers propose using IBM Storage Scale as a persistent storage tier specifically designed for KV cache offloading. Key capabilities include:

- **Performance:** "300 GB/s, 13 Million IOPS w/ sub-microsecond latency"
- **Scalability:** Supporting "100K+ nodes"
- **Integration:** Native compatibility with inference frameworks like vLLM and llm-d

## Performance Results

Testing with Llama3-70B demonstrated substantial improvements:

- **DRAM caching:** 23.6x speedup versus recomputation (TTFT: 0.8s)
- **Storage Scale tier:** 8-12x speedup versus recomputation (TTFT: 1.6s)
- **Practical benefit:** Reducing TTFT from 19 seconds to 2 seconds or less at scale

The solution enables "KV cache sharing between hundreds or even thousands of GPU servers," allowing single-GPU-generated caches to benefit entire clusters while "minimizing software complexity for the service operator."
