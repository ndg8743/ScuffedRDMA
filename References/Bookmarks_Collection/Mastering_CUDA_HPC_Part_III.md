# Mastering CUDA and High-Performance Computing, Part III

**Source URL:** https://softwarefrontier.substack.com/p/mastering-cuda-and-high-performance-204
**Date accessed:** 2026-03-11

---

**Authors:** Lorenzo Bradanini and Lorenzo Tettamanti
**Published:** March 4, 2026

## Overview

This comprehensive technical article explores GPU execution beyond kernel-level abstractions, examining how CUDA submissions traverse from host to hardware through multiple architectural layers.

## Key Concepts

### The Submission Model

The authors reframe GPU performance fundamentally: *"A kernel is not computation. It is a submission"* – a descriptor assembled by drivers and serialized across PCIe/NVLink buses to firmware-managed command processors. Launch latency remains constant (~5-15 microseconds) regardless of grid size because the dominant cost comes from the submission pathway, not computation itself.

### Runtime to Driver Transition

When invoking kernels via triple-chevron syntax, the CUDA Runtime API (`libcudart`) resolves fat binary function pointers containing SASS (Shader Assembly) for multiple compute capabilities. The driver performs several tasks:

- Resolves appropriate cubin objects embedded in `.nv_fatbin` sections
- Applies JIT compilation when necessary, caching results in `~/.cache/nvidia/ComputeCache/`
- Constructs parameter buffers respecting ABA alignment rules (max 8-byte natural alignment)
- Creates launch descriptors with grid/block dimensions and shared memory allocation

### Front-End Architecture

The GPU's **GigaThread Engine** maintains hardware work queues, dynamically dispatching thread blocks to Streaming Multiprocessors only when resources permit. This prevents deadlock and ensures forward progress at block granularity.

### Resource-Constrained Residency

Block scheduling depends on the most restrictive of four resources:

- Register consumption (65,536 per SM on Ampere)
- Shared memory allocation (up to 164 KB on Ampere)
- Maximum resident threads (2,048 per SM)
- Maximum blocks per SM (32 on Ampere)

Register spilling to local memory occurs when variables exceed file capacity, incurring expensive DRAM latency penalties.

### Memory Hierarchy

The article distinguishes between pageable and pinned host memory:

- **Pageable memory** (malloc/new) requires driver-managed bounce buffers, forcing triple-copy overhead
- **Pinned memory** (`cudaMallocHost`) enables direct DMA access without staging, critical for overlapping transfers with computation

### Interconnect Reality

PCIe 4.0 x16 provides ~32 GB/s effective bandwidth (theoretical max); NVLink 3.0 (A100) delivers 600 GB/s. Data movement physics creates immutable throughput floors: transferring 20 GB at 25 GB/s costs minimum 0.8 seconds regardless of kernel optimization.

### Stream Orchestration

Streams represent logical command queues enabling potential parallelism. The scheduler decides dynamically whether to overlap operations from different streams based on SM capacity, warp slot availability, and copy engine utilization. Explicit `cudaStreamWaitEvent` synchronization prevents resource contention.

## Practical Implications

The authors emphasize multi-layer optimization: register pressure cascades upward, reducing warp counts and destroying latency-hiding capability. Memory allocation strategy (pinned vs. pageable) fundamentally constrains achievable throughput.

Kernel performance cannot be optimized in isolation—submission orchestration, firmware scheduling, and microarchitectural resource allocation collectively determine real-world performance.
