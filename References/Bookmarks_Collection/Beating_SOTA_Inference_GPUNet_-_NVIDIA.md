# Beating SOTA Inference Performance on NVIDIA GPUs with GPUNet

**Source URL:** https://developer.nvidia.com/blog/beating-sota-inference-performance-on-nvidia-gpus-with-gpunet/
**Date accessed:** 2026-03-11

---

**Authors:** Satish Salian, Carl (Izzy) Putterman, Linnan Wang, and Krzysztof Kudrynski
**Publication Date:** August 30, 2022
**Category:** Computer Vision / Video Analytics

## Overview

## Key Content Summary

### What is GPUNet?

GPUNet represents "a class of convolutional neural networks designed to maximize the performance of NVIDIA GPUs using NVIDIA TensorRT." The models achieve performance improvements up to 2x faster than competing architectures like EfficientNet-X and FBNet-V3.

### Development Methodology

The architecture was created using novel neural architecture search (NAS) techniques. A specialized AI agent "automatically orchestrates hundreds of GPUs in the Selene supercomputer without any intervention from domain experts," enabling efficient architecture design tailored to GPU hardware constraints.

### Technical Architecture

GPUNet implements an eight-stage design based on EfficientNet-V2, incorporating searchable variables including:
- Operation types
- Kernel sizes and strides
- Layer counts
- Activation functions
- Channel filters
- Squeeze-excitation mechanisms

Each candidate model encodes as a 41-element integer vector enabling systematic evaluation across latency budgets.

### Deployment Ready

The reported latencies "include all the performance optimization available in the shipping version of TensorRT, including fused kernels, quantization, and other optimized paths," making models immediately deployable without additional optimization work.

### Resources

Models are available through PyTorch Hub, NGC checkpoints, and Google Colab instances for developer experimentation.
