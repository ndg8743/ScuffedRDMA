# Reimplementing FlashAttention for Performance and Giggles

**Source URL:** https://aminediro.com/posts/flash_attn/
**Date accessed:** 2026-03-11

---

**Author:** Amine Dirhoussi
**Published:** December 4, 2025

## Overview

This comprehensive technical article explores the step-by-step implementation and optimization of FlashAttention, a transformative algorithm for efficient attention computation in transformers. Rather than simply applying the published algorithm, the author reconstructs the engineering journey that led from v1 to v2, using GPU profiling tools to identify bottlenecks and iteratively improve performance.

## Core Problem

Traditional attention mechanisms face a critical bottleneck: computing attention scores creates a quadratic memory footprint. For a sequence length of 8,192 with head dimension of 64, the intermediate attention matrix requires gigabytes of GPU memory. As the author notes, "the attention mechanism has a critical bottleneck: **quadratic memory complexity**" in the naive implementation.

## Key Technical Insights

**GPU Memory Hierarchy:** The article emphasizes that modern GPUs have compute throughput far exceeding memory bandwidth. The solution exploits this asymmetry by restructuring computation to maximize time spent computing rather than accessing slow memory.

**Online Softmax:** Rather than computing the complete softmax after generating all attention scores, the algorithm computes it incrementally using running statistics (maximum values and sums). This enables "exact attention without materializing the entire attention matrix in memory."

**Tiling Strategy:** Breaking computation into blocks that fit within fast on-chip SRAM (shared memory) dramatically reduces main memory traffic. The algorithm loads small tiles of Q, K, and V once, processes them, and writes results back.

## Implementation Journey

**v1 Implementation:** Faithfully follows the original 2022 paper but exhibits critical inefficiencies. Profiling reveals "11.58 GB reads and 5.54 GB writes" due to repeatedly reloading accumulators from main memory in the inner loop.

**v2 Implementation:** Reorganizes the loop structure to parallelize across query blocks rather than key blocks. This keeps query data and accumulators in fast registers throughout execution, reducing main memory traffic by approximately 93%.

**v2 Transpose Variant:** Discovers that the matrix multiplication generates severe shared memory bank conflicts. By pre-transposing the key matrix, the kernel achieves 145% improvement over v1 and eliminates most bank conflicts.

## Hardware Limitations Encountered

The RTX 2070 (Turing architecture, SM 7.5) lacks efficient tensor core support for the operations Triton generates, forcing reliance on slower CUDA cores rather than specialized matrix multiply units. The author candidly acknowledges needing newer hardware to fully validate optimization strategies.

## Practical Takeaways

The article demonstrates three foundational principles for efficient GPU programming:

1. Understanding the memory hierarchy and designing algorithms to exploit fast, local memories
2. Minimizing expensive operations like transcendentals that bypass high-throughput compute units
3. Iterative profiling and optimization guided by actual hardware metrics rather than theoretical models

The journey from theory to implementation reveals why subsequent FlashAttention versions (v2, v3, v4) introduced specific changes—each addresses real performance bottlenecks discovered through measurement, not speculation.
