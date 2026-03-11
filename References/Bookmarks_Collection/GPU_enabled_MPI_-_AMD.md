# GPU-enabled Message Passing Interface

**Source URL:** https://instinct.docs.amd.com/projects/gpu-cluster-networking/en/latest/how-to/gpu-enabled-mpi.html
**Date Accessed:** 2026-03-11

## Overview

This documentation from AMD's GPU Systems and Infrastructure covers enabling Message Passing Interface (MPI) for GPU clusters. The guide explains how to configure ROCm-aware Open MPI to leverage GPU capabilities for distributed computing.

## Key Technologies

### PeerDirect & RDMA
The AMD kernel driver exposes remote direct memory access through PeerDirect interfaces, enabling network interface cards to directly access GPU device memory for high-speed data transfers.

### UCX Framework
Described as "an open source, cross-platform framework designed to provide a common set of communication interfaces," UCX serves as the standard communication library for InfiniBand and RoCE networks.

## Two Main Configuration Approaches

### 1. UCX-based Implementation (InfiniBand/RoCE)

The guide provides step-by-step installation instructions for:
- UCX library with ROCm support
- Open MPI compiled with UCX and ROCm flags
- Optional UCC library for collective GPU operations

Performance benchmarks show inter-GPU bandwidth reaching approximately 150 GB/sec for messages over 67 MB on MI250 systems.

### 2. libfabric Implementation (Other Networks)

For networks like HPE Slingshot, the documentation recommends libfabric. A caveat notes that "shared memory communication between processes on the same node...has fundamental support for GPU memory" but uses staging buffers, resulting in lower-than-peak performance for device-to-device transfers.

## Practical Testing

Both approaches support OSU Micro Benchmarks for performance evaluation, with configuration examples for single-node and multi-node execution.
