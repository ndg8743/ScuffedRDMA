# Unified Communication - X Framework Library (UCX)

**Source URL:** https://docs.nvidia.com/networking/display/hpcxv215/unified+communication+-+x+framework+library

**Date Fetched:** 2026-04-12

## Overview

UCX is an open-source acceleration library integrated into Open MPI and OpenSHMEM. According to the documentation, it's "designed to achieve the highest performance for HPC applications" with optimizations for low-overhead communication.

## Key Capabilities

**Supported Transports:**
- InfiniBand (UD, RC, DC, accelerated verbs)
- Shared Memory (KNEM, CMA, XPMEM)
- RoCE and TCP
- CUDA GPU support

**CPU Architectures:** x86, ARM, and PowerPC

## Configuration & Usage

UCX is the default point-to-point layer (pml) in Open MPI and default single-program multiple-data layer (spml) in OpenSHMEM as of v2.1. Users can enable it explicitly with:

```
mpirun --mca pml ucx -mca osc ucx ...
```

## Notable Features

- **Hardware Tag Matching** (ConnectX-5+): Offloads message matching to hardware for improved performance
- **SR-IOV Support**: Enables virtual function provisioning on ConnectX-5 and above
- **Adaptive Routing**: Load-balancing across multiple network paths
- **Multi-Rail**: Leverages multiple active ports for increased throughput
- **CUDA GPU Memory**: Direct GPU memory integration for communication
- **RoCE LAG Support**: Automatic link aggregation detection

## Performance Tuning

The documentation indicates "default UCX settings are already optimized." However, parameters like `UCX_RNDV_THRESH`, `UCX_TLS`, and `UCX_NET_DEVICES` allow customization for specific environments.
