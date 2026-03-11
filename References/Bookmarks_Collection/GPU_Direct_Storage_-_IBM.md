# GPU Direct Storage Documentation

**Source URL:** https://www.ibm.com/docs/en/scalecontainernative/6.0.0?topic=planning-gpu-direct-storage
**Date accessed:** 2026-03-11

## Overview

This technical documentation covers enabling GPU Direct Storage (GDS) on OpenShift Container Platform with IBM Storage Scale.

## Key Concept

"GPUDirect Storage (GDS) is an NVIDIA technology that enables a direct data path for data transfers between storage devices and GPU memory, bypassing the CPU." This approach enhances system bandwidth, reduces latency, and decreases CPU demand.

## Prerequisites

The setup requires:
- NVIDIA InfiniBand or RoCE networking on the OpenShift cluster
- IBM Storage Scale with RDMA networking enabled
- NVIDIA GPU Operator installed with RDMA support and GDS driver
- GDS enabled on both storage and client clusters

## Configuration Process

The enablement involves eight sequential steps:

1. Scale down the operator pod to zero replicas
2. Identify a core pod from the cluster
3. Unmount all file systems
4. Halt the GPFS daemon across all nodes
5. Configure GDS using `mmchconfig verbsGPUDirectStorage=enable`
6. Restart the GPFS daemon
7. Verify cluster node states
8. Restart the operator pod

## Verification Steps

To validate the configuration:

- Deploy a test pod containing CUDA and GDS tools (gdscheck, gdsio)
- Verify GPFS is accessible within the pod
- Configure CUDA settings, particularly `rdma_dev_addr_list` and `allow_compat_mode`
- Run gdscheck to confirm "IBM Spectrum Scale : Supported"
- Execute gdsio read and write operations for functional testing
