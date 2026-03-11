# My First Multi-GPU Kernel: Writing All-to-All for AMD MI300X

**Source URL:** https://gau-nernst.github.io/amd-a2a/
**Date accessed:** 2026-03-11

---

**Author:** gau-nernst
**Published:** November 2, 2025

## Overview

This technical article documents the author's experience participating in the AMD Distributed Challenge hosted by GPU MODE, focusing on implementing an all-to-all communication kernel for the AMD MI300X GPU.

## Key Technical Concepts Covered

**Problem Context:**
The author addresses the implementation of "dispatch" and "combine" kernels for Mixture-of-Experts (MoE) models with Expert-Parallelism across multiple GPUs. As explained, "dispatch sends tokens to their respective experts, which are now sharded across GPUs."

**Fundamental Techniques:**

1. **Peer-to-Peer Memory Access:** The author demonstrates how to leverage P2P capabilities, stating that "P2P memory access can be broadly understood as the ability for devices to read from and write to memory of other devices."

2. **Symmetric Memory & Symmetric Heap:** A design pattern where "memory of the same size allocated on each GPU" becomes accessible across all devices, enabling efficient remote memory operations.

3. **Acquire-Release Semantics:** Memory ordering guarantees ensuring "all memory writes prior to the flag store have finished before the flag is set," critical for correct multi-GPU synchronization.

## Development Progression

The author documents seven major versions with measured improvements:

- **Reference implementation:** 93,540 microseconds
- **PyTorch-optimized approach:** 1,311 microseconds (71× improvement)
- **HIP kernel with P2P:** 517 microseconds
- **Final version with work distribution optimization:** 292 microseconds (320× improvement over reference)

## Notable Optimizations

**Kernel Fusion:** Combining the grouped GEMM computation with the combine operation reduced latency significantly.

**Fine-grained Locking:** Switching from coarse-grained (per-rank) to fine-grained (per-token) locks improved synchronization efficiency and enabled better pipelining.

**Work Distribution:** Addressing uneven token distribution across threadblocks through careful loop restructuring ensured more balanced execution.

**Intra-kernel Profiling:** The author developed a custom profiling mechanism using AMD GPU timestamps to identify bottlenecks at the instruction level, enabling targeted optimizations.

## Key Insights

The development process was iterative and non-monotonic. The author notes that "ideas didn't pan out, some implementations were slower than their previous versions," but systematic profiling and analysis guided subsequent improvements. The exact grid size of 304 threadblocks (matching MI300X compute units) produced near 3× speedups for specific kernels, suggesting hardware-specific tuning opportunities.
