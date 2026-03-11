# NVIDIA Tensor Core Evolution: From Volta To Blackwell

**Source URL:** https://newsletter.semianalysis.com/p/nvidia-tensor-core-evolution-from-volta-to-blackwell

**Date Accessed:** 2026-03-11

---

**Authors:** Dylan Patel and Kimbo Chen
**Publication Date:** June 23, 2025

## Overview

This technical article examines the progression of NVIDIA's Tensor Core architectures across five generations, from Volta through Blackwell. The analysis explores how architectural innovations have driven performance improvements faster than Moore's Law, enabling accelerated AI and deep learning capabilities.

## Key Technical Concepts

### Performance First Principles

- **Amdahl's Law** limits parallelization speedup based on serial execution portions
- **Strong scaling** addresses fixed-problem performance improvements; weak scaling handles larger problems
- Data movement is fundamentally slower because modern DRAM cells operate at tens of nanoseconds while transistors switch at sub-nanosecond speeds

## Architectural Evolution Summary

### Volta (2017)

Introduced the first Tensor Core with half-precision matrix multiply-accumulate (HMMA) instructions, achieving 1024 FLOPs per cycle per SM with warp-scoped operations.

### Turing

Added INT8 and INT4 precision support while maintaining warp-level synchronous MMA operations.

### Ampere

Doubled performance to 2048 dense FLOPs per cycle per SM, introduced asynchronous data copy (cp.async), and implemented warp-level MMA with ldmatrix operations for improved register efficiency.

### Hopper

Implemented warpgroup-level asynchronous MMA (wgmma), thread block clusters, and Tensor Memory Accelerator (TMA) for bulk asynchronous data transfers.

### Blackwell

Introduced fifth-generation Tensor Cores with single-thread semantics, Tensor Memory (TMEM) specialized storage, CTA pair configurations, and support for sub-8-bit data formats including MXFP and NVFP4.

## Memory Hierarchy Evolution

NVIDIA prioritized shared memory expansion over register file growth because "Tensor Core throughput doubled every generation, but global memory load latency didn't decrease and in fact increased."

Blackwell's shared memory remained constant relative to Hopper since tcgen05 MMA can leverage two SMs, effectively doubling capacity per SM.

## Data Type Progression

Generations progressively reduced precision requirements—from 16-bit FP16 to modern 4-bit formats—reflecting deep learning's tolerance for lower precision while improving power efficiency and silicon utilization.
