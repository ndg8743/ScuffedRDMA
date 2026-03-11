# The vLLM MoE Playbook: A Practical Guide to TP, DP, PP and Expert Parallelism

**Source URL:** https://rocm.blogs.amd.com/software-tools-optimization/vllm-moe-guide/README.html
**Date Accessed:** 2026-03-11

**Title:** The vLLM MoE Playbook: A Practical Guide to TP, DP, PP and Expert Parallelism

**Published:** November 24, 2025

**Authors:** Pin Siang Tan, Hongxia Yang, Peng Sun, Andy Luo, Jun Kang Chow, Ye Hur Cheong, Tun Jian Tan

**Source:** ROCm Blogs

---

## Overview

This comprehensive guide addresses the challenge of efficiently deploying large Mixture-of-Experts (MoE) models like DeepSeek-R1 using vLLM's parallelism strategies. The authors explain that selecting the correct approach prevents critical issues such as duplicated KV caches consuming excessive memory or communication overhead that reduces throughput.

## Core Concepts

The guide covers three fundamental parallelism strategies:

**Tensor Parallelism (TP):** Shards individual model layers across GPUs with synchronized results through AllReduce communication. Optimal for single-request processing across multiple devices.

**Data Parallelism (DP):** Creates multiple complete model replicas, each processing different requests independently. Increases throughput for concurrent requests without inter-GPU communication.

**Pipeline Parallelism (PP):** Distributes model layers sequentially across GPUs. vLLM optimizes this by processing multiple requests concurrently through pipeline stages, reducing idle GPU time compared to vanilla implementations.

## Critical Misconceptions Addressed

The document clarifies four major misunderstandings:

1. **Expert Parallelism isn't standalone**—the `--enable-expert-parallel` flag modifies communication patterns and must combine with TP or DP.

2. **DP Attention differs fundamentally from traditional DP**—it operates within a single model replica with partitioned KV cache and inter-GPU communication, unlike independent DP replicas.

3. **MoE models contain two expert types**—routed experts activate conditionally (distributed with EP), while shared experts always activate (treated as standard MLPs).

4. **TP+EP uses AllReduce, not AllToAll**—AllToAll communication requires `dp_size > 1`, which TP-only configurations lack.

## Key Technical Insights

**KV Cache Management:** For Multi-Latent Attention (MLA) models like DeepSeek-R1, TP configurations duplicate full KV cache across ranks because the single KV head cannot be sharded by dimension. DP+EP avoids this by partitioning KV cache across GPU ranks, enabling 8× larger batch sizes.

**Expert Activation Density:** The benefit of the EP flag correlates with activation density—ultra-sparse models (<1%) perform better without EP, while denser models (>3%) benefit from AllToAll communication efficiency.

**Memory Requirements:** DeepSeek-R1 benchmarks show DP=8+EP uses similar total memory as DP=8 without EP, but enables partitioned KV cache for higher effective concurrency.

## Performance Benchmarks

Testing on 8× AMD Instinct MI300X GPUs revealed:

- **Low concurrency (≤128 requests):** TP=8+EP delivers 40-86% higher throughput
- **High concurrency (≥512 requests):** DP=8+EP achieves 16-47% higher throughput
- **Crossover point:** Between 256-512 concurrent requests
- **Ultra-sparse models:** EP=0 outperforms EP=1 by 7-12% (Llama-4-Maverick example)

## Decision Framework

The authors provide four key decision questions:

1. **Concurrency level:** Low/moderate favors TP; high favors DP
2. **Expert activation density:** <1% suggests EP=0; >3% suggests EP=1
3. **Attention architecture:** MLA/MQA models require EP=1 with DP for correctness
4. **Hardware constraints:** Single-node deployments prefer TP or DP over PP

## Configuration Recommendations

For **DeepSeek-R1 (MLA, 671B):**
- Interactive chat: `--tensor-parallel-size 8 --enable-expert-parallel`
- Batch processing: `--data-parallel-size 8 --enable-expert-parallel`

For **Llama-4-Maverick (0.78% density, 17B):**
- Interactive chat: `--tensor-parallel-size 8` (no EP flag)
- Batch processing: `--data-parallel-size 8` (no EP flag)

## Parallelism Combination Constraints

Expert Parallelism only activates when `TP_SIZE × DP_SIZE > 1`. Pipeline Parallelism combinations with EP require AITER (Advanced Inter-node Tensor-parallelism Engine Runtime) for stability with large MoE models. Supported combinations include TP+EP, DP+EP, and TP+DP+EP, but PP+EP requires careful configuration.

## Conclusion

The guide emphasizes that no single configuration suits all scenarios. The optimal strategy depends on workload concurrency, model architecture characteristics, and hardware capabilities. AMD Instinct MI300X's 192GB HBM3 and high-bandwidth XGMI enable single-node deployments of massive models while supporting both latency-optimized and throughput-optimized configurations.
