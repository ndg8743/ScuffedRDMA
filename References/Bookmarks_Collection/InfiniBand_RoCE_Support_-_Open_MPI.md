# InfiniBand / RoCE Support in Open MPI

**Source URL:** https://docs.open-mpi.org/en/main/tuning-apps/networking/ib-and-roce.html
**Date accessed:** 2026-03-11

## Overview

This documentation section covers InfiniBand and RoCE (RDMA over Converged Ethernet) device support in Open MPI v6.1.x and later versions.

## Key Points

**Current Support Method:**
In Open MPI v6.1.x, InfiniBand and RoCE devices are supported exclusively through the UCX (Unified Communication X) PML. The previously available `openib` BTL has been removed.

**What is UCX:**
According to the documentation, "UCX is an open-source optimized communication library which supports multiple networks, including RoCE, InfiniBand, uGNI, TCP, shared memory, and others." It automatically selects optimal transports and includes GPU support for CUDA and ROCm providers.

**Default Configuration:**
When UCX support is compiled into Open MPI, it's enabled by default. The system automatically uses the highest-bandwidth network port for inter-node communication and shared memory for intra-node communication.

## Configuration Examples

**Selecting specific network devices:**
Users can specify devices via environment variables (e.g., `UCX_NET_DEVICES=mlx5_0:1`)

**Setting InfiniBand Service Levels:**
Use the `UCX_IB_SL` environment variable with values between 0-15

**RoCE Configuration:**
Specify the Ethernet port and optionally the GID index using UCX environment variables

## Troubleshooting Guidance

The documentation recommends gathering diagnostic information including UCX/OpenFabrics versions, Linux distribution details, output from `ibv_devinfo` and `ifconfig` commands, and memory lock settings before seeking support.
