# Accelerating Transformers with NVIDIA cuDNN 9

**Source URL:** https://developer.nvidia.com/blog/accelerating-transformers-with-nvidia-cudnn-9/
**Date accessed:** 2026-03-11

---

**Author:** Matthew Nicely
**Published:** May 24, 2024

## Overview

NVIDIA's cuDNN library has achieved significant performance improvements for transformer-based models. The library reached "1.2 PFLOPS in FP8" on H200 GPUs and delivered a 1.15x speedup for Llama2 70B LoRA fine-tuning tasks.

## Key Performance Achievements

**Scaled Dot Product Attention (SDPA)** represents a critical optimization area. Benchmarks show cuDNN 9's BF16 implementation runs "up to 2x faster than PyTorch's eager implementation," with FP8 achieving "up to 3x faster" performance. These improvements enable longer sequence lengths and reduced training iterations.

A practical demonstration used NeMo with Transformer Engine across eight H200 nodes:
- Baseline (cuDNN disabled): 1x
- BF16 SDPA: 1.11x speedup
- FP8 SDPA: 1.15x speedup

## Technical Flexibility

The cuDNN attention implementation supports various configurations through graph-based operations. Users can apply causal masking, adjust head dimensions, and insert custom pointwise operations between computation stages while maintaining fused-kernel performance benefits.

## Additional Features in cuDNN 9

- **Mixed precision support** for matrix operations with INT8/FP16 combinations
- **Improved error reporting** with categorized codes and programmatic access
- **Hardware forward compatibility** enabling future GPU support without library upgrades
- **Streamlined installation** via pip and simplified Linux package management
