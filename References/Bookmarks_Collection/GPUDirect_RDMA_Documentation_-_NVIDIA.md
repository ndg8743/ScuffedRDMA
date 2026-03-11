# GPUDirect RDMA 13.2 Documentation

**Source URL:** https://docs.nvidia.com/cuda/gpudirect-rdma/#how-gpudirect-rdma-works
**Date accessed:** 2026-03-11

## Overview

This is the API reference guide for enabling GPUDirect RDMA connections to NVIDIA GPUs on Linux kernel modules.

**Core Technology**: GPUDirect RDMA, introduced in Kepler-class GPUs and CUDA 5.0, enables "a direct path for data exchange between the GPU and a third-party peer device using standard features of PCI Express." Examples include network interfaces, video acquisition devices, and storage adapters.

## Key Capabilities

- Available on both Tesla and Quadro GPUs
- Requires devices to share the same upstream PCI Express root complex
- Supported on Jetson AGX Xavier (CUDA 10.1+), DRIVE AGX Xavier (CUDA 11.2+), and Jetson Orin (CUDA 11.4+) platforms

## How It Works

The technology leverages physical address spaces and PCI BAR (Base Address Register) windows. Traditional approaches use the CPU's MMU for memory-mapped I/O; instead, "the NVIDIA kernel driver exports functions to perform the necessary address translations and mappings."

## Key Design Considerations

**Memory Management**:
- Lazy unpinning optimization minimizes pinning overhead by keeping memory pinned after transfers complete
- Registration caches help optimize repeated memory operations

**Hardware Constraints**:
- GPU BAR space is limited (e.g., 256 MB on Kepler, with 32 MB reserved)
- Large BARs (16GB+) may cause BIOS compatibility issues on older motherboards

**API Evolution**:
- CUDA 6.0 eliminated mandatory peer-to-peer tokens
- CUDA 12.2 introduced persistent mapping APIs due to race condition fixes

## Core APIs

**User-Space Functions**:
- `cuPointerSetAttribute()` — enables synchronization behavior
- `cuPointerGetAttribute()` — retrieves buffer metadata and IDs
- `cuPointerGetAttributes()` — inspects multiple attributes simultaneously

**Kernel-Space Functions**:
- `nvidia_p2p_get_pages()` — pins GPU memory pages
- `nvidia_p2p_put_pages()` — releases pinned pages
- `nvidia_p2p_dma_map_pages()` — maps pages for DMA devices

## Special Considerations

**Synchronization Requirements**: The documentation emphasizes that "only CUDA synchronization and work submission APIs provide memory ordering of GPUDirect RDMA operations." Concurrent GPU kernels and RDMA operations constitute a data race.

**Callback Handling**: When the NVIDIA driver revokes memory access, it invokes a synchronous callback. Drivers must "wait for outstanding DMAs to complete" and call `nvidia_p2p_free_page_table()` rather than `nvidia_p2p_put_pages()`.

**Platform-Specific Differences**: Tegra implementations (Jetson/Drive) require different allocators (`cudaHostAlloc()` instead of `cudaMalloc()`) and simplified kernel APIs without token parameters.

## Recent Updates (CUDA 12.2)

A race condition bug in earlier drivers was fixed, requiring new persistent mapping APIs: `nvidia_p2p_put_pages_persistent()` and `nvidia_p2p_get_pages_persistent()`.

## Additional Resources

The documentation includes sections on lazy unpinning optimization, registration caches, PCI BAR management, and porting guidance for Tegra platforms, plus comprehensive kernel module integration instructions.
