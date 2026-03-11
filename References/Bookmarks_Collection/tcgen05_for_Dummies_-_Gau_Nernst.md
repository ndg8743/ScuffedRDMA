# tcgen05 for Dummies

**Source URL:** https://gau-nernst.github.io/tcgen05/
**Date accessed:** 2026-03-11

---

**Author:** gau-nernst
**Published:** December 21, 2025

## Overview

This comprehensive tutorial explores programming NVIDIA's Blackwell GPU Tensor Cores using PTX instructions, achieving "98%" of CuBLAS performance on a 4096³ matrix multiplication problem.

## Core Topics Covered

### 1. **Foundational Concepts**

The article begins by explaining tiled matrix multiplication, showing how modern implementations divide problems into blocks that leverage specialized hardware. The author notes that "each generation of NVIDIA GPUs has their own set of PTX instructions to perform load and compute."

### 2. **Key Hardware Components**

**Tensor Memory Accelerator (TMA):**
Enables large-grain data transfers with minimal register overhead, replacing older `cp.async` instructions.

**mbarrier Synchronization:**
Coordinates asynchronous memory operations and tracks completion through arrival/transmission counts.

**Tensor Memory:**
A 128×512 element dedicated storage for 32-bit accumulation results.

### 3. **Progressive Optimization Iterations**

| Version | Approach | Performance |
|---------|----------|-------------|
| v1 | Basic tcgen05 with 16B TMA | 254-252 TFLOPS |
| v2 | 128-byte swizzling | 681-695 TFLOPS |
| v3 | Pipelining | 939.61 TFLOPS |
| v4 | Warp specialization | 1208.83 TFLOPS |
| v5 | 2-SM MMA | 1302.29 TFLOPS |
| v6 | Persistent kernel | 1475.93 TFLOPS |

### 4. **Key Technical Insights**

**Swizzling Benefits:**
While swizzling prevents bank conflicts, the author observes that performance gains stem partly from using wider (128-byte) TMA tiles rather than just conflict avoidance.

**Warp Specialization:**
Dedicating specific warps to TMA issuance, MMA computation, and epilogue operations eliminates branch divergence overhead.

**2-SM MMA:**
Allows cooperative computation across threadblock clusters, doubling the `MMA_M` dimension to 256.

**Persistent Kernels:**
Launch exactly one threadblock per SM, enabling each to process multiple output tiles sequentially and overlapping epilogue computation with MMA operations.

## Notable Design Patterns

The author emphasizes shared memory layout requirements: "each 8x16B tile must be contiguous" for proper MMA operation, necessitating unconventional tensor layouts compared to simpler algorithms.

## Challenges Highlighted

- Limited publicly available Blackwell tutorials at publication time
- Complex synchronization between asynchronous TMA and MMA components
- Shared memory layout constraints for swizzled operations
- Coordinating multiple producer-consumer pairs in persistent kernels

## Code Availability

Complete source code is available on GitHub, with progressive versions demonstrating incremental optimizations.

## Author's Conclusions

The author suggests Blackwell Tensor Core programming offers a "somewhat small" design space but enables intuitive tile-level thinking. However, mixing Tensor Core operations with general CUDA kernels (like in attention mechanisms) presents synchronization challenges warranting further investigation.
