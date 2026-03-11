# Train With Mixed Precision - NVIDIA Docs

**Source URL:** https://docs.nvidia.com/deeplearning/performance/mixed-precision-training/index.html
**Date accessed:** 2026-03-11

## Overview

This NVIDIA documentation guide covers mixed precision training methods for deep neural networks, combining different numerical formats in computational workloads to achieve performance improvements while maintaining accuracy.

## Key Concepts

**Mixed Precision Definition**: The approach combines "half-precision (FP16) data with single-precision (FP32) representations, using lower precision where beneficial and full precision where necessary for numerical stability."

### Primary Benefits

The documentation identifies three main advantages:

1. **Memory Efficiency**: FP16 uses 16 bits versus 32 for FP32, enabling larger models and batch sizes
2. **Bandwidth Improvement**: Reduced memory transfers accelerate data-limited operations
3. **Computational Speed**: GPUs with Tensor Core support deliver significantly faster math operations in reduced precision

## Technical Implementation

### Loss Scaling Strategy

A critical technique outlined involves scaling loss values before backpropagation. The process multiplies the loss by factor S, allowing gradients to occupy more of the FP16 representable range, then divides by 1/S after backward propagation to restore proper weight update magnitudes.

**Dynamic Loss Scaling**: The system starts with a large scaling factor, increases it every N iterations (default 2000) without overflow, and decreases it immediately upon detecting gradient overflow (Inf/NaN values).

### Tensor Core Optimization

Shape constraints require:
- Matrix multiplication: all dimensions (M, N, K) must be multiples of 8 for FP16
- Convolution: input and output channels must be multiples of 8

## Framework Support

**Automatic Mixed Precision (AMP)** is now available in:
- TensorFlow (1.14+)
- PyTorch (with APEX extension)
- MXNet (1.5+)

These implementations automate FP16 casting, loss scaling, and master weight management, often requiring minimal code modifications.

## Performance Results

Documentation provides benchmark examples showing speedups ranging from 1.1x to 3.5x across various architectures including BERT, GNMT, ResNet-50, and SSD models.
