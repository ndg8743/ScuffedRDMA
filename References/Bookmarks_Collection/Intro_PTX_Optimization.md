# Intro to PTX Optimization: Part 1

**Source URL:** https://dhmnr.sh/posts/intro-to-ptx-optimization/

**Date Fetched:** 2026-04-12

## Overview

This comprehensive guide introduces PTX (Parallel Thread Execution), NVIDIA's intermediate GPU instruction set, and explains when and why developers should use it.

## Core Concepts

**What is PTX?**
PTX serves as a virtual instruction set that gets JIT-compiled to SASS (the actual hardware binary). The key advantage is portability—"PTX written today can run on future GPUs without recompiling."

**Basic Structure**
PTX instructions follow a pattern of opcode, modifiers, and operands. Memory operations explicitly specify their space (global, shared, local, constant), and registers are declared upfront with types like `.reg .f32 %f<8>` for floating-point registers.

## Practical Applications

The article emphasizes that PTX matters most for controlling hardware features the compiler won't expose:

1. **Async Memory Operations** - Using `cp.async` instructions for software pipelining, overlapping memory transfers with computation
2. **Cache Control** - Streaming hints (`ld.cs`, `st.wt`) for data that's accessed once
3. **Tensor Core Access** - Direct `mma` instructions provide documented thread-to-element mapping that WMMA's fragment API doesn't offer

## Real-World Impact: Attention Kernels

The most striking example involves fused attention. WMMA's `fragment.x[]` provides element values but not their matrix positions. Row-wise operations like softmax require round-tripping through shared memory. PTX's `mma` instruction documents exact layouts, keeping computation in registers—yielding **2.7x speedup** on RTX 4090.

## Key Takeaway

PTX isn't for everyday coding. Use it for bottleneck optimization after profiling, particularly for async copies, warp-level operations, and Tensor Core control where high-level APIs fall short.
