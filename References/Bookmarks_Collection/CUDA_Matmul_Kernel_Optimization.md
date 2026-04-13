# How to Optimize a CUDA Matmul Kernel for cuBLAS-like Performance: A Worklog
**Source URL:** https://siboehm.com/articles/22/CUDA-MMM
**Date Fetched:** 2026-04-12

**Author:** Simon Boehm  
**Date:** December 2022

## Overview

This comprehensive worklog documents the iterative optimization of a matrix multiplication (SGEMM) kernel written in CUDA, progressing from a naive implementation achieving 1.3% of cuBLAS performance to a highly optimized version reaching 93.7% performance.

## Key Findings

The author demonstrates how understanding GPU hardware characteristics drives performance improvements:

- **Memory Coalescing:** Aligning global memory accesses allows the GPU to combine multiple thread requests into fewer transactions, improving throughput from 15GB/s to 110GB/s
- **Shared Memory Caching:** Utilizing fast on-chip memory reduces redundant global memory accesses
- **Arithmetic Intensity:** Computing more results per thread reduces memory-to-computation ratios, enabling compute-bound kernels
- **Multi-level Tiling:** Block-level, warp-level, and thread-level tiling expose parallelism across different GPU execution units

## Kernel Progression

| Kernel | GFLOPs/s | % of cuBLAS |
|--------|----------|-----------|
| Naive | 309.0 | 1.3% |
| Global Memory Coalescing | 1,986.5 | 8.5% |
| Shared Memory Caching | 2,980.3 | 12.8% |
| 2D Blocktiling | 15,971.7 | 68.7% |
| Vectorized Access | 18,237.3 | 78.4% |
| Warptiling | 21,779.3 | 93.7% |

## Critical Optimizations

**Global Memory Coalescing:** Threads that are in the same warp have to access consecutive addresses for hardware to combine requests efficiently.

**Shared Memory Efficiency:** Reducing per-block SMEM usage maintains occupancy, allowing more blocks per streaming multiprocessor.

**Register Blocking:** Explicit caching of SMEM values in registers reduces memory instruction pressure and enables compiler optimizations.

## Hardware Insights

The analysis reveals that matrix multiplication on modern GPUs is fundamentally memory-bound for practical sizes. The author calculates that even with peak 30 TFLOPs compute and 768GB/s bandwidth, computation dominates by 10x, making bandwidth optimization paramount.

## Notable Challenges

- **Autotuning:** Optimal parameters vary significantly by GPU architecture, requiring exhaustive parameter search
- **Compiler Dependencies:** Modern compilers enable sophisticated optimizations (loop unrolling, vectorization) automatically when given proper hints
- **Occupancy vs. Performance:** Higher occupancy isn't always beneficial; sometimes lower occupancy with better register locality performs better

## Conclusion

The worklog emphasizes that optimizing SGEMM iteratively is one of the best ways to deeply understand the performance characteristics of the hardware. The author notes power-law diminishing returns: reaching 80% peak performance required two weekends, while the final 14% took four additional weekends.
