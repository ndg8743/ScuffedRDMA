# Accelerate Model Training on OpenShift AI with NVIDIA GPUDirect RDMA

**Source URL:** https://developers.redhat.com/articles/2025/04/29/accelerate-model-training-openshift-ai-nvidia-gpudirect-rdma
**Date accessed:** 2026-03-11

**Authors:** Antonin Stefanutti, Erwan Gallen, Benjamin Schmaus
**Publication Date:** April 29, 2025

## Overview

This article demonstrates how to leverage NVIDIA GPUDirect RDMA technology to significantly improve distributed machine learning model training performance on Red Hat OpenShift AI. The authors address a critical bottleneck in scaled deep learning: communication overhead between GPUs.

## Key Problem

When training large language models across multiple GPUs using frameworks like PyTorch FSDP or DeepSpeed ZeRO, substantial peer-to-peer communication occurs. The standard OpenShift OVN-Kubernetes network CNI plugin, designed for general-purpose pod communication, creates a performance bottleneck that can severely degrade training efficiency.

## Solution Architecture

The solution integrates several components:

- **NVIDIA Network Operator** - Automates deployment of networking drivers and device plugins
- **NVIDIA GPU Operator** - Manages GPU software components and enables GPUDirect RDMA
- **NVIDIA NCCL** - Implements collective operations, detecting optimal GPU interconnects
- **Kubeflow Training Operator** - Configures distributed PyTorch training jobs
- **SR-IOV Operator** - Enables virtual function attachments for network devices
- **NVIDIA Spectrum-X Platform** - Provides high-speed Ethernet/InfiniBand interconnects using BlueField-3 SuperNICs

## Configuration Requirements

The implementation requires:

1. **NicClusterPolicy** resource defining RDMA shared device plugins
2. **MacvlanNetwork** for RoCE (RDMA over Converged Ethernet)
3. **CRI-O container engine** configuration to increase pinned memory limits for non-root users via Machine Configuration Operator
4. **ClusterPolicy** updates enabling GPU driver RDMA support

## LLM Fine-Tuning Example

The article provides a complete implementation example using:
- **Model:** Meta-Llama 3.1 8B Instruct
- **Dataset:** GSM8K
- **Techniques:** LoRA with FSDP, Flash Attention, Liger Kernels

Key configuration modifications include adding secondary network attachments and RDMA resource specifications to PyTorchJob definitions.

## Performance Results

Testing on 2 Dell PowerEdge R760xa nodes (each with 2 NVIDIA A40 GPUs):

- **Baseline (OVN network):** 5 hours completion time
- **TCP/Socket on Spectrum-4 Ethernet:** 2 hours 30 minutes
- **GPUDirect RDMA:** 1 hour 40 minutes (**~3x speedup**)

The RDMA configuration shifts the workload from I/O-bound to compute-bound, enabling additional optimization benefits from fused kernel implementations.

## Technical Insights

NCCL logs confirm proper configuration with messages like: "GPU Direct RDMA Enabled for GPU 1 / HCA 1" and channels operating via "NET/IB/1/GDRDMA."

Testing with varying batch sizes (32-112) showed constant completion times under RDMA, indicating compute-bound behavior rather than network saturation.

## Broader Implications

This architecture pattern extends beyond training to distributed model serving and other GPU-accelerated workloads. The partnership between NVIDIA and Red Hat enables enterprise-grade AI/ML platforms combining hardware acceleration with Kubernetes orchestration capabilities.
