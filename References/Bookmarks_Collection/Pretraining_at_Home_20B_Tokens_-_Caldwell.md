# Pretraining at Home: Optimizing LLM Training

**Source URL:** https://hackbot.dad/writing/pretraining-at-home/
**Date accessed:** 2026-03-11

**Author:** Shane Caldwell
**Date:** November 23, 2025
**Topic:** Optimizing Llama 3.2 1B model pretraining from 222 hours to 12 hours

## Overview

Caldwell documents his journey optimizing a language model pretraining pipeline to achieve results "within a day without going broke." The article explains how he reduced training time for 20 billion tokens from an estimated 222 hours to approximately 12 hours using a single node with eight H100 GPUs.

## Key Motivation

The author argues that while large-scale pretraining is economically prohibitive (claiming an 8B model costs "$12,672" for minimal training), small models offer educational value. He wanted to regain "modeling intuition" about architectural decisions by training a 1B parameter model personally.

## Technical Approach

**Model Choice:** Llama-3.2-1B architecture with fresh initialization

**Compute:** Modal cloud platform with H100 GPUs and free storage through 2026

**Data:** 20 billion tokens from FineWeb-EDU's 100BT subset via HuggingFace streaming

## Optimization Pipeline

### Initial Baseline
- **MFU:** 15%
- **Time estimate:** 222.2 hours

### Single GPU Optimizations

1. **BF16 precision** → 40% MFU (83.8 hours)
2. **Flash Attention 2** → 55% MFU (60.6 hours)
3. **Batch size 4** → 85% MFU (39.2 hours)

### Multi-GPU Scaling
- 8 H100s with distributed data parallelism
- Final MFU: 40%
- Final time: ~11 hours

## Key Technical Insights

**Model FLOPs Utilization (MFU):** Caldwell explains MFU calculation: "6 times the number of parameters in your model" per token during training, derived from forward pass (2 FLOPs) and backward pass (4 FLOPs).

**NVIDIA Specifications:** The author discovered H100 datasheet values include sparsity multipliers, requiring interpretation: dense BF16 performance is 989.5 TFLOPs, not the 1979 TFLOPs shown with 2:4 sparsity.

**Profiling Tools:** PyTorch profiler with TensorBoard visualization proved more useful than raw trace files for identifying "CPU overhead" bottlenecks.

## Notable Challenges

- Naive attention implementation caused out-of-memory errors with minibatch sizes >1
- Initial validation loss calculations dominated training time
- Distributed training required careful rank-based logging to avoid redundant computation

## Future Work

The author acknowledges remaining optimizations (pre-tokenization, `torch.compile`, Triton kernels) but prioritizes data quality validation in subsequent posts.
