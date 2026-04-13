# Efficiently Serving Fine-Tuned Models with vLLM on AWS

**Source URL:** https://vllm.ai/blog/multi-lora

**Date Fetched:** 2026-04-12

## Overview

This blog post from the vLLM team describes how AWS and the vLLM community collaborated to optimize multi-LoRA (Low-Rank Adaptation) inference for Mixture of Experts (MoE) models. The solution enables multiple customized AI models to share a single GPU efficiently.

## Key Problem

Organizations running multiple specialized models face the challenge of paying for unused GPU capacity. For instance, five customers each using only 10% of a dedicated GPU could be consolidated into one efficiently shared resource through multi-LoRA serving.

## Technical Implementation

**Multi-LoRA Basics:**
The approach keeps original model weights frozen while adding small, trainable adapter layers. At inference time, these adapters can be swapped per request, allowing different users' models to share compute resources.

**MoE Architecture Challenge:**
MoE models route tokens to specialized expert networks. Each expert contains two weight projections (`gate_up` and `down`), and each LoRA adapter adds four kernel operations: "shrink and expand" operations for both projections. This creates a significant performance bottleneck in multi-adapter scenarios.

## Optimization Strategies

**Execution Optimizations:**
The team discovered that the Triton compiler was recompiling kernels for each new input length. They resolved this by adding a compiler hint preventing specialization on context-length variables, eliminating unnecessary recompilation overhead.

**Kernel Optimizations:**
- **Split-K strategy**: Distributes summation work across multiple thread groups for better load balancing on "skinny" matrices
- **CTA swizzling**: Reorders thread scheduling to improve L2 cache locality
- **Conditional removal**: Eliminated unnecessary masking operations when matrix dimensions align perfectly with block sizes
- **Weight fusion**: Combined LoRA weight addition with base model weights in a single kernel launch

## Results

Starting from an initial implementation, the team achieved:
- 454% improvement in output tokens per second (OTPS) by vLLM 0.15.0
- 87% reduction in time-to-first-token (TTFT)
- Additional 19% OTPS improvement with AWS-specific tuning for GPT-OSS 20B

The optimizations also benefited dense models, improving Qwen3 32B OTPS by 99%.

## Availability

These improvements are available in vLLM 0.15.0+ for local deployments, with enhanced performance on Amazon SageMaker AI and Amazon Bedrock.
