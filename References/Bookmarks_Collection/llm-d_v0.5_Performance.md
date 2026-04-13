# llm-d 0.5: Sustaining Performance at Scale

**Source URL:** https://llm-d.ai/blog/llm-d-v0.5-sustaining-performance-at-scale

**Date Fetched:** 2026-04-12

## Overview

This blog post announces llm-d version 0.5, released February 4, 2026, by engineers from Red Hat, Google, and IBM. The release emphasizes operational stability and cost efficiency alongside performance improvements.

## Key Features

**Developer Experience**
The team implemented reproducible benchmarking with "Research Paper Principle" requirements. They created simplified in-guide benchmarks for distinct user personas: "feature developers" testing code changes, "config tuners" performing parameter exploration, and service owners tracking regressions.

**Hierarchical KV Offloading**
A new storage backend decouples cache capacity from GPU memory by implementing a three-tier hierarchy (GPU, CPU, filesystem). This enables cross-replica cache reuse and maintains throughput under growing concurrency, achieving "13.9x improvement at 250 users" versus GPU-only deployments on Llama-3.1-70B.

**Advanced Scheduling**
Updates include LoRA adapter support with precise prefix caching, unified tokenization pipelines, and dynamic pod discovery for active-active high availability scenarios.

**Resilient Networking**
The UCCL backend in the NIXL layer provides host-driven congestion control, demonstrating "2.4x greater resilience" to network stress compared to baseline transports in evaluated scenarios.

**Autoscaling**
Scale-to-zero capabilities enable cost-efficient handling of intermittent workloads, with specialized activators managing cold starts without dropping requests.

## Performance Results

- **Throughput**: Wide-EP topology achieved ~50k output tokens/second on 16×16 prefill/decode configuration
- **Latency**: Inference scheduling demonstrated 4.5-11k tokens/second throughput with P50 TTFT of 136-157ms, showing "109% higher throughput and 99% lower TTFT vs baseline"
