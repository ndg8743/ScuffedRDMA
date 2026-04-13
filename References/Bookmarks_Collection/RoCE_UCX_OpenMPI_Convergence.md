# Putting RoCE to Work: Troubleshooting High Performance Ethernet

**Source URL:** https://www.stackhpc.com/roce-ucx-openmpi.html

**Date Fetched:** 2026-04-12

**Published:** August 30, 2024  
**Author:** Bertie Thorpe

## Overview

This article explores Remote Direct Memory Access (RDMA) over Converged Ethernet (RoCE) and the challenges encountered when configuring OpenMPI to use specific network devices. The investigation reveals how RoCE provides cost-effective RDMA capabilities compared to traditional InfiniBand, while highlighting configuration complexities in modern HPC environments.

## Key Findings

**RoCE's Advantages:**
RoCE leverages existing Ethernet infrastructure, reducing deployment costs while achieving near-InfiniBand latencies. The unified transport simplifies network management by combining RDMA and standard IP traffic.

**The Problem:**
When attempting to restrict OpenMPI to specific network devices using the UCX library's `UCX_NET_DEVICES` parameter, unexpected behavior occurred. Settings were ignored, and RDMA traffic continued regardless of configurations intended to force TCP usage.

**Root Cause:**
The article identifies that OpenMPI's Modular Component Architecture (MCA) has competing components for RDMA support. The build configuration (using `--without-verbs`) disabled the openib BTL, creating ambiguity in how network devices were selected. "UCX PML is the preferred mechanism for running over RoCE-based networks" as of version 4.0.0.

**Solution:**
Adding specific flags to mpirun resolved the issue:
```
-mca pml_ucx_tls any -mca pml_ucx_devices any
```

This enabled proper device selection and confirmed correct protocol usage through network traffic monitoring.

## Conclusion

Successful RoCE deployment requires careful attention to MPI stack configuration, network monitoring, and documented reference implementations.
