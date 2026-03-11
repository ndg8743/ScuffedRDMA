# GPUDirect Storage Support for IBM Storage Scale

**Source URL:** https://www.ibm.com/docs/en/storage-scale/5.2.3?topic=architecture-gpudirect-storage-support-storage-scale
**Date Accessed:** 2026-03-11

## Overview

IBM Storage Scale incorporates NVIDIA's GPUDirect Storage (GDS) to establish "a direct path between GPU memory and storage," significantly reducing latency and CPU overhead. The technology leverages RDMA protocols over InfiniBand or RoCE fabrics to transfer data directly from NSD server palepools to GPU buffers.

## Key Benefits

GDS proves particularly valuable in scenarios where "the CPU stands as a bottleneck to overall system performance." By eliminating intermediate buffer copies in system memory, the solution delivers enhanced data transfer rates, decreased latency, and reduced CPU utilization.

## Implementation Requirements

The solution requires NVIDIA CUDA installation on client systems and necessitates "high speed Ethernet fabric with GDS capable hardware." I/O operations initiated through `cuFileRead()` or `cuFileWrite()` CUDA APIs execute as RDMA requests on NSD servers.

## Compatibility Mode

When direct RDMA pathways aren't viable, GDS transitions to compatibility mode, handling operations through buffered I/O without performance advantages. This occurs for files under 4096 bytes, encrypted files, memory-mapped files, compressed files, and other specific scenarios.

## Operational Limitations

IBM Storage Scale does not support GDS with asynchronous "poll" mode operations, concurrent buffered reads alongside GDS reads, or files utilizing data tiering technologies.
