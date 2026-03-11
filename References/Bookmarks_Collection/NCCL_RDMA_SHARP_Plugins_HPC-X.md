# NCCL-RDMA-SHARP Plugins - NVIDIA HPC-X Documentation

**Source URL:** https://docs.nvidia.com/networking/display/hpcxv2200/nccl-rdma-sharp+plugins
**Date Accessed:** 2026-03-11

## Overview

This documentation covers NCCL-RDMA-SHARP plugins within NVIDIA's HPC-X Software Toolkit (version 2.20.0). The plugins enable "RDMA and switch-based collectives (SHARP) with NVIDIA's NCCL library."

These plugins replace default inter-node NCCL communication with RDMA-based transports, supporting both point-to-point communication (using IB verbs or UCX) and collective operations (including SHARP collective transport).

## Key Features

**Plugin Control:** The `NCCL_IBEXT_DISABLE` environment variable manages plugin functionality. Setting it to 1 disables the plugin, reverting to native NCCL communication.

## NCCL UCX Plugin

The UCX plugin substitutes "verbs-based inter-node communication routines with UCX-based communication routines."

### Setup Requirements

1. Add plugin directory to library path: `export LD_LIBRARY_PATH=<plugin_install_dir>/lib:$LD_LIBRARY_PATH`
2. Enable UCX: `export NCCL_PLUGIN_P2P=ucx`

### Performance Optimization

For GPU-NIC configurations sharing PCIe infrastructure, GPU Direct RDMA delivers optimal performance through these variables:
- `NCCL_UCX_RNDV_THRESH=0`
- `NCCL_UCX_RNDV_SCHEME=get_zcopy`

Multi-NIC systems require: `NCCL_UCX_TLS=dc,cuda_copy,cuda_ipc`

**Important:** Disable UCX memory type caching with `UCX_MEMTYPE_CACHE=n` when NCCL is built statically.

## NCCL SHARP Plugin

SHARP collective operations activate via:
- `NCCL_COLLNET_ENABLE=1`
- `NCCL_ALGO=CollNet`

**Limitation:** NVIDIA switches support maximum 2 concurrent streaming aggregation flows, requiring careful cluster topology design for multi-GPU, multi-HCA systems.

## Benchmarking

Documentation includes NCCL test examples demonstrating performance validation using the nccl-tests suite, available at the official NVIDIA GitHub repository.
