# Understanding Flash Attention: Writing Triton Kernel Code

**Source URL:** https://alexdremov.me/understanding-flash-attention-writing-the-algorithm-from-scratch-in-triton/
**Date accessed:** 2026-03-11

---

**Author:** Alex Dremov
**Published:** January 12, 2025
**Read time:** 10 minutes
**Tags:** Machine Learning, Algorithms, Code

## Overview

This article explains Flash Attention—a technique that dramatically accelerates the attention mechanism in transformer models—and demonstrates how to implement it using Triton, a Python-based GPU kernel programming tool.

## Key Concepts

**What is Attention?**

The scaled dot-product attention formula is: `Attention(Q, K, V) = softmax(QK^T/√d_k)V`

Naive implementations require O(n²) memory and computation time, where n is sequence length.

**Core Innovation of Flash Attention**

The breakthrough principle involves making "attention algorithms IO-aware—accounting for reads and writes between levels of GPU memory." Modern GPUs have distinct memory types: SRAM (fast, small) and HBM (slower, larger). Data transfers between these aren't free, creating a significant bottleneck.

Flash Attention computes attention in tiles without explicitly materializing the full attention scores matrix. This reduces memory complexity from O(n²) to O(n) and avoids expensive data transfers.

**The Tiled Softmax Algorithm**

Rather than computing the complete softmax across all tokens, Flash Attention processes data in blocks using concatenated softmax rules. When processing new tile data, the algorithm recalculates the maximum and denominator using:

- `m(x) = max(m(x¹), m(x²))`
- `l(x) = e^(m(x¹)-m(x))·l(x¹) + e^(m(x²)-m(x))·l(x²)`

This enables incremental softmax computation without loading the entire sequence.

## Implementation Details

Each GPU job processes:
- One Q tile (single query batch)
- All K and V tiles (iterates through entire key-value sequence)
- Stores one output tile

The Triton kernel accumulates results in FP32 precision for numerical stability, applies masking for variable sequence lengths, and divides by the softmax denominator only at the end.

## Performance Results

Benchmarking showed the Triton implementation significantly outperforms naive approaches. While slightly slower than PyTorch's optimized `scaled_dot_product_attention`, the performance gap remains modest given the custom nature of the implementation.

## Resources

The complete implementation is available on [GitHub](https://github.com/alexdremov/kernels), including tested kernel code and benchmarking utilities.
